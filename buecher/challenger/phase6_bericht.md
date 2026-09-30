Guthaben: 0,00 $

# Challenger-Gehirn, Stufe 6: Gefahr aus dem Modell (Auftrag 036)

**TOR NICHT ERREICHT – noch nicht gemessen.** Der Umbau steht, gemessen wird bei Carlos. In der Cloud fehlen
`daten/` (Riot-Momente, Modelle) und `aufnahmen/`. Kein Claude-Aufruf, kein Guthaben, der Coach wurde nicht
gestartet. Zwei Befehle bei Carlos, ohne Claude Code:

```
python werkzeuge\challenger\gefahr_schwelle.py
python werkzeuge\abnahme_035.py
```

Das erste bestimmt die Schwelle und schreibt sie nach `wissen/kern.toml`. Das zweite misst alles:
`buecher/challenger/phase5_messung.md`, jetzt mit der Tor-Zeile aus 036, den Warnungszahlen, den Fehlfällen
Stillstand/Basis und dem Grund jedes roten Szenarios.

## Tor-Tabelle vorher und nachher

„Vorher“: Carlos' Lauf mit 035 (`phase5_messung.md`, 30.09.2026).
„Bot“: das Bot-Nachspiel `tests/botspiel_riven_2` in der Cloud, ohne Gehirn. Es prüft nur die Verdrahtung.

| Maß | Soll | vorher (035) | nachher (036) |
|---|---|---|---|
| **Tor 036:** Treffer gegen „häufigste je Rolle und Minute“ | höher | 14,8 % gegen 32,7 % ✘ | bei Carlos |
| **Tor 036:** Wert gegen „häufigste je Rolle und Minute“ | höher | −0,47 gegen +0,45 ✘ | bei Carlos |
| Challenger-Treue (035) | alle drei Vergleiche deutlich | ✘ | bei Carlos |
| Warnungen | Anteil klein, Tod danach ≥ 2 × ohne | 87,3 %; 20,0 % gegen 19,7 % | ≤ 15 % und ≥ 2 × (Wahl der Schwelle) – bei Carlos |
| Sicherheit | 0 | 0 ✔ | Bot: 0 ✔ |
| Widerspruch | ≤ 1 je Partie | 0 ✔ | Bot: 0 ✔ |
| Füllsätze | ≤ 5 % | 0 % ✔ | Bot: 0 % ✔ |
| Lücke p90 / längste | ≤ 20 s / ≤ 35 s | 9 s / 26 s ✔ | Bot: 11 s / 28 s ✔ |
| Stillstand | ≥ 95 % | 153/191 = 80 % ✘ | Bot: 15/15 ✔ – die Ursachen unten sind behoben, bei Carlos |
| Basis | ≥ 95 % | 86/104 = 83 % ✘ | Bot: keine Fälle – bei Carlos |
| Laufzeit je Takt | < 50 ms | p95 11,2 ms ✔ | Bot ohne Gehirn p95 1,4 ms; Gate ohne Mehrkosten |
| Guthaben | 0 $ | 0 $ ✔ | 0 $ ✔ |

Im Bot-Nachspiel fielen die Warnungen von 61 auf 0: ohne Gehirn warnt nur noch B4, und B4 kam in dieser Partie
nicht vor. Die Ansagen fielen von 151 auf 105, und alle Verdrahtungsmaße halten. Das ist kein Beleg für das
Können; der zählt erst in Carlos' Lauf.

## 1. Gefahr kommt aus dem Modell

**Befund aus 035:** 87 % aller Lagen waren Warnungen, vor allem J5 (19.425 von 30.000) und J4 (3.893). Tod in 60 s
nach einer Warnung: 20,0 %, ohne Warnung: 19,7 %. Die Warnungen waren Rauschen und verdrängten jede andere Anweisung.

**Umbau:**
- **Todeswahrscheinlichkeit der Lage:** `Hirn.tod60` (`makro/lage.py`) ist das Gefahr-Modell aus 031
  (`gefahr60`) je Aktion, gewichtet mit dem, was High-Elo-Spieler hier tun (`pi`). Das ist die Chance, in den
  nächsten 60 s zu sterben, wenn man spielt wie sie.
- **Bestätigung:** `vorrang.bestaetigt`.
  - Eine Gefahr-Entscheidung zählt nur, wenn `tod60 >= gefahr_schwelle`. Die Handregel (J4, J5, J9 …) ist nur
    noch Zusatzbedingung: Das Modell allein warnt nicht, die Handregel allein auch nicht.
  - Ohne Modellwert warnt nur `OHNE_MODELL = ("B4",)`: wenig Leben mit Gegnern in der Nähe, das R1 des alten
    Kerns.
  - Die Sperre des alten Kerns (R1, Kill-Check) bleibt unverändert davor.
- **Entscheider:** `Entscheider.entscheide` wirft nicht bestätigte Warnungen vor dem Vorrang heraus. Das Protokoll
  `<stamm>_makro.jsonl` schreibt dazu `tod60` und `unbestaetigt`.
  - Ein gehaltener Warn-Plan endet, sobald das Modell ihn nicht mehr bestätigt (Grund „erledigt“).
  - **Nie Schweigen:** Fällt die Warnung weg, spricht die beste andere Anweisung, sonst G0.
- **Vorrang:** `vorrang.py` stellt Gefahr weiter nach vorn, aber nur eine bestätigte. Sonst entscheidet der
  Aktionswert. Die Reihenfolge bleibt `"wert"`, wie 036 1.4 es sagt. Den Unterschied zu „fest“ aus 035
  (Treffer 14,3 gegen 14,8 %, Wert −0,45 gegen −0,47) deckt der Standardfehler (0,18); `abnahme_035.py` misst
  beide wieder.
- **Tod und Brunnen:** Tot hält eine Warnung wie im Brunnen keinen Plan mehr fest. In 035 bekam ein Toter
  „Zurück zum Turm“.

### Die Schwelle

- **Vorläufig `gefahr_schwelle = 0.40`** in `wissen/kern.toml [makro_gehirn]`. Das ist die doppelte Grundrate
  (Tod in 60 s: 19,7 % in 035), also das Ziel „mindestens doppelt so wahrscheinlich“, direkt als Schwelle gesetzt.
  Sie ist nicht gemessen und nicht gewählt.
- **Gewählt wird sie bei Carlos:** `werkzeuge/challenger/gefahr_schwelle.py`.
  - Je Prüfmoment läuft der echte Entscheider zweimal: mit Schwelle 0 (jede Handregel warnt) und mit Schwelle
    unendlich (keine warnt). Alle Handregeln einer Lage teilen denselben Wert `tod60`. Deshalb ist der Coach bei
    jeder Schwelle s genau einer der beiden Läufe, und die ganze Kurve 0,000–0,950 ist exakt berechnet.
  - Gewählt wird die **kleinste** Schwelle, also die mit den meisten Warnungen, für die gilt: Tod nach Warnung
    ≥ 2 × Tod ohne Warnung **und** Warnungen ≤ 15 % aller Ansagen, bei mindestens 50 Warnungen.
  - Gewählt wird an der einen Hälfte der Prüfpartien (nach Partie geteilt), geprüft an der anderen. Beide stehen
    in der Ausgabe und in `buecher/challenger/gefahr_schwelle.json`.
  - Dazu die Treue bei dieser Schwelle gegen „immer farmen“ und „häufigste je Rolle und Minute“, sowie „jede
    Handregel warnt“ (wie 035) und „keine warnt“.
  - Das Werkzeug schreibt den Wert mit Faktor und Anteil als Kommentar nach `kern.toml`.
- **Wenn keine Schwelle beide Bedingungen erfüllt,** schreibt es die mit dem höchsten Faktor unter 15 % und sagt
  klar „ZIEL NICHT ERREICHT“. Dann trennt das Gefahr-Modell die Lagen der Handregeln nicht scharf genug. Das ist
  ein Befund über das Modell, keiner über die Schwelle.
- **Prüfsteine** (Kategorie G unten): 0904-drei-kommen, 0545-back-bei-40-prozent, 2531-warnung-bleibt und
  0923-gewarnt-nicht-nebel verlangen eine Warnung. Werden sie mit der gewählten Schwelle rot, ist sie zu hoch.

## 2. Verdrahtung: Stillstand 80 % und Basis 83 %

**Der Lauf aus 035 hat keine Fehlfälle je Zeit geschrieben,** nur die Summen. Deshalb gibt es hier keine Zeile je
Fall aus Carlos' Partien. Neu:
- `pakete_messen.hoeren` schreibt jeden Fehlfall mit Zeit, Ort und dem Satz davor (`still_fehl`, `basis_fehl`).
- `makro_messen.py` gibt sie aus (`STILLSTAND …`, `BASIS …`).
- `abnahme_035.py` stellt sie als Tabelle „je eine Zeile“ in `phase5_messung.md`.

**Die Ursachen, im Code gegen die Messung aus 027 gefunden und behoben:**

| Fall | Ursache | behoben |
|---|---|---|
| Stillstand im Brunnen nach dem Einkauf | 027 beginnt das Stehen nach den 10 s Einkauf neu. Der Coach behielt seinen Anker, zählte den Kauf-Satz als „seit er steht, kam eine Anweisung“, und das „Los“ kam nie. Jedes Stehen im Brunnen nach dem Kauf war ein Fehlfall. | Anker neu nach Einkauf; Einkauf wie 027: ein Satz mit „Kauf“ in der ganzen Basis (`einbau._stillstand`) |
| Stillstand nach dem Recall-Kanal | wie oben: der Back-Ruf galt als Anweisung fürs spätere Stehen | Anker neu nach dem Kanal (16 s) |
| Stillstand nach einem Kampf am selben Fleck | 027 beginnt nach KAMPF neu, der Coach nicht | Anker neu im KAMPF |
| Basis: Ankunft zu Fuß | 027 misst ab dem Betreten der eigenen Basis (`m.bereich == "basis_eigen"`). B7 feuerte erst am Brunnen (1200 Einheiten), Sekunden zu spät für ≤ 2 s. | `Spieler.in_basis` (`live.py`); B7 in der ganzen Basis, wenn der Kaufplan ein Bauteil jetzt kaufbar sieht |
| Basis: Ankunft mitten in einem gehaltenen Plan | Der Kauf brauchte einen Grund für den Planwechsel (Regel 028) und blieb bis zu 20 s hinter dem alten Plan | Der Wechsel zum Kauf in der Basis oder im Tod ist ein Ereignis (`takt.py`) |
| Basis: Kauf wartete aufs Budget | ein Ereignis-Wechsel binnen 8 s nach dem letzten Wendepunkt ging als PLAN ins Budget | Kauf beim Ankommen: WENDEPUNKT ohne Abstand und Budget (`einbau.py`) |
| Basis nach langem Tod | B7 („Kauf …“) kam beim Sterben und wurde gehalten. B8 („Du lebst in …: Kauf-Kette“) kam nie durch, und der Kauf-Satz lag mehr als 14 s vor dem Respawn. | B8 geht B7 vor, der Wechsel ist ein Ereignis |

Geprüft mit konstruierten Lagen (`tests/makro/test_einbau.py: stillstand_und_basis_036`). Ob damit 95 % erreicht
sind, zeigt Carlos' Lauf. Jeder verbleibende Fehlfall steht dann als eigene Zeile da.

## 3. Die roten Szenarien

Unter `--kern makro` waren in 035 121 von 383 rot. **Neu messen geht nur bei Carlos,** denn jede Szenario-Datei
braucht ihre Aufnahme. Deshalb ist hier jedes Rot einzeln beurteilt: aus dem, was es prüft, gegen das, was der
makro-Entscheider sagt. Den Grund des Rots schreibt `szenarien.py --json` ab jetzt mit (`gruende`), und
`phase5_messung.md` zeigt ihn. Nichts ist gelöscht.

| Kategorie | Anzahl | Bedeutung |
|---|---:|---|
| W | 50 | Warnungsflut: Die Warnung (meist J5 „Zurück zum Turm“) verdrängte die geprüfte Anweisung. Mit Teil 1 neu messen. |
| G | 4 | Gefahr-Prüfstein: Hier MUSS gewarnt werden. Grün nur, wenn das Modell bestätigt. Prüft die Schwelle. |
| T2 | 7 | Kauf in der Basis oder im Tod: durch Teil 2 behoben, neu messen |
| U | 11 | umgeschrieben: Das Szenario prüfte eine alte Formulierung. Die makro-Fassung ist als weitere Alternative ergänzt, die alte bleibt (`--kern neu` prüft dasselbe wie vorher). |
| F | 15 | alte Formulierung oder Kategorie (LAGEBILD, INFO_BASIS, Teamplan-Sätze): nach dem Neumessen umschreiben, Vorschlag je Zeile |
| B | 34 | Befund: Der neue Entscheider macht es wirklich falsch oder gar nicht. Liste unten. |

| Szenario | Datei | neu (035) | Kat. | Beurteilung |
|---|---|---|---|---|
| m01-mehrere-events-259 | 2026-09-26_120049_auftrag025 | gruen | W | Soll Welle/Gruppe; die Warnung (ZURUECK) stand vorn - neu messen |
| m02-mehrere-events-508 | 2026-09-26_120049_auftrag025 | gruen | W | Soll Welle/Rotation; die Warnung stand vorn - neu messen |
| m03-mehrere-events-728 | 2026-09-26_120049_auftrag025 | rot | W | Soll Back/Objective; auch unter neu rot - nach Teil 1 neu messen, dann Befund oder Soll pruefen |
| m04-mehrere-events-225 | 2026-09-26_125902_auftrag025 | - | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m05-mehrere-events-445 | 2026-09-26_125902_auftrag025 | - | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m06-mehrere-events-643 | 2026-09-26_125902_auftrag025 | rot | W | Soll Back/Seitenwelle/Gruppe; auch unter neu rot - neu messen |
| m07-mehrere-events-138 | 2026-09-26_164809_auftrag025 | rot | W | Soll Back/Kauf bei 1:38; auch unter neu rot - neu messen |
| m08-mehrere-events-504 | 2026-09-26_164809_auftrag025 | - | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m09-mehrere-events-808 | 2026-09-26_164809_auftrag025 | - | W | Soll Back oder Larven; die Warnung stand vorn - neu messen |
| 0904-drei-kommen | 2026-09-27_102112 | gruen | G | Drei Gegner kommen: hier MUSS die Warnung bleiben (Soll ZURUECK). Gruen nur, wenn das Gefahr-Modell bestaetigt - Pruefstein fuer die Schwelle |
| 2522-kein-baron-drache-lebt | 2026-09-27_102112 | gruen | W | Soll Druecken/Gruppe, nicht Baron; die Warnung stand vorn. Nach Teil 1 pruefen, ob O4 'Baron' sagt - dann Befund |
| 2847-baron-statt-drache | 2026-09-27_102112 | gruen | W | Wie 2522: Soll Druecken/Nehmen ohne Baron - neu messen |
| 3500-drache-solo | 2026-09-27_102112 | gruen | B | SOLL_ICH-Frage: die makro-Antwort ist der ganze Plan-Satz, ohne Ja/Nein zur gefragten Handlung (muss 'Ja/nimm') - Befund: SOLL_ICH braucht ein Ja/Nein gegen den Aktionswert der gefragten Aktion |
| 3632-ende-statt-back | 2026-09-27_102112 | gruen | W | Spaetphase: Soll Druecken Mid/Inhibitor, kein Back mit 4400 Gold. Nach Teil 1 pruefen, ob B1/B2 (Back-Grund Gold) vorn steht - dann Befund |
| 0545-back-bei-40-prozent | 2026-09-27_102112_buch3 | gruen | G | Soll Rueckzug/Back bei 40 % Leben, Fiddlesticks kommt - Gefahr-Pruefstein (Modell muss bestaetigen), darf nicht 'Kampf an' |
| 0600-basis-kauf | 2026-09-27_102112_buch3 | gruen | T2 | Kauf in der Basis: B7 in der ganzen Basis, Kauf-Wechsel als Ereignis ohne Budget (Teil 2) - neu messen |
| 1315-crash-dann-back | 2026-09-27_102112_buch3 | gruen | W | Soll Back nach dem Crash; die Warnung stand vorn - neu messen |
| 3451-drache-an-der-grube | 2026-09-27_102112_buch6 | gruen | W | Soll Drache nehmen (an der Grube, drei tot); die Warnung stand vorn - neu messen |
| 3831-nexus-nicht-inhib | 2026-09-27_102112_buch6 | gruen | W | Soll Nexus druecken; die Warnung stand vorn (P4/J5) - neu messen |
| 1453-herold-ein-satz | 2026-09-27_102112_buch6 | gruen | W | Kein Herold, keine neue Info wiederholen, <= 18 Woerter; Warnungen wiederholten sich - neu messen |
| 2501-sona-allein | 2026-09-27_102112_buch7 | gruen | B | Soll 'Rein/Annehmen' in <= 8 Woertern; im KAMPF spricht makro nur Gefahr (034, Buch 17: Mikro macht Carlos) - Befund/Entscheidung fuer Carlos: sollen Annehmen-Rufe im Kampf kommen? |
| 2613-fiddlesticks-allein | 2026-09-27_102112_buch7 | gruen | B | Wie 2501 (Annehmen im Kampf) - Entscheidung fuer Carlos |
| 2631-zu-zweit-rein | 2026-09-27_102112_buch7 | gruen | B | Wie 2501 (Annehmen im Kampf) - Entscheidung fuer Carlos |
| 3002-basis-ein-ziel | 2026-09-27_102112_pruefung | gruen | T2 | In der Basis nur ein Ziel: jetzt Kauf zuerst, Wechsel als Ereignis - neu messen |
| 0647-mid-larven-zu-frueh | 2026-09-27_140253_buch6 | gruen | T2 | Soll Kauf (Ziel Mid), keine Larven zu frueh: Kauf in der Basis (Teil 2) - neu messen |
| 0843-todesrueckblick | 2026-09-27_140253_pruefung | gruen | B | Todesrueckblick ('Raus kam ...', Schluessel tod) ist eine Regel des alten Systems und schweigt unter makro - Befund: der Rueckblick nach dem Tod fehlt |
| 1005-tod-ohne-kopfgeld | 2026-09-27_140253_pruefung | gruen | B | Wie 0843 (Todesrueckblick fehlt unter makro) |
| 0349-ein-plan | 2026-09-27_140253_pruefung | gruen | W | Hoechstens ein Planwechsel 3:45-4:35; Warnungen wechselten - neu messen |
| 0622-tod-gegen-gangplank | 2026-09-27_144655_buch7 | gruen | B | Wie 0843 (Todesrueckblick fehlt unter makro) |
| 0701-lane-hinten-plan | 2026-09-27_144655_pruefung | gruen | W | Soll Welle halten/farmen mit Plan, nicht 'Gangplank kommt.'; die Warnung stand vorn - neu messen |
| 0449-rueckzug-ein-satz | 2026-09-27_144655_pruefung | gruen | W | Hoechstens 2 Ansagen, eine Fassung; Warnungen wiederholten sich - neu messen |
| 0159-wohin-risiko | 2026-09-27_144655_pruefung | gruen | W | Soll WOHIN (Rueckweg nach Top); die Warnung stand vorn - neu messen |
| 0923-gewarnt-nicht-nebel | 2026-09-27_144655_pruefung | gruen | G | Muss Kha'Zix nennen (war gewarnt): Gefahr-Pruefstein - nach der Schwelle pruefen, ob die Warnung bleibt |
| 1400-teamplan | 2026-09-27_164326_buch4 | gruen | F | Prueft die Teamplan-Saetze des alten Systems ('Gold vorn ... erzwingen/skalieren'); makro sagt V2/V3 ('Vorsprung umwandeln', 'Rueckstand spielen') - umschreiben auf V2/V3, wenn es nach Teil 1 rot bleibt |
| 3048-naafiri-unten-fenster-oben | 2026-09-27_164326_buch4 | gruen | F | Prueft 'Naafiri ... frei' (altes Fenster); makro J3 sagt 'Er ist <Lane>: <n> s Ruhe' - umschreiben auf 'Ruhe', wenn rot bleibt |
| 3302-sie-haben-den-baron | 2026-09-27_164326_kritik008 | gruen | F | Prueft 'Sie haben den Baron' (Ereignis-Satz des alten Systems); makro nennt den Baron-Verlust nicht als eigenen Satz - umschreiben oder Befund (Ereignis-Ansage fehlt) |
| 2239-keine-doppelwarnung | 2026-09-27_164326_pruefung_c | gruen | W | Hoechstens 2 Warnungen 22:30-23:20 - genau die Warnungsflut; neu messen |
| wendepunkt-ansage | 2026-09-27_164326_pruefung_c | rot | W | Plan-Satz <= 3 s nach Turmfall/Objective/Basis; auch unter neu rot. Unter makro verdraengten Warnungen den Wendepunkt - neu messen |
| 1400-teamplan | 2026-09-27_173159_buch4 | gruen | F | Prueft die Teamplan-Saetze des alten Systems ('Gold vorn ... erzwingen/skalieren'); makro sagt V2/V3 ('Vorsprung umwandeln', 'Rueckstand spielen') - umschreiben auf V2/V3, wenn es nach Teil 1 rot bleibt |
| back-dauerton | 2026-09-27_173159_pruefung_c | gruen | B | Kein 'Back' ohne neue Info: die Erinnerung ('Weiter: Back.') wiederholt den Back-Ruf - Befund: Back-Kommandos nicht als Erinnerung wiederholen |
| wendepunkt-ansage | 2026-09-27_173159_pruefung_c | rot | W | Plan-Satz <= 3 s nach Turmfall/Objective/Basis; auch unter neu rot. Unter makro verdraengten Warnungen den Wendepunkt - neu messen |
| 0455-sona-ohne-flash | 2026-09-27_213624 | gruen | W | J8 sagt 'Sona ohne Flash ...' - kam nicht durch, weil die Warnung vorn stand; neu messen |
| 0841-rumble-ohne-flash | 2026-09-27_213624 | gruen | W | Wie 0455 (J8 Rumble) - neu messen |
| 1900-raus-unter-15 | 2026-09-27_213624 | gruen | U | Umgeschrieben: makro sagt bei wenig Leben 'Back' (B4) - 'Back'/'Zurueck' ergaenzt, 'Raus' bleibt |
| 0944-turm-ist-down | 2026-09-27_213624 | gruen | F | Prueft 'Turm ist down/weg'; makro R6 formuliert die Rotation nach Turmverlust anders - nach Teil 1 den Satz ansehen, dann umschreiben |
| wendepunkt-ansage | 2026-09-27_213624 | rot | W | Plan-Satz <= 3 s nach Turmfall/Objective/Basis; auch unter neu rot. Unter makro verdraengten Warnungen den Wendepunkt - neu messen |
| 2209-von-der-bot-lane | 2026-09-27_213624_auftrag011 | gruen | F | Prueft 'Von der Bot-Lane ... Mid-Turm' (alte Rotation); makro R-Kommandos formulieren anders - umschreiben auf die Plan-Art, wenn rot bleibt |
| 1617-drei-von-ihnen-tot | 2026-09-27_213624_buch4 | gruen | F | Prueft 'von ihnen tot' + Ziel (altes Umwandeln); makro K4 'Nach dem Sieg: umwandeln' formuliert anders - umschreiben, wenn rot bleibt |
| 0119-warum-raus-zum-turm | 2026-09-27_213624_fragen | gruen | U | Umgeschrieben: die Warnung heisst unter makro 'Zurueck zum Turm' - 'Zurueck' ergaenzt |
| 0127-warum-raus-obwohl-ich-gewinne | 2026-09-27_213624_fragen | gruen | U | Wie 0119 |
| 0404-xin-ist-bei-mir-oben | 2026-09-27_213624_fragen | gruen | B | JETZT-Frage mit Korrektur ('Der ist bei mir'): die makro-Antwort ist der Plan-Satz und nennt Xin nicht - Befund: Korrekturen zur Lage werden unter makro nicht aufgenommen |
| 0458-soll-ich-team-helfen | 2026-09-27_213624_fragen | gruen | W | SOLL_ICH mit Handlung: die Antwort war die Warnung - neu messen (Ja/Nein siehe 3500) |
| 0955-tower-down-was-jetzt | 2026-09-27_213624_fragen | gruen | W | JETZT mit Ziel (Turm/Drache/Team): die Antwort war die Warnung - neu messen |
| 1036-habe-ich-und-was-jetzt | 2026-09-27_213624_fragen | gruen | W | JETZT mit Ziel - neu messen |
| 1052-warum-nicht-drache-helfen | 2026-09-27_213624_fragen | gruen | B | WARUM zur Alternative 'Drache': die makro-Antwort nennt nur den eigenen Grund und die zweite Option, nicht die gefragte - Befund: WARUM muss die gefragte Alternative mit ihrem Aktionswert beantworten |
| 1135-warum-top-und-nicht-drache | 2026-09-27_213624_fragen | gruen | B | Wie 1052 (gefragte Alternative Drache) |
| 1205-warum-top-statt-drache | 2026-09-27_213624_fragen | gruen | B | Wie 1052 (gefragte Alternative Drache) |
| 1223-drache-war-kuerzer | 2026-09-27_213624_fragen | gruen | B | JETZT mit Einwand 'Drache war kuerzer': Antwort ohne den Drachen - wie 1052 |
| 1256-drache-oder-turm | 2026-09-27_213624_fragen | gruen | B | ENTWEDER 'Drache oder Turm': die makro-Antwort vergleicht die zwei gefragten Optionen nicht - Befund |
| 1312-was-mache-ich-jetzt | 2026-09-27_213624_fragen | gruen | W | JETZT, muss Drache, nicht 'Farm': die Antwort war die Warnung - neu messen |
| 1316-welche-welle-welche-lane | 2026-09-27_213624_fragen | gruen | W | JETZT mit Lane/Drache - neu messen |
| 1336-drache-tot-wohin | 2026-09-27_213624_fragen | gruen | W | JETZT mit Ziel nach dem Drachen - neu messen |
| 1348-was-jetzt-leerlauf | 2026-09-27_213624_fragen | gruen | W | JETZT mit Ziel - neu messen |
| 1437-okay-was-jetzt | 2026-09-27_213624_fragen | gruen | W | JETZT mit Ziel - neu messen |
| 1640-was-nach-dem-tower | 2026-09-27_213624_fragen | gruen | W | DANACH mit Ziel (Turm/Drache/Baron): 'Danach ...' kommt aus dem Plan - neu messen |
| a1-warnungen-je-30min | 2026-09-28_101426_auftrag008 | gruen | W | Hoechstens 11 Warnungen je 30 min - genau die Warnungsflut; mit Teil 1 erwartet gruen |
| 2531-warnung-bleibt | 2026-09-28_101426_auftrag008 | gruen | G | Die Warnung muss hier bleiben ('Raus/Zurueck') - Gefahr-Pruefstein fuer die Schwelle |
| a2-konkrete-sprache | 2026-09-28_101426_auftrag008 | gruen | W | Konkrete Sprache: 'Zurueck zum Turm' ohne Lane war der haeufigste Satz - neu messen |
| 3213-ich-bin-tot | 2026-09-28_101426_auftrag008 | gruen | F | Muss 'Sekunden' nennen: makro schreibt '25 s', die Stimme spricht 'Sekunden' (stimme.py) - der Pruefer liest den Text vor der Aussprache. Vorschlag: szenarien.py prueft den gesprochenen Text (stimme-Umschrift) |
| 3216-ja-ich-bin-auch-tot | 2026-09-28_101426_auftrag008 | gruen | F | Wie 3213 ('s' statt 'Sekunden') |
| 2839-kein-kontrollauge-ohne-platz | 2026-09-28_101426_auftrag008 | gruen | B | B7 haengt 'Kontroll-Auge' an, ohne den Inventar-Platz zu pruefen - Befund |
| 1938-korrektur-twitch-bei-mir | 2026-09-28_101426_auftrag008 | gruen | B | Korrektur 'Twitch war bei mir': wie 0404 - Befund |
| 2650-lage-auf-abruf | 2026-09-28_101426_auftrag008 | gruen | F | LAGE-Antwort unter makro: Kills, Drachen, Siegchance + Plan - ohne 'oben/Mitte/unten/fehlen'. Vorschlag: die LAGE-Antwort nennt, wer fehlt (wie RISIKO) |
| a4-lagebild-ungefragt | 2026-09-28_101426_auftrag008 | rot | F | Prueft die Kategorie LAGEBILD des alten Systems (unter makro stumm); auch unter neu rot - umschreiben oder streichen (Carlos) |
| lagebild-folgerung-handelt | 2026-09-28_101426_auftrag009 | gruen | F | Kategorie LAGEBILD des alten Systems - wie a4 |
| bauteil-mit-ziel | 2026-09-28_101426_auftrag009 | gruen | B | B7 sagt 'Kauf Langschwert' ohne das Ziel-Item ('fuer ...') - Befund (Kaufplan kennt das Ziel) |
| 2440-bard-tot-ziel | 2026-09-28_101426_auftrag010 | gruen | W | Mindestens ein PLAN/WENDEPUNKT: die Warnung (GEFAHR) stand vorn - neu messen |
| 3338-drache-drin-ziel | 2026-09-28_101426_auftrag010 | gruen | W | Wie 2440 - neu messen |
| 1037-flash-ohne-ort | 2026-09-28_101426_auftrag010 | gruen | U | Umgeschrieben: J8 sagt 'Aurora ohne Flash' - ergaenzt |
| 2010-keine-wiederholung | 2026-09-28_101426_auftrag011 | gruen | W | Hoechstens 1 Warnung - die Warnungsflut; neu messen |
| m11-mehrere-events-427 | 2026-09-28_101426_auftrag025 | rot | W | Soll Back/Kauf; auch unter neu rot - neu messen |
| m12-mehrere-events-608 | 2026-09-28_101426_auftrag025 | gruen | W | Soll an der Welle bleiben; die Warnung stand vorn - neu messen |
| m15-mehrere-events-637 | 2026-09-28_192113_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| 0354-soll-ich-nicht-durchpushen | 2026-09-28_192113_fragen | gruen | B | SOLL_ICH ohne 'Nein/Back' - wie 3500 (Ja/Nein fehlt) |
| 1024-soll-ich-zum-drake | 2026-09-28_192113_fragen | gruen | B | SOLL_ICH 'zum Drake?': ohne Ja/Nein und ohne Drache - wie 3500/1052 |
| 1034-warum-nicht-zum-drake | 2026-09-28_192113_fragen | gruen | B | WARUM zur Alternative Drache - wie 1052 |
| 1354-wieso-nicht-flash | 2026-09-28_192113_fragen | gruen | B | WARUM nach einem Flash-Satz: makro faengt jede WARUM-Frage ab und antwortet mit dem Plan, der Flash-Fakt fehlt - Befund: WARUM zu einer Fakten-Ansage gehoert dem Faktenweg |
| 1430-warum-weisst-du-nichts-flash | 2026-09-28_192113_fragen | gruen | B | Wie 1354 (Flash-Frage) |
| 1522-sobald-im-fountain-lang | 2026-09-28_192113_fragen | gruen | U | Umgeschrieben: die DANACH-Antwort beginnt mit 'Danach' - ergaenzt |
| 1521-sobald-im-fountain | 2026-09-28_192113_fragen | gruen | U | Wie 1522 |
| 1846-top-farmen-andere | 2026-09-28_192113_fragen | gruen | B | Carlos widerspricht ('Top farmen schon andere'): kein 'Stimmt', der Plan bleibt 'Top-Welle' - Befund: der Einspruch zur Lage (alter Weg: 'Stimmt ...') fehlt unter makro |
| 1940-zwei-leute-farmen-top | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 1948-top-reingepusht | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2014-kein-minion | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2024-teemo-hat-farm-geholt | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2039-warum-nicht-mid | 2026-09-28_192113_fragen | gruen | B | Wie 1846, dazu WARUM zur Alternative Mid (wie 1052) |
| 2052-kein-minion-oben | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2204-adc-farmt-top | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2354-topwelle-am-nexus | 2026-09-28_192113_fragen | gruen | B | Wie 1846 (Einspruch) |
| 2402-drache-erst-in-zwei-minuten | 2026-09-28_192113_fragen | gruen | B | WARUM mit Einwand zum Drachen - wie 1052 |
| 2438-keine-sorgen-vier-unsichtbar | 2026-09-28_192113_fragen | gruen | U | Umgeschrieben: die RISIKO-Antwort sagt 'Unbekannt sind ...' - ergaenzt |
| 2444-warum-sicher-botwelle | 2026-09-28_192113_fragen | gruen | U | Wie 2438 |
| 2514-druecken-obwohl-keiner-zu-sehen | 2026-09-28_192113_fragen | gruen | U | Wie 2438 |
| 0437-drache-timer-zur-sprechzeit | 2026-09-28_192113_fragen | gruen | F | Prueft 'Drache in 1/2 ...' zur Sprechzeit (alter Timer-Satz); makro O7 nennt die Zeit anders ('Drache in 1:30 min') - nach Teil 1 den Satz ansehen, dann umschreiben |
| m17-mehrere-events-403 | 2026-09-29_133448_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m18-mehrere-events-708 | 2026-09-29_133448_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| 1836-was-wenn-ich-lebe | 2026-09-29_183125_auftrag018 | gruen | T2 | Frage im Tod: B8 ('Du lebst in ...: Kauf-Kette, dann direkt <Ziel>') geht jetzt B7 vor - neu messen |
| 1912-plan-nach-respawn | 2026-09-29_183125_auftrag018 | gruen | T2 | Plan mit Ziel nach dem Respawn: B8 nennt das Ziel - neu messen |
| 1935-steht-in-der-basis | 2026-09-29_183125_auftrag018 | gruen | F | Prueft die Kategorie INFO_BASIS des alten Systems; makro spricht dort Kauf (B7) und 'Los: ...' (STILL) - umschreiben auf STILL|PLAN|WENDEPUNKT |
| m19-mehrere-events-441 | 2026-09-29_183125_auftrag025 | rot | W | Soll Back/Kauf; auch unter neu rot - neu messen |
| m20-mehrere-events-701 | 2026-09-29_183125_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m21-mehrere-events-910 | 2026-09-29_183125_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| 0519-tp-weg | 2026-09-29_231200_auftrag024 | gruen | U | Umgeschrieben: J7 sagt 'Xerath hat TP benutzt' - ergaenzt |
| m23-mehrere-events-655 | 2026-09-29_231200_auftrag025 | gruen | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| m24-mehrere-events-854 | 2026-09-29_231200_auftrag025 | - | W | Soll Back/Kauf beim Gold-Spike (blinder Kritiker); unter makro gewann die Warnung (J5 -> ZURUECK). Mit Teil 1 kann B1/B2 (Back-Grund Gold) vorn stehen - neu messen |
| 0118-udyr-weg-platten | 2026-09-29_231200_auftrag026 | gruen | U | Umgeschrieben: J6 sagt '... die Platte holen' - 'Platte' ergaenzt |
| 0402-back-zur-frist | 2026-09-29_231200_auftrag026 | gruen | F | Prueft 'puenktlich zur Kanone' (Wellen-Uhr des alten Systems; 1401 verbietet genau diesen Satz) - umschreiben auf die Plan-Art Back 4:00-4:10 |
| 1753-tot-kauf-vor-respawn | 2026-09-30_091311_auftrag027 | gruen | T2 | Muss 'Kauf' kurz vor dem Respawn: B8 geht B7 vor (Teil 2) - neu messen |
| 2554-kauf-im-tod | 2026-09-30_091311_auftrag027 | gruen | T2 | Wie 1753 |
| 0231-tp-oder-laufen | 2026-09-30_134020_auftrag028 | gruen | B | ENTWEDER 'TP oder laufen': die makro-Antwort ist der Plan-Satz, ohne die zwei Optionen - wie 1256 |
| 1401-kein-back-zum-kaufen | 2026-09-30_134020_auftrag028 | gruen | B | Ornn kauft ohne Back (sonderregeln.toml): der Back-Grund 'Gold fuer ein Bauteil' im Gehirn (back_gruende) kennt die Sonderregel nicht - Befund |

### Die Befunde (B), zusammengefasst

Sie sind nicht behoben. Jeder ist eine eigene Arbeit und lag außerhalb von 036.
1. **Fragen, die der Entscheider abfängt, beantworten nicht die Frage** (13 Szenarien). SOLL_ICH ohne Ja/Nein;
   WARUM/ENTWEDER ohne die gefragte Alternative (etwa „Drache“), obwohl das Gehirn ihren Aktionswert kennt; WARUM
   nach einem Flash-Satz verliert den Fakt.
   - Vorschlag: `MakroCoach.beantworte` sucht die gefragte Aktion in `hirn.optionen` und antwortet mit Ja/Nein
     und dem Wertvergleich.
   - WARUM zu einer Fakten-Ansage geht an den Faktenweg.
2. **Einspruch und Korrektur zur Lage** (11 Szenarien: 1846 … 2354, 0404, 1938). Der alte Weg sagte „Stimmt …“
   und wechselte. Unter makro bleibt der Plan-Satz, obwohl Carlos die Lage korrigiert.
3. **Todesrückblick fehlt** (0843, 1005, 0622). Die Regel des alten Systems schweigt unter makro.
4. **Annehmen im Kampf** (2501, 2613, 2631). Im KAMPF spricht makro nur Gefahr (034, Buch 17). Carlos entscheidet,
   ob „Rein!“-Rufe kommen sollen.
5. **Kauf-Sätze:** B7 ohne Ziel-Item (bauteil-mit-ziel), Kontroll-Auge ohne Inventar-Platz (2839), Back-Grund
   „Gold“ trotz Ornns Sonderregel (1401).
6. **Back als Erinnerung wiederholt** (back-dauerton): „Weiter: Back.“ ohne neue Information.

## Geänderte Dateien

- **Gefahr aus dem Modell:**
  - `lolcoach/makro/lage.py`: `Hirn.tod60`, `Spieler.in_basis`;
  - `vorrang.py`: `bestaetigt`, `schwelle`, `OHNE_MODELL`;
  - `takt.py`: Gate, `unbestaetigt`, `tod60`; Kauf-Vorrang in der Basis und im Tod als Ereignis; tot wie
    Brunnen.
- **Verdrahtung:**
  - `lolcoach/makro/einbau.py`: Schwelle aus `kern.toml`, Protokoll, Stillstand-Anker, Kauf ohne Budget;
  - `live.py`: `in_basis`;
  - `entscheidungen/back.py`: B7 in der Basis.
- **Konfiguration:** `wissen/kern.toml`: `gefahr_schwelle = 0.40` (vorläufig).
- **Werkzeuge:**
  - neu: `werkzeuge/challenger/gefahr_schwelle.py`;
  - `treue.py`: `laden()`, Schwelle je Lauf, Tod ohne Warnung;
  - `abnahme_035.py`: Tor-Zeile 036, Warnungen, Fehlfälle, Szenario-Gründe;
  - `makro_messen.py` und `pakete_messen.py`: Fehlfälle je Zeile;
  - `szenarien.py`: `--json` mit Gründen.
- **Szenarien:** 11 Szenarien in 6 Dateien unter `tests/szenarien/` (U: makro-Fassung ergänzt).
- **Tests:** `tests/makro/test_einbau.py` (`gefahr_aus_dem_modell`, `stillstand_und_basis_036`, bestehende
  Tests mit bestätigter Gefahr), `tests/makro/test_treue.py` (`gefahr_schwelle_rechnung`).

## Prüfung in der Cloud

- `tests/makro/alle.py`: 7/7 grün.
- `tests/einzeln.py --basis`: 86 grün, 34 rot, **neu rot: keine**. Die 34 brauchen `daten/`, Data Dragon oder
  Windows, wie vor 036.
- Konstruierte Lagen (`szenarien.py --konstruiert`): 37/40, wie vor 036.
- Bot-Nachspiel: alle Verdrahtungsmaße im Soll (Tabelle oben).

## Was Carlos tun muss

1. `python werkzeuge\challenger\gefahr_schwelle.py`: die Schwelle; die Ausgabe sagt ZIEL ERREICHT oder NICHT.
2. `python werkzeuge\abnahme_035.py`: alles messen, dann `phase5_messung.md` lesen.
   - Tor 036: Treffer und Wert gegen „häufigste je Rolle und Minute“.
   - Die G-Szenarien müssen grün sein.
   - Jeder Fehlfall Stillstand/Basis steht als eigene Zeile da.
3. **Reicht es nicht,** liegt es wahrscheinlich nicht mehr an den Warnungen. Dann trifft der Rest der 111
   Handregeln selten, was High-Elo-Spieler tun: In 035 kamen `klar`, `geteilt` und `unklar` zusammen auf 12 %
   der Lagen. `phase5_messung.md` zeigt die Formen und Kommandos je Politik. Nicht an der Schwelle drehen, bis die
   Zahl passt.
