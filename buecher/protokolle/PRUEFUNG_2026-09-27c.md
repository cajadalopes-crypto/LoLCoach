# Protokoll-Prüfung 27.09.2026, dritte Runde (Claude, Chat)

Geprüft wurden alle sieben Protokolle nach Schritt 5 (`a2e418d`, `842b502`). Den Schwerpunkt bilden die zwei langen
echten Partien von Carlos:

- **164326:** Riven gegen Teemo, CLASSIC, 42,8 min, gewonnen, 96 Ansagen
- **173159:** Riven gegen Cho'Gath, CLASSIC, 38,3 min, 94 Ansagen

Dazu kam ein Blick auf seine tatsächlichen Items in beiden Partien (API).

**Urteil: nicht freigegeben.**

**Was jetzt gut ist:**

- Der Lane-Plan bei verlorener Lane kommt einmal lang und einmal kurz (G1 hält).
- Im Kampf gibt es nur noch „Raus, zum Turm!“; die stummen Rufe stehen richtig im Protokoll.
- Das Umwandeln bis zum Nexus stimmt: 164326, 42:22: „Nexus-Turm jetzt: 3 von ihnen sind noch 18 Sekunden tot …“.

**Was fehlt:** Mit Schritt 5 schickt der Kern Carlos jetzt **selbst** in Kämpfe und zu Objectives, und dabei fehlen
Schranken, die ein Mensch nie vergessen würde:

- 173159, 35:12: „Zum Ältesten mit Graves und Trundle: ihr seid vier.“ Riven hat **15 %** Leben und steht in ihrer
  Basis. Tod um 35:24.
- 173159, 28:50: „Ältester bestreiten: ihr seid vier.“ (p_tod 0,34) Tod um 29:03, und der Rückblick sagt danach:
  „allein hast du gegen sie keine Chance.“
- 173159, 14:23: „Zum Kampf, jetzt: ihr seid 2 gegen 2, mit dir 3 gegen 2.“ Das bei **16 %** Leben.
- 164326, 41:13: „Drache bestreiten: ihr seid drei.“ Riven steht an der Baron-Grube, p_tod **0,64**.

Dazu schlägt der Kaufplan in beiden Partien ab Minute 12 falsche Items vor, und die Back-Rufe kommen im Dauerton.

Die Punkte sind nach Schaden geordnet. Für jeden gilt: erst das Szenario, das mit dem heutigen Stand rot ist, dann
beheben. Die Szenarien gehören in `tests/szenarien/<aufnahme>_pruefung_c.toml`.

---

## R1. Keine Vorwärts-Handlung mit wenig Leben oder hohem Risiko

**Soll** (gilt für jeden Modus außer KAMPF, wo Buch 7 gilt):

- **Leben:** Unter `vor_leben_min` (0,4) sind diese Handlungen weder Kandidat noch Ansage: `DRUECKEN`, `MIT_GRUPPE`,
  `NEHMEN`, `BESTREITEN`, `ZUR_GRUPPE`, `TP_SPIEL`, `PLATTEN`, `SEITENWELLE`, `WELLE_KLAEREN`,
  `VORBEREITEN_OBJECTIVE`, `ANNEHMEN`.
  - Einzige Ausnahme: `NEHMEN`, wenn du schon in der Grube stehst, `P_kampf < 0,1` gilt und das Objective in ≤ 5 s fällt.
- **Risiko:** Eine Vorwärts-Handlung mit `p_tod ≥ vor_p_tod_max` (0,3) wird nie gesagt.

**Szenarien:**

| id | Aufnahme | zeit / fenster | darf nicht | darf nicht sagen |
|---|---|---|---|---|
| `3512-kein-aeltester-mit-15` | 173159 | 35:12 / 35:05–35:24 | NEHMEN | „Ältesten“ |
| `2850-kein-aeltester-bestreiten` | 173159 | 28:50 / 28:45–29:03 | BESTREITEN | „bestreiten“ |
| `1423-kein-kampf-mit-16` | 173159 | 14:23 / 14:16–14:40 | ZUR_GRUPPE | „Zum Kampf“ |
| `2200-kein-druecken-mit-36` | 173159 | 22:00 / 21:55–22:19 | DRUECKEN | „Drück“ |
| `4113-kein-drache-von-baron` | 164326 | 41:13 / 41:10–41:26 | BESTREITEN | „Drache bestreiten“ |

## R2. Wo der Kampf entscheidet, spricht das ungeeichte Modell nicht

Entscheidung 2 der letzten Runde stellte ANNEHMEN, REIN und DREHEN stumm. Dieselbe ungeeichte Zahl `p_gewinn` steckt
aber auch in anderen Rufen:

- `BESTREITEN` („ihr seid vier“)
- `ZUR_GRUPPE` mit Kampf
- `TP_SPIEL`
- `DRUECKEN` und `MIT_GRUPPE` mit dem Grund „du schlägst X“

Die Kampf-Eichung zeigt, dass das Gold sogar verkehrt herum wirkt (AUC 0,30). „Du schlägst Teemo“ ist also eine
Behauptung ohne Beleg.

**Soll, bis die Kampf-Eichung besteht (Buch 7, 3.3):**

1. **BESTREITEN und TP_SPIEL:** berechnen, protokollieren, **stumm**.
2. **ZUR_GRUPPE zu einem Kampf:** nur gesprochen, wenn eure Zahl nach deiner Ankunft um ≥ 1 höher ist als ihre
   (Köpfe, keine Kraft) **und** dein Leben ≥ 60 % ist. Der Satz nennt den Ort: „Zu Graves in den Mid-Fluss: mit dir
   drei gegen zwei.“ „Zum Kampf, jetzt“ ohne Ort gibt es nicht mehr.
3. **DRUECKEN, MIT_GRUPPE und NEHMEN:** gesprochen nur, wenn das Ziel **vor dem ersten Verteidiger** fällt, also nach dem
   Fenster und nicht nach dem Kampf.
   - Der Grund ist dann das Fenster: „Teemo ist noch 52 Sekunden tot“.
   - Ein Ziel, das nur über „du schlägst X“ trägt, bleibt stumm.
   - Das Wort „schlägst“ fällt aus allen Satzbausteinen, bis die Eichung besteht.
4. **NEHMEN mit Kampf** (`P_kampf ≥ 0,1`): stumm.

**Szenarien:**

- `1737-kein-du-schlaegst` (164326, 17:30–19:30): darf_nicht_sagen „schlägst“.
- `2109-zur-gruppe-mit-ort` (173159, 21:09, und 164326 an jeder ZUR_GRUPPE-Stelle): „Zum Kampf, jetzt“ darf nicht
  vorkommen.

## R3. Der Kaufplan folgt Carlos' echtem Build

**Befund (API-Items):**

| Partie | Zeit | Carlos hat | Coach sagt |
|---|---|---|---|
| 164326 | 25–38 min | Axiombogen, Eklipse, Ionische Stiefel, Gefräßige Hydra, Schutzengel, dann Tanz des Todes und Seryldas | bis 38:09 „Kauf Caulfields Kriegshammer“; 38:33 bei vollem Inventar „Kauf Langschwert und Stiefel“ |
| 173159 | 12–24 min | Vampirisches Zepter, Gottlose Hydra, Endloser Hunger | zwölf Minuten lang „… Gold für Spitzhacke“ |

**Soll:**

1. **Das nächste Item:**
   - Zuerst das Item, dessen Bauteile Carlos schon hat. Aus Data Dragon `from`/`into` und seinen aktuellen Items.
   - Sonst das nächste Item aus **seinem eigenen** Riven-Build. Das ist die häufigste Reihenfolge fertiger Items in
     seinen Aufnahmen (`profil`). Beispiel aus diesen zwei Partien: Axiombogen → Hydra (Gefräßige oder Gottlose) →
     Eklipse oder Endloser Hunger → Schutzengel → Tanz des Todes / Seryldas.
   - Erst als letzter Rückfall der statische Plan.
2. **Volles Inventar** (6 Item-Plätze, ohne Schmuckstück):
   - Kein Kauf-Satz außer Kontroll-Auge oder Elixier.
   - Kein Back-Grund „Gold für …“.
3. **Genannte Items müssen kaufbar sein:**
   - Test: Das genannte Item passt zum aktuellen Inventar. Entweder ist ein Platz frei, oder es verbraucht eigene
     Bauteile.
   - Test: Das genannte Item ist nicht schon im Inventar.
   - Test: Das genannte Item baut in das Ziel-Item ein, oder es ist das Ziel-Item selbst.

**Szenarien:**

- `2626-kauf-passt-zum-build` (164326, 26:26, 38:09, 38:33): darf_nicht_sagen „Caulfields“, „Stiefel“.
- `1204-kein-spitzhacke-dauerton` (173159, 12:00–24:30): „Spitzhacke“ höchstens 2 Mal, solange sie nicht ins Ziel-Item
  gehört.

## R4. Back-Rufe: einmal sagen, dann Ruhe

**Befund:**

- 173159: 12 Back-Rufe zwischen 12:04 und 34:59, die meisten ignoriert.
- 164326: 11 zwischen 25:27 und 39:49.
- 164326, 8:53: „Back jetzt: 0 Prozent Leben.“ Da stirbt Riven gerade.

**Soll:**

1. **Nach einem ignorierten Back-Ruf** (kein Recall in 30 s) kommt ein neuer erst nach `back_ignoriert_s` (90 s).
   Ausnahmen: Das Leben fällt unter 30 %, oder das Gold erreicht eine neue Stufe (Ziel-Item komplett kaufbar).
2. **Höchstens 3 Back-Rufe je 10 Minuten.**
3. **Kein Back-Ruf** bei Leben < 10 % oder in KAMPF. Dort gilt RAUS.
4. **Der Grund muss für Back sprechen.** Ein toter Lane-Gegner („Cho'Gath ist tot“, 173159 28:11) ist ein Grund für
   Platten oder Drücken. Für Back taugt er nur zusammen mit Gold oder Leben.

**Szenarien:**

- `0853-kein-back-bei-0` (164326): darf_nicht_sagen „0 Prozent“.
- `back-dauerton` (173159, 12:00–35:00, und 164326, 25:00–40:00): höchstens 3 Back-Rufe je 10 Minuten, neuer
  Prüfschlüssel oder `text_max`.

## R5. Der Lane-Gegner allein ist keine Gefahr

**Befund:** 173159, Lane-Phase: sieben Mal „Raus zu deinem Top-Tier-1-Turm: Cho'Gath (und Olaf) kommt/kommen“. Um 7:45
sagt der Coach das bei 100 % Leben, nur weil Cho'Gath zur Welle läuft. Die Lane war nicht verloren, der Schutzplan
griff also nicht.

**Soll:**

- **Keine GEFAHR, wenn nur der Lane-Gegner kommt,** solange dein Leben ≥ 60 % ist und `kraefte()[0] ≥ −0,5`. Das gilt,
  bis Buch 2 die Matchups bringt.
- **Mit einem zweiten Gegner** (Jungler) bleibt die Gefahr, wie gehabt.
- **Dieselbe Gegnermenge** innerhalb von `gefahr_gleiche_s` (45 s) wird nicht erneut gewarnt. Ausnahme: `p_tod` steigt
  um ≥ 0,15. Beispiel 164326, 22:39 und 23:12: zweimal „Teemo und Naafiri kommen“.
- **Kein Gefahr-Satz, während Carlos schon zum sicheren Ort läuft.** Er nähert sich ihm in 2 s um ≥ 300.

**Szenarien:**

- `0745-cho-allein` (173159, 7:40–7:50): darf_nicht_sagen „Cho'Gath kommt“.
- `2239-keine-doppelwarnung` (164326, 22:30–23:20): höchstens 2 GEFAHR-Sätze.

## R6. WOHIN: kürzer, und der Rückfall muss Sinn ergeben

**Befund:**

- „Geh zur Top-Welle: dort nimmt sie sonst niemand.“ kommt in jeder Partie 8–12 Mal.
- 173159, 22:58: „warte am inneren Top-Turm auf dein Team: einer von ihnen sind oben“. Das ist falsches Deutsch, und
  der Wert ist p_tod 0,85.
- 173159, 36:06: „warte am Inhibitor-Top-Turm auf dein Team: vier von ihnen sind unten“. p_tod 0,90, und dein Team ist
  vermutlich genau dort unten.
- 164326, 7:48: „Zu den Larven: Spawn um 8 00, **du kommst zu spät**“.

**Soll:**

1. **Kurzform nach der ersten Nennung je Partie:** „Dann Top-Welle.“ bzw. „… dann Top.“
2. **Rückfall:**
   - Sind ≥ 2 Mitspieler zusammen, ist das Ziel **dein Team**: „Zu deinem Team nach unten.“
   - „Warte am Turm“ gilt nur, wenn dein Team tot ist oder verstreut.
   - Ein Rückfall-Ziel mit p_tod ≥ 0,3 wird nicht gesagt, dann bleibt es beim Kauf-Satz ohne Ziel.
3. **Einzahl und Mehrzahl:** „einer von ihnen ist“, „1 Vasall“.
4. **Turmnamen einheitlich:** „Top-Inhibitor-Turm“, nie „Inhibitor-Top-Turm“.
5. **Objective als WOHIN:** nie, wenn du zu spät kommst. Das heißt: `objective_zieht` mit deiner Ankunft aus dem
   Brunnen.

**Szenarien:**

- `wohin-kurz` (164326 und 173159): „nimmt sie sonst niemand“ höchstens 1 Mal je Partie.
- `0748-nicht-zu-spaet` (164326): darf_nicht_sagen „zu spät“.
- `3606-zum-team` (173159, 36:06): darf_nicht_sagen „warte am“.

## R7. Kleine Wellen sind keine Ansage

**Befund:**

- 173159, 32:32: „Hol die Bot-Welle: 1 Vasallen laufen in deinen Turm.“
- 173159, 33:56: „Klär die Top-Welle am Inhibitor-Turm: 1 Vasallen …“
- 164326, 33:02: „Hol deine Top-Welle: **0** Vasallen laufen in deinen Turm.“

**Soll:**

- `SEITENWELLE` und `WELLE_KLAEREN` nur ab `welle_min` (4) Vasallen, oder mit Kanone bzw. Supervasall.
- Die Zahl stimmt mit der Grammatik überein.
- Ein Satz mit 0 Vasallen ist ein Fehler. Seine Ursache kommt in messungen.md.

**Szenario:** `3302-keine-null-welle` (164326) und `3232-keine-kleine-welle` (173159).

## R8. Bestätigung „da war er“: Mehrzahl stimmt noch nicht

**Befund:** 164326 11:42, 173159 9:32 und 13:26. Das sind G4-Fälle, die noch falsch sind: Gewarnt wurde vor zwei oder
drei Gegnern, gesagt wird „da war er“.

**Soll:**

- Das Pronomen folgt der Zahl der genannten Gegner.
- Besser noch: ganz ohne Pronomen, „Gut raus.“

**Szenario:** `0932-mehrzahl` (173159), darf_nicht_sagen „da war er“.

## R9. Rückblick: Rolle, Pronomen, eigene Rufe

**Befund:**

- 173159, 35:24: „Kai'Sa kam aus dem Nebel, keiner hatte **ihn** gesehen. Ohne Sicht auf **ihren Jungler** …“ Kai'Sa ist
  ihre ADC, und das Pronomen ist falsch.
- 173159, 29:03: „allein hast du gegen sie keine Chance“. 13 s vorher hatte der Coach selbst „Ältester bestreiten“
  gesagt.

**Soll:**

1. Keine Pronomen für Champions, stattdessen der Name.
2. „Jungler“ nur, wenn der Täter der Jungler ist (Smite in der API oder Rolle aus der Startseite). Sonst heißt es
   „ohne Sicht auf Kai'Sa“.
3. Kam in den 20 s vor dem Tod ein Vorwärts-Ruf des Coaches, darf der Rückblick nicht gegen diesen Ruf lehren.
   - Die Lage wird dann nüchtern beschrieben: „Am Ältesten kamen drei von ihnen zusammen.“
   - Der Ruf wird in `_kern.jsonl` als „Ruf vor Tod“ markiert, damit ich ihn in der nächsten Prüfung sehe.

**Szenarien:** `3524-rueckblick-ohne-jungler` und `2903-rueckblick-nach-ruf` (173159).

## R10. Verbliebene Fassungswechsel

In 102112, 133930 und 164326 gibt es noch 2, 1 und 3 Fassungswechsel (Soll 0).

**Soll:** Jeden Fall in messungen.md mit Uhrzeit und Ursache nennen und beheben, oder begründen, warum der zweite Satz
richtig war.

---

## Ziel nach dieser Runde

1. **Alle Szenarien grün**, alte und neue.
2. **Ungefragte Ansagen ≤ 50 je 30 min** in 164326 und 173159. Heute sind es 67 und 74. R4 und R5 sollten den größten
   Teil davon wegnehmen.
3. **In keinem Protokoll:**
   - eine Vorwärts-Handlung mit Leben < 40 % oder mit p_tod ≥ 0,3,
   - „schlägst“,
   - ein Kauf-Satz mit einem Item, das nicht zum Inventar passt.

   Dafür bekommt `kennzahlen.py` die Spalte „Schranken-Verstöße“, Soll 0.
4. **Neue Protokolle** für alle sieben Partien, dazu messungen.md, Abschnitt „Qualitätsrunde 3“.
