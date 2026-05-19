"""
Trend analysis: compares last 15 hands vs previous 15 to detect
style changes in any player.
"""
from hero_analysis import calc_recent_stats

TREND_THRESHOLD = 10   # % point change required to flag as trend
KEY_STATS = ["vpip", "pfr", "threebet", "af", "cbet", "fold_to_cbet", "fold_to_3bet", "steal"]


def calc_trends(recent_hands: list) -> dict:
    """
    Compare last 15 hands vs previous 15 (hands[-30:-15]).
    Returns {stat: {dir: "up"|"down"|"stable", delta: float}}.
    Empty dict if not enough data.
    """
    if len(recent_hands) < 20:
        return {}

    window = min(15, len(recent_hands) // 2)
    last = recent_hands[-window:]
    prev = recent_hands[-window * 2: -window]

    if not prev:
        return {}

    last_s = calc_recent_stats(last)
    prev_s = calc_recent_stats(prev)

    trends = {}
    for stat in KEY_STATS:
        r = last_s.get(stat, 0) or 0
        p = prev_s.get(stat, 0) or 0
        delta = round(r - p, 1)
        if abs(delta) >= TREND_THRESHOLD:
            trends[stat] = {"dir": "up" if delta > 0 else "down", "delta": delta}
        else:
            trends[stat] = {"dir": "stable", "delta": delta}

    return trends


def describe_trend(trends: dict) -> list:
    """Human-readable trend descriptions."""
    msgs = []
    labels = {
        "vpip":         ("VPIP", "mais mãos", "menos mãos"),
        "pfr":          ("PFR",  "mais raises", "menos raises"),
        "threebet":     ("3BET", "mais 3-bets", "menos 3-bets"),
        "af":           ("AF",   "mais agressivo", "mais passivo"),
        "cbet":         ("CBET", "c-bet subiu", "c-bet caiu"),
        "fold_to_cbet": ("F.CBET", "foldando mais p/ cbet", "defendendo mais cbet"),
        "fold_to_3bet": ("F.3BET", "foldando mais p/ 3bet", "defendendo mais 3bet"),
        "steal":        ("Steal", "roubando mais", "roubando menos"),
    }
    for stat, t in trends.items():
        if t["dir"] == "stable":
            continue
        label, up_desc, down_desc = labels.get(stat, (stat, "subiu", "caiu"))
        desc = up_desc if t["dir"] == "up" else down_desc
        delta = t["delta"]
        sign = "+" if delta > 0 else ""
        msgs.append(f"{label} {desc} ({sign}{delta}%)")
    return msgs
