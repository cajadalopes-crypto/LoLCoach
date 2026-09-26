LoL AI-Coach: Anforderungen

Sep 26, 2026 · zusammengestellt mit @Carlos

Ziel & Vision

Ein KI-gestütztes Coaching-Tool für League of Legends, das während laufender Ranked-Spiele wie ein menschlicher Coach mitschaut ("zweites Paar Augen") und in Echtzeit erklärt, was zu tun ist und warum.

Zielgruppe: der Spieler selbst  Ziel Diamond und höher.

Funktionsumfang

Durchgehende Begleitung über das gesamte Spiel, nicht nur im Nachhinein

Erkennt Spielsituationen (Gegner-Position auf der Minimap, Item-/Summoner-Status, Score-Verlauf und vieles weitere was hilft fundierte tipps zu geben) und gibt konkrete, umsetzbare Empfehlungen

Erklärt nicht nur WAS zu tun ist, sondern WARUM — Lerneffekt statt Blind-Befolgen

Gibt Rückmeldung, wenn erkennbar etwas suboptimal gespielt wurde ("das war hier ungünstig, weil…" entweder während des spiels oder im after game. Gerne kann die replay funktion benutzt werden um lerninhalte zu veranschaulichen)

Ausgabe per Sprachausgabe (TTS) während des laufenden Spiels

Ergänzt durch eine Post-Game-Analyse für die vertiefte Auswertung ganzer Spiele/Sessions

Datenquellen

Zwei Quellen, kombiniert:

Live Client Data API (offizielle, lokale Riot-Schnittstelle): liefert strukturiert Items, Summoner-Spell-Cooldowns, Gold, CS, KDA, Level und Events (Kills, Objectives) für alle sichtbaren/erlaubten Felder, in Echtzeit 

Echtzeit Bildschirm analyse. 

Beide Quellen zusammen ergeben das vollständige Bild, das auch ein menschlicher Coach beim Zuschauen hätte.

Harte Grenzen (nicht verhandelbar)

Kein Auslesen von Spiel-Prozess-Speicher (Memory Reading), keine Injection, keine "unsichtbaren" Infos wie Gegner-Positionen außerhalb der eigenen Vision. Riots Vanguard-Anticheat erkennt das aktiv; Strafen reichen bis zu Hardware-ID-Bans.

Das Tool sieht ausschließlich das, was der Spieler selbst sehen könnte (Bildschirm) plus offiziell freigegebene, lokale APIs. Keine Inputs oder Automatisierung — reine Beobachtung und Empfehlung, keine Aktionen im Spiel.

Skin-Injection-Tools (z. B. CSLOL) sind technisch unverwandt und liefern für dieses Projekt keinen Mehrwert (reines Asset-Overlay, keine Datenquelle) — zur Klarstellung, falls das als Vorbild diskutiert wird.

Architektur (Vorschlag)

Hier hast du freies spiel. Das ziel kennst du: ein challenger coach mit analystischen fähigkeiten, der mich guided in einem spiel als würde ich für ihn discord live streamen und er mir in echtzeit sagt was ich am besten tun soll, und warum, wo der gegnerische jungler ist etc. als würde ich einfach mit einem coach spielen der mir hilft. Gerne auch mit UI inhalten falls sinnvoll. 

Wissensbasis: Makro-Regelwerk & Meta-Wissen

Damit der Coach nicht nur generisch reagiert, sondern tatsächlich auf hohem Elo-Niveau berät:

Explizites Makro-Regelwerk (Wellenmanagement, Prioritäten, Roam-Fenster, typisches Matchup-Verhalten) als eigene, gepflegte Wissensbasis — nicht nur "aus dem Bauch" des Modells

Aktuelles Meta-/Matchup-Wissen (Champion-Stärken, Build-Pfade, Patch-Stand) separat gepflegt und regelmäßig aktualisiert, da reines Modell-Trainingswissen nach jedem Patch veraltet

Knowledge zu allen champions damit tiefanalytisch entschieden werden kann. 
