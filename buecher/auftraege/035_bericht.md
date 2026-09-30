Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 035 – Stufe 5: Die Abnahme

Der vollständige Bericht steht in `buecher/challenger/phase5_bericht.md`.

**TOR NICHT ERREICHT:** in der Cloud nicht messbar. Es fehlen `daten/` (Modelle, Riot-Momente), `aufnahmen/`,
Data Dragon und Windows. Alle Werkzeuge stehen. Ein Befehl bei Carlos liefert die Zahlen:
`python werkzeuge/abnahme_035.py`.

**Commit** auf Zweig `stufe5-abnahme` (von `main` mit 034; Cloud-Sitzung, gepusht, kein Pull Request). Den Coach
nicht gestartet, Claude nicht aufgerufen, die Abo-Runde nicht gelaufen.

- **Neu:**
  - `lolcoach/makro/aktionen.py`: Kommando → Aktion des Gehirns.
  - `werkzeuge/makro_messen.py` (Teil 1), `werkzeuge/challenger/treue.py` (Teil 2), `werkzeuge/abnahme_035.py`
    (alles ohne Guthaben).
  - `tests/makro/test_vorrang.py`, `tests/makro/test_treue.py`.
- **Geändert:**
  - `makro/vorrang.py`: Reihenfolge `wert` (Gefahr vorn, dann Aktionswert, fester Wert als Ersatz) oder `fest`.
  - `makro/takt.py`: Gefahr-Pingpong, Kaufen im Brunnen, Satzlänge 14/8, volle Anweisung für Stimme und Prüfung.
  - `makro/einbau.py`: Kampf-Stille, „Weiter:“, Stillstand „Los:“, Erinnerung nach 25 s, Stub-Stimme.
  - `makro/live.py`: keine falschen Lane-Kämpfe.
  - `makro/stimme.py`.
  - vier Kommandotexte.
  - `kern/herzschlag.py`, `kern/__init__.py`.
  - `wissen/kern.toml`.
  - Messwerkzeuge auf `--kern makro`: `szenarien`, `protokoll`, `kennzahlen`, `nachspielen`, `pakete_messen`,
    `makro_protokoll`.
  - `CLAUDE.md`, `OFFEN.md`.

**Tests:**
- `tests/makro/alle.py` 7/7 grün.
- `tests/einzeln.py --basis`: 86 grün, 34 rot, **neu rot: keine**.

| Bot-Nachspiel (`tests/botspiel_riven_2`, ohne Gehirn) | Wert | Soll |
|---|---|---|
| Sicherheit | 0 | 0 |
| Widerspruch | 0 | ≤ 1 |
| Füllsätze | 0 % | ≤ 5 % |
| Lücke p90 / längste | 8 s / 22 s | ≤ 20 / ≤ 35 s |
| Stillstand | 15/15 | ≥ 95 % |
| Laufzeit je Takt p95 | 1,4–1,6 ms (Gehirn allein 4,7 ms) | < 50 ms |

**Offen / zu entscheiden (Carlos):**
- **Messlauf:**
  1. `python werkzeuge/abnahme_035.py`.
  2. Die Reihenfolge nach den Treue-Zahlen festlegen (Default jetzt `wert`).
  3. Die 14 Roten beurteilen (Vorab-Urteil im Bericht).
  4. Danach die Abo-Runde (Befehl im Bericht).
- **Warnungen:** Im Bot-Nachspiel kommen ≈ 97 Warnungen je 30 min (J4/J5/J9 ohne Gefahr-Modell). Ob das zu viel
  ist, sagt die Warnungs-Präzision aus `treue.py`.
- **Szenario a4-lagebild-ungefragt** hängt am alten LAGEBILD: neu fassen oder streichen?
