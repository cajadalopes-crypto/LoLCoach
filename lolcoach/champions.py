"""Faktenwissen je Champion aus Data Dragon (championFull.json, de_DE), je Patch.

Nichts hier ist gepflegt: alles kommt aus Riots Dateien der aktuellen
Version (`ddragon.version()`), und mit dem Patch aendert es sich von selbst.
Schluessel sind die Data-Dragon-IDs ("MonkeyKing", "LeeSin") - genau das,
was `Spieler.champion_id` liefert.

    steckbrief("Riven")            -> Text fuer das Sprachmodell
    steckbrief("Riven", kurz=True) -> eine Zeile je Faehigkeit, nur Name + CD
"""
from __future__ import annotations

import re
from functools import lru_cache

from . import ddragon

TASTEN = "QWER"
KLASSEN = {"Fighter": "Kämpfer", "Tank": "Tank", "Mage": "Magier",
           "Assassin": "Assassine", "Marksman": "Schütze", "Support": "Unterstützer"}
LANG_ZEICHEN = 220  # Beschreibung je Faehigkeit im langen Steckbrief


@lru_cache(maxsize=1)
def _alle() -> dict[str, dict]:
    return ddragon._lade("championFull.json")


@lru_cache(maxsize=1)
def _index() -> dict[str, str]:
    """Kleinschreibung von ID und Anzeigename -> ID ("wukong" -> "MonkeyKing")."""
    return {k.lower(): cid for cid, ch in _alle().items() for k in (cid, ch["name"])}


def _champ(champion_id: str) -> dict | None:
    alle = _alle()
    return alle.get(champion_id) or alle.get(_index().get(champion_id.lower(), ""))


def _rein(text: str) -> str:
    """HTML, Platzhalter ({{ e1 }}) und Leerraum-Reste aus Riots Texten entfernen."""
    t = re.sub(r"<br\s*/?>", " ", text)
    t = re.sub(r"<[^>]+>|\{\{[^}]*\}\}", "", t).replace("&nbsp;", " ")
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"\s+([.,;:!?)])", r"\1", t).strip()


def _kuerzen(text: str, grenze: int = LANG_ZEICHEN) -> str:
    """Ganze Saetze bis zur Grenze; mindestens der erste."""
    saetze = re.split(r"(?<=[.!?])\s+", text)
    aus = saetze[0]
    for s in saetze[1:]:
        if len(aus) + 1 + len(s) > grenze:
            break
        aus += " " + s
    return aus


def _zahl(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _cd(werte: list[float]) -> str:
    if not werte or not any(werte):
        return ""
    if len(set(werte)) == 1:
        return f"CD {_zahl(werte[0])} s"
    return "CD " + "/".join(_zahl(w) for w in werte) + " s"


def steckbrief(champion_id: str, kurz: bool = False) -> str:
    ch = _champ(champion_id)
    if not ch:
        return ""
    klassen = ", ".join(KLASSEN.get(t, t) for t in ch.get("tags", []))
    zeilen = [f"{ch['name']} ({klassen})" if kurz else
              f"{ch['name']}, {ch['title']} ({klassen}; Ressource: {ch.get('partype') or 'keine'})"]
    if not kurz:
        p = ch["passive"]
        zeilen.append(f"Passiv: {p['name']} - {_kuerzen(_rein(p['description']))}")
    for taste, s in zip(TASTEN, ch["spells"]):
        kopf = f"{taste}: {s['name']}"
        cd = _cd(s.get("cooldown", []))
        if cd:
            kopf += f" - {cd}"
        if _bewegt_sich(_rein(s["description"] + " " + s.get("tooltip", "")), ch):
            kopf += " (Dash)"  # steht oft nur im Tooltip: Rivens Q/E "springt"
        zeilen.append(kopf if kurz else f"{kopf}. {_kuerzen(_rein(s['description']))}")
    return "\n".join(zeilen)


def ult_cooldown(champion_id: str) -> list[float]:
    ch = _champ(champion_id)
    return [float(x) for x in ch["spells"][3]["cooldown"]] if ch else []


# Bewegungsverben, wie Riots deutsche Texte sie verwenden (ausgezaehlt an
# championFull 16.19). "sprintet"/"saust" sind dort Lauftempo, "Sprung" meist
# ein Abprallen - beides bewusst draussen.
_VERB = re.compile(r"\b(springt|stürmt|stürzt|hüpft|rollt|teleportiert|versetzt|hechtet|"
                   r"katapultiert|rutscht|gleitet|fliegt|zurückgestoßen|weggestoßen)\b")
# Wendungen, die fuer sich sprechen (Amumu, Bel'Veth, Fiora, Tryndamere, Tahm Kench, Bard ...)
_WENDUNG = re.compile(r"teleportiert sich|versetzt sich|\bzieht sich\b|\bzieht (?:[A-ZÄÖÜ]\S* ){1,2}sich\b|"
                      r"sich (?:\S+ ){0,4}(?:heranzuziehen|zu stürzen)|zum Zielort zu teleportieren|"
                      r"bewegt sich schnell|Ausfallschritt|wirbelt zu|taucht ab und|"
                      r"durch das Terrain zu reisen|Hechtrolle|Sprungangriff|Sprungschlag")
_OBJEKT = {"den", "die", "das", "dem", "einen", "eine", "ihn", "es", "alle"}
_PRAEP = {"von", "zu", "auf", "mit", "bei", "um", "an"}
_NEBENSATZ = re.compile(r",\s*(?:der|die|das|dem|den|welche\w*|wodurch|bis|wenn|falls|während|bevor)\b")


def _subjekte(ch: dict) -> set[str]:
    teile = ch["name"].split()
    return {ch["name"], teile[0], teile[-1]}


def _bewegt_sich(text: str, ch: dict) -> bool:
    """Das Verb zaehlt nur, wenn der Champion selbst Subjekt ist: "Riven springt",
    "springt Neeko", "Diana wird zum Mond, springt zu ..." - nicht "die Kugel
    fliegt", "springt Pix zu", "ein Kristall, der fliegt"."""
    if _WENDUNG.search(text):
        return True
    namen = _subjekte(ch)
    for m in _VERB.finditer(text):
        satz = re.split(r"(?<=[a-zäöüß0-9)])[.!?] ", text[:m.start()])[-1]
        danach = text[m.end():m.end() + 40]
        nach = danach.split()
        if re.match(r" (?:\S+ )?in die Luft", danach):  # Xayah/Neeko: hoch, am selben Ort runter
            continue
        if nach and nach[0] in _OBJEKT:  # "teleportiert den Champion" bewegt einen anderen
            continue
        davor = [w.strip(",") for w in satz.split()[-4:]]
        if (any(w in namen and (i == 0 or davor[i - 1] not in _PRAEP) for i, w in enumerate(davor))
                or (nach and nach[0] in namen)
                or re.match(r" (?:er|sie) (?:in eine Richtung|auf die|zu|zum|nach vorn|vorwärts)\b", danach)
                or ((satz.startswith(ch["name"]) or satz.split()[:1] == [ch["name"].split()[0]])
                    and not _NEBENSATZ.search(satz))):
            return True
    return False


@lru_cache(maxsize=256)
def hat_blink_oder_dash(champion_id: str) -> bool:
    """Grob aus den Faehigkeitstexten: hat der Champion einen Sprung/Dash/Teleport?"""
    ch = _champ(champion_id)
    if not ch:
        return False
    return any(_bewegt_sich(_rein(s["description"] + " " + s.get("tooltip", "")), ch)
               for s in ch["spells"])


@lru_cache(maxsize=1)
def _zauber() -> dict[str, dict]:
    return ddragon._lade("summoner.json")


def zauber_cooldown(schluessel: str) -> float:
    """Beschwoererzauber, z. B. "SummonerFlash" -> 300.0; unbekannt -> 0.0."""
    z = _zauber().get(schluessel)
    return float(z["cooldown"][0]) if z and z.get("cooldown") else 0.0
