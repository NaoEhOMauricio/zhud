"""
Hero (self) analysis engine.
Identifies leaks in your own game and gives actionable improvement tips.

When recent_hands data is available (from rolling window), uses only those hands
for analysis. Falls back to all-time stats if the window is too small.
"""


# ─── Recent hands calculator ──────────────────────────────────────────────────

def _rate(hands: list, key: str) -> float | None:
    """
    Calc a % rate from recent hands using only hands where the player had an
    opportunity (value is not None).
    Returns None if no opportunities.
    """
    relevant = [h[key] for h in hands if h.get(key) is not None]
    if not relevant:
        return None
    return round(sum(relevant) / len(relevant) * 100, 1)


def _af(hands: list) -> float:
    """Aggression Factor from recent hands."""
    bets   = sum(h.get("ab", 0) for h in hands)
    calls  = sum(h.get("ac", 0) for h in hands)
    return round(bets / max(calls, 1), 2)


def calc_recent_stats(recent_hands: list) -> dict:
    """
    Calculate stat rates from a list of per-hand snapshots.
    Returns a dict with the same keys used in to_stats_dict().
    """
    n = len(recent_hands)
    if n == 0:
        return {}

    def r(key):
        return _rate(recent_hands, key)

    vpip_rate = r("v")
    pfr_rate  = r("p")

    return {
        "vpip":         vpip_rate or 0.0,
        "pfr":          pfr_rate  or 0.0,
        "threebet":     r("3b") or 0.0,
        "fourbet":      r("4b") or 0.0,
        "squeeze":      r("sq") or 0.0,
        "fold_to_3bet": r("fb") or 0.0,
        "cbet":         r("cb") or 0.0,
        "fold_to_cbet": r("fc") or 0.0,
        "steal":        r("st") or 0.0,
        "donk_bet":     r("dk") or 0.0,
        "wtsd":         r("ws") or 0.0,
        "af":           _af(recent_hands),
        "_window":      n,
    }


# ─── Hero analysis ────────────────────────────────────────────────────────────

def analyze_hero(stats: dict) -> dict:
    """
    Returns:
      leaks      — sorted list of {severity, title, detail, tip}
      strengths  — list of str
      overall    — one-sentence summary
      priority   — most important leak dict, or None
      leak_count — int
      grade      — A/B/C/D/F
      window     — int (how many recent hands were used)
      using_recent — bool
    """
    # ── Decide which stats to use ─────────────────────────────────────────────
    recent_hands = stats.get("recent_hands", [])
    MIN_RECENT   = 20   # minimum hands in recent window to use it

    if len(recent_hands) >= MIN_RECENT:
        src        = calc_recent_stats(recent_hands)
        window     = src["_window"]
        using_recent = True
    else:
        src        = stats          # fall back to all-time
        window     = stats.get("hands", 0)
        using_recent = False

    vpip         = src.get("vpip", 0)
    pfr          = src.get("pfr", 0)
    threebet     = src.get("threebet", 0)
    fourbet      = src.get("fourbet", 0)
    squeeze      = src.get("squeeze", 0)
    af           = src.get("af", 0)
    cbet         = src.get("cbet", 0)
    fold_cbet    = src.get("fold_to_cbet", 0)
    fold_3bet    = src.get("fold_to_3bet", 0)
    steal        = src.get("steal", 0)
    wtsd         = src.get("wtsd", 0)
    cold_call    = src.get("cold_call", 0)
    donk_bet     = src.get("donk_bet", 0)
    gap          = vpip - pfr

    total_hands  = stats.get("hands", 0)

    # Position stats always use all-time (rarely enough recent data per-position)
    pos_btn = stats.get("pos_btn", {})
    pos_ep  = stats.get("pos_ep", {})

    leaks: list[dict] = []
    strengths: list[str] = []

    def leak(severity: int, title: str, detail: str, tip: str):
        leaks.append({"severity": severity, "title": title, "detail": detail, "tip": tip})

    if total_hands < 30:
        return {
            "leaks": [], "strengths": [],
            "overall": f"Amostra insuficiente ({total_hands} maos) - jogue mais para analise precisa",
            "priority": None, "leak_count": 0, "grade": "?",
            "window": 0, "using_recent": False,
        }

    # ── Preflop leaks ─────────────────────────────────────────────────────────

    if vpip > 38:
        leak(3, f"VPIP muito alto ({vpip}%)",
             "Voce esta entrando em muitos potes com maos fracas. Isso cria situacoes dificeis pos-flop onde voce frequentemente tem a pior mao.",
             "Reduza para 22-28% em 6-max. Antes de entrar, pergunte: 'Esta mao lucra em posicao?'")
    elif vpip > 30:
        leak(2, f"VPIP elevado ({vpip}%)",
             "Acima do ideal para 6-max. Pode estar limping ou calling demais com maos marginais.",
             "Mire em 22-28%. Corte combos fracos: Ax offsuit baixos, J8o, T7o.")
    elif vpip < 14 and total_hands > 60:
        leak(2, f"VPIP muito baixo ({vpip}%)",
             "Voce e previsivel quando entra - oponentes sabem que voce tem mao forte e pagam pouco.",
             "Expanda para 20-28%. Adicione suited connectors, PPs pequenos e broadways.")
    else:
        strengths.append(f"VPIP calibrado ({vpip}%) - range preflop adequado para 6-max")

    if gap > 14:
        leak(3, f"Limp excessivo (gap VPIP-PFR = {gap:.0f}%)",
             "Entrar sem raise da odd barata para todo mundo, revela fraqueza e coloca voce OOP sem iniciativa.",
             "Regra: se nao vale um raise, provavelmente nao vale entrar. Substitua 100% dos limps por raises ou folds.")
    elif gap > 8:
        leak(2, f"Limping moderado (gap = {gap:.0f}%)",
             "Voce esta limping em algumas situacoes. Isso enfraquece sua linha e da informacao gratis.",
             "Mantenha gap < 6%. Aceite limp apenas no SB ocasionalmente com maos playable.")
    else:
        strengths.append(f"Pouco limping (gap {gap:.0f}%) - bom habito preflop")

    if threebet < 4 and total_hands > 60:
        leak(2, f"3-bet muito baixo ({threebet}%)",
             "Voce esta deixando EV na mesa ao nao re-raisear steal attempts. Oponentes te exploram abrindo largo.",
             "Adicione 3-bet bluff com: A2s-A5s (blocker), KQo, QJo IP. Mire 6-10% em 6-max.")
    elif threebet > 15:
        leak(2, f"3-bet excessivo ({threebet}%)",
             "Range de 3-bet desequilibrado. Voce esta 3-betando maos sem equity suficiente.",
             "Reduza para 7-11%. Tenha range polarizado: maos premium + bluffs com blocker.")
    elif 6 <= threebet <= 11:
        strengths.append(f"3-bet frequencia adequada ({threebet}%)")

    if fold_3bet > 72:
        leak(3, f"Folda muito para 3-bet ({fold_3bet}%)",
             "Seus opens sao facilmente exploitaveis. Oponentes podem 3-bet voce com qualquer duas cartas lucrativamente.",
             "Reduza fold-to-3bet para 55-65%. Adicione 4-bet bluffs (A5s, A4s, KQo) e calls IP com PPs e SC.")
    elif fold_3bet > 62:
        leak(1, f"Fold to 3-bet um pouco alto ({fold_3bet}%)",
             "Ainda ok, mas margem de exploracao existe.",
             "Adicione alguns 4-bet bluffs (~3%) para balancear. A5s e KQo sao bons candidatos.")

    if steal < 28 and total_hands > 60:
        leak(2, f"Steal baixo ({steal}%)",
             "Voce nao esta aproveitando posicao no BTN/CO/SB para atacar blinds. Em torneios custa fichas valiosas.",
             "No BTN/CO abra 35-50% quando folded to. Em Hyper-Turbo com stack curto, agressividade e fundamental.")
    elif steal >= 40:
        strengths.append(f"Bom steal ({steal}%) - aproveitando posicao regularmente")

    if cold_call > 22 and total_hands > 50:
        leak(2, f"Cold-call alto ({cold_call}%)",
             "Entrar flat com raise a frente (sem re-raise) coloca voce sem iniciativa. Spots dificeis pos-flop.",
             "Prefira 3-bet ou fold. Cold-call so IP com speculative hands (PPs, SC) quando pot odds justificam.")

    # ── Postflop leaks ────────────────────────────────────────────────────────

    if cbet > 82 and total_hands > 40:
        leak(2, f"C-bet automatico ({cbet}%)",
             "Apostar todo flop sem selecionar board texture e exploitavel. Oponentes podem check-raise em boards ruins.",
             "Selecione c-bets: aposte em boards high/dry que favorecem sua range como PFR. Skip em boards low-connected OOP.")
    elif cbet < 45 and total_hands > 40:
        leak(2, f"C-bet muito baixo ({cbet}%)",
             "Voce esta desistindo da iniciativa preflop. Checar como PFR frequentemente cede o controle.",
             "Mire 55-72% c-bet. Em posicao suba mais. Sempre aposte valor hands + bluffs balanceados.")
    elif 52 <= cbet <= 78 and total_hands > 40:
        strengths.append(f"C-bet bem calibrado ({cbet}%)")

    if fold_cbet > 68:
        leak(2, f"Folda muito para c-bets ({fold_cbet}%)",
             "Oponentes podem c-bet quase qualquer flop contra voce lucrativamente.",
             "Defenda mais: float calls IP com overcards/gutshot, check-raise em boards de bluff com draws.")
    elif fold_cbet < 30 and total_hands > 40:
        leak(2, f"Chama muita c-bet ({fold_cbet}% fold)",
             "Defender demais leva a spots dificeis no turn sem equity.",
             "Seja mais seletivo: fold maos com pouca equity e sem backdoors.")
    elif 38 <= fold_cbet <= 62 and total_hands > 40:
        strengths.append(f"Boa defesa de c-bet ({fold_cbet}% fold)")

    if af < 1.5 and total_hands > 50:
        leak(3, f"Jogo muito passivo pos-flop (AF {af})",
             "Voce esta chamando quando deveria apostar ou raisear. Da showdown value barato para oponentes.",
             "Seja mais agressivo: bet/raise com top-pair+, draws com equity, e bluffs em posicao com fold equity.")
    elif af < 2.2:
        leak(1, f"Levemente passivo pos-flop (AF {af})",
             "Margem de melhoria na agressividade pos-flop.",
             "Adicione mais bets em posicao e check-raises OOP com seus melhores draws e valor.")
    elif af >= 3.0:
        strengths.append(f"Boa agressividade pos-flop (AF {af})")

    if wtsd > 38:
        leak(2, f"Vai ao showdown demais ({wtsd}%)",
             "Voce esta pagando com maos que provavelmente nao vencem. EV negativo.",
             "Seja mais disciplinado no river. Fold maos medias (one pair fraco) contra multi-street aggression.")
    elif wtsd < 16 and total_hands > 50:
        leak(1, f"Vai ao showdown de menos ({wtsd}%)",
             "Pode estar foldando boas maos no river.",
             "Revise folds no river. Com pot odds corretas (>33%), top-pair razoavel deve ir ao showdown.")
    elif 20 <= wtsd <= 32:
        strengths.append(f"WTSD equilibrado ({wtsd}%)")

    if donk_bet > 28 and total_hands > 40:
        leak(1, f"Donk bet frequente ({donk_bet}%)",
             "Apostar OOP sem iniciativa expoe range fraco e perde valor de maos fortes.",
             "Prefira check-call ou check-raise OOP. Use donk bet raramente e com proposito especifico.")

    # ── Positional leaks (always use all-time) ────────────────────────────────

    if pos_btn.get("hands", 0) >= 15:
        btn_vpip = pos_btn.get("vpip", 0)
        if btn_vpip < 32:
            leak(2, f"Tight demais no BTN (VPIP {btn_vpip}%)",
                 "O BTN e a melhor posicao - posicao garantida por toda a mao. Voce esta desperdicando EV.",
                 "No BTN com fold to you: abra 40-55%. Mire PFR BTN > 35%.")

    if pos_ep.get("hands", 0) >= 15:
        ep_vpip = pos_ep.get("vpip", 0)
        if ep_vpip > 26:
            leak(2, f"VPIP alto UTG/EP ({ep_vpip}%)",
                 "Posicao ruim exige range tight. Maos marginais UTG tem problemas se 3-betadas ou em multi-way.",
                 "Em UTG/EP: reduza para 12-18% VPIP. Foque em maos que toleram 3-bet (QQ+, AKs, AQs+).")

    # ── Grade + overall ───────────────────────────────────────────────────────
    leaks.sort(key=lambda x: -x["severity"])
    critical = sum(1 for l in leaks if l["severity"] == 3)
    major    = sum(1 for l in leaks if l["severity"] == 2)

    if critical >= 2 or (critical + major) >= 5:
        grade   = "D"
        overall = "Varios vazamentos criticos - foque nos fundamentos preflop primeiro"
    elif critical == 1 or major >= 3:
        grade   = "C"
        overall = "Jogo com padroes exploraveis claros - priorize o vazamento principal"
    elif major <= 2 and critical == 0:
        grade   = "B"
        overall = "Jogo solido com alguns pontos a refinar"
    elif not leaks:
        grade   = "A"
        overall = "Jogo equilibrado - continue refinando frequencias e sizing"
    else:
        grade   = "B"
        overall = "Base boa com 1-2 ajustes que fariamdiferenca"

    if not strengths and not leaks:
        strengths.append("Continue jogando para acumular dados suficientes")

    return {
        "leaks":        leaks,
        "strengths":    strengths,
        "overall":      overall,
        "priority":     leaks[0] if leaks else None,
        "leak_count":   len(leaks),
        "grade":        grade,
        "window":       window,
        "using_recent": using_recent,
    }
