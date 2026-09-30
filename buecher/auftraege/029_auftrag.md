# Auftrag 029 – Challenger-Gehirn, Phase 0: Prüfung der Daten (Claude, Chat, 30.09.2026 15:10)

**Guthaben: 0 $** (Sparprotokoll, Buch 16). Keine Testpartien, starte den Coach nicht.

**Läuft parallel zu 028** in einem eigenen Fenster. Daher gilt:
- Nur **neue Dateien** unter `werkzeuge/challenger/` und `buecher/challenger/`.
- Nichts in `lolcoach/` ändern.
- Nur die eigenen Pfade committen.

**Grundlage:** `buecher/17_makro_gehirn.md`, Teil A. **Entscheidungen von Carlos (30.09.2026 15:09):**
- Kommando-Stil: „Tu dies, tu jenes“ mit Warum. Die Wahl im Spiel trifft Carlos.
- Die Flash-Timer bleiben.

## Ziel

Vor jedem Modell wird geprüft, was die Partien wirklich hergeben. Carlos soll an einem Tag sehen, ob echte Analyse
herauskommt. Bauweise für die späteren Phasen:
- Ein **Entscheider aus Daten** wählt die Aktion. Claude formuliert nur noch.
- **Lage → Aktion → Folge:** 30, 60 und 120 s später, dazu die Siegchance.
- **Kein Maphack:** Eine Lage enthält nur, was der Spieler wissen kann: eigenes Team, Scoreboard, allen angesagte
  Ereignisse (Kills, Türme, Objectives).

## 1. Datenbestand prüfen (`daten/riot/`, auch alles, was der laufende Download neu bringt)

- Anzahl, Patch (`gameVersion`), Queue, Dauer. Remakes und Partien unter 15 min heraus.
- Rollen vollständig (`teamPosition`), Doppelte, Zeitleiste vorhanden.
- **Liga je Spieler:** drei Abrufe der Challenger-, Grandmaster- und Master-Liste mit dem Schlüssel aus
  `geheim/riot_key.txt`. Den Schlüssel nie ausgeben. Ergebnis ist eine Zuordnung Spieler → Liga.
- Tabelle: wie viele Spieler-Partien je Liga und je Rolle.

## 2. Feldkatalog

Alle Felder, die in Match und Zeitleiste wirklich vorkommen, mit Füllquote. Dazu eine Liste dessen, was fehlt: Wellen,
Ward-Orte, Nebel, Abklingzeiten, Wege zwischen den Minuten.

## 3. Ableitungen prüfen

Je eine Funktion, jede an 50 Stichproben auf Stimmigkeit geprüft (Treffer und Zweifelsfälle zählen):
- **Back:** Käufe plus Basis-Position.
- **TP:** Positionssprung, der zu Fuß nicht geht, plus `summonerXCasts`.
- **Kampf:** Kills eng in Zeit und Raum.
- **Umkämpftes Objective:** Kills am Ort innerhalb von ±30 s.
- **Gank:** Jungler beteiligt am Lane-Kill.
- **Rotation, Gruppe, Split:** aus den Positionen.

## 4. Eine Partie komplett: zehn Entscheidungsmomente

- **Partie:** ein Top-Laner mit TP, Siegerteam, etwa 30 min.
- **Momente:** erster Back, erster Drache, Larven/Herold, erster Turm, erster Kampf, Mitte, Baron, Schluss.
- **Je Moment, in Deutsch für Carlos:**
  - Lage (nur Wissbares);
  - was der Top-Laner in den nächsten 60 s tat;
  - was daraus wurde (30, 60 und 120 s);
  - welches Kommando ein Challenger-Coach hier gegeben hätte, und warum.
- **Jede Angabe markiert:** beobachtet / geschätzt / unbekannt.

## 5. Entwurf für Phase 1

- **Lage-Merkmale:** nur Wissbares.
- **Aktions-Liste:** beobachtbar mit Erkennungsregel. Lane halten, Back, zu Objective X, Rotation zu Lane Y, Gruppe,
  Split, Jungle, TP, Warten.
- **Folge-Maße.**
- **Aufteilung Training/Prüfung** nach Spielern und Zeitraum.
- **Downloader-Zweig für Silber und Gold** (`league-exp-v4`, etwa 5000 Partien) bauen, **nicht starten**. Das
  startet Carlos.

## Ende

- **`buecher/challenger/phase0_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“;
  - Datenqualität, Feldkatalog, Prüfung der Ableitungen;
  - die zehn Momente, lesbar;
  - der Entwurf für Phase 1, offene Fragen.
- Knapp. Committen, nur eigene Dateien. Starte den Coach nicht.
