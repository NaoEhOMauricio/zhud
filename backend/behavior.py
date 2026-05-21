"""
Behavior engine — rule-based player profiling, tilt detection, and bet sizing analysis.
Zero cost: no external APIs, fully local.
"""


# ─── Profile classification ───────────────────────────────────────────────────

def classify_profile(vpip: float, pfr: float, af: float, hands: int) -> str:
    if hands < 8:
        return "Amostra pequena"
    gap = vpip - pfr
    if vpip < 13:
        return "Nit"
    if vpip <= 26 and pfr >= 14 and af >= 2:
        return "TAG"
    if vpip > 26 and vpip <= 36 and af >= 3:
        return "LAG"
    if vpip > 38 and pfr < 20:
        return "Calling Station"
    if vpip > 45 and af > 5:
        return "Maniac"
    if vpip <= 26 and pfr < 14:
        return "Passivo"
    return "Regular"


def classify_aggression(af: float) -> str:
    if af < 1.0:
        return "Muito Passivo"
    if af < 2.0:
        return "Passivo"
    if af < 3.5:
        return "Moderado"
    if af < 5.0:
        return "Agressivo"
    return "Muito Agressivo"


# ─── Tilt detection ───────────────────────────────────────────────────────────

def detect_tilt(recent_decisions: list, overall_vpip: float) -> dict:
    """
    recent_decisions: list of int OR dict (1=vpipped, 0=folded), last 30 hands.
    When dicts, they may contain 'np' (number of players) for context-aware detection.
    overall_vpip: player's overall VPIP% (0–100).

    HU (np=2) and 3-handed (np=3) games naturally have very high VPIP,
    so tilt detection based on VPIP is skipped for those hands.
    """
    if len(recent_decisions) < 10:
        return {"score": 0, "label": "Sem dados", "recent_vpip": 0.0, "delta": 0.0}

    # Filter: only use hands with 4+ players for VPIP-based tilt detection
    # (HU and 3-handed have naturally inflated VPIP — not tilt signals)
    if isinstance(recent_decisions[0], dict):
        multi_way = [h for h in recent_decisions if h.get("np", 6) >= 4]
        vpip_values = [h.get("v", 0) for h in multi_way]
    else:
        # Legacy format (plain ints) — no player count available, use all
        multi_way = recent_decisions
        vpip_values = recent_decisions

    # Need at least 10 multi-way hands for reliable comparison
    if len(vpip_values) < 10:
        return {"score": 0, "label": "Sem dados (HU/3-max)", "recent_vpip": 0.0, "delta": 0.0}

    window = vpip_values[-15:] if len(vpip_values) >= 15 else vpip_values
    recent_vpip = round(sum(window) / len(window) * 100, 1)
    delta = recent_vpip - overall_vpip

    if delta < 8:
        label, score = "Normal", max(0, int(delta * 2))
    elif delta < 15:
        label, score = "Leve", 35
    elif delta < 25:
        label, score = "Moderado", 65
    else:
        label, score = "Severo", min(100, int(80 + delta))

    return {
        "score":        score,
        "label":        label,
        "recent_vpip":  recent_vpip,
        "delta":        round(delta, 1),
    }


# ─── Bet sizing analysis ──────────────────────────────────────────────────────

def analyze_bet_sizing(sizing: dict) -> list:
    """Generate insight strings from a player's bet sizing distribution."""
    insights = []
    if (sizing.get("total") or 0) < 10:
        return insights

    overbet  = sizing.get("overbet", 0)
    potbet   = sizing.get("potbet", 0)
    halfpot  = sizing.get("halfpot", 0)
    underbet = sizing.get("underbet", 0)

    if overbet > 25:
        insights.append(f"Overbet frequente ({overbet}%) — range polarizado ou mega blefe")
    if underbet > 40:
        insights.append(f"Underbet constante ({underbet}%) — mãos fracas ou trapping")
    if potbet + overbet > 60:
        insights.append("Preferência por apostas grandes — range polarizado")
    if halfpot > 70:
        insights.append("Half-pot consistente — range equilibrado / merged")

    big = potbet + overbet
    small = halfpot + underbet
    if big > small + 30:
        insights.append("Sizing muito grande — extraia valor, ele aposta grande com tudo")
    elif small > big + 30:
        insights.append("Sizing conservador — pode callar mais, não larga fácil")

    return insights


# ─── Observation + vulnerability generation ───────────────────────────────────

def generate_observations(stats: dict) -> list:
    obs = []
    vpip          = stats.get("vpip", 0)
    pfr           = stats.get("pfr", 0)
    af            = stats.get("af", 0)
    cbet          = stats.get("cbet", 0)
    fold_to_cbet  = stats.get("fold_to_cbet", 0)
    fold_to_3bet  = stats.get("fold_to_3bet", 0)
    threebet      = stats.get("threebet", 0)
    fourbet       = stats.get("fourbet", 0)
    squeeze       = stats.get("squeeze", 0)
    cold_call     = stats.get("cold_call", 0)
    donk_bet      = stats.get("donk_bet", 0)
    steal         = stats.get("steal", 0)
    wtsd          = stats.get("wtsd", 0)
    hands         = stats.get("hands", 0)

    if hands < 20:
        obs.append(f"Amostra pequena ({hands} mãos) — dados provisórios")
        return obs

    # VPIP
    if vpip < 12:
        obs.append(f"Extremamente tight (VPIP {vpip}%) — range de premium")
    elif vpip > 40:
        obs.append(f"Muito loose (VPIP {vpip}%) — ampla faixa de mãos")

    # PFR
    if pfr > 28:
        obs.append(f"Raises preflop excessivo (PFR {pfr}%)")
    elif pfr < 8 and vpip > 18:
        obs.append(f"Limp frequente — entra mas não sobe (gap VPIP−PFR = {vpip - pfr:.0f}%)")

    # 3BET / 4BET
    if threebet > 12:
        obs.append(f"3-bet excessivo ({threebet}%) — range amplo de re-raises")
    elif threebet < 3 and hands > 50:
        obs.append(f"Raramente faz 3-bet ({threebet}%) — range muito defensivo")
    if fourbet > 10:
        obs.append(f"4-bet frequente ({fourbet}%) — jogo de pressão preflop")

    # Squeeze / Cold Call
    if squeeze > 15:
        obs.append(f"Squeeze com frequência ({squeeze}%) — explora multi-way pots")
    if cold_call > 30:
        obs.append(f"Cold-call alto ({cold_call}%) — entra em potes sem re-raise")

    # Fold to 3bet
    if fold_to_3bet > 68:
        obs.append(f"Folda muito para 3-bet ({fold_to_3bet}%) — abandona sob pressão")
    elif fold_to_3bet < 35 and hands > 50:
        obs.append(f"Defende agressivamente contra 3-bet ({fold_to_3bet}% fold)")

    # C-bet
    if cbet > 85:
        obs.append(f"C-bet quase automático ({cbet}%) — aposta flop sem seleção")
    elif cbet < 40 and hands > 50:
        obs.append(f"C-bet baixo ({cbet}%) — abandona flop com frequência")

    # Fold to c-bet
    if fold_to_cbet > 65:
        obs.append(f"Folda muito para c-bet ({fold_to_cbet}%) — fraqueza no flop")
    elif fold_to_cbet < 30 and hands > 50:
        obs.append(f"Chama muita c-bet ({fold_to_cbet}% fold) — float frequente")

    # Donk bet
    if donk_bet > 30:
        obs.append(f"Donk bet frequente ({donk_bet}%) — aposta OOP sem ter iniciativa")

    # Steal
    if steal > 55:
        obs.append(f"Steal excessivo ({steal}%) — agressivo em posição")
    elif steal < 20 and hands > 50:
        obs.append(f"Steal baixo ({steal}%) — passivo em posição")

    # AF
    if af > 5.5:
        obs.append(f"AF extremamente alto ({af}) — agressividade máxima pós-flop")
    elif af < 1.2:
        obs.append(f"Jogo muito passivo pós-flop (AF {af})")

    # WTSD
    if wtsd > 35:
        obs.append(f"Vai muito ao showdown ({wtsd}%) — chama até o river")
    elif wtsd < 18 and hands > 50:
        obs.append(f"Raramente vai ao showdown ({wtsd}%) — desiste cedo")

    return obs


def generate_vulnerabilities(stats: dict) -> list:
    vuln = []
    vpip         = stats.get("vpip", 0)
    pfr          = stats.get("pfr", 0)
    af           = stats.get("af", 0)
    cbet         = stats.get("cbet", 0)
    fold_to_cbet = stats.get("fold_to_cbet", 0)
    fold_to_3bet = stats.get("fold_to_3bet", 0)
    threebet     = stats.get("threebet", 0)
    squeeze      = stats.get("squeeze", 0)
    steal        = stats.get("steal", 0)
    wtsd         = stats.get("wtsd", 0)
    donk_bet     = stats.get("donk_bet", 0)
    hands        = stats.get("hands", 0)

    if hands < 20:
        return []

    if fold_to_3bet > 68:
        vuln.append(f"3-bet light de posição — folda {fold_to_3bet}% das vezes")
    if fold_to_cbet > 62:
        vuln.append(f"Aposte quase todo flop — folda {fold_to_cbet}% para c-bet")
    if vpip > 38 and pfr < 18:
        vuln.append("Isolate raise — chama muito mas não resiste à pressão")
    if cbet > 85 and hands > 40:
        vuln.append("Float e raise no turn — c-bet automático com range fraco")
    if steal > 55:
        vuln.append(f"3-bet re-steal — abre muito do BTN/CO ({steal}%)")
    if threebet > 14:
        vuln.append("4-bet bluff — 3-bet frequente com faixa desequilibrada")
    if wtsd > 35 and af < 2:
        vuln.append("Value bet grosso no river — paga até o showdown")
    if af > 5.5:
        vuln.append("Check-raise traps — super agressivo, vulnerável a slow-play")
    if donk_bet > 30:
        vuln.append("Raise o donk bet — aposta OOP sem iniciativa, range fraco")
    if squeeze > 15:
        vuln.append(f"Cold 4-bet vs squeeze — range de squeeze ({squeeze}%) é amplo")

    return vuln


# ─── Main analysis function ───────────────────────────────────────────────────

def analyze_player(stats: dict) -> dict:
    vpip  = stats.get("vpip", 0)
    pfr   = stats.get("pfr", 0)
    af    = stats.get("af", 0)
    hands = stats.get("hands", 0)

    profile          = classify_profile(vpip, pfr, af, hands)
    aggression_label = classify_aggression(af)
    observations     = generate_observations(stats)
    vulnerabilities  = generate_vulnerabilities(stats)

    # Tilt detection — prefer recent_hands (has np=player count) over legacy vpip list
    recent_hands = stats.get("recent_hands", [])
    if recent_hands and isinstance(recent_hands[0], dict):
        tilt = detect_tilt(recent_hands, vpip)
    else:
        tilt = detect_tilt(stats.get("recent_vpip_decisions", []), vpip)

    # Bet sizing insights
    sizing = stats.get("bet_sizing", {})
    sizing_insights = analyze_bet_sizing(sizing)

    # Trend analysis from recent hands
    recent_hands = stats.get("recent_hands", [])
    try:
        from trend import calc_trends, describe_trend
        trends = calc_trends(recent_hands)
        trend_msgs = describe_trend(trends)
    except Exception:
        trends = {}
        trend_msgs = []

    return {
        "profile": profile,
        "aggression_label": aggression_label,
        "observations": observations + sizing_insights + trend_msgs,
        "vulnerabilities": vulnerabilities,
        "tilt": tilt,
        "trends": trends,
    }
