Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Stufe 4 – Der Einbau (Auftrag 034, 30.09.2026, Cloud-Sitzung, Zweig `stufe4-einbau`)

**Der Coach entscheidet mit dem Challenger-Gehirn.** `--kern makro` ist neu und Standard. `--kern neu` gibt den
Stand davor, zum Vergleich. Geprüft ist alles nur mit konstruierten Lagen: In der Cloud gibt es kein `daten/`, keine
`aufnahmen/` und keine Modelle. Den Coach habe ich nicht gestartet, Claude nicht aufgerufen.

## Was gebaut wurde

| Datei | Aufgabe |
|---|---|
| `lolcoach/makro/live.py` | **MakroLage live** aus Live-API, Minimap, HUD, Chat und den Lesern aus 033, dazu die Merkmale fürs Gehirn (Namen und Geometrie wie im Training) |
| `lolcoach/makro/takt.py` | **Entscheider:** Gehirn + 111 Entscheidungen + Vorrang ergeben genau eine Anweisung; Planwechsel nur mit Grund; die Klarheit bestimmt die Form |
| `lolcoach/makro/stimme.py` | **Claude spricht nur:** Er formt den Satz aus den Fakten. Weicht er ab, fällt er aus oder ist er zu langsam, spricht die Vorlage |
| `lolcoach/makro/einbau.py` | **MakroCoach:** Takt im Coach, Budget, Erinnerung, Fragen, Protokoll `<stamm>_makro.jsonl` |
| `lolcoach/kern/__init__.py` | Stellung `makro`: Der alte Kern rechnet mit und ist nur noch die **Sicherheits-Sperre** (`makro_sperre`), Dashboard und Claude-Kontext zeigen den neuen Plan |
| `lolcoach/regeln.py`, `sprechplan.py`, `antworten.py`, `__main__.py` | alte Regeln in `makro` stumm (INFO bleibt auf dem Dashboard); Fragen an den Entscheider; `--kern makro` als Standard |
| `lolcoach/makro/kommando.py` | Sätze sprechbar: „für“ statt „fuer“, „der Drache steht jetzt“ statt „ist in 0 s“ |
| `wissen/kern.toml [makro_gehirn]` | Takt 1 s, Start 45 s, Halten 20 s, Erinnern 25 s, Claude-Frist 2 s |
| `tests/makro/test_einbau.py` | 14 Tests (unten) |
| `tests/einzeln.py` | jede Testfunktion einzeln, mit `--basis` nur die Abweichungen zu einem früheren Lauf |
| `werkzeuge/makro_protokoll.py` | Auswertung des Makro-Protokolls für den Messlauf |

### 1. MakroLage live (`LageBau`)

- **Takt:** Entschieden wird höchstens einmal je Sekunde; der Coach taktet weiter viermal je Sekunde.
- **Quellen:**
  - API: Uhr, Ereignisse, Scoreboard, Items, Gold, Tote und Respawn, Monster-Timer;
  - Minimap: eigene Position, Mitspieler, Gegner-Sichtungen mit Alter, Wellen aller Lanes, Platten, TP-Sprünge;
  - HUD: Leben und Ult der Mitspieler, eigene Zauber, Trinket-Ladungen;
  - Chat: Flash-Timer;
  - 033: Wards deines Teams;
  - der Wellen-Zustand des alten Kerns (Buch 1): Crash und Kanonen-Uhr.
- **Fehlende Wahrnehmung bleibt leer:**
  - Jeder Takt führt `lage.vorhanden`, also welche Eingaben gerade frisch da sind.
  - Fehlt eine Eingabe, schweigt jede Entscheidung, die sie liest; die anderen sprechen.
  - Die sechs unzuverlässigen Eingaben aus 033 werden nie gefüllt: Ward weg, Blitz der Mitspieler, TP-Stand der
    Gegner, Recall des Lane-Gegners, Kopfgeld, Busch. Ihre Entscheidungen S11, S12, B5, T9, O12 und P2 schweigen immer.
- **Merkmale fürs Gehirn:**
  - alle 100 Modell-Merkmale aus `modelle.BASIS_NAMEN`, ohne das Gegner-Scoreboard (Entscheidung zu Stufe 2);
  - Unbekanntes ist `None`, also NaN im Modell;
  - der Kartenbereich rechnet wie `phase1.bereich_np` (Test an 3600 Punkten);
  - Platten aus der Minimap-Ziffer, Stand bis 14:00.

### 2. Der Entscheider im Takt

- **Ablauf:**
  1. `gehirn.bewerte(merkmale, kontext)` und `lage_info` liefern Optionen, Klarheit, Siegchance und Jungler-Karte.
  2. Alle 111 Entscheidungen laufen.
  3. Die Sperre streicht, was nicht gesagt werden darf.
  4. `vorrang.ordnen` sortiert.
- **Kontext fürs Gehirn** (Back nur mit Grund): Welle gecrasht, Kaufplan. Der Recall des Lane-Gegners fehlt, weil er
  unzuverlässig ist.
- **Genau eine Anweisung je Moment. Form nach Klarheit:**
  - Gefahr ist immer ein Kommando;
  - klar: ein Kommando;
  - geteilt: „Zwei Optionen. A … Oder: B – …“;
  - unklar: die Objective-Kette, sonst die häufigste High-Elo-Aktion (Z3).
- **Nie Schweigen:**
  - Feuert nichts, gilt G0: „Bleib an deiner Top-Welle …“, tot „Warte … auf den Respawn“.
  - Streicht die Sperre alles: „Zurück zu deinem Turm“.
  - Steht der Plan still, kommt eine Erinnerung „Weiter: …“ nach 25 s Stille, dann nach 50 s und 100 s, damit sie
    nicht zum Echo wird.
- **Regel 028: ein Planwechsel nur mit Grund.** Gründe sind Gefahr, Event (Kill, Tod, Respawn, Back, Gebäude,
  Monster) oder Frage. Dazu, abgeleitet aus `herzschlag.WECHSEL_S`:
  - Der Plan ist erledigt: seine Entscheidung feuert nicht mehr.
  - Er steht länger als 20 s.
  - Sonst bleibt der Plan, mit frischen Zahlen.
- **Die Sicherheits-Sperre ist der alte Kern** (`Kern.makro_sperre`):
  - R1: nichts nach vorn mit zu wenig Leben;
  - Angriff ohne Kill-Check, „schwach“ ohne Beleg, innere Begriffe;
  - Carlos' Einsprüche;
  - Fakten: lebt oder tot laut API;
  - verbotene Gründe: Floskel, Tautologie.
  - Der Sprechplan prüft beim Sprechen noch einmal (028).
- **Sprechplan:**
  - Gefahr ist SOFORT, Plan und Wendepunkt WICHTIG, die Erinnerung HINWEIS.
  - Das Budget ist das des alten Kerns (`abstand_s`, `max_je_minute`); Gefahr und Event-Wechsel sind frei.
  - Jeder zugelassene Wechsel trägt seinen Grund, damit `_ein_plan` (028) ihn nicht verwirft.
  - Verwirft der Sprechplan doch einen Plan-Satz (Sprech-Tor, Back-Sperre, zu alt), kommt er erneut. Sonst hörte
    Carlos den neuen Plan nie; beim Durchlesen gefunden.

### 3. Claude spricht nur noch

- **Was Claude bekommt:** Er erhält TU, WEIL, DANACH und die Vorlage als Fakten und formt einen Satz.
- **Treue-Prüfung.** Die Vorlage spricht, wenn der Satz:
  - eine Zahl nennt, die nicht in der Vorlage steht;
  - einen Champion nennt, der nicht in der Vorlage steht;
  - eine Handlungsart erfindet oder weglässt (vor, zurück, Back, TP, Ward, Objective);
  - eine Verneinung ändert;
  - die Handlung nicht nennt;
  - länger als 30 Wörter ist.
- **Ausfall oder zu langsam** (Frist 2 s): Es spricht die Vorlage, der Coach schweigt nie deswegen. Gefahr formt
  Claude nie, sie geht sofort als Vorlage heraus.
- **Nur live und nur über die API.** Das Abo braucht 4–11 s, jeder Aufruf wäre bei 2 s Frist verschenkt. Beim
  Abspielen spricht immer die Vorlage.
- **Fragen: erst die Antwort, dann der Plan.**
  - JETZT, SOLL_ICH, ENTWEDER, DANACH, WARUM, LAGE und RISIKO beantwortet der Entscheider selbst.
  - Timer, Wo, Kauf usw. liefern die Fakten des alten Wegs mit „Plan: …“ angehängt.
  - Eine Frage erlaubt den Planwechsel.
  - Offene Fragen gehen wie bisher an Claude, der Kontext trägt den entschiedenen Plan.

### 4. Der alte Kern entscheidet nicht mehr

- In `makro` rechnet er weiter mit: Modus, Merkmale, Wellen-Zustand, „wuerde_sagen“ in `_kern.jsonl`.
- Gesprochen wird nichts davon, auch keine alte Regel.
- `--kern neu` gibt den Stand vor 034 zurück.
- Der Makro-Stratege aus 015 (Claude entscheidet) läuft nur noch unter `neu`.

## Laufzeit je Takt

| gemessen (Cloud, eine CPU) | Median | p95 | max |
|---|---:|---:|---:|
| Entscheider: 111 Entscheidungen + Vorrang + Form + Halten, Gehirn-Attrappe | 0,22–0,28 ms | 0,27–0,46 ms | 0,4–1,0 ms |
| Lagebau + Entscheider (Schnappschuss, Lagebild, Bewertung) | 0,52–0,60 ms | – | 0,8–1,2 ms |
| ganzer Makro-Takt im Kern (120 Takte, Protokoll) | 1,0 ms | 1,7 ms | 18,9 ms (erster Takt) |
| **dazu das echte Gehirn** (nicht messbar hier; 032: `bewerte()` 4,7 ms Median, Gründe ~1 ms) | ~6 ms | – | – |

**Erwartet sind unter 10 ms je Entscheidung, das Soll ist 50 ms.** Mit echten Modellen wird bei Carlos gemessen:
`python werkzeuge/challenger/gehirn.py` und `werkzeuge/makro_protokoll.py` (Spalten `ms` und `ms_hirn`).

## Tests

**`tests/makro/alle.py` 6/6 grün.** Neu ist `test_einbau`, 14 Tests ohne Aufnahmen, Modelle und Claude:
- MakroLage aus einem konstruierten Live-API-Schnappschuss plus konstruierten Leser-Werten, auch ohne Minimap (dann
  fehlt, was fehlt);
- Kartenbereich wie im Training;
- genau eine Anweisung je Takt, G0 bei nichts;
- Gehirn-Attrappe klar, geteilt, unklar und Ausfall;
- die echte `bewerte()`-Logik mit Live-Merkmalen: Back rutscht ohne Grund, mit gecrashter Welle steht Back vorn;
- kein Planwechsel ohne Grund (gehalten, Event, erledigt, Frage, abgelaufen, Gefahr);
- Sicherheits-Sperre mit Attrappe und mit dem echten alten Kern (R1, Fakten, Tautologie);
- Claude: Ausfall, zu langsam, Abweichung, treu, Gefahr;
- fehlende Wahrnehmung;
- Laufzeit;
- Kern in `makro` mit Regelwerk und Sprechplan: nur `kern:MAKRO_*`, alte Regeln stumm, Erinnerung, Event;
- ein verworfener Plan-Satz kommt wieder;
- Fragen: Antwort, dann Plan.

**`tests/alle.py`:** Ohne `daten/` (Data Dragon ist über den Proxy gesperrt, 403) laufen in der Cloud 3 von 11
Dateien durch. Das war vor 034 genauso. Deshalb habe ich jede Testfunktion einzeln verglichen
(`tests/einzeln.py --basis`):
- vorher 86 grün, 34 rot; nachher 86 grün, 34 rot;
- **neu rot: keine.**

Übersprungen, weil sie `daten/` (Data Dragon: Items, Champions, `map11.png`), Aufnahmen, Windows oder fehlende Pakete
brauchen – alle schon vor 034 rot:

| Datei | Funktionen |
|---|---|
| `test_regeln` | main (Aufnahme + Items) |
| `test_zauber` | chat_formate (Champion-Namen aus Data Dragon) |
| `test_champions` | main |
| `test_flash` | ganz (`map11.png` aus Data Dragon) |
| `test_bausteine` | item_namen, bewertung_und_plan, denkkette, faehigkeiten_aus_spieldaten, icon_in_der_brunnen_ecke, stimme_spielt_ab_dem_ersten_stueck (Paket `av`), konter_kauf_ohne_eigenes, minimap_groesse_aus_der_einstellung (game.cfg) |
| `test_kern` | konstruierte_lagen, kontrollauge_nur_mit_platz, stratege_pruefung, stratege_pruefung_015, pflichtenheft_016, inhalt_017, respawn_018, kauf_018, kampf_rechner_020, aufraeumen_022, stimme_023 (Paket `anthropic`), udyr_024, ornn_028 |
| `test_kaufplan` | alle neun (Item-Namen aus Data Dragon) |
| `test_sparsam` | werkzeuge_reichen_nicht_weiter (Windows, `ctypes.windll`) |

## Was in der Cloud NICHT geprüft werden konnte (für Carlos' Messlauf, Stufe 5)

1. **Das echte Gehirn im Takt:** Modelle laden (`daten/challenger/modelle`), Laufzeit mit Modell, dass die
   Live-Merkmale die Modelle nicht verzerren (live ist das Alter der Sichtungen kleiner als im Training;
   live_merkmale.md).
2. **`tests/alle.py` vollständig** mit `daten/` und Aufnahmen, vor allem `test_kern` und `test_bausteine`.
3. **Nachspiele mit `--kern makro`:** `abspielen --kern makro`; die Werkzeuge `szenarien.py`, `protokoll.py` und
   `kennzahlen.py` stehen noch auf `--kern neu` als Vorgabe und messen den Plan des alten Kerns. Für Stufe 5 auf den
   Makro-Plan umstellen (`_makro.jsonl`, `a._makro`).
4. **Generalprobe** (`werkzeuge/generalprobe.py`): der ganze Live-Weg mit `--kern makro`, Latenz Entstehung bis Ohr.
5. **Claude als Stimme über die API** (nur live, `Coach starten.cmd`): Wie oft kommt der Satz vor der Frist
   (Haiku 1,6 s Median in 019), wie oft greift die Treue-Prüfung zu Unrecht (`quelle` im Protokoll)?
6. **Wahrnehmung live:** Anteil der Takte je fehlender Eingabe (`makro_protokoll.py`: „fehlende Wahrnehmung“), vor
   allem `eigene_zauber`, `kaufplan` und `wellen_alle`.
7. **Sprechmenge:** Ansagen je 30 min, Erinnerungen, Widersprüche und Hin und Her mit dem neuen Entscheider; die
   Startwerte in `[makro_gehirn]` danach einstellen.
8. **Dashboard** mit dem Makro-Plan (Art = Nummer aus Buch 17, Teil B).

## Offene Punkte

- **Vorrang ohne Gehirn-Wert:** `vorrang.ordnen` sortiert nach Klasse (Gefahr, Objective, Rest) und dem festen Wert
  der Entscheidung, nicht nach dem Aktionswert des Gehirns. Im nachgestellten Ablauf gewinnt die Objective-Kette oft
  gegen die Lane (10:00: „Lass die Welle und geh: der Drache steht jetzt.“). Ob das richtig ist, zeigt erst das
  Können an High-Elo-Partien (Tor Stufe 4).
- **Siegbedingung (V1) und Kontroll-Auge gesetzt:** Die Team-Aufstellung ist live nicht als Klasse vorhanden, V1
  schweigt. Ob Carlos' Kontroll-Auge steht, liest der Coach nicht verlässlich; S6 kennt nur das Inventar.
- **Briefing** des Strategen (Claude, Spielbeginn) läuft weiter wie bisher. Es ist keine Moment-Entscheidung, aber
  Claude formuliert dort Inhalt. Carlos entscheidet, ob es in `makro` bleibt.
- **Offene Fragen an Claude:** Die Antwort bekommt den entschiedenen Plan im Kontext und geht durch den Kill-Check.
  Dass sie keine andere Handlung vorschlägt, wird nicht hart geprüft; das tut nur die Stimme für die Ansagen.
- **Sätze aus 032:** Umlaute und „0 s“ sind jetzt sprechbar. Einige Sätze sind länger als die 14 Wörter aus Auftrag
  002, weil die Form „Tu X, weil Y, danach Z“ es verlangt; Claude kürzt live auf höchstens 22.
- **Abweichung von Carlos' Satz:** Der Planwechsel ist auch erlaubt, wenn der Plan erledigt ist oder länger als 20 s
  steht. Ohne das bliebe ein erledigter Plan stehen und würde weiter erinnert.
