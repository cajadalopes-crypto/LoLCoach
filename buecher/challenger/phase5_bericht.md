Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Challenger-Gehirn, Stufe 5: Die Abnahme (Auftrag 035)

**TOR NICHT ERREICHT** – nicht weil ein Maß gerissen wurde, sondern weil die Abnahme in dieser Sitzung nicht
laufen kann. 035 läuft bei Carlos: lokal, mit `daten/` (Modelle, Riot-Momente), `aufnahmen/` und Windows. Die
Cloud-Sitzung hat nichts davon. `daten/challenger/modelle` fehlt, keine Aufnahme liegt vor, Data Dragon ist hinter
dem Proxy (403), kein Windows. Gebaut wurde daher alles, was die Abnahme braucht, dazu jeder Fix, der sich ohne
Daten prüfen ließ. Gemessen wurde nur am Bot-Nachspiel aus `tests/`. **Ein Befehl erzeugt alle Zahlen bei Carlos:**

```
python werkzeuge/abnahme_035.py          # Teil 1-3 ohne Guthaben -> buecher/challenger/phase5_messung.md
```

Kein Aufruf von Claude, kein Guthaben. Der Coach wurde nicht gestartet.

## Tor Stufe 5

„Bot“ heißt: gemessen am Bot-Nachspiel `tests/botspiel_riven_2` (eine Partie gegen Bots, Stub-Stimme, **ohne
Gehirn**). Es prüft nur die Verdrahtung und ersetzt keine Testpartie.

| Maß | Soll | Ist | |
|---|---|---|---|
| Challenger-Treue | schlägt alle drei Vergleiche deutlich | nicht gemessen (keine Riot-Momente, keine Modelle) | – |
| Sicherheit | 0 | Bot: 0 (140 Sätze) | Bot ✔ |
| Widerspruch (automatisch) | ≤ 1 je Partie | Bot: 0 | Bot ✔ |
| Füllsätze | ≤ 5 % | Bot: 0/140 (0 %) | Bot ✔ |
| Anweisungs-Lücke p90 / längste | ≤ 20 s / ≤ 35 s | Bot: 8 s / 22 s | Bot ✔ |
| Stillstand | ≥ 95 % | Bot: 15/15 (100 %) | Bot ✔ |
| Basis | ≥ 95 % | keine Fälle (ohne Data Dragon kein Kaufplan) | – |
| Laufzeit je Takt | < 50 ms | ohne Gehirn p95 1,4–1,6 ms, max 15 ms; Gehirn allein 032: 4,7 ms | erwartet ✔ |
| Guthaben | 0 $ | 0,00 $ (`werkzeuge/guthaben.py`) | ✔ |

Weiter im Bot-Nachspiel: 1495 Entscheidungen, 151 Ansagen, 1 Satz verworfen, negativ allein 0, Hin und Her 0.
Quellen der Sätze: Stub-„Claude“ 36, Vorlage bei Gefahr 61, „Weiter:“-Wiederholung 27, Erinnerung 12,
Stillstand 10, Kampf 5. Gefahr, Erinnerung und Stillstand spricht absichtlich die Vorlage (kurz, ohne Frist). Daher
der hohe Vorlage-Anteil von 76 %; er sagt nichts über Claude.

**Offen im Können:** Das Bot-Nachspiel hat viele Ansagen (≈ 166 je 30 min) und viele Warnungen (≈ 97 je 30 min),
fast alle aus J4/J5/J9. Die Warnungen feuern ohne das Gefahr-Modell des Gehirns, und gegen Bots, die ständig
sichtbar sind. Ob das zu viel ist, misst die Warnungs-Präzision in `treue.py` an High-Elo-Daten (Tod in 60 s nach
einer Warnung gegen die Grundrate). An Carlos' Partien wurde nichts eingestellt (Harte Regel).

## Teil 0: Vorbereiten

- **Zweig:** `main` enthält 034 (42aea4c). Die Arbeit liegt auf `stufe5-abnahme`.
- **Messwerkzeuge auf `--kern makro`:**
  - `szenarien.py`, `protokoll.py`, `kennzahlen.py`, `nachspielen.py` und `pakete_messen.py` messen per Default
    den Makro-Entscheider. `--kern neu` gibt den alten Stand.
  - `nachspielen.plan_art` bildet ein Makro-Kommando auf die alten Handlungs-Arten ab (`makro/aktionen.plan_art`).
    Damit gelten die Soll-Listen der Szenarien weiter.
  - `szenarien.py --json DATEI` schreibt Rot und Grün je Szenario für den Vergleich makro/neu.
  - `kennzahlen.py` wertet den Fassungswechsel „Weiter:“/„Los:“ desselben Kommandos nicht als Wechsel.
- **Briefing:** bleibt bei Claude (unverändert).
- **Reihenfolge:**
  - `makro/vorrang.py` kennt zwei Reihenfolgen.
    - `"wert"`: Gefahr vorn, dann der Aktionswert des Gehirns (`aktionen.wert`: der Wert der Option des Kommandos,
      sonst der beste Wert seiner Aktion). Wo kein Wert da ist, gilt der feste Wert als Ersatz.
    - `"fest"`: der Stand aus 034, Klasse und fester Wert.
  - Schalter: `wissen/kern.toml [makro_gehirn] reihenfolge`. Default ist `"wert"` nach 035.
  - `makro/aktionen.py` ordnet jedem der 111 Kommandos die Aktion des Gehirns zu, mit Ziel (Objective-Monster,
    Rotations-Zone). Verneinte Kommandos („nicht“, „kein“, „lass“, „zu spät“) kehren die Richtung um. Sicht und
    Info haben keine Aktion.

**Die Reihenfolge-Entscheidung steht noch aus.** Ohne Gehirn sind beide Reihenfolgen im Bot-Nachspiel gleich (Zahlen
oben, identisch). Die Entscheidung fällt an den Treue-Zahlen:

- `treue.py` misst beide.
- `abnahme_035.py` schreibt, welche besser ist.
- Die bessere bleibt: `reihenfolge` in `kern.toml` bei Bedarf auf `"fest"` zurückstellen.

## Teil 1: Verdrahtung

- **`werkzeuge/makro_messen.py [stamm …] [--reihenfolge fest|wert] [--kern makro|neu]`:**
  - spielt alle Testpartien parallel nach, mit Stub-Stimme (`LOLCOACH_MAKRO_STIMME=stub`: der Weg über
    `stimme.py`, der Satz ist die Vorlage);
  - rechnet die 027-Maße (`pakete_messen.hoeren`) auf den gesprochenen Makro-Sätzen, dazu die Zahlen aus
    `makro_protokoll.py`: Laufzeit je Entscheidung, stumme Entscheidungen wegen fehlender Wahrnehmung, Vorlage
    statt Claude;
  - gibt die Tor-Zeilen von Teil 1 aus.
- **Generalprobe:** `abnahme_035.py` ruft `werkzeuge/generalprobe.py` mit `--kern makro` (nur Windows).
- **Laufzeit mit echtem Gehirn:** `abnahme_035.py` misst `gehirn.py` allein und schreibt die Takt-Laufzeit aus dem
  Makro-Protokoll.
- **Fixes, die das Bot-Nachspiel gefunden hat** (Verdrahtung, kein Entscheidungswissen):
  - **Gefahr-Pingpong:** Eine Gefahr löst eine andere nur ab, wenn die alte erledigt ist.
  - **Kaufen:** Im Brunnen und tot rückt eine Gefahr nach hinten (außer M9). Kaufen geht dort vor.
  - **Falsche Kämpfe:** Vor 14:00 zählt ein Gegner-Haufen im Lane-Bereich ohne frischen Kill nicht als Kampf
    (`live._kampf`). Im KAMPF spricht der Coach nur Gefahr, mit höchstens 5 Wörtern.
  - **Erinnerung ohne Rückfall-Pause:**
    - Die Erinnerung kommt nach 25 s Stille, wenn Platz ist (vorher bis zu 78 s Lücke).
    - Dasselbe Kommando kommt in 30 s höchstens einmal, sonst kurz als „Weiter: …“.
  - **Stillstand:**
    - Nach 3,5 s ohne Bewegung (Radius 120) kommt „Los: …“.
    - Keine Meldung nach einem Back, nach einem Kauf im Brunnen, oder wenn seit dem Stehen schon gesprochen wurde.
  - **Satzlänge:**
    - Die Vorlage ist höchstens 14 Wörter lang, bei Gefahr höchstens 8. Sonst wird sie gekürzt: ganz → Tun + Weil
      → Tun.
    - Bei Stimme und Prüfung fehlt aber nie ein Fakt der vollen Anweisung (`Anweisung.voll`).
  - **Nicht gehörte Sätze:** Ein verworfener Satz sperrt nicht die Wiederholung desselben Kommandos.
  - **Grund:** Der Grund einer Anweisung kommt nur bei erstem Plan, Gefahr, Ereignis, Frage oder Erledigt
    (`_mit_grund`, im Herzschlag geachtet).

## Teil 2: Challenger-Treue

`werkzeuge/challenger/treue.py [--n 30000] [--alt 3000] [--beispiele 10]` → `buecher/challenger/treue.json`.

- **Grundlage:** die zurückgelegten Prüfpartien aus 030 (`aufteilung.json`), dieselbe Stichprobe wie
  `analyse.Pruefdaten`.
- **Lage:** `lage_aus_moment` baut die `MakroLage` aus dem Riot-Moment (Namen und Werte der Phase-1-Merkmale).
  Wellen, Wards, Büsche, Trinket, Abklingzeiten, Kaufplan und Chat bleiben leer. Entscheidungen, die sie brauchen,
  schweigen (`VORHANDEN`). Sie zählen nicht als Fehler, `stumm_je_entscheidung` weist sie getrennt aus.
- **Kommando:** der Entscheider aus `takt.py` mit den vorberechneten Modellwerten des Moments (identisch mit
  `gehirn.bewerte`). Jeder Moment ist ein erster Takt, ohne Sperre, denn die Sperre braucht die Live-Merkmale des
  alten Kerns.
- **Gemessen:**
  - Treffer streng (a0) und locker (die Aktion trifft in den 60 s irgendwann zu). Bei „geteilt“ zählt eine der
    zwei Optionen.
  - Treffer nur bei Siegern, nur bei Challenger-Spielern, beides.
  - Wert: doppelt robust (AIPW ψ − Y, Standardfehler über Partien), dazu das reine Modell.
  - Abdeckung: der Coach feuert eine Entscheidung (nicht nur die Grund-Anweisung) bzw. eine mit Aktion.
  - Warnungs-Präzision.
- **Vergleiche:**
  - „immer farmen“;
  - die häufigste Aktion je Rolle und Minute (aus den Trainingspartien);
  - der alte Kern (`--kern neu`, `testlage.pruefen`) auf den Momenten, an die er sich anlegen lässt: Top, Lane-Phase,
    Welle unbekannt. Der Coach wird dort auf denselben Momenten gemessen.
- **„Deutlich“** (Messdefinition in `abnahme_035.py`): gegen jeden Vergleich mindestens 5 Prozentpunkte mehr Treffer
  **und** ein um mehr als zwei gemeinsame Standardfehler höherer Wert.
- **Geprüft:** `tests/makro/test_treue.py` mit konstruierten Momenten (Lage, Treffer, geteilt, Politiken). Die
  Zahlen selbst gibt es erst mit `daten/challenger/phase1` und den Modellen.

**Zehn Beispiel-Momente:** `treue.py` schreibt sie nach `treue.json` (Lage, Kommando, was der Challenger tat, Folge)
und `abnahme_035.py` in `phase5_messung.md`. Hier nicht möglich (keine Riot-Daten).

## Teil 3: Sicherheit, Szenarien, Abo-Runde

- **Sicherheit:**
  - Jeder Makro-Satz geht durch `Kern.makro_sperre` (R1, Kill-Check, Fakten, verbotene Begriffe) und beim Sprechen
    durch `stratege.sicherheit`. Bot-Nachspiel: 0.
  - Die Probe mit falschem Claude (`nachspiel_abdeckung`, abweichende Sätze) zeigte: Ein Satz mit fremden Zahlen,
    Namen oder Aktionen wird nie gesprochen, dann spricht die Vorlage.
- **Szenarien:** `szenarien.py` läuft mit `--kern makro`; in der Cloud 0/43, jede Datei braucht ihre Aufnahme.
  Die 14 bekannten Roten, vorab beurteilt am Code. Die Zeile je Szenario schreibt Carlos' Lauf
  (`phase5_messung.md`, Spalte „Beurteilung“).

| Szenario | Vorab-Urteil |
|---|---|
| s23-plan-hoechstens-14 | Regel bleibt richtig. Der Makro-Satz ist jetzt höchstens 14 Wörter lang (Gefahr 8); erwartet grün |
| a4-lagebild-ungefragt | an die alten Regeln gebunden (LAGEBILD des alten Systems, das unter `makro` schweigt) – neu fassen oder streichen |
| wendepunkt-ansage (×3) | bleibt richtig: Turmfall, Objective und Basis verlassen sind Anlässe für einen neuen Plan, und `_mit_grund` gilt als Wendepunkt. Im Lauf prüfen, ob der Satz in ≤ 3 s kommt |
| 0944-turm-ist-down | bleibt richtig; R6 („Ihr Turm ist weg“) deckt es ab – im Lauf prüfen |
| 0944-nach-turmfall-kein-farmen | bleibt richtig; nach dem Turmfall rotiert die Makro-Kette – erwartet grün |
| 0944-erster-tower-was-jetzt | Frage an den Entscheider (JETZT-Antwort = volle Anweisung) – im Lauf prüfen |
| wohin-kurz | bleibt richtig (Wiederholung); „Weiter:“ statt des ganzen Satzes – erwartet grün |
| m-Szenarien „mehrere Events“ (×7) | bleiben richtig (Soll vom blinden Challenger-Kritiker). Über `plan_art` gilt die Aktion des Makro-Kommandos; das Urteil gibt der Lauf |

- **Abo-Runde (091311, 134020, 164809):** erst, wenn Teil 1 und 2 stehen. `abnahme_035.py` prüft das und nennt
  am Ende den Befehl, startet ihn aber nie:
  ```
  python werkzeuge/nachspiel_abdeckung.py laufen 2026-09-30_091311 2026-09-30_134020 2026-09-26_164809 --aus buecher/protokolle/proben/abo_035
  ```
  Danach die Kritiker (`werkzeuge/kritik_mehrheit.py`). Hier nicht gelaufen (kein Guthaben, keine Aufnahmen).
- **134020, Notiz-Stellen 028 neben 035:** Das gibt die Abo-Runde; hier nicht möglich.

## Was bei Carlos zu tun ist

1. `python werkzeuge/abnahme_035.py` (ohne Guthaben).
2. `buecher/challenger/phase5_messung.md` lesen. Reihenfolge festlegen, dann die 14 Roten je Zeile beurteilen.
3. Wenn Teil 1 und 2 stehen: die Abo-Runde mit dem genannten Befehl, dann die Kritiker.
4. Diesen Bericht mit den Zahlen ergänzen und das Tor neu setzen.

## Prüfung in der Cloud

- `tests/makro/alle.py`: 7/7 grün (neu: `test_vorrang`, `test_treue`; `test_einbau` mit Verdrahtung 035 und
  höchstens 14 Wörtern).
- `tests/einzeln.py --basis`: 86 grün, 34 rot, **neu rot: keine** (die 34 brauchen `daten/`, Data Dragon oder
  Windows, wie vor 034).
