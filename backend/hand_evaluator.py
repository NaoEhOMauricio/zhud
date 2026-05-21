"""
Hand evaluator — given two hole cards and a position, tells the player
what to do: which range group the hand belongs to, or fold if outside range.
"""

RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
RANK_IDX = {r: i for i, r in enumerate(RANKS)}


def normalize_hand(r1: str, r2: str, suited: bool) -> str:
    """Returns canonical hand string: 'AKs', 'AKo', 'AA'."""
    r1, r2 = r1.upper(), r2.upper()
    if r1 == r2:
        return r1 + r2
    if RANK_IDX[r1] < RANK_IDX[r2]:
        r1, r2 = r2, r1
    return r1 + r2 + ('s' if suited else 'o')


def _expand(token: str) -> set:
    """Expand one range token to a set of canonical hand strings."""
    token = token.strip()
    if not token:
        return set()
    plus = token.endswith('+')
    if plus:
        token = token[:-1]

    # Pair: "AA", "TT+"
    if len(token) == 2 and token[0].upper() == token[1].upper():
        r = token[0].upper()
        if r not in RANK_IDX:
            return set()
        if plus:
            return {RANKS[i] * 2 for i in range(RANK_IDX[r], 13)}
        return {r + r}

    # Pair range: "JJ-22"
    if (len(token) == 5 and token[2] == '-'
            and token[0].upper() == token[1].upper()
            and token[3].upper() == token[4].upper()):
        hi_r, lo_r = token[0].upper(), token[3].upper()
        if hi_r not in RANK_IDX or lo_r not in RANK_IDX:
            return set()
        lo_i = min(RANK_IDX[hi_r], RANK_IDX[lo_r])
        hi_i = max(RANK_IDX[hi_r], RANK_IDX[lo_r])
        return {RANKS[i] * 2 for i in range(lo_i, hi_i + 1)}

    # Offsuit/suited range: "AQo-A2o", "KTs-K2s"
    if '-' in token:
        parts = token.split('-')
        if (len(parts) == 2 and len(parts[0]) == 3 and len(parts[1]) == 3):
            h1, l1, s1 = parts[0][0].upper(), parts[0][1].upper(), parts[0][2].lower()
            h2, l2, s2 = parts[1][0].upper(), parts[1][1].upper(), parts[1][2].lower()
            if h1 == h2 and s1 == s2 and s1 in ('s', 'o'):
                lo_i = min(RANK_IDX[l1], RANK_IDX[l2])
                hi_i = max(RANK_IDX[l1], RANK_IDX[l2])
                return {h1 + RANKS[i] + s1
                        for i in range(lo_i, hi_i + 1)
                        if RANKS[i] != h1}
        return set()

    # Suited/offsuit single or "+": "AKs", "ATo+"
    if len(token) == 3:
        h, l, suit = token[0].upper(), token[1].upper(), token[2].lower()
        if h not in RANK_IDX or l not in RANK_IDX or suit not in ('s', 'o'):
            return set()
        if RANK_IDX[h] < RANK_IDX[l]:
            h, l = l, h
        if plus:
            return {h + RANKS[i] + suit for i in range(RANK_IDX[l], RANK_IDX[h])}
        return {h + l + suit}

    return set()


def parse_range(range_str: str) -> set:
    """Parse a range string like 'TT+, AQo+, AJs+, KQs' into a set of hands."""
    hands: set = set()
    for token in range_str.replace(',', ' ').split():
        hands |= _expand(token)
    return hands


# ── Per-position, per-group machine-readable ranges ───────────────────────────
POSITION_GROUPS: dict = {
    "ep": [
        ("Abre + re-raise (4bet)",  "red",    "KK+ AKs",
         "4bet/call vs qualquer re-raise. Mão premium."),
        ("Abre + chama 3bet",       "orange", "QQ JJ TT AKo AQs",
         "Abra 2.5x, chame 3bet e vá para showdown."),
        ("Abre + fold a 3bet",      "yellow", "AJs KQs",
         "Abra 2.5x, mas fold vs 3bet agressivo. OOP difícil."),
    ],
    "hj": [
        ("Abre + 4bet",             "red",    "KK+ AKs",
         "4bet/call. Mão premium, não perca valor."),
        ("Abre + chama 3bet",       "orange", "QQ JJ TT AKo AQo",
         "Abra 2.5x, chame 3bet."),
        ("Abre + fold a 3bet",      "yellow", "99 AJo ATs+ A9s KTo+ KJs QJs JTs",
         "Abra 2.5x, fold vs 3bet — mão marginal OOP."),
    ],
    "co": [
        ("Abre + 4bet",             "red",    "KK+ AKs AKo",
         "4bet/call. Não subestime AKo no CO."),
        ("Abre + chama 3bet",       "orange", "QQ JJ TT 99 AQo AJs",
         "Abra 2.5x, chame 3bet com posição."),
        ("Abre + fold a 3bet",      "yellow", "88-22 ATo A8s+ KJo+ K9s+ QJo QTs+ JTs T9s",
         "Abra 2.5x, fold vs 3bet — muita equity perdida OOP."),
    ],
    "btn": [
        ("Abre + 4bet",             "red",    "KK+ QQ AKs AKo",
         "4bet/call. Você é BTN — maxvalue."),
        ("Abre + chama 3bet",       "orange", "JJ TT 99 AQo AJs+ KQs",
         "Abra 2-2.5x, chame 3bet IP."),
        ("Abre + fold a 3bet",      "yellow", "88-22 ATo A2s+ KJo K5s+ QJs JTs T9s 98s 87s",
         "Abra 2x, fold vs 3bet — mão especulativa."),
        ("Abre largo (vs passivos)", "blue",  "Q5s+ Q9o+ J6s+ JTo T7s+ T9o 76s 65s 54s",
         "Abra vs blinds passivos. Fold vs 3bet ou defensores ativos."),
    ],
    "sb": [
        ("Abre + 4bet",             "red",    "KK+ AKs AKo",
         "4bet/call. Mão premium mesmo OOP."),
        ("Abre + chama 3bet",       "orange", "QQ JJ TT AQo AJs",
         "Abra 3x, chame 3bet. Jogue direto pós-flop."),
        ("Abre + fold a 3bet (OOP)", "yellow", "99-22 ATo A2s+ KTs+ KJo+ QJs JTs T9s 98s",
         "Abra 3x, fold vs 3bet. Você é OOP toda a mão."),
    ],
    "bb": [
        ("3bet para valor",         "red",    "KK+ AKs AKo QQ",
         "3bet sempre. Não slow-play AA/KK no BB."),
        ("3bet bluff (blockers)",   "orange", "A5s A4s A3s A2s KJs",
         "3bet bluff: tem blocker de Nut + equity pós-flop."),
        ("Defende vs raise ≤3BB",   "yellow",
         "JJ-22 AQo-A2o AQs-A2s KQo-K2o KQs-K2s QJo-Q2o QJs-Q2s JTo-J2o JTs-J2s T9o-T2o T9s-T2s",
         "Você tem pot odds. Chame e jogue pós-flop."),
        ("Fold vs raise ≥4BB",      "gray",
         "72o 83o 92o 73o 84o 93o 82o 74o 63o 52o",
         "Fold vs raise grande — lixo sem equity."),
    ],
}

OPEN_RANGE_STR: dict = {
    "ep":  "TT+ AQo+ AJs+ KQs",
    "hj":  "TT+ AJo+ A9s+ KTo+ KJs QJs JTs",
    "co":  "99+ ATo+ A8s+ KJo+ K9s+ QJo QTs+ JTs T9s",
    "btn": "22+ A2s+ ATo+ K5s+ KJo+ Q5s+ Q9o+ J6s+ JTo T7s+ T9o 87s 76s 65s 54s",
    "sb":  "22+ A2s+ ATo+ KTs+ KJo+ QJs JTs T9s 98s",
    "bb":  "",   # BB defends based on pot odds — almost everything
}

OPEN_RANGE_STR_FR: dict = {
    "ep": "JJ+ AQo+ AJs+ KQs",
    "hj": "TT+ AJo+ ATs+ KJo+ KTs QJs JTs",
}

# Explicit trash hands that fold even in BB vs large raise
_BB_FOLD_VS_BIG = parse_range("72o 83o 92o 73o 84o 93o 82o 74o 63o 52o 64o 53o")


def evaluate_hand(r1: str, r2: str, suited: bool,
                  position: str, stack_bb: float = 40,
                  n_players: int = 6) -> dict:
    pos  = (position or "ep").lower()
    hand = normalize_hand(r1, r2, suited)

    base_range_str = OPEN_RANGE_STR.get(pos, "")
    if n_players >= 7 and pos in OPEN_RANGE_STR_FR:
        base_range_str = OPEN_RANGE_STR_FR[pos]

    # BB: everything except absolute trash is "in range"
    if pos == "bb":
        in_range = hand not in _BB_FOLD_VS_BIG
    else:
        in_range = hand in parse_range(base_range_str)

    # Find matching group
    groups = POSITION_GROUPS.get(pos, [])
    matched_group = None
    for label, color, rng_str, action in groups:
        if hand in parse_range(rng_str):
            matched_group = (label, color, action)
            break

    # Stack overrides
    extra = ""
    if stack_bb <= 10:
        extra = " Stack crítico: all-in ou fold diretamente."
    elif stack_bb <= 15 and in_range:
        extra = " Stack curto: prefira push direto."

    # Full-ring EP tightening
    if n_players >= 7 and pos == "ep" and in_range and not matched_group:
        in_range = False

    if not in_range:
        return {
            "hand":     hand,
            "in_range": False,
            "group":    "Fora do range — fold",
            "color":    "gray",
            "action":   "FOLD",
            "advice":   f"{hand} está fora do range para {pos.upper()}. Fold pré-flop.",
        }

    if matched_group:
        label, color, action = matched_group
        return {
            "hand":     hand,
            "in_range": True,
            "group":    label,
            "color":    color,
            "action":   action.split(".")[0],
            "advice":   action + extra,
        }

    # In range but no specific group — generic advice per position
    generic = {
        "bb": f"{hand} no BB — chame raise pequeno (≤3BB) com pot odds. Fold vs 4BB+.",
        "sb": f"{hand} no SB — abra 3x vs BB passivo. Fold vs 3bet.",
    }.get(pos, f"{hand} no range de {pos.upper()} — abra e jogue situacionalmente.{extra}")

    return {
        "hand":     hand,
        "in_range": True,
        "group":    "No range — jogue",
        "color":    "orange",
        "action":   "Abra / Defenda",
        "advice":   generic,
    }
