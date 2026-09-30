# Auftrag 034 – Challenger-Gehirn, Stufe 4: Der Einbau (Claude, Chat, 30.09.2026 21:00)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.

## Wo dieser Auftrag läuft

**In einer Cloud-Sitzung** (claude.ai/code, Repository `cajadalopes-crypto/LoLCoach`). Daraus folgt:
- **Es gibt keine `daten/`, keine `aufnahmen/`, keine trainierten Modelle und keine Schlüssel.** Sie sind in
  `.gitignore` und bleiben auf Carlos' PC.
- **Gearbeitet wird auf einem eigenen Zweig** `stufe4-einbau`, der nach GitHub gepusht wird. Dafür das Repository
  mit Schreibrechten anhängen. Kein Pull Request nötig.
- **Getestet wird nur mit konstruierten Lagen**, wie in 032. `werkzeuge/challenger/gehirn.py` lädt Modelle aus
  `daten/`, die hier fehlen: In den Tests kommt eine Attrappe davor, nie die echten Modelle.
- **Nicht gemessen wird hier.** Nachspiele, Szenarien gegen Aufnahmen und Kennzahlen laufen später bei Carlos.

## Grundlage

- `buecher/17_makro_gehirn.md`: Teil B (die 111 Entscheidungen), Teil C (Stufe 4), „Harte Regel: Woher das Können
  kommt";
- `buecher/challenger/phase3a_bericht.md`, `phase3b_bericht.md`, `abdeckung.md`;
- `lolcoach/makro/` (Lage, Rechner, Regeln, Vorrang, Entscheidungen, Wahrnehmung);
- `werkzeuge/challenger/gehirn.py` (`bewerte`).

## Das Ziel

Der Coach entscheidet ab jetzt mit dem Challenger-Gehirn, nicht mehr mit den alten Regeln.

1. **`MakroLage` live bauen** (der offene Punkt aus 033):
   - aus Live-API, Minimap, HUD, Chat und den Lesern aus 033;
   - je Takt, höchstens einmal je Sekunde;
   - **fehlende Wahrnehmung bleibt leer**, nie geraten. Die sechs unzuverlässigen Eingaben aus 033 sind aus
     (`wahrnehmung.py`).
2. **Der Entscheider im Takt:**
   - `gehirn.bewerte(lage)` und die 111 Entscheidungen laufen, `vorrang.py` wählt aus.
   - **Genau eine Anweisung je Moment.** Regel aus 028: ein Planwechsel nur mit Gefahr, Event oder Frage.
   - Die Klarheit entscheidet die Form: klar ein Kommando, geteilt zwei Optionen, unklar die häufigste
     High-Elo-Aktion. **Nie Schweigen.**
   - **Laufzeit:** die Entscheidung unter 50 ms je Takt. Messen und im Bericht nennen.
3. **Claude spricht nur noch:**
   - Er bekommt Kommando, Grund und nächsten Schritt als Fakten und formt daraus einen gesprochenen Satz.
   - **Er erfindet keine Aktion.** Weicht sein Satz vom Kommando ab, wird die Vorlage gesprochen.
   - Antworten auf Carlos' Fragen: zuerst die Antwort, dann der Plan (aus 028).
   - Fällt Claude aus oder ist er zu langsam, spricht die Vorlage. Der Coach schweigt nie deswegen.
4. **Der alte Kern entscheidet nicht mehr:**
   - Er bleibt als **Sicherheits-Sperre**: R1, Kill-Check, Fakten-Prüfung, verbotene Begriffe.
   - Was er sonst an Kandidaten und Plänen baute, wird nicht mehr gesprochen.
   - Alles bleibt umschaltbar: `--kern makro` ist neu und Standard, `--kern neu` gibt den alten Stand. So lässt
     sich später vergleichen.
5. **Sprechplan:** Vorrang, Themen-Sperre und Budget arbeiten mit dem neuen Entscheider zusammen, nicht gegen ihn.

## Tests (ohne Aufnahmen, ohne Modelle)

- **`tests/makro/`** erweitern:
  - `MakroLage` aus einem konstruierten Schnappschuss der Live-API plus konstruierten Leser-Werten;
  - der Takt gibt aus einer Lage genau eine Anweisung;
  - Gehirn-Attrappe: feste Werte rein, erwartetes Kommando raus;
  - kein Planwechsel ohne Grund; Sicherheits-Sperre greift; Claude-Ausfall führt zur Vorlage;
  - fehlende Wahrnehmung: die betroffene Entscheidung schweigt, die anderen sprechen.
- **`tests/alle.py`** muss grün bleiben, soweit ohne `daten/` und `aufnahmen/` lauffähig. Was Daten braucht,
  überspringen und im Bericht auflisten.

## Ende

- **`buecher/challenger/phase4_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)";
  - was gebaut wurde, Laufzeit je Takt;
  - was in der Cloud **nicht** geprüft werden konnte, als Liste für Carlos' Messlauf;
  - offene Punkte.
- Committen und den Zweig `stufe4-einbau` pushen. Starte den Coach nicht.

## Danach, bei Carlos (Stufe 5, Auftrag 035)

Generalprobe, Nachspiele, Szenarien, Kennzahlen; das Können an zurückgelegten High-Elo-Partien, die Verdrahtung an
Carlos' Aufnahmen.
