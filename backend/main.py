"""
ZHud Backend — FastAPI + WebSocket + SQLite
Manages: player stats, active tables, sessions, notes, notable hands, tilt alerts.
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc

from db import (
    init_db, AsyncSessionLocal,
    PlayerStats, PlayerNote, Session, NotableHand,
)
from behavior import analyze_player
from cluster import run_clustering
from watcher import start_watching
import config as cfg_module
from hero_analysis import analyze_hero
from push_fold import get_recommendation, POSITION_ORDER, POSITION_LABELS

DEFAULT_HH_PATH = str(Path.home() / "AppData" / "Local" / "PokerStars" / "HandHistory")

update_queue: asyncio.Queue = asyncio.Queue()
connected_clients: set[WebSocket] = set()
_observer = None   # watchdog Observer — stored so we can restart it

# ── In-memory state ──────────────────────────────────────────────────────────
_active_tables: dict = {}       # table_name -> {players, game_type, last_hand}
_current_session: dict = {      # lightweight current session tracker
    "id": None,
    "start": None,
    "hands": 0,
    "last_hand": None,
    "game_type": "tournament",
}
_hands_since_cluster = 0
_CLUSTER_INTERVAL = 30
_SESSION_GAP_MIN = 30           # minutes of inactivity = new session
_TILT_ALERT_THRESHOLD = 60      # tilt score to trigger alert


# ─── Broadcast ────────────────────────────────────────────────────────────────

async def _broadcast(data: dict):
    msg = json.dumps(data, ensure_ascii=False)
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


# ─── Session helpers ──────────────────────────────────────────────────────────

async def _record_session_hand(game_type: str):
    global _current_session
    now = datetime.utcnow()

    # Check for session gap
    if _current_session["last_hand"]:
        gap = (now - _current_session["last_hand"]).total_seconds() / 60
        if gap > _SESSION_GAP_MIN:
            await _close_session()

    if _current_session["start"] is None:
        # Start new session
        async with AsyncSessionLocal() as sess:
            new_s = Session(start_time=now, game_type=game_type, hands_count=0)
            sess.add(new_s)
            await sess.flush()
            sid = new_s.id
            await sess.commit()
        _current_session.update({"id": sid, "start": now, "hands": 0, "game_type": game_type})

    _current_session["hands"] += 1
    _current_session["last_hand"] = now

    # Persist hand count every 5 hands
    if _current_session["hands"] % 5 == 0 and _current_session["id"]:
        async with AsyncSessionLocal() as sess:
            result = await sess.execute(select(Session).where(Session.id == _current_session["id"]))
            s = result.scalar_one_or_none()
            if s:
                s.hands_count = _current_session["hands"]
                await sess.commit()


async def _close_session():
    global _current_session
    if _current_session["id"] and _current_session["hands"] > 0:
        async with AsyncSessionLocal() as sess:
            result = await sess.execute(select(Session).where(Session.id == _current_session["id"]))
            s = result.scalar_one_or_none()
            if s:
                s.end_time = datetime.utcnow()
                s.hands_count = _current_session["hands"]
                await sess.commit()
    _current_session.update({"id": None, "start": None, "hands": 0, "last_hand": None})


# ─── Queue processor ──────────────────────────────────────────────────────────

async def _queue_processor():
    global _hands_since_cluster

    while True:
        try:
            update = await asyncio.wait_for(update_queue.get(), timeout=2.0)
        except asyncio.TimeoutError:
            continue

        try:
            if update.get("type") != "hand":
                continue

            player_updates: dict = update["updates"]
            table_name:  str  = update.get("table_name", "")
            game_type:   str  = update.get("game_type", "tournament")
            hand_players: list = update.get("players", [])
            _hands_since_cluster += 1

            # Update active table — use REAL hand time so startup scan of old
            # files doesn't make them appear as "active now"
            hand_time_str: str = update.get("hand_time") or ""
            if table_name:
                _active_tables[table_name] = {
                    "table":      table_name,
                    "game_type":  game_type,
                    "players":    hand_players,
                    "last_hand":  hand_time_str or datetime.utcnow().isoformat(),
                }

            # Session tracking
            await _record_session_hand(game_type)

            # Notable hand detection (grab from any player's delta)
            notable_info = None
            for deltas in player_updates.values():
                notable_info = deltas.pop("_notable", None)
                if notable_info:
                    break
            # Remove from all other players
            for deltas in player_updates.values():
                deltas.pop("_notable", None)

            # Save notable hand
            if notable_info:
                asyncio.create_task(_save_notable_hand(notable_info))

            updated_players = []

            async with AsyncSessionLocal() as session:
                for nickname, deltas in player_updates.items():
                    result = await session.execute(
                        select(PlayerStats).where(PlayerStats.nickname == nickname)
                    )
                    player = result.scalar_one_or_none()

                    if player is None:
                        player = PlayerStats(nickname=nickname)
                        session.add(player)

                    # Rolling VPIP window (tilt detection)
                    vpip_decision = deltas.pop("_vpip_decision", None)
                    if vpip_decision is not None:
                        try:
                            recent = json.loads(player.recent_vpip_json or "[]")
                        except Exception:
                            recent = []
                        recent.append(int(vpip_decision))
                        player.recent_vpip_json = json.dumps(recent[-30:])

                    # Recent hands window (hero analysis + trends)
                    snapshot = deltas.pop("_recent_snapshot", None)
                    if snapshot is not None:
                        window = cfg_module.load().get("recent_window", 50)
                        try:
                            hands_list = json.loads(player.recent_hands_json or "[]")
                        except Exception:
                            hands_list = []
                        hands_list.append(snapshot)
                        player.recent_hands_json = json.dumps(hands_list[-window:])

                    # Apply incremental deltas
                    for stat, delta in deltas.items():
                        current = getattr(player, stat, 0) or 0
                        setattr(player, stat, current + delta)

                    player.last_seen = datetime.utcnow()
                    await session.flush()

                    stats = player.to_stats_dict()
                    analysis = analyze_player(stats)
                    updated_players.append({**stats, **analysis})

                await session.commit()

            for player_data in updated_players:
                await _broadcast({"type": "player_update", "data": player_data})

                # Tilt alert
                tilt = player_data.get("tilt", {})
                if tilt.get("score", 0) >= _TILT_ALERT_THRESHOLD:
                    await _broadcast({
                        "type": "tilt_alert",
                        "data": {
                            "nickname":     player_data["nickname"],
                            "tilt_label":   tilt.get("label", ""),
                            "tilt_score":   tilt.get("score", 0),
                            "recent_vpip":  tilt.get("recent_vpip", 0),
                            "delta":        tilt.get("delta", 0),
                        },
                    })

            # Active table broadcast — send full payload with player stats
            if table_name:
                tables_payload = await _build_active_tables_payload()
                await _broadcast({
                    "type": "active_tables_full",
                    "data": tables_payload,
                })

            # Re-cluster
            if _hands_since_cluster >= _CLUSTER_INTERVAL:
                _hands_since_cluster = 0
                asyncio.create_task(_run_cluster_pass())

        except Exception as exc:
            print(f"[queue] Error: {exc}")
        finally:
            update_queue.task_done()


async def _save_notable_hand(info: dict):
    try:
        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(NotableHand).where(NotableHand.hand_id == info["hand_id"])
            )
            if existing.scalar_one_or_none():
                return
            nh = NotableHand(
                hand_id=info["hand_id"],
                table_name=info.get("table", ""),
                game_type=info.get("game_type", "tournament"),
                players_json=json.dumps(info.get("players", []), ensure_ascii=False),
                summary=info.get("summary", ""),
                actions_json=json.dumps(info.get("actions", []), ensure_ascii=False),
                pot=info.get("pot", 0.0),
                reason=info.get("reason", ""),
                hand_time=datetime.utcnow(),
            )
            session.add(nh)
            await session.commit()
    except Exception as exc:
        print(f"[notable] Error: {exc}")


async def _run_cluster_pass():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PlayerStats).where(PlayerStats.hands_dealt >= 20)
            )
            all_players = result.scalars().all()
        if len(all_players) < 6:
            return
        stats_list = []
        for p in all_players:
            s = p.to_stats_dict()
            a = analyze_player(s)
            stats_list.append({**s, **a, "_db_id": p.id})
        clustered = run_clustering(stats_list)
        async with AsyncSessionLocal() as session:
            for item in clustered:
                if item.get("cluster_id", -1) < 0:
                    continue
                result = await session.execute(select(PlayerStats).where(PlayerStats.id == item["_db_id"]))
                p = result.scalar_one_or_none()
                if p:
                    p.cluster_id = item["cluster_id"]
                    p.cluster_label = item.get("cluster_label", "")
            await session.commit()
        for item in clustered:
            if item.get("cluster_id", -1) >= 0:
                await _broadcast({"type": "cluster_update", "data": {
                    "nickname": item["nickname"],
                    "cluster_id": item["cluster_id"],
                    "cluster_label": item["cluster_label"],
                }})
    except Exception as exc:
        print(f"[cluster] Error: {exc}")


# ─── App lifespan ─────────────────────────────────────────────────────────────

def _resolve_hh_path() -> str:
    """Priority: env var → config file → auto-detect first found → default."""
    env = os.environ.get("HH_PATH", "").strip()
    if env:
        return env
    cfg = cfg_module.load().get("hh_path", "").strip()
    if cfg:
        return cfg
    found = cfg_module.find_hh_dirs()
    if found:
        return found[0]["path"]
    return DEFAULT_HH_PATH


async def _restart_watcher(new_path: str):
    global _observer
    if _observer:
        try:
            _observer.stop()
            _observer.join(timeout=3)
        except Exception:
            pass
    _observer = start_watching(new_path, update_queue)
    print(f"[watcher] Restarted → {new_path}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _observer
    await init_db()
    asyncio.create_task(_queue_processor())
    hh_path = _resolve_hh_path()
    _observer = start_watching(hh_path, update_queue)
    print(f"[server] ZHud backend at http://127.0.0.1:8765")
    yield
    await _close_session()


app = FastAPI(title="ZHud", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── WebSocket ────────────────────────────────────────────────────────────────

async def _build_active_tables_payload() -> list:
    """Returns active tables WITH full player stats — used by snapshot and broadcasts."""
    tables = _get_active_tables()
    if not tables:
        return []
    hero = cfg_module.get_hero()
    result = []
    async with AsyncSessionLocal() as session:
        for t in tables:
            players_data = []
            for nick in t.get("players", []):
                r = await session.execute(
                    select(PlayerStats).where(PlayerStats.nickname == nick)
                )
                p = r.scalar_one_or_none()
                if p:
                    s = p.to_stats_dict()
                    a = analyze_player(s)
                    players_data.append({**s, **a, "is_hero": nick == hero})
                else:
                    players_data.append({"nickname": nick, "hands": 0, "is_hero": nick == hero})
            result.append({**t, "players_data": players_data})
    return result


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    try:
        # Player snapshot
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PlayerStats).order_by(PlayerStats.last_seen.desc()).limit(30)
            )
            players = result.scalars().all()
        snapshot = []
        for p in players:
            s = p.to_stats_dict()
            a = analyze_player(s)
            snapshot.append({**s, **a})
        await ws.send_text(json.dumps({"type": "snapshot", "data": snapshot}))

        # Active tables snapshot WITH player stats
        tables_payload = await _build_active_tables_payload()
        await ws.send_text(json.dumps({"type": "active_tables_snapshot", "data": tables_payload}))
    except Exception:
        pass
    try:
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect, RuntimeError, Exception):
        connected_clients.discard(ws)


# ─── Players ──────────────────────────────────────────────────────────────────

@app.get("/players")
async def list_players(limit: int = 50):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PlayerStats).order_by(PlayerStats.last_seen.desc()).limit(limit)
        )
        players = result.scalars().all()
    return [{**p.to_stats_dict(), **analyze_player(p.to_stats_dict())} for p in players]


@app.get("/player/{nickname}")
async def get_player(nickname: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PlayerStats).where(PlayerStats.nickname == nickname))
        p = result.scalar_one_or_none()
    if p is None:
        return {"error": "Jogador nao encontrado"}
    s = p.to_stats_dict()
    return {**s, **analyze_player(s)}


@app.get("/search")
async def search_players(q: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PlayerStats).where(PlayerStats.nickname.ilike(f"%{q}%")).limit(20)
        )
        players = result.scalars().all()
    return [{**p.to_stats_dict(), **analyze_player(p.to_stats_dict())} for p in players]


# ─── Notes ────────────────────────────────────────────────────────────────────

@app.get("/player/{nickname}/notes")
async def get_notes(nickname: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PlayerNote)
            .where(PlayerNote.nickname == nickname)
            .order_by(desc(PlayerNote.created_at))
        )
        notes = result.scalars().all()
    return [{"id": n.id, "note": n.note, "created_at": n.created_at.isoformat()} for n in notes]


@app.post("/player/{nickname}/notes")
async def add_note(nickname: str, body: dict):
    note_text = (body.get("note") or "").strip()
    if not note_text:
        return {"error": "Nota vazia"}
    async with AsyncSessionLocal() as session:
        n = PlayerNote(nickname=nickname, note=note_text)
        session.add(n)
        await session.flush()
        nid = n.id
        ts  = n.created_at.isoformat()
        await session.commit()
    return {"id": nid, "note": note_text, "created_at": ts}


@app.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PlayerNote).where(PlayerNote.id == note_id))
        n = result.scalar_one_or_none()
        if n:
            await session.delete(n)
            await session.commit()
    return {"status": "deleted"}


# ─── Active tables ────────────────────────────────────────────────────────────

def _get_active_tables() -> list:
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    return [
        t for t in _active_tables.values()
        if datetime.fromisoformat(t["last_hand"]) > cutoff
    ]


@app.get("/active-tables")
async def active_tables_endpoint():
    tables = _get_active_tables()
    hero = cfg_module.get_hero()
    result = []
    for t in tables:
        players_with_stats = []
        async with AsyncSessionLocal() as session:
            for nick in t["players"]:
                r = await session.execute(select(PlayerStats).where(PlayerStats.nickname == nick))
                p = r.scalar_one_or_none()
                if p:
                    s = p.to_stats_dict()
                    a = analyze_player(s)
                    players_with_stats.append({**s, **a, "is_hero": nick == hero})
                else:
                    players_with_stats.append({"nickname": nick, "hands": 0, "is_hero": nick == hero})
        result.append({**t, "players_data": players_with_stats})
    return result


@app.get("/active-tables/comparison")
async def table_comparison():
    """Hero stats vs current table average."""
    hero = cfg_module.get_hero()
    tables = _get_active_tables()
    if not tables or not hero:
        return {"error": "Nenhuma mesa ativa ou hero nao configurado"}

    # Use the most recently active table
    latest = max(tables, key=lambda t: t["last_hand"])
    all_nicks = latest["players"]
    other_nicks = [n for n in all_nicks if n != hero]

    if not other_nicks:
        return {"error": "Sem oponentes na mesa"}

    # Fetch hero stats
    async with AsyncSessionLocal() as session:
        r = await session.execute(select(PlayerStats).where(PlayerStats.nickname == hero))
        hero_p = r.scalar_one_or_none()
        if not hero_p:
            return {"error": "Sem dados do hero"}
        hero_stats = hero_p.to_stats_dict()

        # Fetch opponent stats
        opp_stats = []
        for nick in other_nicks:
            r2 = await session.execute(select(PlayerStats).where(PlayerStats.nickname == nick))
            p2 = r2.scalar_one_or_none()
            if p2 and (p2.hands_dealt or 0) >= 10:
                opp_stats.append(p2.to_stats_dict())

    if not opp_stats:
        return {"error": "Oponentes sem dados suficientes"}

    COMPARED = ["vpip", "pfr", "threebet", "af", "cbet", "fold_to_cbet", "steal", "wtsd"]
    comparison = {}
    for stat in COMPARED:
        hero_val = hero_stats.get(stat, 0) or 0
        avg = sum(o.get(stat, 0) or 0 for o in opp_stats) / len(opp_stats)
        diff = round(hero_val - avg, 1)
        comparison[stat] = {
            "hero":  round(hero_val, 1),
            "table": round(avg, 1),
            "diff":  diff,
            "dir":   "higher" if diff > 3 else "lower" if diff < -3 else "similar",
        }

    return {
        "hero":        hero,
        "table":       latest["table"],
        "opponents":   len(opp_stats),
        "comparison":  comparison,
    }


# ─── Sessions ─────────────────────────────────────────────────────────────────

@app.get("/session/current")
async def current_session():
    if not _current_session["start"]:
        return {"active": False}
    duration = (datetime.utcnow() - _current_session["start"]).total_seconds() / 60
    return {
        "active":    True,
        "start":     _current_session["start"].isoformat(),
        "hands":     _current_session["hands"],
        "duration_min": round(duration, 1),
        "game_type": _current_session["game_type"],
    }


@app.get("/sessions")
async def list_sessions(limit: int = 10):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Session).order_by(desc(Session.start_time)).limit(limit)
        )
        sessions = result.scalars().all()
    out = []
    for s in sessions:
        dur = None
        if s.end_time and s.start_time:
            dur = round((s.end_time - s.start_time).total_seconds() / 60, 1)
        out.append({
            "id":          s.id,
            "start":       s.start_time.isoformat(),
            "end":         s.end_time.isoformat() if s.end_time else None,
            "hands":       s.hands_count,
            "duration_min": dur,
            "game_type":   s.game_type,
        })
    return out


# ─── Notable hands ────────────────────────────────────────────────────────────

@app.get("/player/{nickname}/hands")
async def player_hands(nickname: str, limit: int = 20):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(NotableHand)
            .where(NotableHand.players_json.like(f'%"{nickname}"%'))
            .order_by(desc(NotableHand.hand_time))
            .limit(limit)
        )
        hands = result.scalars().all()
    return [{
        "hand_id":  h.hand_id,
        "table":    h.table_name,
        "reason":   h.reason,
        "summary":  h.summary,
        "pot":      h.pot,
        "players":  json.loads(h.players_json),
        "actions":  json.loads(h.actions_json),
        "time":     h.hand_time.isoformat(),
    } for h in hands]


# ─── Hero ─────────────────────────────────────────────────────────────────────

@app.get("/hero")
async def get_hero():
    nickname = cfg_module.get_hero()
    if not nickname:
        return {"error": "Hero nickname nao configurado"}
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PlayerStats).where(PlayerStats.nickname == nickname))
        p = result.scalar_one_or_none()
    if p is None:
        return {"error": f"Sem dados para '{nickname}' — jogue algumas maos primeiro", "nickname": nickname}
    s = p.to_stats_dict()
    villain_analysis = analyze_player(s)
    self_analysis = analyze_hero(s)
    return {**s, **villain_analysis, "self_analysis": self_analysis, "is_hero": True}


@app.get("/hero/nickname")
async def get_hero_nickname():
    return {"nickname": cfg_module.get_hero()}


@app.post("/hero/nickname")
async def set_hero_nickname(body: dict):
    nickname = (body.get("nickname") or "").strip()
    if not nickname:
        return {"error": "Nickname invalido"}
    cfg_module.set_hero(nickname)
    return {"nickname": nickname, "status": "saved"}


# ─── Push/Fold ────────────────────────────────────────────────────────────────

@app.get("/push-fold")
async def push_fold(position: str, stack_bb: float):
    return get_recommendation(position, stack_bb)


@app.get("/push-fold/positions")
async def push_fold_positions():
    return [{"value": p, "label": POSITION_LABELS.get(p, p)} for p in POSITION_ORDER]


# ─── Cluster ──────────────────────────────────────────────────────────────────

@app.post("/cluster/run")
async def manual_cluster():
    asyncio.create_task(_run_cluster_pass())
    return {"status": "clustering started"}


# ─── Setup / first-run ────────────────────────────────────────────────────────

@app.get("/setup/status")
async def setup_status():
    """Returns config state + auto-detected PokerStars directories."""
    cfg = cfg_module.load()
    return {
        "configured":    cfg_module.is_configured(),
        "hero_nickname": cfg.get("hero_nickname", ""),
        "hh_path":       cfg.get("hh_path", ""),
        "found_dirs":    cfg_module.find_hh_dirs(),
    }


@app.post("/setup/configure")
async def setup_configure(body: dict):
    """Save nick + HH path and restart the file watcher.
    If path is omitted, tries to find it automatically from the nick.
    """
    nick = (body.get("nick") or "").strip()
    path = (body.get("path") or "").strip()

    if not nick:
        return {"error": "Nick e obrigatorio"}

    # Auto-find path from nick when not provided
    if not path:
        path = cfg_module.find_path_for_nick(nick)

    # Last fallback: use first available dir regardless of nick
    if not path:
        found = cfg_module.find_hh_dirs()
        if found:
            path = found[0]["path"]

    if not path:
        return {
            "error": (
                "Pasta do PokerStars nao encontrada automaticamente. "
                "Abra o PokerStars, jogue uma mao e tente novamente."
            )
        }

    cfg_module.set_hero(nick)
    cfg_module.set_hh_path(path)
    asyncio.create_task(_restart_watcher(path))
    return {"status": "ok", "nickname": nick, "path": path}


@app.get("/debug/tables")
async def debug_tables():
    """Show raw _active_tables content for troubleshooting."""
    return {
        "count": len(_active_tables),
        "tables": list(_active_tables.values()),
        "active_count": len(_get_active_tables()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
