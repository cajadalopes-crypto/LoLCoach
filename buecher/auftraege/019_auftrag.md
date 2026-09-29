# Auftrag 019 – Schritt A aus Buch 14: Lagebild und Claude über die API (Claude, Chat, 29.09.2026 19:45)

Lies zuerst `buecher/14_bauplan_gehirn.md`. Direkt nach 017 (vor 018 – Carlos will den Umbau zuerst). Objective-Symbole der Minimap (018) kommen später ins Lagebild; bis dahin nur API-Ereignisse. **Keine Testpartien, frag Carlos nie nach einer
Partie, starte den Coach nicht.**

## Schlüssel

- `geheim/claude_api_key.txt` (sk-ant-…) und `geheim/riot_key.txt` (RGAPI-…) sind da, von Carlos angelegt.
- Nie ausgeben, loggen oder committen. `geheim/` steht in `.gitignore`, prüf das vor jedem Commit.
- Einmal mit einem Mini-Aufruf testen, ob der Claude-Schlüssel geht. Den Riot-Schlüssel erst in Schritt B.

## Teil 0 – Prüfen schneller machen (Carlos: „warum dauern die Aufträge so lange?“)

Die meiste Zeit eines Auftrags geht in Prüfläufe, nicht in Code. Die Ursachen:
- Nachspiele mit echten Claude-Aufrufen laufen einer nach dem anderen (2–7 s je Aufruf, rund 150 je Partie).
- Der volle Szenario-Lauf läuft seriell.
- Nach späten Fixes wird alles noch einmal komplett wiederholt.

Ziel: Die Prüfung eines Auftrags dauert höchstens etwa 30 min Rechenzeit.

1. **Szenarien parallel:** auf alle CPU-Kerne verteilen (`multiprocessing`). Die Zeit vorher und nachher kommt in
   `messungen.md`.
2. **Nachspiele parallel:** alle Partien gleichzeitig, jede in ihrem eigenen Prozess. Die Claude-Aufrufe laufen über
   die API (sie verträgt parallele Aufrufe) statt nacheinander über das Abo.
3. **Während der Arbeit nur die betroffenen Szenarien.** Der volle Lauf kommt einmal am Ende. Nur wenn der rot ist, wird
   nachgebessert und die roten Fälle sowie ein Stichproben-Lauf wiederholt, nicht alles.
4. **Kritiker einmal am Ende,** parallel je Partie.
5. **Nachspiele mit Zwischenspeicher:** Antworten von Claude werden je (Lage, Frage) gespeichert. Ein Wiederholungslauf
   ohne geänderte Lage fragt nicht neu.
6. **Im Bericht:** Rechenzeit je Teil (Bauen, Szenarien, Nachspiele, Kritik).

## Bauen

1. **`lolcoach/welt.py`:** Lagebild wie in Buch 14, Schritt A.1 und A.2.
   - Der Stratege bekommt ab jetzt dieses Lagebild statt des bisherigen Kontexts.
   - Der Kern darf es lesen, muss aber nicht umgebaut werden. Das kommt in Schritt C.
   - Unit-Tests für die eindeutigen Formen („jetzt sichtbar“ gegen „zuletzt gesehen vor N s, vermutlich …“).
   - Tokenzahl je Aufruf messen.
2. **`lolcoach/llm_api.py`** wie in Buch 14, A.3:
   - Streaming, Zwischenspeicher, zwei Modelle, Kostenzähler, Ersatz über das Abo.
   - Stratege, Antworten und Briefing laufen darüber, sobald ein Schlüssel da ist.
   - Schalter in `wissen/kern.toml`: `[llm] weg = "api" | "abo"`.
3. **Ganze Sätze** (017, Teil 0.1): Mit der API wird eine Antwort als ein Satz gesprochen, sobald sie vollständig und
   geprüft ist.

**017 wurde auf Carlos' Wunsch ohne Endmessung abgeschlossen.** Die Spalte „Abo (Stand 017)“ unten holt diese Messung nach (Soll-Liste, Füllsätze, Widersprüche, Latenz), mit der schnellen Prüfung aus Teil 0.

## Messen (Nachspiel, alle echten Aufnahmen mit Fragen: 133448, 192113, 101426, 183125)

| Größe | Abo (Stand 017) | API schnell | API stark |
|---|---|---|---|
| erster ganzer Satz, Median / p90 | | | |
| Kosten je 30 min | – | | |
| Soll-Liste-Treffer (017) | | | |
| Füllsätze / Widersprüche | | | |
| Sicherheit (0 / 0 / 0) | | | |

- **Modelle:** Wähle für Lane-Anlässe, Antworten und Plan-Wechsel je das Modell, das die Soll-Liste am besten trifft,
  unter Latenz-Median ≤ 1,5 s. Wo das starke Modell deutlich besser ist, aber langsamer, nimm es nur für Plan-Wechsel
  an Wendepunkten.
- **Kosten:** Liegen sie über 1,50 $ je 30 min, berichte, woran es liegt, und schlag vor, wie es billiger wird.

## Ende

1. Unit-Tests zuerst rot, dann bauen. Voller Lauf (Szenarien, Tests, konstruierte Lagen).
2. `019_bericht.md`:
   - die Tabelle;
   - die Kosten, die ich Carlos nenne;
   - drei Beispielminuten vorher und nachher.
3. Committen (vorher `geheim/` prüfen). Starte den Coach nicht.
