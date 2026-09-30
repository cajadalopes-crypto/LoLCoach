"""Auftrag 028, 6.3: Carlos' Widerspruch wird eine Sperre fuer ALLE Stimmen - Kern, Herzschlag, Events, Stratege,
Antworten. 134020: nach 16:20, 19:42 und 20:03 ("kein Elixier mitten im Spiel") antwortete Claude "Du hast recht" -
und der Kern empfahl das Elixier trotzdem 22:17, 25:05 und 32:31; 3:17-3:56 wollte Carlos freezen, der Coach sagte
dreimal "crash".

Eine Sperre gilt fuer den Rest der Partie (ein Item, das er nicht will) oder bis sich die Lage klar aendert (ein
Freeze endet mit Tod, Back oder nach FREEZE_S). Sie steht im Stratege-Kontext (SPERREN) und in der Sicherheit des
Kerns (unsicher_jetzt) - was sie trifft, wird nicht gesprochen."""
from __future__ import annotations

import re
from dataclasses import dataclass

FREEZE_S = 120.0

# was Carlos sagt -> was dann nicht mehr gesagt wird
_NEIN = r"\b(kein\w*|nie|niemals|nicht)\b"
_FREEZE = re.compile(r"\b(rein)?fr(ee|ie|e)(s|z)\w*", re.I)
_CRASH = r"\bcrash\w*|\bwelle (rein|drücken)\b|\bdrück (die|deine) (top-|mid-|bot-)?welle\b|\bwelle rein\b|\bpush\w*"
_ELIXIER = re.compile(r"\b(elixi\w*|alexi\w*)", re.I)


@dataclass
class Sperre:
    was: str               # fuer den Stratege-Kontext: "kein Elixier"
    muster: str            # Regex auf einen Satz
    seit: float
    bis: float | None      # Spielzeit, None = Rest der Partie
    bis_tod_oder_back: bool = False


class Einsprueche:
    def __init__(self):
        self.sperren: list[Sperre] = []

    def hoere(self, text: str, zeit: float) -> list[Sperre]:
        """Eine Frage oder Notiz von Carlos: was er ablehnt, wird gesperrt. Die neuen Sperren."""
        t = (text or "").lower()
        neu = []
        if _ELIXIER.search(t) and re.search(_NEIN, t):
            neu.append(Sperre("kein Elixier", r"\belixier\w*", zeit, None))
        if _FREEZE.search(t):
            neu.append(Sperre("nicht crashen oder drücken - er freezt", _CRASH, zeit, zeit + FREEZE_S, True))
        # ein Item, das er ausdruecklich nicht kauft ("ich kaufe kein Dornenpanzer")
        from .. import kaufplan
        for m in re.finditer(r"\bkauf\w* (mir )?(kein\w*|nie) ([\wäöüß' -]{3,40})", t):
            rest = m.group(3)
            for name in kaufplan._nach_name():
                if len(name) >= 5 and name.lower() in rest:
                    neu.append(Sperre(f"kein {name}", re.escape(name), zeit, None))
                    break
        for s in neu:
            self.sperren = [x for x in self.sperren if x.was != s.was] + [s]
        return neu

    def lage(self, zeit: float, tot: bool = False, basis: bool = False) -> list[Sperre]:
        """Die geltenden Sperren; Tod oder Basis beenden die, die nur bis zur naechsten Lage gelten."""
        self.sperren = [s for s in self.sperren if (s.bis is None or zeit <= s.bis)
                        and not (s.bis_tod_oder_back and (tot or basis) and zeit - s.seit > 5.0)]
        return list(self.sperren)

    def trifft(self, satz: str, zeit: float) -> Sperre | None:
        for s in self.sperren:
            if s.seit <= zeit and (s.bis is None or zeit <= s.bis) and re.search(s.muster, satz or "", re.I):
                if re.search(_NEIN + r"[^.]*(" + s.muster + ")", satz, re.I):
                    continue                   # "nicht crashen", "kein Elixier" - das ist die Sperre selbst
                return s
        return None

    def kontext(self, zeit: float) -> str:
        """Fuer den Strategen: "SPERREN (vom Spieler abgelehnt - nie empfehlen): kein Elixier (seit 16:20)"."""
        g = [s for s in self.sperren if s.seit <= zeit and (s.bis is None or zeit <= s.bis)]
        if not g:
            return ""
        return "SPERREN (vom Spieler abgelehnt - nie empfehlen, nicht darueber streiten): " + "; ".join(
            f"{s.was} (seit {int(s.seit // 60)}:{int(s.seit % 60):02d})" for s in g)
