"""
PokerStars hand history parser.
Supports: English + PT-BR, cash games + tournaments, standard + Zoom.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedHand:
    hand_id: str
    table_name: str
    game_type: str          # cash | tournament
    small_blind: float
    big_blind: float
    players: dict           # seat_num -> {name, stack}
    button_seat: int
    actions: list           # [{player, street, action, amount}]
    winners: list           # [{player, amount}]
    preflop_aggressor: Optional[str]
    showdown_players: list
    hand_time: Optional[str] = None   # ISO datetime string from HH header


# ─── Regex patterns (EN + PT-BR) ──────────────────────────────────────────────

# Hand header — just capture the ID; blinds parsed separately
_RE_HAND_ID = re.compile(r"PokerStars\s+(?:Hand|Mão)\s+#(\d+)")

# Hand timestamp: "2026/05/18 21:38:19"
_RE_HAND_TIME = re.compile(r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})")

# Tournament level blinds: "Level II (10/20)" or "Nível II (10/20)"
_RE_TOURN_LEVEL = re.compile(r"(?:Level|Nível)\s+\w+\s+\((\d+)/(\d+)\)")

# Cash game blinds: "($0.10/$0.25)" or "(0.10/0.25)"
# Also handles PT-BR "US$ 0,91" format (comma decimal)
_RE_CASH_BLINDS = re.compile(r"\(\$?(?:US\$\s*)?([\d.,]+)/\$?(?:US\$\s*)?([\d.,]+)")

# Table line — EN: "Table 'Name' 6-max Seat #3 is the button"
#              PT-BR: "Mesa 'Name' 6 Máx Lugar #3 é o dealer"
# Uses search() + \s+ for robustness against spacing/encoding variations
_RE_TABLE = re.compile(
    r"(?:Table|Mesa)\s+'(.+?)'\s+\S.*?\s+(?:Seat|Lugar)\s+#(\d+)\s+(?:is the button|é o dealer)",
    re.IGNORECASE,
)

# Fallback: extract just the table name from any line containing Table/Mesa keyword
_RE_TABLE_FALLBACK = re.compile(r"(?:Table|Mesa)\s+'(.+?)'", re.IGNORECASE)

# Tournament ID from hand header — used as fallback table name
_RE_TOURN_ID = re.compile(r"(?:Tournament|Torneio)\s+#(\d+)", re.IGNORECASE)

# Seat/Lugar line — EN: "Seat 1: Name ($25.00 in chips)"  or  "(1500 in chips, $0.36 bounty)"
#                   PT-BR: "Lugar 1: Nome (1500 em fichas)"
_RE_SEAT = re.compile(
    r"(?:Seat|Lugar) (\d+): (.+?) \(\$?([\d.,]+) (?:in chips|em fichas)"
)

# Blind posts (to exclude from VPIP)
_RE_BLIND = re.compile(
    r"^.+?: (?:posts|posta) (?:small|big|small & big|blind pequeno|blind grande|blind pequeno e grande)"
)

# Action line — covers EN and PT-BR verbs, with optional "to/para" clause
_RE_ACTION = re.compile(
    r"^(.+?): (folds|calls|raises|bets|checks|is all-in"
    r"|desiste|paga|aumenta|aposta|passa|é all-in)"
    r"(?:\s+\$?([\d.]+))?(?:\s+(?:to|para)\s+\$?([\d.]+))?"
)

_ACTION_MAP = {
    "folds":      "fold",
    "desiste":    "fold",
    "calls":      "call",
    "paga":       "call",
    "raises":     "raise",
    "aumenta":    "raise",
    "bets":       "bet",
    "aposta":     "bet",
    "checks":     "check",
    "passa":      "check",
    "is all-in":  "allin",
    "é all-in":   "allin",
}

# Pre-summary winner: "NaoEOMauricio collected 900 from pot"
_RE_WINNER_INLINE = re.compile(r"^(.+?) (?:collected|recolheu) \$?([\d.]+)")

# Summary winner: "Seat 2: Name (big blind) collected (900)"
_RE_WINNER_SUMMARY = re.compile(
    r"(?:Seat|Lugar) \d+: (.+?) \(.+?\) (?:collected|recolheu) [\$\(]?([\d.]+)"
)

# Showdown / mucked lines in SUMMARY block
_RE_SHOWED = re.compile(
    r"(?:Seat|Lugar) \d+: (.+?) (?:showed|mostrou|mucked|desistiu|não mostrou)"
)


def _parse_amount(s: str) -> float:
    """
    Parse amount string handling both EN (1.50) and PT-BR (1,50 or 1.500,50) formats.
    Also strips 'US$' prefix if present.
    """
    s = s.strip().replace("US$", "").replace("R$", "").strip()
    # PT-BR: comma is decimal separator, dot is thousands separator
    if "," in s and "." in s:
        # e.g. "1.500,50" → remove dots, replace comma with dot
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # e.g. "0,91" → replace comma with dot
        s = s.replace(",", ".")
    # else: already "0.91" or "1500"
    try:
        return float(s)
    except ValueError:
        return 0.0


class HandParser:

    def parse_text(self, text: str) -> list:
        parts = re.split(r"\n\n(?=PokerStars)", text)
        hands = []
        for part in parts:
            part = part.strip()
            if "PokerStars" in part:
                h = self._parse_hand(part)
                if h:
                    hands.append(h)
        return hands

    def parse_file_from(self, filepath: str, offset: int) -> tuple:
        """Read from byte offset, return (hands, new_offset).
        Tries UTF-8-BOM first (modern PokerStars), then cp1252 (Windows Latin-1 fallback).
        """
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    f.seek(offset)
                    text = f.read()
                    new_offset = f.tell()
                # Sanity check: valid parse if "PokerStars" is in the text
                if "PokerStars" not in text:
                    return [], offset
                return self.parse_text(text), new_offset
            except UnicodeDecodeError:
                continue
        # Absolute fallback
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            text = f.read()
            new_offset = f.tell()
        return self.parse_text(text), new_offset

    # ── Internal ──────────────────────────────────────────────────────────────

    def _parse_hand(self, text: str) -> Optional[ParsedHand]:
        lines = text.split("\n")
        if not lines:
            return None

        # ── Hand ID ───────────────────────────────────────────────────────────
        hid_m = _RE_HAND_ID.search(lines[0])
        if not hid_m:
            return None
        hand_id = hid_m.group(1)

        # ── Game type ─────────────────────────────────────────────────────────
        game_type = "tournament" if ("Tournament" in lines[0] or "Torneio" in lines[0]) else "cash"

        # ── Hand timestamp ────────────────────────────────────────────────────
        hand_time = None
        ht_m = _RE_HAND_TIME.search(lines[0])
        if ht_m:
            try:
                from datetime import datetime as _dt
                hand_time = _dt.strptime(ht_m.group(1), "%Y/%m/%d %H:%M:%S").isoformat()
            except ValueError:
                pass

        # ── Blinds ────────────────────────────────────────────────────────────
        sb, bb = 0.01, 0.02
        tourn_m = _RE_TOURN_LEVEL.search(lines[0])
        if tourn_m:
            sb = float(tourn_m.group(1))
            bb = float(tourn_m.group(2))
        else:
            cash_m = _RE_CASH_BLINDS.search(lines[0])
            if cash_m:
                sb = _parse_amount(cash_m.group(1))
                bb = _parse_amount(cash_m.group(2))

        # ── Table + button ────────────────────────────────────────────────────
        table_name = ""
        button_seat = 0

        # Try full regex (search, not match — robust to leading chars/spaces)
        for line in lines[:10]:
            tm = _RE_TABLE.search(line)
            if tm:
                table_name = tm.group(1).strip()
                try:
                    button_seat = int(tm.group(2))
                except ValueError:
                    pass
                break

        # Fallback 1: extract just the table name from Table/Mesa line
        if not table_name:
            for line in lines[:10]:
                fb = _RE_TABLE_FALLBACK.search(line)
                if fb:
                    table_name = fb.group(1).strip()
                    break

        # Fallback 2: use tournament ID as table name
        if not table_name and game_type == "tournament":
            tid_m = _RE_TOURN_ID.search(lines[0])
            if tid_m:
                table_name = f"T{tid_m.group(1)}"

        # ── Seats ─────────────────────────────────────────────────────────────
        players = {}
        for line in lines:
            sm = _RE_SEAT.match(line)
            if sm:
                seat  = int(sm.group(1))
                name  = sm.group(2).strip()
                stack = _parse_amount(sm.group(3))
                players[seat] = {"name": name, "stack": stack}
            # Stop at first street marker
            if "*** HOLE CARDS ***" in line or "*** CARTAS DO BARALHO ***" in line:
                break

        if not players:
            return None

        # ── Actions + section markers ─────────────────────────────────────────
        actions = []
        current_street = "preflop"
        in_summary = False
        preflop_aggressor = None
        pf_raise_count = 0
        winners = []
        showdown_players = []

        for line in lines:
            # Section markers
            if "*** HOLE CARDS ***" in line or "*** CARTAS DO BARALHO ***" in line:
                current_street = "preflop"
                continue
            if re.match(r"\*\*\* FLOP \*\*\*", line):
                current_street = "flop"
                continue
            if re.match(r"\*\*\* TURN \*\*\*", line):
                current_street = "turn"
                continue
            if re.match(r"\*\*\* RIVER \*\*\*", line):
                current_street = "river"
                continue
            if "*** SHOW DOWN ***" in line or "*** SHOWDOWN ***" in line:
                current_street = "showdown"
                continue
            if "*** SUMMARY ***" in line or "*** RESUMO ***" in line:
                in_summary = True
                continue

            # Summary block
            if in_summary:
                wm = _RE_WINNER_SUMMARY.search(line)
                if wm:
                    winners.append({
                        "player": wm.group(1).strip(),
                        "amount": _parse_amount(wm.group(2)),
                    })
                sm2 = _RE_SHOWED.search(line)
                if sm2:
                    showdown_players.append(sm2.group(1).strip())
                continue

            # Pre-summary inline winner: "Player collected 900 from pot"
            wm_inline = _RE_WINNER_INLINE.match(line)
            if wm_inline:
                pname = wm_inline.group(1).strip()
                # Only count if player is actually at the table
                if any(info["name"] == pname for info in players.values()):
                    if not any(w["player"] == pname for w in winners):
                        winners.append({
                            "player": pname,
                            "amount": _parse_amount(wm_inline.group(2)),
                        })
                continue

            # Skip blind posts
            if _RE_BLIND.match(line):
                continue

            # Parse action
            am = _RE_ACTION.match(line)
            if am:
                player = am.group(1).strip()
                raw    = am.group(2)
                # prefer "to/para" amount over raw amount
                amt_str = am.group(4) or am.group(3)
                amount  = _parse_amount(amt_str) if amt_str else 0.0
                action  = _ACTION_MAP.get(raw, raw)

                if current_street == "preflop":
                    if action in ("raise", "allin", "bet"):
                        pf_raise_count += 1
                        preflop_aggressor = player

                actions.append({
                    "player":        player,
                    "street":        current_street,
                    "action":        action,
                    "amount":        amount,
                    "pf_raise_count": pf_raise_count if current_street == "preflop" else 0,
                })

        return ParsedHand(
            hand_id=hand_id,
            table_name=table_name,
            game_type=game_type,
            small_blind=sb,
            big_blind=bb,
            players=players,
            button_seat=button_seat,
            actions=actions,
            winners=winners,
            preflop_aggressor=preflop_aggressor,
            showdown_players=showdown_players,
            hand_time=hand_time,
        )
