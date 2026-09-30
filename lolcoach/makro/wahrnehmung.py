"""Welche Live-Eingabe gibt es heute, welche fehlt (Buch 17, "Was der Coach dafuer live sehen muss").

Stand 30.09.2026 (Auftrag 033), geprueft am Code und GEMESSEN an beschrifteten Bildern aus Carlos' Aufnahmen
(buecher/challenger/phase3b_bericht.md, Beschriftungen in buecher/challenger/sehen/). Verlaesslich heisst: Treffer
>= 90 % und Fehlalarme <= 5 % an einer frischen Stichprobe. Was das nicht schafft, steht hier mit False - die
Entscheidung schweigt dann, statt zu raten.

Neu verlaesslich (033): Wellen aller Lanes (welle.py mit Pulk-Zerlegung und Totenkopf-Filter: 26/27 Wellen, 1/27
Fehlalarm), Wards deines Teams (sehen.wards: 116/118, 1/117), Trinket-Ladungen (sehen.trinket: 80/80).
Nicht verlaesslich: wem ein Ward gehoert und wann es weg ist (6-14 % Fehlalarme), Recall des Lane-Gegners (nur die
Haelfte der erkannten bestaetigt), TP-Stand der Gegner (10 Spruenge in 10 Partien - Treffer nicht messbar),
Objective-Kopfgeld (Goldrand lesbar, Bedeutung nicht belegt), Busch ohne Sicht (Minimap-Nebel zu grob), Blitz der
Mitspieler (HUD zeigt ihn nicht, im Chat 0 von 50 Blitz-Pings).
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
    # Auftrag 033 - gemessen (phase3b_bericht.md)
    "wellen_alle": ("Minimap: Wellen aller Lanes (welle.py; Pulks per Schablone, Totenkopf-Filter) - 26/27, 1/27", True),
    "eigene_wards": ("Minimap: Wards deines Teams, Ort und Alter (sehen.wards/Wardspur) - 116/118, 1/117", True),
    "trinket_ladungen": ("HUD: Ladungen des gelben Trinkets (sehen.trinket) - 80/80", True),
    "ward_weg": ("Minimap: eigener Ward weg - wem er gehoert und 'weg' 6-14 % falsch (Icon/Text darueber)", False),
    "mitspieler_zauber": ("Blitz der Mitspieler - HUD zeigt ihn nicht, Chat: 0 von 50 Blitz-Pings", False),
    "tp_stand_gegner": ("TP-Stand der Gegner - 10 Spruenge in 10 Partien erkannt, Treffer nicht messbar", False),
    "gegner_recall": ("Recall des Lane-Gegners - 18 von 36 erkannten bestaetigt (Items/Basis)", False),
    "kopfgeld": ("Objective-Kopfgeld - Goldrand an Tuermen lesbar, Bedeutung nicht belegt, API ohne Ereignis", False),
    "busch_sicht": ("Busch vor dir ohne Sicht - Minimap-Nebel zu grob, nicht gebaut", False),
}


def fehlt(eingaben) -> list[str]:
    return [e for e in eingaben if not EINGABEN[e][1]]


def gibt_es(name: str) -> bool:
    return name in EINGABEN
