import json
import os
import sys
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Float, text
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _db_path() -> str:
    """Returns the full path to zhud.db, respecting packaged/dev mode."""
    data_dir = os.environ.get("ZHUD_DATA_DIR", "").strip()
    if not data_dir:
        if getattr(sys, "frozen", False):
            data_dir = os.path.dirname(sys.executable)
        else:
            data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "zhud.db")


DATABASE_URL = f"sqlite+aiosqlite:///{_db_path()}"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # ── Preflop ───────────────────────────────────────────────────────────────
    hands_dealt: Mapped[int] = mapped_column(Integer, default=0)
    vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    pfr_count: Mapped[int] = mapped_column(Integer, default=0)
    threebet_count: Mapped[int] = mapped_column(Integer, default=0)
    threebet_opp: Mapped[int] = mapped_column(Integer, default=0)
    fourbet_count: Mapped[int] = mapped_column(Integer, default=0)
    fourbet_opp: Mapped[int] = mapped_column(Integer, default=0)
    squeeze_count: Mapped[int] = mapped_column(Integer, default=0)
    squeeze_opp: Mapped[int] = mapped_column(Integer, default=0)
    cold_call_count: Mapped[int] = mapped_column(Integer, default=0)
    cold_call_opp: Mapped[int] = mapped_column(Integer, default=0)
    fold_to_3bet_count: Mapped[int] = mapped_column(Integer, default=0)
    fold_to_3bet_opp: Mapped[int] = mapped_column(Integer, default=0)
    steal_count: Mapped[int] = mapped_column(Integer, default=0)
    steal_opp: Mapped[int] = mapped_column(Integer, default=0)

    # ── Postflop ──────────────────────────────────────────────────────────────
    cbet_count: Mapped[int] = mapped_column(Integer, default=0)
    cbet_opp: Mapped[int] = mapped_column(Integer, default=0)
    fold_to_cbet_count: Mapped[int] = mapped_column(Integer, default=0)
    fold_to_cbet_opp: Mapped[int] = mapped_column(Integer, default=0)
    donk_bet_count: Mapped[int] = mapped_column(Integer, default=0)
    donk_bet_opp: Mapped[int] = mapped_column(Integer, default=0)
    bets_raises_post: Mapped[int] = mapped_column(Integer, default=0)
    calls_post: Mapped[int] = mapped_column(Integer, default=0)
    wtsd_count: Mapped[int] = mapped_column(Integer, default=0)
    saw_flop_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── Position stats ────────────────────────────────────────────────────────
    btn_hands: Mapped[int] = mapped_column(Integer, default=0)
    btn_vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    btn_pfr_count: Mapped[int] = mapped_column(Integer, default=0)
    co_hands: Mapped[int] = mapped_column(Integer, default=0)
    co_vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    co_pfr_count: Mapped[int] = mapped_column(Integer, default=0)
    sb_hands: Mapped[int] = mapped_column(Integer, default=0)
    sb_vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    sb_pfr_count: Mapped[int] = mapped_column(Integer, default=0)
    bb_hands: Mapped[int] = mapped_column(Integer, default=0)
    bb_vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    bb_pfr_count: Mapped[int] = mapped_column(Integer, default=0)
    ep_hands: Mapped[int] = mapped_column(Integer, default=0)
    ep_vpip_count: Mapped[int] = mapped_column(Integer, default=0)
    ep_pfr_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── Bet sizing (postflop bets/raises, categorized by pot%) ───────────────
    overbet_count: Mapped[int] = mapped_column(Integer, default=0)   # >100% pot
    potbet_count: Mapped[int] = mapped_column(Integer, default=0)    # 67-100%
    halfpot_count: Mapped[int] = mapped_column(Integer, default=0)   # 25-66%
    underbet_count: Mapped[int] = mapped_column(Integer, default=0)  # <25%
    total_bet_spots: Mapped[int] = mapped_column(Integer, default=0)

    # ── Tilt tracking ─────────────────────────────────────────────────────────
    # JSON array of last 30 VPIP decisions [1,0,1,...] (kept for tilt detection)
    recent_vpip_json: Mapped[str] = mapped_column(Text, default="[]")

    # ── Recent hands window for hero self-analysis ────────────────────────────
    # JSON array of per-hand snapshots, last N hands (N = config.recent_window)
    recent_hands_json: Mapped[str] = mapped_column(Text, default="[]")

    # ── Cluster ───────────────────────────────────────────────────────────────
    cluster_id: Mapped[int] = mapped_column(Integer, default=-1)
    cluster_label: Mapped[str] = mapped_column(String(60), default="")

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_stats_dict(self) -> dict:
        def pct(n, d):
            return round((n or 0) / max(d or 1, 1) * 100, 1)

        def pos(prefix):
            h = getattr(self, f"{prefix}_hands") or 0
            return {
                "hands": h,
                "vpip": pct(getattr(self, f"{prefix}_vpip_count") or 0, h),
                "pfr": pct(getattr(self, f"{prefix}_pfr_count") or 0, h),
            }

        tb = (
            (self.overbet_count or 0)
            + (self.potbet_count or 0)
            + (self.halfpot_count or 0)
            + (self.underbet_count or 0)
        )

        try:
            recent_vpip = json.loads(self.recent_vpip_json or "[]")
        except Exception:
            recent_vpip = []

        try:
            recent_hands = json.loads(self.recent_hands_json or "[]")
        except Exception:
            recent_hands = []

        return {
            "nickname": self.nickname,
            "hands": self.hands_dealt or 0,
            # Preflop
            "vpip": pct(self.vpip_count, self.hands_dealt),
            "pfr": pct(self.pfr_count, self.hands_dealt),
            "threebet": pct(self.threebet_count, self.threebet_opp),
            "fourbet": pct(self.fourbet_count, self.fourbet_opp),
            "squeeze": pct(self.squeeze_count, self.squeeze_opp),
            "cold_call": pct(self.cold_call_count, self.cold_call_opp),
            "fold_to_3bet": pct(self.fold_to_3bet_count, self.fold_to_3bet_opp),
            "steal": pct(self.steal_count, self.steal_opp),
            # Postflop
            "af": round((self.bets_raises_post or 0) / max(self.calls_post or 1, 1), 2),
            "cbet": pct(self.cbet_count, self.cbet_opp),
            "fold_to_cbet": pct(self.fold_to_cbet_count, self.fold_to_cbet_opp),
            "donk_bet": pct(self.donk_bet_count, self.donk_bet_opp),
            "wtsd": pct(self.wtsd_count, self.saw_flop_count),
            # Position
            "pos_btn": pos("btn"),
            "pos_co": pos("co"),
            "pos_sb": pos("sb"),
            "pos_bb": pos("bb"),
            "pos_ep": pos("ep"),
            # Bet sizing
            "bet_sizing": {
                "overbet": pct(self.overbet_count, tb),
                "potbet": pct(self.potbet_count, tb),
                "halfpot": pct(self.halfpot_count, tb),
                "underbet": pct(self.underbet_count, tb),
                "total": tb,
            },
            # For tilt and hero analysis
            "recent_vpip_decisions": recent_vpip,
            "recent_hands": recent_hands,
            # Cluster
            "cluster_id": self.cluster_id if self.cluster_id is not None else -1,
            "cluster_label": self.cluster_label or "",
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


# ─── Supporting models ────────────────────────────────────────────────────────

class PlayerNote(Base):
    __tablename__ = "player_notes"

    id: Mapped[int]      = mapped_column(Integer, primary_key=True)
    nickname: Mapped[str] = mapped_column(String(100), index=True)
    note: Mapped[str]    = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int]        = mapped_column(Integer, primary_key=True)
    start_time: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hands_count: Mapped[int] = mapped_column(Integer, default=0)
    game_type: Mapped[str]   = mapped_column(String(20), default="tournament")


class NotableHand(Base):
    __tablename__ = "notable_hands"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True)
    hand_id: Mapped[str]      = mapped_column(String(30), unique=True, index=True)
    table_name: Mapped[str]   = mapped_column(String(200))
    game_type: Mapped[str]    = mapped_column(String(20), default="tournament")
    players_json: Mapped[str] = mapped_column(Text, default="[]")
    summary: Mapped[str]      = mapped_column(Text, default="")
    actions_json: Mapped[str] = mapped_column(Text, default="[]")
    pot: Mapped[float]        = mapped_column(Float, default=0.0)
    reason: Mapped[str]       = mapped_column(String(30), default="")  # allin|showdown|big_pot
    hand_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlayerEncounter(Base):
    """Tracks how many hands the hero has played at the same table as a given villain."""
    __tablename__ = "player_encounters"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True)
    hero_nick: Mapped[str]    = mapped_column(String(100), index=True)
    villain_nick: Mapped[str] = mapped_column(String(100), index=True)
    hands_together: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    """Create tables and run auto-migration for schema upgrades."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(text("PRAGMA table_info(player_stats)"))
        existing = {row[1] for row in result.fetchall()}

        new_cols = {
            "fourbet_count": "INTEGER NOT NULL DEFAULT 0",
            "fourbet_opp": "INTEGER NOT NULL DEFAULT 0",
            "squeeze_count": "INTEGER NOT NULL DEFAULT 0",
            "squeeze_opp": "INTEGER NOT NULL DEFAULT 0",
            "cold_call_count": "INTEGER NOT NULL DEFAULT 0",
            "cold_call_opp": "INTEGER NOT NULL DEFAULT 0",
            "donk_bet_count": "INTEGER NOT NULL DEFAULT 0",
            "donk_bet_opp": "INTEGER NOT NULL DEFAULT 0",
            "btn_hands": "INTEGER NOT NULL DEFAULT 0",
            "btn_vpip_count": "INTEGER NOT NULL DEFAULT 0",
            "btn_pfr_count": "INTEGER NOT NULL DEFAULT 0",
            "co_hands": "INTEGER NOT NULL DEFAULT 0",
            "co_vpip_count": "INTEGER NOT NULL DEFAULT 0",
            "co_pfr_count": "INTEGER NOT NULL DEFAULT 0",
            "sb_hands": "INTEGER NOT NULL DEFAULT 0",
            "sb_vpip_count": "INTEGER NOT NULL DEFAULT 0",
            "sb_pfr_count": "INTEGER NOT NULL DEFAULT 0",
            "bb_hands": "INTEGER NOT NULL DEFAULT 0",
            "bb_vpip_count": "INTEGER NOT NULL DEFAULT 0",
            "bb_pfr_count": "INTEGER NOT NULL DEFAULT 0",
            "ep_hands": "INTEGER NOT NULL DEFAULT 0",
            "ep_vpip_count": "INTEGER NOT NULL DEFAULT 0",
            "ep_pfr_count": "INTEGER NOT NULL DEFAULT 0",
            "overbet_count": "INTEGER NOT NULL DEFAULT 0",
            "potbet_count": "INTEGER NOT NULL DEFAULT 0",
            "halfpot_count": "INTEGER NOT NULL DEFAULT 0",
            "underbet_count": "INTEGER NOT NULL DEFAULT 0",
            "total_bet_spots": "INTEGER NOT NULL DEFAULT 0",
            "recent_vpip_json": "TEXT NOT NULL DEFAULT '[]'",
            "recent_hands_json": "TEXT NOT NULL DEFAULT '[]'",
            "cluster_id": "INTEGER NOT NULL DEFAULT -1",
            "cluster_label": "TEXT NOT NULL DEFAULT ''",
        }

        for col, defn in new_cols.items():
            if col not in existing:
                await conn.execute(text(f"ALTER TABLE player_stats ADD COLUMN {col} {defn}"))
                print(f"[db] migration: added column {col}")

        # Ensure unique index on player_encounters (hero_nick, villain_nick)
        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_encounter_pair "
                "ON player_encounters (hero_nick, villain_nick)"
            ))
        except Exception:
            pass
