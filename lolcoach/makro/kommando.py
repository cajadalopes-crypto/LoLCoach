"""Das Kommando: "Tu X: weil Y. Danach Z." - Warten ist ein Kommando. Keine internen Begriffe."""
from __future__ import annotations

import re
from dataclasses import dataclass

KLASSEN = ("gefahr", "objective", "rest")      # Vorrang in dieser Reihenfolge (vorrang.py)
# "danach"-Teile, die schon selbst einen Anschluss haben: nicht noch "Danach" davor
EIGENE_ANFAENGE = ("danach", "dann", "erst", "jetzt", "bis", "in ", "tp ist", "sofort", "warten", "nicht", "direkt", "sonst")


@dataclass
class Kommando:
    id: str                 # Nummer aus Buch 17, Teil B (S1 ... Z3)
    tu: str                 # was
    weil: str               # warum
    danach: str = ""        # was danach
    klasse: str = "rest"    # gefahr / objective / rest
    wert: float = 0.0       # Siegchance-Punkte oder Gewicht fuer den Rest

    @property
    def text(self) -> str:
        trenner = " – " if ":" in self.tu else ": "
        s = f"{_gross(self.tu)}{trenner}{self.weil}."
        if self.danach:
            d = self.danach.strip()
            eigen = d.lower().startswith(EIGENE_ANFAENGE)
            s += f" {_gross(d)}." if eigen else f" Danach {d}."
        return sprechbar(jetzt_statt_null(s.replace("..", ".")))


def jetzt_statt_null(s: str) -> str:
    """Stufe 4: live steht ein Monster oft schon (spawn_in 0) - "der Drache ist in 0 s" heisst dann "der Drache steht
    jetzt", "in 0 s" sonst "jetzt"."""
    s = re.sub(r"\bist in 0 s(?=[.,;:]|$)", "steht jetzt", s)
    return re.sub(r"\bin 0 s\b", "jetzt", s)


# Stufe 4 (Auftrag 034): die Saetze aus 032 schreiben Umlaute als ae/oe/ue und ss statt ß ("fuer", "zurueck") - die
# Stimme spricht das falsch. Ersetzt werden nur bekannte Wortstaemme (nie "Feuer", "Aatrox", "Quelle").
STAEMME = {"drueck": "drück", "kaempf": "kämpf", "faell": "fäll", "gebaeude": "gebäude", "naeh": "näh", "tuerm": "türm",
           "ueber": "über", "zurueck": "zurück", "fuer": "für", "gehoer": "gehör", "haeufig": "häufig", "koenn": "könn",
           "laeuft": "läuft", "muess": "müss", "naechst": "nächst", "raeum": "räum", "spaet": "spät", "staerk": "stärk",
           "gruend": "gründ", "rueck": "rück", "groess": "größ", "moeglich": "möglich", "waehl": "wähl",
           "zerstoer": "zerstör", "frueh": "früh", "pruef": "prüf", "hoeh": "höh", "oeffn": "öffn", "waer": "wär",
           "unterstuetz": "unterstütz", "schuetz": "schütz", "aelter": "älter", "aeltest": "ältest", "laeng": "läng",
           "fuehr": "führ", "zaehl": "zähl", "haelt": "hält", "laess": "läss", "traeg": "träg", "schaetz": "schätz",
           "waechst": "wächst", "haett": "hätt", "moecht": "möcht", "duerf": "dürf", "wuerd": "würd", "koepf": "köpf",
           "kuerz": "kürz", "luecke": "lücke", "gegenueber": "gegenüber", "rueckprall": "rückprall", "saeub": "säub",
           "haelfte": "hälfte", "aender": "änder", "tuer": "tür", "schluess": "schlüss", "stuetz": "stütz",
           "muede": "müde", "haend": "händ", "laed": "läd", "fuell": "füll", "kaeuf": "käuf", "gewaehr": "gewähr",
           "spaeh": "späh", "flaech": "fläch", "zuerst": "zuerst"}
SZ = {"fuss": "fuß", "weisst": "weißt", "gross": "groß", "grosse": "große", "grossen": "großen", "heiss": "heiß",
      "stoss": "stoß", "gruess": "grüß", "draussen": "draußen", "ausserhalb": "außerhalb", "aussen": "außen",
      "schliesslich": "schließlich", "blossen": "bloßen", "mass": "maß", "massen": "maßen"}
_STAMM = re.compile("|".join(sorted(STAEMME, key=len, reverse=True)), re.I)
_SZ = re.compile(r"\b(" + "|".join(sorted(SZ, key=len, reverse=True)) + r")\b", re.I)


def _wie(alt: str, neu: str) -> str:
    return neu[:1].upper() + neu[1:] if alt[:1].isupper() else neu


def sprechbar(text: str) -> str:
    """ae/oe/ue/ss aus den Kommando-Texten als Umlaut und ß - nur fuer bekannte Stamm-Woerter."""
    text = _STAMM.sub(lambda m: _wie(m.group(0), STAEMME[m.group(0).lower()]), text)
    return _SZ.sub(lambda m: _wie(m.group(0), SZ[m.group(0).lower()]), text)


def _gross(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def sek(s: float | None) -> str:
    """Sekunden fuers Sprechen: '25 s', '1:30 min'."""
    if s is None:
        return "?"
    s = max(0, int(round(s)))
    return f"{s} s" if s < 90 else f"{s // 60}:{s % 60:02d} min"
