Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 030 – Challenger-Gehirn, Stufe 1: Datenbasis der Entscheidungsmomente

Der vollständige Bericht steht in `buecher/challenger/phase1_bericht.md`, die Tabellen in `phase1_pruefung.md`, das
Merkmals-Verzeichnis in `merkmale.md`.

**Commit:** Auftrag 030, nur neue Dateien:
- `werkzeuge/challenger/`: `phase1.py`, `phase1_pruefen.py`, `test_kein_maphack.py`;
- `buecher/challenger/`: Bericht, Prüfung, Merkmale, Aufteilung;
- dieser Bericht.

Die Daten liegen in `daten/challenger/phase1/` (nicht im Git). Nichts in `lolcoach/` geändert, den Coach nicht
gestartet.

**Tests:** alle grün.
- **`test_kein_maphack.py`:** grün, dazu die Sabotage-Gegenprobe (fällt wie verlangt durch).
- **Rohdaten-Abgleich:** 30/30, dazu 300 Momente mit allen Feldern gleich.
- **Nullprobe je Label:** alle klar unter 100 %; einzige Ausnahme ist „Jungle“ beim Jungler mit 69 %.
- Keine Coach-Tests nötig, weil kein Coach-Code geändert wurde.

**Kennzahlen:**

| | |
|---|---|
| Momente | 2.565.410 aus 3504 Partien, laden in 0,8 s |
| Aufteilung | Training 1,68 Mio.; Prüfung Spieler 421 k / Zeit 377 k / beides 91 k |
| Dünne Zellen (< 200, Training) | 29 von 150: TP überall, Split spät, Jungle bei Lanern, Lane spät bei ADC/Support |
| Objective bestritten (ohne Kill, ≥ 3 Gegner ≤ 3000) | 1–3 %; die 40 % aus Phase 0 waren Minuten-Unschärfe |
| Behobene Fehler | Item-Wert bei gleichem Zeitstempel, Minuten-Versatz 0,4 s, Todeszeit an Leben-0-Minuten gekappt |
| Neu | Label „Unterwegs“ (20 %). „Warten“ ist jetzt die Phase-0-Regel (1,5 %). |

**Offen, braucht eine Entscheidung** (Einzelheiten im Bericht, „Was Stufe 2 davon braucht“):
- Soll „Unterwegs“ in Stufe 2 ein Ziel bekommen (Zone, Grube, Mitspieler), oder bleibt es „anderes“?
- „Nahe sichtbar“ mit 1200 trifft in der Lane vor 14:00 nur 31 %. Soll die Sichtweite größer werden (Minions geben
  Sicht)?

**Für Carlos:** nichts zu testen. Die Datenbasis für Stufe 2 steht.
