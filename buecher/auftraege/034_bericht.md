Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 034 – Stufe 4: Der Einbau

Der vollständige Bericht steht in `buecher/challenger/phase4_bericht.md`.

**Commit** auf Zweig `stufe4-einbau` (Cloud-Sitzung, gepusht, kein Pull Request). Den Coach nicht gestartet, Claude
nicht aufgerufen.
- **Neu:**
  - `lolcoach/makro/live.py` (MakroLage live);
  - `takt.py` (Entscheider: eine Anweisung, Wechsel nur mit Grund, Form nach Klarheit, nie Schweigen);
  - `stimme.py` (Claude nur Satz, sonst Vorlage);
  - `einbau.py` (Takt, Budget, Erinnerung, Fragen, `<stamm>_makro.jsonl`);
  - `tests/makro/test_einbau.py`, `tests/einzeln.py`, `werkzeuge/makro_protokoll.py`.
- **Geändert:**
  - `kern/__init__.py`: Stellung `makro`, der alte Kern ist nur Sperre (`makro_sperre`), Dashboard und Kontext mit
    dem Makro-Plan;
  - `regeln.py`: alte Regeln stumm;
  - `sprechplan.py`, `antworten.py`: Fragen an den Entscheider, erst Antwort, dann Plan;
  - `__main__.py`: `--kern makro` ist Standard, Claude als Stimme nur live über die API;
  - `makro/kommando.py`: sprechbare Umlaute, „steht jetzt“;
  - `makro/lage.py`: `vorhanden`;
  - `wissen/kern.toml [makro_gehirn]`; `CLAUDE.md`, `OFFEN.md`.

**Tests:**
- `tests/makro/alle.py` 6/6 grün (neu: `test_einbau`, 14 Tests).
- `tests/alle.py` in der Cloud 3/11 Dateien grün – wie vor 034, es fehlen `daten/`, Data Dragon (Proxy 403) und
  Windows.
- Je Funktion (`tests/einzeln.py --basis`): 86 grün, 34 rot, **neu rot: keine**.
- Szenarien und Nachspiele: nicht gelaufen (keine Aufnahmen).

| Kennzahl | Wert |
|---|---|
| Entscheidung je Takt (ohne Modell) | 0,22–0,28 ms Median, p95 ≤ 0,46 ms |
| Lagebau + Entscheidung | 0,52–0,60 ms Median |
| mit echtem Gehirn (032 gemessen: 4,7 ms) | erwartet ~6 ms – Soll < 50 ms |
| Modell-Merkmale live gefüllt | 100/100 Namen passen; unbekannt = NaN |
| Entscheidungen, die ohne Wahrnehmung schweigen | S11, S12, B5, T9, O12, P2 (immer) + je Takt, was fehlt |

**Offen / zu entscheiden:**
- **Messlauf bei Carlos (035):** die Liste „nicht geprüft“ im Bericht – echtes Gehirn, Nachspiele und Szenarien mit
  `--kern makro` (die Werkzeuge stehen noch auf `neu`), Generalprobe, Claude-Stimme über die API.
- **Carlos:** Soll das Briefing (Claude, Spielbeginn) in `makro` bleiben?
- **Vorrang:** Er sortiert nach Klasse und festem Wert, nicht nach dem Aktionswert des Gehirns. Ob die
  Objective-Kette zu oft gewinnt, zeigt die Challenger-Treue.
