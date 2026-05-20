"""
Stats engine — converts ParsedHand into incremental DB deltas.
Returns {player_name: {stat_field: delta, ...}} plus special keys:
  _vpip_decision: 0|1            — for tilt rolling window (handled in main)
  _recent_snapshot: dict          — compact per-hand stats for hero recent window
"""
from parser import ParsedHand

# ─── Position helpers ──────────────────────────────────────────────────────────

def _player_positions(hand: ParsedHand) -> dict:
    """Returns {player_name: position_str} where position_str ∈ {btn,co,sb,bb,ep}."""
    seats = sorted(hand.players.keys())
    n = len(seats)
    if hand.button_seat not in seats or n < 2:
        return {}

    btn_i = seats.index(hand.button_seat)
    result = {}
    for seat, info in hand.players.items():
        offset = (seats.index(seat) - btn_i) % n
        if offset == 0:
            pos = "btn"
        elif offset == 1:
            pos = "sb"
        elif offset == 2:
            pos = "bb"
        elif offset == n - 1:
            pos = "co"
        else:
            pos = "ep"
        result[info["name"]] = pos
    return result


# ─── Pot estimator ─────────────────────────────────────────────────────────────

def _pot_by_action(hand: ParsedHand) -> dict:
    """
    Estimates pot size just before each action (by index).
    Simplified: tracks round contributions per player, resets each street.
    """
    pots = {}
    pot = hand.small_blind + hand.big_blind
    contributions = {}  # player -> amount invested in current street
    current_street = None

    for i, action in enumerate(hand.actions):
        street = action["street"]
        if street != current_street:
            current_street = street
            contributions = {}

        pots[i] = max(pot, 0)

        act = action["action"]
        amount = action["amount"]

        if act in ("call", "bet", "allin"):
            prev = contributions.get(action["player"], 0)
            added = max(amount - prev, 0)
            pot += added
            contributions[action["player"]] = max(
                contributions.get(action["player"], 0), amount
            )
        elif act == "raise":
            # amount is the "to" total for raises
            prev = contributions.get(action["player"], 0)
            added = max(amount - prev, 0)
            pot += added
            contributions[action["player"]] = amount

    return pots


# ─── Main entry point ──────────────────────────────────────────────────────────

def process_hand(hand: ParsedHand) -> dict:
    updates: dict = {}
    player_names = {info["name"] for info in hand.players.values()}
    for name in player_names:
        updates[name] = {"hands_dealt": 1}

    seats = sorted(hand.players.keys())
    n = len(seats)
    positions = _player_positions(hand)

    bb_player = None
    if hand.button_seat in seats and n >= 2:
        btn_i = seats.index(hand.button_seat)
        bb_seat = seats[(btn_i + 2) % n]
        bb_player = hand.players.get(bb_seat, {}).get("name")

    pots = _pot_by_action(hand)

    _preflop(hand, updates, player_names, bb_player, seats, positions)
    _postflop(hand, updates, player_names, pots)
    _steal(hand, updates, player_names, seats)
    _position_stats(hand, updates, player_names, positions)
    _showdown(hand, updates, player_names)

    # Attach per-hand snapshot (includes game_type + player count for context-aware analysis)
    gt = "T" if hand.game_type == "tournament" else "C"
    n_players = len(player_names)
    for name in player_names:
        d = updates[name]
        updates[name]["_recent_snapshot"] = _make_snapshot(
            d, positions.get(name, "ep"), gt, n_players
        )

    # Attach notable hand info if this hand qualifies
    notable = _notable_hand(hand)
    if notable:
        for name in player_names:
            updates[name]["_notable"] = notable

    return updates


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _add(updates, player, stat, n=1):
    if player in updates:
        updates[player][stat] = updates[player].get(stat, 0) + n


def _bet_size_cat(amount: float, pot: float) -> str | None:
    if pot <= 0 or amount <= 0:
        return None
    ratio = amount / pot
    if ratio >= 1.0:
        return "overbet"
    if ratio >= 0.67:
        return "potbet"
    if ratio >= 0.25:
        return "halfpot"
    return "underbet"


# ─── Preflop ──────────────────────────────────────────────────────────────────

def _preflop(hand, updates, player_names, bb_player, seats, positions):
    pf = [a for a in hand.actions if a["street"] == "preflop"]

    raise_count = 0         # 0=no raise, 1=open raise, 2=3bet, 3=4bet...
    first_raiser = None
    second_raiser = None    # 3-bettor
    callers_after_open = 0  # for squeeze detection
    player_invested = set() # players who put money in voluntarily this street
    vpipped_players = set() # to avoid double-counting VPIP (once per hand)

    # Track each player's first action index so we can test "not yet acted"
    for i, a in enumerate(pf):
        p = a["player"]
        if p not in player_names:
            continue
        act = a["action"]

        # ── VPIP (count only once per hand) ───────────────────────────────────
        if act in ("call", "raise", "bet", "allin"):
            if p not in vpipped_players:
                _add(updates, p, "vpip_count")
                vpipped_players.add(p)
            updates[p]["_vpip_decision"] = 1
            player_invested.add(p)
        else:
            if "_vpip_decision" not in updates.get(p, {}):
                updates[p]["_vpip_decision"] = 0  # fold/check = no vpip

        # ── PFR ───────────────────────────────────────────────────────────────
        if act in ("raise", "bet", "allin") and raise_count == 0:
            first_raiser = p
            _add(updates, p, "pfr_count")

        # ── COLD CALL ─────────────────────────────────────────────────────────
        # Calling with money on the table (raise exists) without having invested before
        if act == "call" and raise_count >= 1 and p not in player_invested:
            _add(updates, p, "cold_call_count")
            _add(updates, p, "cold_call_opp")
        elif act in ("raise", "allin") and raise_count >= 1 and p not in player_invested:
            # Had opp to cold call but raised instead
            _add(updates, p, "cold_call_opp")

        # ── SQUEEZE ───────────────────────────────────────────────────────────
        # 3-bet when there's been an open raise + at least 1 caller
        if raise_count == 1 and callers_after_open >= 1:
            if act in ("raise", "bet", "allin") and p != first_raiser:
                _add(updates, p, "squeeze_count")
                _add(updates, p, "squeeze_opp")
            elif act in ("call", "fold"):
                _add(updates, p, "squeeze_opp")

        # ── 3BET ──────────────────────────────────────────────────────────────
        if raise_count == 1 and act in ("raise", "allin") and p != first_raiser:
            _add(updates, p, "threebet_count")
            _add(updates, p, "threebet_opp")
            second_raiser = p
        elif raise_count == 1 and act in ("call", "fold") and p != first_raiser:
            _add(updates, p, "threebet_opp")

        # ── 4BET ──────────────────────────────────────────────────────────────
        if raise_count == 2 and act in ("raise", "allin"):
            _add(updates, p, "fourbet_count")
            _add(updates, p, "fourbet_opp")
        elif raise_count == 2 and act in ("call", "fold"):
            _add(updates, p, "fourbet_opp")

        # ── FOLD TO 3BET ──────────────────────────────────────────────────────
        if second_raiser is not None and p == first_raiser:
            _add(updates, p, "fold_to_3bet_opp")
            if act == "fold":
                _add(updates, p, "fold_to_3bet_count")

        # ── Update raise / caller counters ────────────────────────────────────
        if act in ("raise", "bet", "allin"):
            raise_count += 1
        elif act == "call" and raise_count == 1:
            callers_after_open += 1

    # Ensure every dealt player has a _vpip_decision
    for name in player_names:
        if "_vpip_decision" not in updates.get(name, {}):
            updates[name]["_vpip_decision"] = 0


# ─── Postflop ─────────────────────────────────────────────────────────────────

def _postflop(hand, updates, player_names, pots):
    preflop_agg = hand.preflop_aggressor

    for street in ("flop", "turn", "river"):
        st_actions = [a for a in hand.actions if a["street"] == street]
        if not st_actions:
            continue

        st_players = {a["player"] for a in st_actions if a["player"] in player_names}

        # ── SAW FLOP ──────────────────────────────────────────────────────────
        if street == "flop":
            for p in st_players:
                _add(updates, p, "saw_flop_count")

            # ── CBET ──────────────────────────────────────────────────────────
            if preflop_agg and preflop_agg in st_players:
                _add(updates, preflop_agg, "cbet_opp")
                first_bet_i = next(
                    (i for i, a in enumerate(st_actions)
                     if a["player"] == preflop_agg and a["action"] in ("bet", "raise", "allin")),
                    None,
                )
                if first_bet_i is not None:
                    _add(updates, preflop_agg, "cbet_count")
                    for a in st_actions[first_bet_i + 1:]:
                        if a["player"] != preflop_agg and a["player"] in player_names:
                            _add(updates, a["player"], "fold_to_cbet_opp")
                            if a["action"] == "fold":
                                _add(updates, a["player"], "fold_to_cbet_count")
                            break

            # ── DONK BET ──────────────────────────────────────────────────────
            if preflop_agg:
                first_bet = next(
                    (a for a in st_actions if a["action"] in ("bet", "raise", "allin")),
                    None,
                )
                if first_bet and first_bet["player"] != preflop_agg:
                    # Preflop aggressor hadn't acted before this bet
                    donker = first_bet["player"]
                    if donker in player_names:
                        _add(updates, donker, "donk_bet_count")

                for p in st_players:
                    if p != preflop_agg and p in player_names:
                        _add(updates, p, "donk_bet_opp")

        # ── AF + BET SIZING ───────────────────────────────────────────────────
        action_indices = {id(a): i for i, a in enumerate(hand.actions)}
        for a in st_actions:
            p = a["player"]
            if p not in player_names:
                continue
            if a["action"] in ("bet", "raise", "allin"):
                _add(updates, p, "bets_raises_post")
                # Bet sizing categorization
                global_idx = action_indices.get(id(a))
                pot = pots.get(global_idx, 0) if global_idx is not None else 0
                cat = _bet_size_cat(a["amount"], pot)
                if cat:
                    _add(updates, p, f"{cat}_count")
                    _add(updates, p, "total_bet_spots")
            elif a["action"] == "call":
                _add(updates, p, "calls_post")


# ─── Steal ────────────────────────────────────────────────────────────────────

def _steal(hand, updates, player_names, seats):
    n = len(seats)
    if hand.button_seat not in seats or n < 4:
        return

    btn_i = seats.index(hand.button_seat)
    steal_seats = {
        seats[btn_i],
        seats[(btn_i - 1) % n],  # CO
        seats[(btn_i + 1) % n],  # SB
    }
    steal_players = {hand.players[s]["name"] for s in steal_seats if s in hand.players}

    pf = [a for a in hand.actions if a["street"] == "preflop"]
    seen_non_fold = False
    processed = set()

    for a in pf:
        p = a["player"]
        if p in steal_players and p not in processed:
            processed.add(p)
            if not seen_non_fold:
                _add(updates, p, "steal_opp")
                if a["action"] in ("raise", "bet", "allin"):
                    _add(updates, p, "steal_count")
        if a["action"] not in ("fold",):
            seen_non_fold = True


# ─── Position stats ───────────────────────────────────────────────────────────

def _position_stats(hand, updates, player_names, positions):
    pf = [a for a in hand.actions if a["street"] == "preflop"]

    vpipped = set()
    pf_raised = set()
    for a in pf:
        p = a["player"]
        if a["action"] in ("call", "raise", "bet", "allin"):
            vpipped.add(p)
        if a["action"] in ("raise", "bet", "allin"):
            pf_raised.add(p)

    for name in player_names:
        pos = positions.get(name)
        if not pos:
            continue
        _add(updates, name, f"{pos}_hands")
        if name in vpipped:
            _add(updates, name, f"{pos}_vpip_count")
        if name in pf_raised:
            _add(updates, name, f"{pos}_pfr_count")


# ─── Showdown ─────────────────────────────────────────────────────────────────

def _showdown(hand, updates, player_names):
    flop_players = {a["player"] for a in hand.actions if a["street"] == "flop"}
    sd_players = set(hand.showdown_players) | {w["player"] for w in hand.winners}
    for p in sd_players:
        if p in player_names and p in flop_players:
            _add(updates, p, "wtsd_count")


# ─── Per-hand snapshot (for recent-window analysis) ────────────────────────────

def _flag(deltas, yes_key, opp_key):
    """Return 1/0/None: 1=did it, 0=missed opp, None=no opportunity."""
    if deltas.get(yes_key, 0) > 0:
        return 1
    if deltas.get(opp_key, 0) > 0:
        return 0
    return None


def _notable_hand(hand) -> dict | None:
    """Return info if this hand is worth highlighting, else None."""
    pf_allins = [a for a in hand.actions if a["action"] == "allin" and a["street"] == "preflop"]
    if pf_allins:
        names = list({a["player"] for a in pf_allins})
        return {
            "hand_id":  hand.hand_id,
            "table":    hand.table_name,
            "game_type": hand.game_type,
            "reason":   "allin",
            "players":  [info["name"] for info in hand.players.values()],
            "summary":  f"All-in pre-flop: {', '.join(names[:2])}",
            "actions":  [{"p": a["player"], "a": a["action"], "s": a["street"]} for a in hand.actions[-8:]],
            "pot":      sum(w["amount"] for w in hand.winners),
        }
    if hand.showdown_players:
        return {
            "hand_id":  hand.hand_id,
            "table":    hand.table_name,
            "game_type": hand.game_type,
            "reason":   "showdown",
            "players":  [info["name"] for info in hand.players.values()],
            "summary":  f"Showdown: {', '.join(hand.showdown_players[:2])}",
            "actions":  [{"p": a["player"], "a": a["action"], "s": a["street"]} for a in hand.actions[-8:]],
            "pot":      sum(w["amount"] for w in hand.winners),
        }
    return None


def _make_snapshot(deltas: dict, position: str, game_type: str = "T",
                   n_players: int = 6) -> dict:
    """
    Compact per-hand stats snapshot for one player.
    Keys use short names to keep JSON small.
    np = number of players at the table (used by tilt detection to skip HU hands).
    """
    saw_flop = deltas.get("saw_flop_count", 0) > 0
    return {
        "v":   1 if deltas.get("vpip_count", 0) > 0 else 0,
        "p":   1 if deltas.get("pfr_count", 0) > 0 else 0,
        "3b":  _flag(deltas, "threebet_count",      "threebet_opp"),
        "fb":  _flag(deltas, "fold_to_3bet_count",  "fold_to_3bet_opp"),
        "cb":  _flag(deltas, "cbet_count",          "cbet_opp"),
        "fc":  _flag(deltas, "fold_to_cbet_count",  "fold_to_cbet_opp"),
        "st":  _flag(deltas, "steal_count",         "steal_opp"),
        "4b":  _flag(deltas, "fourbet_count",       "fourbet_opp"),
        "sq":  _flag(deltas, "squeeze_count",       "squeeze_opp"),
        "dk":  _flag(deltas, "donk_bet_count",      "donk_bet_opp"),
        "ab":  deltas.get("bets_raises_post", 0),
        "ac":  deltas.get("calls_post", 0),
        "ws":  (1 if deltas.get("wtsd_count", 0) > 0
                else 0 if saw_flop
                else None),
        "pos": position,
        "gt":  game_type,   # "T"=tournament, "C"=cash
        "np":  n_players,   # number of players at table (HU = 2)
    }
