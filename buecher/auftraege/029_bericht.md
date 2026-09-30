Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 029 – Challenger-Gehirn, Phase 0: Prüfung der Daten

Der vollständige Bericht steht in `buecher/challenger/phase0_bericht.md`, mit den zehn Momenten zum Lesen.

**Commit:** Auftrag 029 (nur neue Dateien unter `werkzeuge/challenger/` und `buecher/challenger/` sowie dieser Bericht;
nichts in `lolcoach/` geändert, den Coach nicht gestartet).

**Tests:** keine Coach-Tests nötig (kein Coach-Code geändert). Geprüft wurde anders:
- Jede Ableitung an 50 Stichproben, dazu eine Nullprobe.
- `silber_download.py` kompiliert, `--trocken` ohne Abruf.

**Kennzahlen:**

| | |
|---|---|
| Partien gültig | 2792 von 2822 (Download läuft weiter, alles wiederholbar) |
| Patch | 16.17–16.19 |
| Top-Spieler-Partien | 5553, davon Challenger 1718 |
| Riot-Abrufe | 3 (Ligalisten) |
| Ableitungen, die tragen (Nullprobe klar tiefer) | Gank, Kampf, Rotation; brauchbar: Split, Gruppe, Todeszeit |
| Back | per Spielregel sicher |
| Schwach | umkämpftes Objective (40 % der „freien“ mit ≥ 3 Gegnern an der Grube) |
| TP | nur 3 % der Einsätze zeitlich erkennbar (etwa 79 % davon echt) |
| Zehn Momente | Ambessa (Challenger) gegen Aatrox, 30:02, Sieg; je Moment Lage/Tat/Folge/Kommando, markiert B/G/U |
| Silber/Gold-Download | gebaut, **nicht gestartet** |

**Offen, braucht eine Entscheidung (Einzelheiten im Bericht, Abschnitt 6):**
1. Lane-Gegner in der Lage, wenn er ≤ 1200 neben dem Spieler steht?
2. TP als gelernte Aktion oder erst als Rechner?
3. „Umkämpft“ auch ohne Kill, wenn Gegner an der Grube standen?
4. Buch 17 korrigieren: kein Atakhan, Patch 16.17–16.19, Larven je Stück?

**Für Carlos:**
- Die zehn Momente lesen (Tor 0b: plausibel?).
- Den Silber/Gold-Download nach dem großen Download starten.

`buecher/messungen.md` ist nicht ergänzt, weil in 029 nur neue Dateien erlaubt waren.
