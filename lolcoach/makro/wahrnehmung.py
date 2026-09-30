"""Welche Live-Eingabe gibt es heute, welche fehlt (Buch 17, "Was der Coach dafuer live sehen muss").

Stand 30.09.2026, geprueft am Code: minimap.py (Champions, Flash-Spruenge), lage.py (zuletzt gesehen, TP-/Ult-Spruenge),
hud.py (Mitspieler-Leben und -Ult, eigene Q W E R D F), welle.py (Wellenstand - heute nur die eigene Lane),
platten.py (Platten-Ziffer), zauber.py (Flash-/TP-Timer aus Chat-Pings und Spruengen), liveapi.py (Scoreboard,
Ereignisse, Uhr, eigenes Gold, Items). Fehlt: eigene Wards auf der Minimap, Trinket-Ladungen, Beschwoererzauber der
Mitspieler, Wellen der anderen Lanes, zuverlaessiger TP-Stand der Gegner, Recall des Gegners, Objective-Kopfgeld.
"""
from __future__ import annotations

# Name -> (Quelle, heute live?)
EINGABEN: dict[str, tuple[str, bool]] = {
    "uhr": ("Live-API gameTime", True),
    "ereignisse": ("Live-API Ereignisse (Kills, Tuerme, Monster, Ace)", True),
    "scoreboard": ("Live-API allPlayers: Level, KDA, CS, tot + Respawn", True),
    "eigene_items": ("Live-API: eigene Items, Gold, Kontroll-Auge im Inventar, Trinket", True),
    "gegner_items": ("Live-API: Gegner-Items 'wie zuletzt gesehen'", True),
    "kaufplan": ("lolcoach/kaufplan.py: Gold bis zum naechsten Bauteil", True),
    "eigene_position": ("Minimap: eigenes Icon", True),
    "mitspieler_positionen": ("Minimap: Mitspieler (immer sichtbar)", True),
    "gegner_sichtungen": ("Minimap + lage.Lagebild: zuletzt gesehen, Ort und Alter", True),
    "mitspieler_hud": ("HUD-Leiste: Leben und Ult der Mitspieler", True),
    "eigene_zauber": ("HUD: eigene Q W E R D F bereit (auch TP)", True),
    "gegner_flash": ("zauber.py: Flash-Timer aus Minimap-Spruengen und Chat", True),
    "tp_sprung": ("lage.py: TP-Sprung eines Gegners auf der Minimap", True),
    "welle_eigen": ("welle.py: Wellenstand der eigenen Lane", True),
    "platten": ("platten.py: Platten-Ziffer der Tuerme", True),
    "monster_timer": ("Ereignisse + wissen/objektive.toml", True),
    "chat": ("texterkennung.py: Pings im Chat", True),
    "kampf": ("Minimap: Champions beider Teams eng beieinander + Ereignisse", True),
    # fehlt heute -> Auftrag 033
    "wellen_alle": ("Minimap: Wellen der anderen Lanes", False),
    "eigene_wards": ("Minimap: eigene Wards (Ort, Ablauf, zerstoert)", False),
    "trinket_ladungen": ("HUD: Trinket-Ladungen", False),
    "mitspieler_zauber": ("HUD: Beschwoererzauber der Mitspieler (Flash)", False),
    "tp_stand_gegner": ("zuverlaessiger TP-Stand der Gegner (heute nur nach gesehenem Sprung)", False),
    "gegner_recall": ("Spielbild/Minimap: Lane-Gegner beginnt Recall", False),
    "kopfgeld": ("Minimap: markierte Objective-Kopfgelder", False),
    "busch_sicht": ("Spielbild: Busch vor dir ohne Sicht", False),
}


def fehlt(eingaben) -> list[str]:
    return [e for e in eingaben if not EINGABEN[e][1]]


def gibt_es(name: str) -> bool:
    return name in EINGABEN
