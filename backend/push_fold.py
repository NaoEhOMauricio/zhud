"""
Push/Fold ranges for 6-max Hyper-Turbo SNGs.
Based on simplified ICM / Nash equilibrium approximations.
Each entry: (max_stack_bb, push_pct, hand_description)
"""

# Format: position -> list of (max_bb, push_pct, hands_to_push)
# When stack <= max_bb, use that row.
RANGES: dict = {
    "BTN": [
        (6,  100, "Qualquer duas cartas"),
        (8,  88,  "Quase tudo — fold apenas 72o, 82o e similares"),
        (10, 75,  "Pares, Ax, Kx, Q6s+, Q9o+, J7s+, JTo, T8s+, T9o, 98s, 87s"),
        (12, 65,  "Pares, Ax, KTs+, KJo+, Q8s+, QTo+, J9s+, JTo, T9s"),
        (15, 55,  "Pares, ATo+, ATs+, KJs+, KQo, QTs+, QJo, JTs"),
        (20, 0,   "Jogo normal — raise/fold padrão"),
    ],
    "CO": [
        (6,  82,  "Pares, Ax, Kx, Q5s+, Q8o+, J7s+, T8s+, 98s"),
        (8,  66,  "Pares 33+, A4o+, A2s+, K8o+, K7s+, QTo+, Q8s+, JTo, J9s+"),
        (10, 54,  "Pares 44+, A7o+, A4s+, KTo+, K9s+, QJo, QTs+, JTs"),
        (12, 46,  "Pares 55+, A8o+, A5s+, KJo+, KTs+, QJs"),
        (15, 38,  "Pares 77+, ATo+, ATs+, KQo, KJs+"),
        (20, 0,   "Jogo normal"),
    ],
    "SB": [
        (6,  100, "Qualquer duas cartas vs BB"),
        (8,  85,  "Pares, Ax, K5o+, K4s+, Q7o+, Q5s+, J8o+, J7s+, T9s"),
        (10, 71,  "Pares, A6o+, A3s+, K9o+, K7s+, QTo+, Q8s+, JTs"),
        (12, 62,  "Pares, A8o+, A5s+, KTo+, K9s+, QTs+"),
        (15, 53,  "Pares, AJo+, ATs+, KQo, KJs+, QJs"),
        (20, 0,   "Jogo normal"),
    ],
    "HJ": [
        (6,  70,  "Pares, Ax, K7o+, K5s+, Q8o+, Q6s+, J8o+, J7s+, T9s, T8s"),
        (8,  56,  "Pares 33+, A5o+, A3s+, K9o+, K8s+, QTo+, Q9s+, JTs"),
        (10, 44,  "Pares 55+, A8o+, A5s+, KJo+, KTs+, QJs"),
        (12, 37,  "Pares 77+, ATo+, A9s+, KQo, KJs+"),
        (15, 30,  "Pares 99+, AQo+, AJs+"),
        (20, 0,   "Jogo normal"),
    ],
    "UTG": [
        (6,  64,  "Pares, A5o+, A2s+, K8o+, K7s+, QTo+, Q8s+, J9s+"),
        (8,  50,  "Pares 44+, A7o+, A4s+, KTo+, K9s+, QJo, QTs+"),
        (10, 38,  "Pares 66+, A9o+, A7s+, KQo, KJs+, QJs"),
        (12, 31,  "Pares 88+, AJo+, ATs+, KQs"),
        (15, 25,  "Pares TT+, AKo, AQs+"),
        (20, 0,   "Jogo normal"),
    ],
    "BB": [
        (6,  60,  "Chame push com quase tudo — pot odds excelentes"),
        (8,  46,  "Call com Pares, Ax, KTo+, KTs+, QJo, QTs+, JTs"),
        (10, 37,  "Call com Pares 44+, A8o+, A5s+, KJo+, KTs+"),
        (12, 30,  "Call com Pares 77+, ATo+, ATs+, KQs"),
        (15, 24,  "Call com Pares 99+, AQo+, AJs+"),
        (20, 0,   "Jogo normal"),
    ],
}

# Positions in order from BTN to UTG (for display)
POSITION_ORDER = ["BTN", "CO", "HJ", "UTG", "SB", "BB"]
POSITION_LABELS = {
    "BTN": "Botão (BTN)",
    "CO": "Cutoff (CO)",
    "HJ": "Hijack (HJ)",
    "UTG": "Under the Gun (UTG)",
    "SB": "Small Blind (SB)",
    "BB": "Big Blind (BB)",
}


def get_recommendation(position: str, stack_bb: float) -> dict:
    """
    Get push/fold recommendation for a given position and stack.
    Returns dict with push_pct, hands, action, and advice.
    """
    pos = position.upper()
    rows = RANGES.get(pos)
    if not rows:
        return {"action": "normal", "push_pct": 0, "hands": "Posição inválida", "advice": ""}

    for max_bb, push_pct, hands in rows:
        if stack_bb <= max_bb:
            if push_pct == 0:
                return {
                    "action": "normal",
                    "push_pct": 0,
                    "hands": hands,
                    "advice": f"Stack de {stack_bb:.0f}BB — use jogo normal (raise/fold 2.0-2.5x)",
                }
            action = "call" if pos == "BB" else "push"
            label = "CALL" if pos == "BB" else "ALL-IN"
            advice = _build_advice(pos, stack_bb, push_pct)
            return {
                "action": action,
                "label": label,
                "push_pct": push_pct,
                "hands": hands,
                "advice": advice,
                "stack_bb": round(stack_bb, 1),
            }

    # Stack > 20BB
    return {"action": "normal", "push_pct": 0, "hands": "Jogo normal", "advice": "Stack profundo — use linha normal"}


def _build_advice(pos: str, stack: float, pct: float) -> str:
    if pos == "BB":
        return f"Com {stack:.0f}BB no BB, você precisa defender ~{pct}% vs push — pot odds exigem call amplo"
    if pct >= 80:
        return f"Stack crítico ({stack:.0f}BB). Push ou fold — não abra pequeno. Vá all-in com qualquer mão playable"
    if pct >= 60:
        return f"Stack curto ({stack:.0f}BB). Push all-in com ~{pct}% das mãos em {pos}"
    return f"Com {stack:.0f}BB em {pos}, push all-in com top {pct}% do range"
