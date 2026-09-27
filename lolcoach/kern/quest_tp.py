"""Quest-Teleport der Toplane (Saison 2026): `m.tp_in` fuer Top-Spieler ohne Teleport als Beschwoererzauber.

saison2026.md, Rollenquests: wer Top KEIN Teleport nimmt, bekommt mit der Quest (spaetestens 13:35) ein Quest-TP im
Quest-Slot (Taste V), 390 s Abklingzeit (26.19). Die Live-API zeigt davon nichts - kein Beschwoererzauber, kein
Gegenstand, kein Ereignis (gemessen 27.09.2026 an vier Riven-Partien). Deshalb, Werte in kern.toml [quest_tp]:
  - bereit ab Quest-Ende (`quest_ende_s`, die Regel - gemessen war die Quest schon 9:46 bis 12:07 fertig),
  - `abklingzeit_s` weg nach einem erkannten eigenen Teleport: dein Icon steht binnen `fenster_s` mindestens
    `sprung_min` Einheiten weiter, schneller als man laeuft (`tempo_min`; aus der Basis `tempo_basis_min`, dort
    traegt dich die Heimgarde), nicht in der Basis (das waere ein Recall), nicht ueber einen Tod hinweg. Verworfen,
    wenn das naechste Bild binnen `bestaetigt_s` wieder naeher am Absprung steht (falsch zugeordnetes Einzelbild).
    Nach dem Teleport verliert die Minimap dein Icon oft fuer 30 s - darauf wird nicht gewartet.
Gelesen wird nur, was die Minimap wirklich fand (`lb.verlauf`), nicht `lb.gesehen`: dort haelt das Lagebild dich
auch unter fremden Icons fest, und das Umspringen auf dein echtes Icon sah aus wie ein Teleport (164326 35:15).
Ein erkannter Teleport vor dem Quest-Ende beweist das Quest-Ende mit.
"""
from __future__ import annotations

from collections import deque

from .. import minimap
from ..bewertung import abstand, einheiten


def _basis(x: float, y: float) -> bool:
    return "Basis" in minimap.ort(x, y)


class QuestTP:
    def __init__(self, cfg: dict | None):
        self.c = cfg
        self.spur: deque = deque()          # (Spielzeit, x, y) deiner Sichtungen der letzten fenster_s
        self.kandidat: tuple | None = None  # (Zeit, Landung, Absprung) bis bestaetigt_s ohne Widerspruch
        self.benutzt: float | None = None   # Spielzeit der letzten erkannten Landung
        self.gelesen = -1e9                 # Zeit der letzten verarbeiteten Sichtung

    def gilt(self, p) -> bool:
        ich = getattr(p, "ich", None)
        return bool(self.c and ich is not None and ich.rolle == "TOP" and getattr(p, "modus", None) in self.c["modi"]
                    and not any("Teleport" in z for z in (ich.zauber or ())))

    def tp_in(self, p, lb, zeit: float) -> float | None:
        """Sekunden bis das Quest-TP bereit ist (0 = bereit). None: gilt nicht, oder die Quest ist nicht sicher fertig."""
        if not self.gilt(p):
            return None
        self._beobachten(p, lb, zeit)
        if self.benutzt is not None:
            return max(0.0, self.benutzt + self.c["abklingzeit_s"] - zeit)
        return 0.0 if zeit >= self.c["quest_ende_s"] else None

    def _beobachten(self, p, lb, zeit: float) -> None:
        if p.ich.tot:                      # nach dem Tod stehst du im Brunnen - das ist kein Sprung
            self.spur.clear()
            self.kandidat = None
            return
        verlauf = getattr(lb, "verlauf", None)
        for t, x, y in list((verlauf or {}).get((p.ich.name, p.ich.team), ())):
            if t > self.gelesen:
                self.gelesen = t
                self._bild(t, x, y)
        if self.kandidat is not None and zeit - self.kandidat[0] > self.c["bestaetigt_s"]:
            self._benutzt(self.kandidat[0])            # nichts hat widersprochen

    def _bild(self, t: float, x: float, y: float) -> None:
        c = self.c
        hier = einheiten(x, y)
        if self.kandidat is not None:
            tk, landung, absprung = self.kandidat
            if t - tk <= c["bestaetigt_s"]:
                self.kandidat = None
                if abstand(hier, landung) < abstand(hier, absprung):
                    self._benutzt(tk)
                else:                      # das Einzelbild ist auch kein Absprung fuer den Weg zurueck
                    while self.spur and self.spur[-1][0] >= tk:
                        self.spur.pop()
            else:
                self._benutzt(tk)
        if _basis(x, y):                   # Recall oder Brunnen: was davor lag, ist kein Absprung mehr
            self.spur.clear()
        while self.spur and self.spur[0][0] < t - c["fenster_s"]:
            self.spur.popleft()
        frei = self.benutzt is None or t >= self.benutzt + c["abklingzeit_s"]
        if frei and self.kandidat is None and t >= c["sprung_ab_s"] and not _basis(x, y):
            for t0, x0, y0 in self.spur:
                d = abstand(einheiten(x0, y0), hier)
                grenze = c["tempo_basis_min"] if _basis(x0, y0) else c["tempo_min"]
                if d >= c["sprung_min"] and d >= grenze * (t - t0):
                    self.kandidat = (t, hier, einheiten(x0, y0))
                    break
        self.spur.append((t, x, y))

    def _benutzt(self, t: float) -> None:
        self.benutzt, self.kandidat = t, None
        self.spur.clear()
