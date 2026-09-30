# Auftrag 030 – Challenger-Gehirn, Stufe 1: Datenbasis der Entscheidungsmomente (Claude, Chat, 30.09.2026 16:00)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.

**Darf parallel zu 028 laufen.** Daher gilt:
- Nur neue Dateien unter `werkzeuge/challenger/`, `buecher/challenger/` und `daten/challenger/`.
- Nichts in `lolcoach/` ändern.
- Nur die eigenen Pfade committen.

**Grundlage:**
- `buecher/17_makro_gehirn.md`: Teil A, „Entscheidungen zu Phase 0“ und Teil C (Stufe 1);
- `buecher/challenger/phase0_bericht.md`, Abschnitt 5: Entwurf für Phase 1;
- die Werkzeuge aus 029.

## Ziel

Alle gültigen High-Elo-Partien werden zu **Entscheidungsmomenten**: **Lage → Aktion → Folge**. Das ist die
Grundlage für Stufe 2 (Modelle). Keine Modelle in diesem Auftrag.

## 1. Momente bauen (alle Rollen, alle gültigen Partien, auch neu geladene)

**Zeitpunkte** je Spieler:
- jede volle Minute;
- jedes Ereignis, das ihn betrifft oder allen angesagt wird: Kill, Tod, Respawn, Back, Turm, Objective,
  Objective-Spawn.

**Lage** nach Phase 0, Abschnitt 5, **nur Wissbares** (kein Maphack):
- eigenes Team, Scoreboard und allen angesagte Ereignisse;
- Gegner nur als „tot + Restzeit“ oder „zuletzt gesehen, Ort + Alter“;
- dazu der **Lane-Gegner, wenn ≤ 1200 neben dem Spieler** (Entscheidung 1, als „nahe sichtbar“ markiert);
- Objective-Timer, Siegchance-Merkmale (Item-Wert, Level, Türme, Drachen, Tote) und Unterschiede.

**Aktion** in den nächsten 60 s, mit den Regeln aus Phase 0:
- Lane halten, Back, zu Objective X, Rotation zu Lane Y, Gruppe, Split, Jungle, Warten;
- **TP** nur in den sicheren Fällen, sonst „TP unbekannt“, nie „kein TP“.

Zusätzlich die **nächsten drei Aktionen** als Folge (für Ketten und Rückwärtsplanung in Stufe 2).

**Objective-Zustand** dreistufig: frei, bestritten oder umkämpft (Entscheidung 3).

**Folge** nach 30, 60 und 120 s:
- eigenes Gold und XP, Team-Gold-Abstand;
- Tod ja/nein, Kills für und gegen;
- Platten, Türme, Objectives für und gegen;
- Sieg der Partie.

**Liga** je Spieler (aus 029) und Rolle an jedem Moment.

**Ablage:**
- unter `daten/challenger/`;
- schnell ladbar, das Format wählst du;
- ein Merkmals-Verzeichnis in `buecher/challenger/merkmale.md` (Name, Bedeutung, Quelle, [B]/[G]/[U]).

## 2. Aufteilung Training und Prüfung

- Wie in Phase 0 vorgeschlagen: 20 % der Spieler fest per Hash, dazu die letzten 20 % der Zeit.
- Prüfspieler kommen im Training nicht vor.
- Gleich festlegen und nie mehr ändern.

## 3. Prüfen

- **Zahlen je Rolle, je Aktion und je Spielphase.** Wo gibt es zu wenige Fälle (< 200)?
- **30 Momente gegen die Rohdaten:** Stimmen Lage, Aktion und Folge?
- **Nullprobe je Aktions-Label** wie in 029: Mit falschem Ort oder falscher Zeit muss das Label klar seltener
  zutreffen.
- **Kein Maphack:** Ein Test beweist, dass keine Gegnerposition in eine Lage kommt, außer tot, zuletzt gesehen oder
  nahe sichtbar.

## 4. Kein Silber/Gold-Vergleich

Entschieden von Carlos am 30.09.2026: Es gibt keinen Vergleich mit Silber/Gold. Nur High-Elo-Daten.

## Ende

- **`buecher/challenger/phase1_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“;
  - Anzahl der Momente, die Tabellen aus Abschnitt 3, Probleme;
  - was Stufe 2 davon braucht.
- Knapp. Committen, nur eigene Dateien. Starte den Coach nicht.
