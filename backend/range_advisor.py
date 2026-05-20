"""
Real-time preflop range advisor.
Ranges baseados em GTO para 6-max (cash + torneio Hyper-Turbo).
Princípio: posição é tudo — range abre mais IP, fecha mais OOP.
"""

# ── Ranges de abertura GTO por posição (6-max) ───────────────────────────────
OPEN_RANGES = {
    "ep": {  # UTG
        "pct": 15,
        "label": "UTG / Early Position",
        "hands": "TT+, AQo+, AJs+, KQs",
        "tip": "UTG você abre para 5 jogadores. Apenas mãos que toleram 3bet e jogam bem OOP.",
        "sizing": "2.5x (3x se stack < 30BB)",
        "groups": [
            {"label": "Abre + re-raise (4bet)",    "color": "red",    "hands": "KK+, AKs"},
            {"label": "Abre + chama 3bet",          "color": "orange", "hands": "QQ, JJ, TT, AKo, AQs"},
            {"label": "Abre + faz fold a 3bet",     "color": "yellow", "hands": "AJs, KQs"},
            {"label": "Fora do range — fold",       "color": "gray",   "hands": "Qualquer outra mão"},
        ],
    },
    "hj": {
        "pct": 20,
        "label": "Hijack (HJ)",
        "hands": "TT+, AJo+, A9s+, KTo+, KJs, QJs, JTs",
        "tip": "HJ: range intermediário. Respeite CO e BTN atrás que podem 3bet.",
        "sizing": "2.5x",
        "groups": [
            {"label": "Abre + 4bet",                "color": "red",    "hands": "KK+, AKs"},
            {"label": "Abre + chama 3bet",          "color": "orange", "hands": "QQ, JJ, TT, AKo, AQo"},
            {"label": "Abre + fold a 3bet",         "color": "yellow", "hands": "99, AJo, A9s+, KTo+, KJs, QJs, JTs"},
            {"label": "Fora do range — fold",       "color": "gray",   "hands": "Suited connectors baixos, Kxo, pares <99"},
        ],
    },
    "co": {
        "pct": 30,
        "label": "Cutoff (CO)",
        "hands": "99+, ATo+, A8s+, KJo+, K9s+, QJo, QTs+, JTs, T9s",
        "tip": "CO é sua segunda melhor posição. Abra firme — se BTN não 3betou você nos últimos limites, abra mais.",
        "sizing": "2.5x",
        "groups": [
            {"label": "Abre + 4bet",                "color": "red",    "hands": "KK+, AKs, AKo"},
            {"label": "Abre + chama 3bet",          "color": "orange", "hands": "QQ, JJ, TT, 99, AQo, AJs"},
            {"label": "Abre + fold a 3bet",         "color": "yellow", "hands": "ATo, A8s+, KJo+, K9s+, QJo, QTs+, JTs, T9s"},
            {"label": "Fora do range — fold",       "color": "gray",   "hands": "88-, K8s-, suited connectors <T9s, Q8o-"},
        ],
    },
    "btn": {
        "pct": 45,
        "label": "Botão (BTN) — posição mais lucrativa",
        "hands": "Todos pares, Ax, Kx, Q5s+, Q9o+, J6s+, JTo, T7s+, T9o, 97s+, 87s, 76s, 65s, 54s",
        "tip": "BTN: você terá posição por toda a mão. Abra muito largo vs SB/BB passivos. Reduza vs 3-bettors frequentes.",
        "sizing": "2.0-2.5x",
        "groups": [
            {"label": "Abre + 4bet se 3betado",     "color": "red",    "hands": "KK+, AKs, AKo, QQ"},
            {"label": "Abre + chama 3bet",          "color": "orange", "hands": "JJ, TT, 99, AQo, AJs+, KQs"},
            {"label": "Abre + fold a 3bet",         "color": "yellow", "hands": "88-22, ATo, A2s+, KJo, K5s+, QJs, JTs, T9s, 98s, 87s"},
            {"label": "Abre largo (vs passivos)",   "color": "blue",   "hands": "Q5s+, Q9o+, J6s+, T7s+, 76s, 65s, 54s"},
        ],
    },
    "sb": {
        "pct": 35,
        "label": "Small Blind (SB)",
        "hands": "Pares, Ax, KTs+, KJo+, QJs, JTs, T9s, 98s",
        "tip": "SB vs apenas BB: abra com força. Use sizing maior (3x) pois jogará OOP por toda a mão.",
        "sizing": "3x (OOP sempre merece raise maior)",
        "groups": [
            {"label": "Abre + 4bet",                "color": "red",    "hands": "KK+, AKs, AKo"},
            {"label": "Abre + chama 3bet",          "color": "orange", "hands": "QQ, JJ, TT, AQo, AJs"},
            {"label": "Abre + fold a 3bet (OOP)",   "color": "yellow", "hands": "99-22, ATo, A2s+, KTs+, KJo+, QJs, JTs, T9s, 98s"},
            {"label": "Fora do range — fold",       "color": "gray",   "hands": "Suited connectors baixos, K9o-, Q9o-"},
        ],
    },
    "bb": {
        "pct": 0,
        "label": "Big Blind (BB) — defesa",
        "hands": "Definido pelos pot odds do raise",
        "tip": "BB: você já investiu 1BB. Pot odds permitem defender muito mais do que intuitivo. Não over-fold.",
        "sizing": "—",
        "groups": [
            {"label": "3bet (re-raise)",             "color": "red",    "hands": "KK+, AKs, QQ (valor) + A5s, A4s, KJs (bluff)"},
            {"label": "Chama e defende",             "color": "orange", "hands": "JJ-22, AQo-A2o, KTo+, QJo, suited connectors"},
            {"label": "Chama vs 2BB, fold vs 4BB+", "color": "yellow", "hands": "Mãos médias: Q8o, J7s, 96s, 85s"},
            {"label": "Fold mesmo no BB",            "color": "gray",   "hands": "72o, 83o, 92o e lixo extremo"},
        ],
    },
}

# ── Tabela de defesa do BB por tamanho do raise ───────────────────────────────
BB_DEFENSE = [
    {"size": "2BB",   "equity": "33%", "range": "Quase tudo (90%+ hands) — fold apenas 72o, 83o e lixo extremo"},
    {"size": "2.5BB", "equity": "38%", "range": "Amplo — pares, Ax, KJo+, QJs+, suited connectors, broadways"},
    {"size": "3BB",   "equity": "43%", "range": "Médio — pares 22+, A9o+, A5s+, KQo, KJs, QJs+"},
    {"size": "4BB+",  "equity": "50%", "range": "Apertado — TT+, AQo+, ATs+, KQs"},
]

# ── Ajustes por stack depth (Hyper-Turbo) ────────────────────────────────────
STACK_ADJUSTMENTS = [
    (50, "Stack profundo — use ranges completos acima."),
    (30, "Stack médio (20-50BB) — feche UTG/HJ, mantenha BTN/SB largos."),
    (15, "Stack curto (10-20BB) — push/fold ativo. Raramente open-raise pequeno."),
    (0,  "Stack crítico (<10BB) — ALL-IN ou FOLD apenas. Veja aba Push/Fold."),
]

# ── Posições IP vs OOP ────────────────────────────────────────────────────────
IP_POSITIONS  = {"co", "hj", "btn"}
OOP_POSITIONS = {"sb", "ep"}

# ── Erros comuns que o sistema detecta ───────────────────────────────────────
MISTAKES = {
    "limp": {
        "title": "Limp — maior vazamento de EV preflop",
        "body":  "Entrar sem raise dá odd barata para todos, revela fraqueza e coloca você OOP sem iniciativa. "
                 "Regra: se não vale um raise, não vale entrar. 100% dos limps viram raise ou fold.",
    },
    "ep_loose": {
        "title": "VPIP alto em UTG — range OOP difícil de jogar",
        "body":  "UTG abre para 5 jogadores com 3bets possíveis de qualquer posição. "
                 "Prefira TT+, AQo+, AJs+. Mãos como 87s só têm valor com muitos callers IP — raramente acontece.",
    },
    "btn_tight": {
        "title": "Jogando tight demais no BTN — perdendo EV",
        "body":  "BTN é a maior fonte de EV em 6-max. Com fold to you, abra 40-50%. "
                 "Inclua suited connectors, pares pequenos, AXs. Você tem posição garantida.",
    },
    "bb_overfold": {
        "title": "Over-folding no BB",
        "body":  "Vs raise 2.5x você precisa de apenas 38% equity para chamar — isso é MUITO amplo. "
                 "Defenda pares, Ax, suited connectors, broadways. Não dê o BB de graça.",
    },
}


def get_range_tips(hero_position: str, opponents: list, hero_stats: dict = None,
                   hero_stack_bb: float = 50) -> dict:
    """
    Retorna dicas de range por posição + ajustes vs oponentes específicos.
    """
    pos = (hero_position or "ep").lower()
    rng = OPEN_RANGES.get(pos, OPEN_RANGES["ep"])

    tips     = []
    warnings = []

    # ── 1. Dica base de abertura ──────────────────────────────────────────────
    if pos != "bb":
        tips.append({
            "icon": "🎯",
            "title": f"Abertura: ~{rng['pct']}% das mãos ({rng['label']})",
            "body":  rng["hands"],
            "detail": f"Sizing: {rng['sizing']}. {rng['tip']}",
        })
    else:
        tips.append({
            "icon": "🛡",
            "title": "BB — use os pot odds",
            "body":  "Sua defesa depende do tamanho do raise. Veja a tabela abaixo.",
            "detail": rng["tip"],
        })

    # ── 2. Ajuste de stack (Hyper-Turbo) ──────────────────────────────────────
    for threshold, msg in STACK_ADJUSTMENTS:
        if hero_stack_bb >= threshold:
            if threshold < 50:
                warnings.append({
                    "icon": "📉",
                    "title": f"Stack {hero_stack_bb:.0f}BB — ajuste de range",
                    "body":  msg,
                    "detail": "Em Hyper-Turbo os stacks ficam curtos rápido. Veja Push/Fold na aba dedicada.",
                })
            break

    # ── 3. Vazamentos do próprio jogo ─────────────────────────────────────────
    if hero_stats:
        vpip = hero_stats.get("vpip", 0) or 0
        pfr  = hero_stats.get("pfr", 0) or 0
        gap  = vpip - pfr

        if gap > 10:
            m = MISTAKES["limp"]
            warnings.append({"icon": "⚠", "title": m["title"], "body": m["body"], "detail": ""})

        if pos == "ep" and vpip > 22:
            m = MISTAKES["ep_loose"]
            warnings.append({"icon": "⚠", "title": m["title"], "body": m["body"], "detail": ""})

        if pos == "btn" and vpip < 32:
            m = MISTAKES["btn_tight"]
            warnings.append({"icon": "💡", "title": m["title"], "body": m["body"], "detail": ""})

        if pos == "bb" and (hero_stats.get("fold_to_cbet", 0) or 0) > 65:
            m = MISTAKES["bb_overfold"]
            warnings.append({"icon": "⚠", "title": m["title"], "body": m["body"], "detail": ""})

    # ── 4. Dicas vs oponentes específicos ────────────────────────────────────
    for opp in (opponents or []):
        if (opp.get("hands") or 0) < 15:
            continue

        nick      = opp.get("nickname", "?")
        vpip      = opp.get("vpip",       0) or 0
        pfr       = opp.get("pfr",        0) or 0
        threebet  = opp.get("threebet",   0) or 0
        fold_3bet = opp.get("fold_to_3bet", 0) or 0
        steal     = opp.get("steal",      0) or 0
        profile   = opp.get("profile",    "") or ""

        # Folda muito p/ 3bet → 3bet light
        if fold_3bet > 68 and pos in ("btn", "co", "sb", "hj"):
            tips.append({
                "icon": "🔥",
                "title": f"3bet light vs {nick} — folda {fold_3bet:.0f}% p/ 3bet",
                "body":  "Use A5s-A2s (blocker + backdoors), KJo, QJo, T9s como 3bets bluff. ~40% do range de 3bet.",
                "detail": "Range de 3bet equilibrado: 60% valor (TT+, AQo+) + 40% bluff com blockers e equity.",
            })

        # 3bet agressivo → cuidado
        if threebet > 12:
            tips.append({
                "icon": "⚠",
                "title": f"Cuidado: {nick} 3bet {threebet:.0f}% — encolha range",
                "body":  "Prefira mãos premium que toleram 3bet: TT+, AQo+. 4bet bluff com A5s, A4s (blockers).",
                "detail": "Vs 3-bettor frequente: 4bet/fold com A5s ou chame IP com SC/pares pequenos.",
            })

        # Calling Station → value puro
        if vpip > 42 and pfr < 22:
            tips.append({
                "icon": "💰",
                "title": f"Value pesado vs {nick} (Calling Station, VPIP {vpip:.0f}%)",
                "body":  "Bet grande (70-100% pot) com top pair+. Nunca blefe. Simplifique: bet/bet/bet com valor.",
                "detail": "Stations pagam — não complique. Bet direto, bet grande. Não tente fazer fold.",
            })

        # Nit steala pouco — BTN pode roubar
        if steal < 25 and pos == "btn":
            tips.append({
                "icon": "🏹",
                "title": f"vs {nick} (steal baixo {steal:.0f}%) no BTN — abra mais",
                "body":  "Jogador tight não defende muito. Amplie range BTN para 50%+ com fold to you.",
                "detail": "Vs nit nos blinds: inclua K5s+, Q8s+, J8o+, T8s+ no range de abertura BTN.",
            })

        # SB agressivo → defesa BB
        if pos == "bb" and steal > 45:
            tips.append({
                "icon": "🛡",
                "title": f"Defenda BB vs steal de {nick} ({steal:.0f}% steal)",
                "body":  "Ele abre muito. No BB defenda amplo: pares, Ax, suited connectors, broadways.",
                "detail": "Vs steal frequente você tem pot odds implícitas. Não dê o blind de graça — 3bet às vezes.",
            })

    # ── 5. Dica IP vs OOP ─────────────────────────────────────────────────────
    if pos in IP_POSITIONS:
        tips.append({
            "icon": "📍",
            "title": "Você está IP — use a posição",
            "body":  "Float com mãos médias, bet no turn quando ele checar duas vezes. Inclua SC e pares pequenos.",
            "detail": "IP você vê a ação do adversário antes de agir. Mais informação = mais lucro.",
        })
    elif pos in OOP_POSITIONS:
        tips.append({
            "icon": "⚠",
            "title": "Você está OOP — jogue mais tight e direto",
            "body":  "Prefira mãos com valor próprio (pares grandes, broadways fortes). Bet/fold ou check/call — evite linhas complicadas.",
            "detail": "OOP você age antes do adversário. Simplifique: não tente linhas criativas sem posição.",
        })

    return {
        "position":    pos,
        "label":       rng["label"],
        "open_pct":    rng["pct"],
        "open_hands":  rng["hands"],
        "hand_groups": rng.get("groups", []),
        "tips":        tips[:5],
        "warnings":    warnings[:3],
        "bb_defense":  BB_DEFENSE if pos == "bb" else None,
        "is_ip":       pos in IP_POSITIONS,
    }
