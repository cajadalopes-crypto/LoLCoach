# Messungen zum Umbau (Buch 0)

Je Schritt: was umgesetzt ist, die Abnahme-Zahlen, Abweichungen vom Buch. Neueste oben.

---

## Qualitätsrunde 3 – Prüfung vom 27.09.2026 (c), R1–R10 (27.09.2026)

Auftrag 001 aus `buecher/auftraege/`. Grundlage: `buecher/protokolle/PRUEFUNG_2026-09-27c.md`, vorher committet in
8f0b8c3 zusammen mit dem Postfach. Offline gemessen, der Coach wurde nicht gestartet.

### Zuerst rot

26 neue Szenarien in `tests/szenarien/2026-09-27_173159_pruefung_c.toml` (15) und `..._164326_pruefung_c.toml` (11).
**Alle 26 waren mit dem Stand 842b502 rot.** Geprüft in einem eigenen Worktree auf dem Commit, damit nichts
Halbfertiges mitlief.

Neue Prüfschlüssel (Buch 0, 12.1 nachgetragen):
- `je_10min_max = { "muster" = n }`: höchstens n Treffer in jedem 10-Minuten-Abschnitt (R4).
- `kategorie_max = { "GEFAHR" = n }`: höchstens n Kern-Sätze einer Kategorie (R5). Dafür trägt jede Kern-Ansage ihre
  Kategorie.

### Umgesetzt

- **R1 Vorwärts-Schranke** (`Kern._schranken`, `[schranken]` in kern.toml):
  - Unter `vor_leben_min` (0,4) ist keine Vorwärts-Handlung Kandidat. Betroffen: DRUECKEN, MIT_GRUPPE, NEHMEN,
    BESTREITEN, ZUR_GRUPPE, TP_SPIEL, PLATTEN, SEITENWELLE, WELLE_KLAEREN, VORBEREITEN_OBJECTIVE, ANNEHMEN.
    Ausnahme: NEHMEN in der Grube, ohne Kampf, fällt in ≤ 5 s.
  - Mit p_tod ≥ `vor_p_tod_max` (0,3) ist keine davon Kandidat.
  - Fällt das Leben, bevor ein Satz dran ist, wird er verworfen (Prüfung vor dem Sprechen).
  - `_kern.jsonl` hat das Feld `schranke`: was in diesem Takt gestrichen wurde.
- **R2 Das ungeeichte Kampfmodell spricht nicht:**
  - BESTREITEN und TP_SPIEL werden berechnet, protokolliert und bleiben stumm.
  - ZUR_GRUPPE zu einem Kampf wird nur gesprochen mit ≥ 1 Kopf mehr nach deiner Ankunft und ≥ 60 % Leben, mit Ort und
    Namen: „Zu Graves in den Mid-Fluss: mit dir drei gegen zwei.“
  - DRUECKEN und MIT_GRUPPE werden nur gesprochen, wenn das Ziel vor dem ersten Verteidiger fällt. Sonst sind sie
    stumm (`modell_stumm`).
  - NEHMEN mit Kampf (P_kampf ≥ 0,1) ist stumm.
  - „schlägst“ kommt in keinem Satzbaustein mehr vor. Das Protokoll führt die stummen Rufe mit.
- **R3 Kaufplan** (`lolcoach/kaufplan.py`):
  - Das nächste Item ist zuerst das, dessen Bauteile du schon hast. Wer Tiamat hat, baut Hydra.
  - Sonst kommt der nächste Schritt aus Carlos' eigenem Build, `wissen/build_carlos.toml`. Er ist aus 11 Riven-Partien
    abgeleitet (`werkzeuge/build_aus_aufnahmen.py`): Axiombogen → Eklipse oder Endloser Hunger → Hydra → Schutzengel →
    Tanz des Todes → Gespaltener Himmel → Seryldas Bitterkeit. Das Lexikon ist nur noch der letzte Rückfall.
  - Volles Inventar ohne passendes Bauteil: kein Kauf (164326 38:33 „Kauf Langschwert und Stiefel“ bei sechs Items).
  - `kaufplan.kaufbar()` prüft jedes genannte Item: Platz frei oder eigene Bauteile verbraucht, nicht schon im
    Inventar, baut ins Ziel ein. Nur ein Hydra-Item (Spielregel, `GRUPPEN`). Tests in `tests/test_kaufplan.py`.
- **R4 Back-Rufe** (`Kern._back_sperre`):
  - Kein Back-Ruf unter 10 % Leben oder in KAMPF, höchstens 3 je 10 Minuten.
  - Nach einem Back-Ruf ohne Recall kommt ein neuer erst nach 90 s. Ausnahmen: Leben < 30 %, oder das Ziel-Item wird
    komplett kaufbar.
  - Das gilt auch für den „Jetzt back“-Schritt und die Erinnerung.
  - Ein toter oder gebackter Lane-Gegner ist allein kein Back-Grund mehr.
- **R5 Gefahr:**
  - Kommt nur der Lane-Gegner, gibt es keine GEFAHR, solange dein Leben ≥ 60 % und `kraefte()` ≥ −0,5 ist. Mit einem
    zweiten Gegner bleibt sie.
  - Dieselbe Gegnermenge wird 45 s nicht erneut gewarnt, außer p_tod steigt um ≥ 0,15.
  - Kein Gefahr-Satz, während du dem sicheren Ort in 2 s ≥ 300 Einheiten näher kommst.
- **R6 WOHIN:**
  - Nach der ersten Nennung je Partie kommt nur noch die Kurzform: „Dann Top-Welle.“, „Kauf X, dann Top-Welle.“
  - Rückfall: Sind ≥ 2 Mitspieler zusammen, ist das Ziel dein Team. „Warte am Turm“ gilt nur, wenn es nicht so ist.
    Ein Rückfall-Ziel mit p_tod ≥ 0,3 wird nicht gesagt; dann gibt es den Kauf-Satz ohne Ziel oder in TOT keinen Satz.
  - „einer von ihnen ist“; „Top-Inhibitor-Turm“ statt „Inhibitor-Top-Turm“.
  - Ein Objective ist nie WOHIN, wenn du zu spät kommst.
- **R7 kleine Wellen:**
  - SEITENWELLE und WELLE_KLAEREN erst ab 4 Vasallen, oder mit Supervasallen.
  - **Ursache der „0 Vasallen“** (164326 33:02): Die Seitenwelle wurde aus dem geglätteten Zustand gewählt, ihre Zahl
    war in diesem Takt 0. Die Schwelle nimmt sie jetzt heraus.
- **R8:** „Gut raus.“ ohne Pronomen.
- **R9 Rückblick:**
  - Keine Pronomen für Champions, „ihren Jungler“ nur, wenn der Täter ihr Jungler ist.
  - Kam in den 20 s vor dem Tod ein Vorwärts-Ruf des Coaches, beschreibt der Rückblick die Lage nüchtern: „Am Ältesten
    kamen drei von ihnen zusammen.“ `_kern.jsonl` markiert den Ruf als `ruf_vor_tod`.
- **Kennzahl „Schranken-Verstöße“** (`kennzahlen.py`, Soll 0): eine Vorwärts-Ansage mit Leben < 0,4 oder p_tod ≥ 0,3
  im Takt des Sprechens, „schlägst“, oder ein Kauf-Satz mit einem Item, das nicht passt (`kaufplan.kaufbar`).

### Abnahme

| Ziel der Prüfung c | Soll | Ist |
|---|---|---|
| 1. Alle Szenarien grün, alte und neue | grün | **86 / 86** in 12 Dateien (2 übersprungen, brauchen Claude); konstruierte Lagen **40 / 40**; Modus-Sollwerte 102112 **16 / 16**; `tests/alle.py` **9 / 9** (neu: `test_kaufplan`) |
| Neue Szenarien zuerst rot | rot mit dem alten Stand | **29 / 29**: 26 aus R1–R9 rot mit 842b502, 3 aus R10/Ziel 2 rot mit 8e91aab |
| 2. Ungefragte Ansagen je 30 min in 164326 und 173159 | ≤ 50 | 164326 **46** (vorher 67), 173159 **52** (vorher 74) – **in 173159 nicht erreicht**, s. u. |
| 3. Schranken-Verstöße in allen Protokollen | 0 | **0** in allen sechs |
| 4. Neue Protokolle für alle sieben Partien | ja | **ja**, `buecher/protokolle/2026-09-27_*.md` |
| Fassungswechsel (R10) | 0 | 102112 **2** (begründet, s. R10), sonst **0** |

**Kennzahlen** (Kern, `kennzahlen.py --nur-kern`):

| Aufnahme | ungefragt (je 30 min) | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | Kampf-Verstöße | Schranken-Verstöße | ohne Chance | GEFAHR / PLAN / ERINNERUNG / BESTÄTIGUNG | stumm (davon Kampf-Rufe) |
|---|---|---|---|---|---|---|---|---|---|
| 102112 | 52 (51) | 0,72 | 0 | 2 | 0 | 0 | 0 | 15 / 35 / 0 / 1 | 68 (37) |
| 133930 | 46 (63) | 1,19 | 0 | 0 | 0 | 0 | 0 | 19 / 20 / 1 / 1 | 26 (11) |
| 140253 | 20 (56) | 0,95 | 0 | 0 | 0 | 0 | 0 | 10 / 8 / 0 / 0 | 7 (7) |
| 144655 | 18 (56) | 0,96 | 0 | 0 | 0 | 0 | 0 | 11 / 4 / 1 / 0 | 7 (7) |
| 164326 | 65 (46) | 0,82 | 0 | 0 | 0 | 0 | 0 | 32 / 27 / 2 / 4 | 62 (23) |
| 173159 | 67 (52) | 0,68 | 0 | 0 | 0 | 0 | 0 | 34 / 26 / 1 / 4 | 59 (28) |

145702 hat nur 0,5 Minuten mit Daten und zählt nicht.

„Stumm“ ist alles, was berechnet und nicht gesagt wurde (R2), über alle sechs Partien:
- REIN 83, ANNEHMEN 16, DREHEN 14,
- DRUECKEN 61, MIT_GRUPPE 24, NEHMEN 21, BESTREITEN 7,
- ABGEBEN_TAUSCHEN 2, TP_SPIEL 1.

ABGEBEN_TAUSCHEN ist dabei, weil sein Tausch-Ziel ein Turm ist, der nur über den Kampf trägt (164326 23:12, 25:29).

**Ziel 2 in 173159 (52 statt ≤ 50):**
- R1–R9 nahmen 27 Sätze weg (94 → 67, je 30 min 74 → 52).
- Was bleibt, ist zur Hälfte GEFAHR: 29 Rückzüge und 5 „Raus, zum Turm!“ in 38 Minuten, fast jeder vor einer anderen
  Gegnermenge.
- Versucht und zurückgenommen, s. Abweichung 5: eine Sperre für die zweite Warnung in 15 s.
- Der nächste Hebel ist die Gefahr-Schwelle selbst. 13:00 „Raus …: Olaf kommt.“ kam bei p_tod 0,09. Das ist Eichung
  (`gefahr_eichung`) und eine Entscheidung, keine Satzregel.

### R10 – Fassungswechsel je Fall

In Prüfung c waren es 2 / 1 / 3 (102112 / 133930 / 164326). Jetzt: **2 / 0 / 0**. Die zwei in 102112 sind neu und
begründet.

| Fall | Ursache | Stand |
|---|---|---|
| 102112 33:20/33:44 und 37:03/37:13: „Back jetzt“ bzw. „Raus zu …“, dann „Jetzt back“ mit neuem Gold | Der Back begann nach dem Rückzug als neuer Plan. | **Weg durch R4:** 90 s nach einem Back-Ruf ohne Recall kein neuer. |
| 133930 10:25/10:37 und 164326 35:00/35:14: das Turm-Ziel wechselt ohne Ereignis | Beide Turm-Sätze trugen nur über „du schlägst X“. | **Weg durch R2.3:** Solche Ziele sind stumm. |
| 164326 38:09/38:33: KAUFEN mit anderer Liste | Der Kaufplan nannte Bauteile bei vollem Inventar. | **Weg durch R3.** |
| 164326 10:21/10:36: „Back jetzt: 23 Prozent …“, dann „Jetzt back: 26 Prozent …“ | Ein BACK_JETZT-Plan hält auch die Rückzug-Episode am Leben. Seine Erinnerung nahm deshalb die Fassung des Rückzug-Schritts. | **Behoben:** Die Erinnerung an einen Back-Plan behält „Back jetzt“ (`1036-back-fassung-bleibt`, rot mit 8e91aab). Dass sie kommt, ist richtig: Leben < 30 %, die Ausnahme von R4. |
| **neu** 102112 37:35 „Dann Baron.“ → 38:01 „Dann Deinem Team.“ → 38:15 „Dann Top-Welle.“ | Vor jedem Satz fielen Kills. 37:33 Kai'Sa: das Team geht zum Baron. 37:59 Galio: kein Baron mehr, zurück zum Team (p_tod 0,20). 38:01–38:03 Sett und Fiddlesticks: die Top-Welle (p_tod 0). | **Der zweite Satz war jeweils richtig** (9.4 Punkt 5: Kill ist ein neues Ereignis). Die Kennzahl erkennt als Ereignis nur einen neuen Namen im Satz. Die Kurzform nennt keine Namen mehr, deshalb zählt sie beide. **Behoben** ist der Grammatikfehler: jetzt „Dann zu deinem Team.“ (`3801-kurzform-zu-deinem-team`, rot mit 8e91aab). |

### Abweichungen und Entscheidungen

1. **Konstruierte Lagen nach R2 und R4:**
   - `m-split-drueck`: Der Turm trägt nur über „du schlägst Sett“, jetzt `darf_nicht DRUECKEN`.
   - `m-tp-spiel`: TP_SPIEL ist stumm, jetzt `darf_nicht`.
   - `k-gegner-gebackt`: Nach R4.4 ist ein gebackter Gegner ohne Gold oder Leben kein Back-Grund, jetzt
     FARMEN/PLATTEN statt WELLE_REIN_UND_BACK.
2. **1516 (133930) und 1025 (140253):** `muss_ziel` entfällt. R6.2: Ist auch der Rückfall ≥ 0,3, wird kein Ziel
   gesagt. Vorher kam „Warte am inneren …-Turm auf dein Team“.
3. **3451 (102112):** NEHMEN Drache wird berechnet, ist aber nach R2.4 stumm (Galio sichtbar, P_kampf ≥ 0,1).
   `soll`/`soll_ziel` zählen jetzt auch den stummen Ruf.
4. **Rückblick bei „Ruf vor Tod“:** Der Ort kommt aus dem Plan zum Zeitpunkt des Todes, sonst „Dort“. Satz 2 ist
   „Schau es dir im Review an.“
5. **Nachwarnungs-Sperre gemessen und zurückgenommen:**
   - Regel: In den 15 s nach einer Warnung kommt eine zweite nur, wenn p_tod um ≥ 0,15 steigt, auch mit neuem Namen.
     Anlass waren 13:00/13:12, 14:59/15:03 und 22:07/22:13 in 173159.
   - Ergebnis: 69 statt 68 ungefragte. Die gestrichenen Warnungen kamen 15–20 s später mit einem Namen mehr zurück.
   - 22:13 fehlte vor dem Tod („Cho'Gath … kommen“), und der Rückblick wurde schlechter: „Gank von Olaf …“ statt
     „Raus kam, du bist geblieben“.
   - Die drei Szenarien dazu sind wieder entfernt.
6. **Warteregel in der Basis:** Sie zählt jetzt auch ab dem letzten gesagten Ziel, nicht nur ab Kauf oder Eintritt.
   Vorher kam 173159 36:50 und 37:10 zweimal „Dann Top-Welle.“ (`3710-basis-einmal`).
7. **Fassungswechsel-Kennzahl und Kills:** Die Kennzahl erkennt ein neues Ereignis nur an einem neuen Namen im
   zweiten Satz. Seit R6 nennt die Kurzform keine Namen mehr. Die zwei Fälle in 102112 folgen je auf Kills (s. R10).
   Offen zur Entscheidung: Soll die Kennzahl Kills, Objectives und Lebensverlust als Ereignis zählen, wie die
   Kehrtwenden (`neues_ereignis`)?

---

## Schritt 5 – KAMPF und OBJECTIVE (Buch 7 und Buch 6) (27.09.2026)

Grundlage: `buecher/07_kampf.md` und `buecher/06_objectives.md` (committet in 705a6a6), Buch 0 Kapitel 0, 5, 6.3, 7
und 8, Buch 5 Kapitel 2, 5 und 8. Dazu Carlos' Entscheidungen 1–5 vom 27.09. (Chat). Offline gemessen, der Coach
wurde nicht gestartet. Der Kern spricht jetzt in allen neun Modi (`KERN_MODI_5`).

### Umgesetzt – Buch 7 (Kampf)

- **Ein Kampfmodell:** `kern/kampf.py: p_gewinn` (Kraft je Seite aus Level, Item-Gold und Leben, Ult/Flash weg,
  Mitspieler-Anteil, Turm).
  - `gefahr.p_verliere` ist jetzt `1 − p_gewinn` mit den Mengen-Gewichten aus G2.
  - `kampf_exponent` und `flucht_turm` fallen weg, `flucht_flash` sitzt jetzt auf p_tod.
  - Veraltete Gegner (G7): Level und Item-Gold werden nachgeschätzt (`gegner_werte`).
- **Modus KAMPF** (`modi/kampf.py`):
  - Kampf-Episode nach Tabelle 5.1 mit REIN, RAUS, DREHEN und HALTEN.
  - Höchstens 5 Wörter, höchstens 3 Rufe je Episode, ein Wechsel nur mit Kampf-Ereignis, keine alte Regel.
  - Nach dem Kampf wird der Plan sofort neu geprüft.
- **ANNEHMEN** vor dem Kampf (Kapitel 4). Solange das Urteil gilt, fällt ZURUECK wegen derselben Gegner weg.
- **Entscheidungspunkte** (`Proben`, 3.3) und der **Todesrückblick** nach Tabelle 8. „Raus kam“ steht nur, wenn der
  Rückzug wirklich gesprochen wurde; es zählt der letzte gesprochene Ruf vor dem Tod.
- **Entscheidung 2 (Carlos):** Solange `[kampf].geeicht = false`, sind ANNEHMEN, REIN und DREHEN stumm.
  - Sie werden berechnet und im Protokoll als „stumm: Modell nicht geeicht“ geführt (`Kern.stumm_modell`,
    `_kern.jsonl` Feld `stumm`), aber nicht gesprochen und nicht als Kandidat genommen.
  - Das ungeeichte Modell ändert also nichts an dem, was sonst gesagt wird. RAUS und der Rückblick sprechen.
  - Folge: 144655 6:10 und 140253 9:49 kommt jetzt der Rückzug-Satz statt „Rein auf …“. Der Rückblick sagt dann
    „Raus kam, du bist geblieben – … hat dich erreicht“ (Tabelle 8, Zeile 2).
- `werkzeuge/kampf_eichung.py`, `kennzahlen.py` mit der Spalte „Kampf-Verstöße“.
- `sperre._afk` ist in KAMPF stumm, wenn der Kern spricht.

### Umgesetzt – Buch 6 (Objectives)

- **Rechnung je Objective** (`kern/objective.py`): wer wann an der Grube ist, Tötungszeit mit Rache und Stufe, Kampf
  und Steal, `p_erfolg`, `anteil`, Werte und Folgewerte.
  - „Wirst du gebraucht?“ in der Lane-Phase (Kapitel 6, streng: Prio nur mit `GECRASHT_BEI_IHM` oder totem bzw.
    abwesendem Lane-Gegner, und euer Jungler geht hin).
  - `objective_zieht` wird einmal je Takt für alle Objectives gerechnet.
- **`objective_zieht` an allen Stellen**, die ein Objective als Ziel oder Grund nennen:
  - STAPELN, WELLE_HALTEN („nicht vor einem Objective“), VORBEREITEN_OBJECTIVE, OBJECTIVE_VORLAUF, der
    Objective-Teil von `nie_back` (sperrt jetzt auch „Welle rein, dann back“);
  - WOHIN aus Basis und Tod (`mindestens` fällt weg), `karte.objective_ruft`, WELLE_UND_RAUS;
  - die Back-Sperre in GRUPPE und UNTERWEGS.
  - Damit ist der Larven-Sog an allen Stellen zu (konstruierte Lage `k-kein-stapeln-ohne-jungler`, Szenarien 0647 und
    1025).
- **Handlungen** (`modi/objective.py`): VORBEREITEN_OBJECTIVE, NEHMEN (Alias ANLAUFEN), BESTREITEN (EV aus 4.4) und
  ABGEBEN_TAUSCHEN (der Tausch zuerst: „Äußerer Top-Turm jetzt: sie sind zu fünft am Drachen.“).
  - Das Urteil kommt einmal je Spawn. Ein zweites Mal nur, wenn es zwischen Nehmen und Abgeben kippt.
  - VORBEREITEN → NEHMEN wird nicht angesagt.
- **Modus OBJECTIVE neu** (5): in der Grube (≤ 30 s bis Spawn) oder mit Objective-Plan ≤ `objective_nah_s`. Er endet
  5 s nach dem Plan. „Mitspieler an der Grube“ löst nicht mehr aus.
  - Objective-Pläne gelten über UNTERWEGS, GRUPPE, SEITE und OBJECTIVE hinweg.
- **Alte Regeln:** `_grosse_objectives`, `_vorwarnung`, `_zahlen`, `_objective_start`, `_ward` und der
  Objective-Plan des Entscheiders sind in allen Modi stumm (Buch 0, Kapitel 14 nachgetragen).
- **Reihenfolge im Umwandel-Fenster** (8): Baron und Ältester 2,5, Drache 1,5. Ein erreichbares Objective
  verdrängt die niedriger eingereihten Türme.
- **Baron-Auslöser** fürs Umwandeln (4.6): euer BaronKill ≤ 180 s her, ≥ 3 mit Buff am Leben.
- **TP_SPIEL zu einem Objective** (4.7) nur, wenn dein TP das Urteil ändert. Flanke ohne Sicht gibt es nicht mehr
  („TP …, dann rein“).
- **Der Älteste** ist ein eigenes Objective (`aeltester`, n_min 3, Wert 3000). Swiftplay: nach zwei Elementardrachen
  oder ab 15:00.
- **Fakten** (Kapitel 12):
  - Ältester **6:00** nach dem 4. Drachen. Quellen: Wiki „Dragon pit“, Abschnitt Spawn, und riftpatchnotes Patch
    14.3: „First spawn timer is now properly 360 seconds“. Die 5:00 im Lexikon stammten aus 14.2.
  - Rache 15 % je Drache, höchstens 60 %; Larven 30 g je Larve; Herold-Auge 20 s; Baron 6:00 / Buff 180 s.
  - Eingetragen in `wissen/objektive.toml` und `saison2026.md`.
- **Entscheidung 1 (Carlos), Nachtrag in Buch 6, 3.3:**
  - „Ohne dich“ zählt nur, wer nachweislich hingeht (an der Grube oder in 10 s um ≥ 1000 genähert).
  - Wer ≤ 1500 bei dir steht und nicht zu einem *anderen* Objective geht, kommt mit dir. Er zählt mit dir, nicht
    ohne dich, und der Satz nennt ihn: „Drache mit Tryndamere: …“.
- **Prüfschlüssel** `soll_ziel`, `max_woerter`, `alte_regeln_max` (Buch 0, 12.1 nachgetragen). `_kern.jsonl`
  schreibt `p_erfolg`, `anteil`, `zieht` je Objective. `kennzahlen.py` hat die Spalte „Objective-Ansagen ohne Chance“.
- `werkzeuge/objective_eichung.py` (Kapitel 10).

### Eichung

**Kampf (Buch 7, 3.3)** – 6 echte Partien (133930, 140253, 144655, 145702, 164326, 173159), 112 Proben, **41
entschieden** (63 % offen):

| Art | Proben | entschieden | Brier | Grundrate |
|---|---|---|---|---|
| 2 (Duell) | 69 | 22 | 0,332 | 0,248 |
| 3–6 | 43 | 19 | 0,305 | 0,249 |
| gesamt | 112 | 41 | **0,320** | 0,249 |

- **Soll nicht erreicht** (Brier < 0,20 und besser als die Grundrate). Das Modell trennt gewonnene und verlorene
  Kämpfe nicht: Das mittlere p liegt bei gewonnenen bei 0,56, bei verlorenen bei 0,62.
- **Faktoren: alle Startwerte.**
  - k: 3.3 Punkt 5 wörtlich hätte k = 1 gesetzt (Brier 0,274 statt 0,320). Das ist aber nur eine Abflachung Richtung
    50 %: Kein Faktorsatz schlägt die Grundrate, und k = 1 kippte 0904, 0806 und 0701, die nach 11.4 grün bleiben
    müssen. `kampf_eichung.py` lässt deshalb die Startwerte stehen, solange kein Faktorsatz die Grundrate schlägt.
  - ult, turm und mitspieler: Gezählt werden nur Proben, in denen der Faktor wirkt – 21, 8 und 19, jeweils < 30.
- Nach Entscheidung 2 bleiben ANNEHMEN, REIN und DREHEN stumm (`geeicht = false`).

**Trennschärfe je Merkmal** (Entscheidung 2, damit das Modell danach gezielt verbessert werden kann; 41 entschiedene
Proben: 22 gewonnen, 19 verloren). Gemessen am Entscheidungspunkt der Probe:
- Level und Gold: Mittel eurer Beteiligten minus Mittel der nahen Gegner. Gegnerwerte mit `kampf.gegner_werte`,
  also der Schätzung des Modells (G7).
- Kopfzahl: `len(wir) − len(gegner)`. Turm: +1 euer, −1 ihrer, 0 keiner.
- AUC: Wahrscheinlichkeit, dass eine zufällige gewonnene Probe den höheren Wert hat als eine zufällige verlorene.
  Gleichstand zählt halb; 0,5 trennt nicht, unter 0,5 trennt verkehrt. Rauschen bei 22/19 Fällen etwa ±0,18 (95 %).

| Merkmal | gewonnen (Mittel) | verloren (Mittel) | AUC | n |
|---|---|---|---|---|
| p (Modell) | 0,56 | 0,62 | 0,40 | 41 |
| Leben | 0,95 | 0,87 | 0,58 | 41 |
| Level-Unterschied | +0,90 | +1,28 | 0,43 | 41 |
| Gold-Unterschied (Item-Gold) | +431 | +1438 | **0,30** | 41 |
| Kopfzahl-Unterschied | +0,77 | +0,63 | 0,51 | 41 |
| Turmnähe | 0,09 | 0,32 | 0,39 | 41 |

- Nur das Leben zeigt in die richtige Richtung, und schwach (0,58, im Rauschen). Level und Kopfzahl trennen nicht.
- Das Gold trennt verkehrt herum (0,30, knapp außerhalb des Rauschens): Verlorene Kämpfe begannen mit dem größeren
  Goldvorsprung. Weil Level und Gold die Kraft im Modell tragen, liegt p selbst verkehrt (0,40).
- Turmnähe: Von den 8 Proben an eurem Turm gingen 6 verloren. Ihr Turm kommt in den entschiedenen Proben nicht vor.
- Nicht geprüfte Deutung: Mit Vorsprung werdet ihr mutiger, und der Ausgang (Kill-Gold in 15 s) misst dann eher das
  Nachsetzen als die Stärke am Einstieg.
- Daten: `kampf_eichung.py --json` (jetzt `{"proben", "trennschaerfe"}`). Die Proben tragen `level_diff`, `gold_diff`
  und `kopf_diff`.
- Die bis zu drei Proben je echter Partie mit dem größten Fehler liegen als Stubs in
  `tests/szenarien/offen/<stamm>_kampf.toml` (Buch 7, 10). Das Soll setzt Carlos.

**Objectives (Buch 6, Kapitel 10)** – dieselben 6 Partien:
- **Urteil gegen Ausgang:** 15 Versuche, Brier 0,276, Grundrate 0,20 → 0,160. Soll nicht erreicht, zu wenige
  Versuche (< 30), also **Startwerte**.
- **Tötungszeiten:** keine Gruppe hat ≥ 3 Fälle, die Tabelle bleibt. Die Einzelwerte streuen stark, von 3 s bis
  123 s: Der Beginn „≥ 1 von euch ≤ 700 an der Grube“ erkennt auch Vorbeilaufen. Die Messung braucht mehr Partien und
  einen strengeren Beginn.

### Wellen-Eichung (Entscheidung 2 der Prüfung b, Entscheidung 3 von heute)

- Beschriftet von Hand aus den behaltenen Minimap-Bildern: je 480 px Gitter, alle Zeitpunkte der Lane-Phase, auf
  denen du auf der Lane stehst. Eindeutig ist ein Punkt nur, wo die Vasallen nicht unter den Champion-Icons liegen.
  Die erste Welle vor dem Treffen zählt nicht.
- Ergebnis:
  - **164326: 13 von 15 eindeutigen richtig (87 %) – erreicht.**
  - **173159: 7 von 12 (58 %) – nicht erreicht.**
- Die meisten eindeutigen Punkte sind „unsere Welle läuft zu ihm, keine roten zu sehen“. Kämpfe an der Welle verdecken
  die Vasallen fast immer (164326: 22 von 37 unklar, 173159: 20 von 32).
- Nach Entscheidung 3 wird nichts umgebaut, die strenge Prio-Regel aus Buch 6, Kapitel 6 bleibt.

**Fehlerursachen je Zeitpunkt** (Entscheidung 3; wie bei 144655 unter F1)

Nachgerechnet mit `wellen_eichung.durchrechnen` und dem WellenPuffer Bild für Bild: roh = `_roh`, Zustand = nach der
Hysterese. Riven spielt CHAOS Top, s aus ihrer Sicht: ihr Turm 0,375, Knick 0,50, Crash-Zone 0,355–0,455.

*173159* (7 von 12):

- **7:33:** Kern GECRASHT_BEI_DIR, wahr ZU_DIR (0:1, Front 0,47, Trend +0,127).
  - Ursache Icon-Deckung (`stand`): Riven steht bei 0,438 am Rand der Zone. Dadurch reicht die Zone bis 0,49, und
    ein roter bei 0,47 genügt. `crash_dir_sofort` schaltet ohne Hysterese.
  - Die übrigen roten liegen unter ihrem Icon und einem „?“-Ping.
- **9:25:** Kern ZU_IHM, wahr GECRASHT_BEI_DIR (6:2, Front 0,37, Trend +0,059).
  - Ursache `Wellenleser.punkte`: Fünf rote kleben vor dem Turm übereinander, gelesen werden 2. Die angeschnittenen
    Stücke liegen unter 22·f, ohne weiße Linie, und fallen heraus. Im Median stehen damit 2 in der Zone, weniger als
    `crash_mindestens` (3).
  - Dann nimmt `_front` unsere frische Welle hinter dem Turm in dieselbe gemischte Gruppe: 6:2, die Zählregel sagt
    ZU_IHM.
- **11:07:** Kern ZU_IHM, wahr ZU_DIR (0:3, Front 0,50, naechste 0,05).
  - Die Trendregel hält ZU_IHM bis 11:04 trotz 0:2. Die Front glitt ohne Sprung (keiner > `front_sprung` 0,12) von
    unserer Welle (0,35 → 0,49) auf die roten (0,51–0,54), und die Regression trug unseren Vormarsch weiter
    (+0,15). In `_roh` steht der Trend vor der Zählung.
  - Ab 11:05 ist roh ZU_DIR, die Hysterese (3 s) schaltet erst 11:08.
- **11:57:** Kern MITTE, wahr ZU_IHM (4:0, Front 0,45).
  - Hysterese: roh ZU_IHM seit 11:55, umgeschaltet 11:58.
  - Davor lagen 11:39–11:50 zwei Kartensymbole unbewegt am Knick: ein roter Totenkopf und ein blaues Zeichen. Sie
    wurden als gemischte Front 1:1 (MITTE) gelesen, unsere Welle lief dahinter als `naechste`.
  - Nach dem Frontsprung gab es keinen Trend, und der 6-s-Median stand noch auf 1:1.
- **12:49:** Kern MITTE, wahr ZU_IHM (4:1, Front 0,37, Trend −0,135).
  - Hysterese: roh ZU_IHM seit 12:47.
  - Davor: Kampf am Knick. Unsere Vasallen dort sind halb verdeckt (unter 22·f) und fallen heraus. Die roten bilden
    die Front gegen unsere frische Welle bei 0,09–0,22: 4:4, Front als Mitte zwischen beiden, also MITTE.

*164326* (13 von 15):

- **3:59:** Kern MITTE, wahr ZU_IHM (6:0, Front 0,55, naechste 0,46).
  - Hysterese: roh ZU_IHM seit 3:58.
  - Davor hielt ein stehender Kampf am Knick die Front 3:28–3:56 bei 0,55, Trend ≈ 0. Die roten lagen vermutlich
    unter Teemos Icon.
  - Unsere neue Welle lief mit einer Lücke > 0,06 dahinter und zählte nur als `naechste`. Ab 3:51 ist „ihre“ None
    (Nebelregel, Front > `nebel_ab`).
- **5:01:** Kern GECRASHT_BEI_DIR, wahr ZU_DIR (0:1, Front 0,48).
  - Wie 7:33: Rivens Icon bei 0,44–0,45 zieht die Zone bis 0,50, ein roter am Knick genügt, sofort.

*Muster:*
- **Vier von sieben Fehlern sind Umschaltverzug** (11:07, 11:57, 12:49, 3:59): roh war 1–2 s vorher schon richtig,
  die Hysterese (3 s) hielt den alten Zustand.
  - Bei den MITTE-Fehlern hielt das 6-s-Fenster eine falsche, verdeckte oder stehende Front fest, während nur unsere
    neue Welle lief.
- **Verdeckung macht die Crash-Regel in beide Richtungen unscharf:**
  - Das eigene Icon am Zonenrand macht aus einem roten einen Crash (7:33, 5:01).
  - Übereinanderliegende Vasallen zählen nicht mit (9:25, 12:4x).
  - Kartensymbole zählen als Vasallen (11:39–11:50).
- **Der Trend überlebt den Wellenwechsel,** wenn die Front ohne Sprung von unserer auf ihre Welle gleitet (11:07).
- Mögliche Ansatzpunkte, nach Entscheidung 3 **nicht umgesetzt**:
  - Icon-Deckung nicht über den Knick hinaus.
  - Trend neu beginnen, wenn die Farbe der Front wechselt.
  - Kürzere Hysterese zwischen ZU_* und MITTE.
  - Stücke an anderen Vasallen zählen, nicht nur an weißen Linien.

### Abnahme Schritt 5

| Abnahme | Soll | Ist |
|---|---|---|
| `tests/alle.py` | grün | **8 / 8** |
| Szenarien (alle Dateien, `--kern neu`) | grün | **57 / 57** (2 übersprungen, brauchen Claude); konstruierte Lagen **40 / 40**; Modus-Sollwerte 102112 **16 / 16** |
| Buch 7, 11.1: Szenarien aus Kapitel 10 | grün über den Kern | **grün**: 0915, 0622, 2501, 2613, 2631, 0338 (erweitert), 0843/1005 (erweitert) |
| Buch 7, 11.2: `kampf_eichung.py` | gelaufen | **ja** – Brier und Faktoren oben, Soll nicht erreicht |
| Buch 7, 11.3: Kampf-Verstöße in allen Protokollen | 0 | **0** in 102112, 133930, 140253, 144655, 164326, 173159 |
| Buch 7, 11.4: 0517, 0850, 0904, 3535, konstruierte Lagen | grün | **grün**; Kehrtwenden **0** in allen sechs |
| Buch 6, 14.1: Szenarien aus Kapitel 13 | grün über den Kern | **grün**: 2522, 2847, 3500, 3451, 3831, 1453, 2516, 3335, 2637, 0647 (beide), 0729, 0427, 1025 |
| Buch 6, 14.2: `objective_eichung.py` | gelaufen | **ja** – Startwerte, zu wenige Versuche |
| Buch 6, 14.3: alte Regel mit Objective-Satz in 102112, 133930, 140253, 144655 | 0 | **0** – in allen sieben Protokollen sprechen alte Regeln nur noch den Todesrückblick (14) und AFK (1) |
| Buch 6, 14.4: Objective-Ansagen ohne Chance | 0 | **0** in allen sechs |
| Fassungswechsel (Prüfung D) | 0 | **nicht erreicht**: 102112 2, 133930 1, 164326 3, sonst 0 (s. u.) |
| Ungefragte Ansagen je 30 min (Prüfung b, Entscheidung 4) | ≤ 45 | **nicht erreicht**: 59–80 (s. u.) |

**Kennzahlen** (Kern, `kennzahlen.py --nur-kern`):

| Aufnahme | ungefragt (je 30 min) | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | Kampf-Verstöße | ohne Chance | GEFAHR / PLAN / ERINNERUNG / BESTÄTIGUNG | stumme Kampf-Rufe |
|---|---|---|---|---|---|---|---|---|
| 102112 | 61 (60) | 0,79 | 0 | 2 | 0 | 0 | 16 / 42 / 1 / 1 | 37 |
| 133930 | 58 (80) | 1,24 | 0 | 1 | 0 | 0 | 21 / 30 / 2 / 0 | 11 |
| 140253 | 25 (70) | 1,18 | 0 | 0 | 0 | 0 | 13 / 9 / 0 / 1 | 7 |
| 144655 | 19 (59) | 1,01 | 0 | 0 | 0 | 0 | 12 / 6 / 0 / 0 | 7 |
| 164326 | 96 (67) | 1,00 | 0 | 3 | 0 | 0 | 40 / 50 / 2 / 2 | 23 |
| 173159 | 94 (74) | 0,86 | 0 | 0 | 0 | 0 | 43 / 44 / 0 / 5 | 28 |

145702 hat nur 0,5 Minuten mit Daten und zählt nicht.

- **Ziel ≤ 45 je 30 min nicht erreicht.** Die alten Regeln sind jetzt bis auf Rückblick und AFK still. Was bleibt,
  sagt der Kern selbst: 40–50 % davon sind GEFAHR, vor allem der Rückzug „Raus zu deinem …-Turm: X und Y kommen“.
  Der nächste Hebel ist die Gefahr-Rechnung selbst: seltener anschlagen und zusammenfassen.
- **Fassungswechsel:**
  - Zweimal folgt auf „Back jetzt: …“ bzw. „Raus zu …“ innerhalb von 10–25 s „Jetzt back: …“ mit neuem Gold
    (102112 33:20/33:44 und 37:03/37:13; 164326 10:21/10:36). Seit ein Rückzug-Plan ohne Gefahr endet (Abweichung
    15), beginnt der Back danach als neuer Plan statt als Schritt des alten.
  - Zweimal wechselt das Turm-Ziel ohne Ereignis in 12–14 s (133930 10:25/10:37, 164326 35:00/35:14).
  - Einmal KAUFEN mit anderer Liste (164326 38:09/38:33).

### Abweichungen vom Buch und Entscheidungen

**Buch 7**
1. **Turm im Kampfurteil:** Der Turm zählt auch, wenn du ≤ 5 s vom eigenen Turm entfernt bist oder dorthin gehst,
   nicht nur ≤ 775 (3.1). Grund: der schützende Freeze (`k-freeze-schuetzend`) wurde sonst rot.
2. **k bleibt 2** trotz 3.3 Punkt 5 (s. Eichung). Die Regel „erst ändern, wenn der Faktor in ≥ 30 entschiedenen
   Proben wirkt“ gilt je Faktor.
3. **Tote Gegner** zählen im Kampfurteil mit ihrem Gewicht aus `p_da_am` (Respawn + Weg). Vorher fehlten sie ganz:
   102112 34:51 zählte am Inhibitor-Turm niemanden von denen, die 11–19 s später daneben aufstanden.
4. **Rückblick:** „Raus kam“ nur nach einem gesprochenen Rückzug; es zählt der letzte gesprochene Ruf (140253 10:16).
5. **ANNEHMEN hält,** solange sein Gegner in `annehmen_abstand` bleibt, auch wenn er nicht weiter näher kommt.
   Das gilt auch für das stumme Urteil (102112 26:29).
6. **Szenarien:**
   - 2501: REIN ist erlaubt, der Kampf lief schon.
   - 2613: zeit 26:28, erst dort ist Fiddlesticks ≤ 2500.
   - 2847: REIN ist erlaubt (Kampf 28:43–28:48).
   - 0622 und 1005: nach Entscheidung 2 Zeile 2 von Tabelle 8.
   - Beim Nachspielen gilt in KAMPF als „Plan“ die Entscheidung der Tabelle 5.1.

**Buch 6**
7. **Wer zählt an der Grube** (3.1/3.3, vor Entscheidung 1):
   - Mitspieler zählen nur, wenn sie hingehen, nicht jeder, der es in der Zeit könnte. Tote Mitspieler zählen nicht.
   - Beleg: 102112 25:24 „Baron jetzt: ihr seid fünf“, zwei davon in der Basis. Buch 6, 8 sagt selbst: „Baron fällt
     heraus, weil zwei eurer Leute in der Basis stehen“.
   - Entscheidung 1 hat das präzisiert (Nachtrag 3.3).
8. **Kampf an der Grube:**
   - NEHMEN: Eure Leute zählen bis zum Ende der Tötungszeit, nicht nur `kampf_fenster_s`.
   - BESTREITEN: Gekämpft wird bei deiner Ankunft (Weg + `kampf_fenster_s`), und nur, wenn mindestens einer von
     ihnen an der Grube steht. Sonst war BESTREITEN der Dauerplan: 102112 24:36–38:36 kam „Baron bestreiten“ mit
     EV ≈ 4000, ohne dass einer von ihnen am Baron war. Die EV aus 4.4 rechnet gegen „sie bekommen es sicher“.
9. **VORBEREITEN:** Passt der Welle-Schritt nicht mehr ins Fenster, geht es ohne ihn. NEHMEN gilt auch von der Lane
   aus. Sonst fiel die Lage zwischen beiden durch (`k-kein-back-kurz-vor-larven`).
10. **TP ändert das Urteil (4.7):**
    - Es gilt um ≥ 0,15 **oder** das Urteil kippt über 0,5.
    - Mit k = 2 und `mitspieler_anteil` 0,8 hebt ein Spieler p bei 4 gegen 4 nur um 0,147. Das Buch-5-Beispiel
      („TP macht es 5 gegen 4“) wäre sonst nie möglich.
    - `m-tp-spiel` ist jetzt 4 gegen 4. Das alte 4 gegen 5 steht als `m-tp-kampf-bleibt-verloren` (dort
      ABGEBEN_TAUSCHEN).
11. **Turm-Prüfung der Karten-Rechnung:**
    - Kommen zwei oder mehr Verteidiger wahrscheinlich (p_da ≥ 0,5), entscheidet `p_gewinn` am Turm mit dir und
      deinen Mitspielern in 1500 (Buch 5). Die Schwelle ist `split_kraft_min` in p umgerechnet (0,59).
    - Kommt nur einer, gilt Buch 5 wie bisher.
    - Beleg: 102112 34:51 „Mid-Inhibitor-Turm“, während drei daneben respawnten; 25:25 „Top-Inhibitor-Turm: du
      schlägst die drei“, 39 s über die Karte.
12. **Tote in ihrer Basis:** Liegt ihr Brunnen ≤ 5000 vom Ziel, sind sie da, sobald Respawn und Weg ≤ T sind – ohne
    Seiten-Faktor und Anlauf-Rampe.
13. **Reihenfolge (8) wörtlich:** Ein erreichbares NEHMEN oder BESTREITEN streicht im Umwandel-Fenster die niedriger
    eingereihten Türme. Die 200 GE je Rang reichten nicht.
14. **Urteil hält (1.6), Entscheidung 4:**
    - `zieht` kippt sofort mit einem Ereignis (Tod, Spawn, Sichtung eines Unbekannten, Struktur fällt).
    - Ohne Ereignis kippt es erst, wenn der neue Wert 3 s besteht (`URTEIL_STABIL_S`).
    - Streng gehalten blieb in 102112 nach dem Drachen 35:16 ein falsches „zieht nicht“ minutenlang stehen, weil ein
      Drachen-Kill kein Ereignis der Liste ist.
    - Ein gemerktes Ziel aus TOT oder BASIS fällt weg, wenn sein Objective nicht mehr zieht (3002).
15. **Rückzug ohne Gefahr:** Ein Plan „nur bei Gefahr“ (ZURUECK) ist ohne Gefahr kein Kandidat mehr. Die G3-Lücke
    (2 s) hält ihn noch kurz. Vorher blieb er Kandidat, solange er Plan war: 102112 24:58 bis 25:22, dann schlug er
    mit seinem Back-Wert den freien Drachen.
16. **Swiftplay in 140253:** 0729 (Larven) und 0427 (Drache) haben ihr Soll aus den Swiftplay-Fakten, nicht aus
    Kapitel 6: Larven gibt es nicht, der erste Drache hat keinen Timer. Das Buch verlangte, das Soll *vor* der
    Umsetzung festzulegen; es wurde erst danach angelegt.
17. **Konstruierte Lagen:**
    - Bekommen, was Buch 6 verlangt (Prio und Jungler): `k-stapeln-vor-larven`, `k-kein-freeze-vor-objective`,
      `k-kein-back-kurz-vor-larven`.
    - `m-welle-und-raus` bekommt euer Team unten.
    - Neu sind `k-kein-stapeln-ohne-jungler` und `m-tp-kampf-bleibt-verloren`.
18. **Modus-Sollwerte neu gerechnet** (13): 15:31 (+SEITE/UNTERWEGS), 25:22 (+SEITE), 29:14 (+UNTERWEGS).
    `2522` bekommt SEITE, `1315` UNTERWEGS. Grund jeweils: kein Objective-Plan, nicht in der Grube.
19. **0159:** `plan_p_tod_max` ist jetzt `wohin_p_tod_max` (0,3). Mit dem Kampfmodell sind es 0,22 statt < 0,2; der
    Plan ist derselbe. Der Fehler E2 lag bei 0,64.
20. **Prüfung vor dem Sprechen:**
    - Ein Plan-Satz fällt weg, wenn beim Sprechen KAMPF gilt (Buch 7, 11.3). Ein Objective-Satz (außer BESTREITEN
      und ABGEBEN_TAUSCHEN) fällt weg, wenn das Objective dann nicht mehr zieht (Buch 6, 14.4). Beleg: 133930 10:49
      „Drache mit Fizz“ kam erst, als der Drache nicht mehr zog.
    - Kennzahlen: Die Kampf-Verstöße zählen nach dem Modus im Takt des Sprechens, wie das Protokoll. Vorher zählten
      sie alles zwischen den Episodengrenzen, auch 144655 6:10, gesprochen in LANE.
    - Der Todesrückblick zählt nicht als alte Regel in KAMPF, er wird in TOT gesprochen.
    - „ohne Chance“ zählt die Liste aus 14.4 – ohne BESTREITEN, das hatte ich zuerst dazugenommen.
21. **Nicht umgesetzt:**
    - Lane-Form von ABGEBEN_TAUSCHEN („Gangplank ist zu den Larven: Platten jetzt“).
    - Herold-Ritt (Kapitel 7, `wert_ritt` mit Turm-Leben); heute grob zwei Platten × 0,8.
    - Folgewert Larven 3:0.
    - Bestätigungen aus Kapitel 9 („Sauber: Drache ohne Kampf“).
    - Alle stehen in `OFFEN.md`.

---

## Qualitätsrunde 2 – Prüfung vom 27.09.2026 (b), Entscheidungen 1–3 und G1–G6 (27.09.2026)

Auftrag: `buecher/protokolle/PRUEFUNG_2026-09-27b.md`. Umgesetzt in 39a858b (Bücher 6 und 7 vorher committet:
705a6a6). Offline gemessen, der Coach wurde nicht gestartet.

### Entscheidungen 1–3

- **1. `0843`:** Die Daten haben recht. Das Szenario nennt jetzt Yasuo und darf „Brand“ nicht sagen.
- **2. F1-Zusätze** (Pfadlinie, Icon-Deckung, `crash_dir_sofort`) bleiben an. Die Bestätigung an 164326 und 173159
  steht unten unter „Schritt 5 → Wellen-Eichung“.
- **3. F2 Flash, Weg 1:** `wissen/dashes.toml` (Stand Data Dragon 16.19.1, von Hand geprüft). 112 Champions mit eigenem
  Dash, dazu die Blinks aus `blinks.toml`. Entfernt wurden Cho'Gath und Udyr, ergänzt Elise und Ryze.
  - Minimap und Bildschirm werten für diese Champions keine Sprünge mehr als Flash (`zauber.dash_champions`).
  - Test: Ein Brand-Sprung ergibt einen Timer, ein Vi-Sprung nicht.
  - Weg 3 (Carlos pingt über die Anzeigetafel) lief schon. Weg 2 steht in `OFFEN.md`, nach Schritt 6.

### G1–G6: zuerst rot, dann behoben

Vor den Fixes: **16 von 28 geprüften rot** (die neuen G-Szenarien und die Spielmodus-Prüfung; Stand 705a6a6).
Nach 39a858b: 42 von 43. Rot blieb `0904-drei-kommen`: Es war vorher nur durch die Doppelzählung der Gefahr grün und wurde
mit dem Kampfmodell aus Schritt 5 wieder grün.

- **G1 Schutzplan (144655, 140253):**
  - Eine verlorene Lane ist jetzt **eine Episode**. Der lange Satz (≤ 18 Wörter) kommt einmal. Nach Tod oder Basis
    kommt höchstens alle 180 s die kurze Fassung: „Weiter: am Turm farmen, kein Trade.“
  - **Ursache des Item-Sprungs:** Das Bauteil war `kaufplan.kaufen[0]` (das teuerste, das du dir leisten kannst) oder
    `naechstes` (das billigste, das du dir nicht leisten kannst). Welches, hing vom Gold im jeweiligen Takt ab. Jetzt
    steht das Bauteil fest, bis es gekauft ist.
  - Die Lane-Kraft wird ohne Leben gerechnet (`lane_kraft`), damit die Episode nicht mit dem Leben flackert.
  - Übergeben heißt nicht gesprochen: Verfällt der Satz, wird er wieder angeboten.
- **G2 WOHIN:**
  - Die Gefahr wird über die **Mengen** der Ankommenden gerechnet statt doppelt gezählt (`_ueber_mengen`). Im eigenen
    Brunnen gilt volles Leben.
  - Unter `wohin_p_tod_max` (0,3) wird das Ziel genannt. Unter `wohin_direkt_max` (0,15) auch eilig, sonst „Zurück
    nach X, bleib am Turm“.
  - Rückfall: Team (≥ 2), sonst ein eigener Turm weiter hinten, sonst „Warte am inneren X-Turm auf dein Team“.
  - Plausibilität (p_tod heute → nach dem Fix; in Klammern mit vollem Leben):

    | Lage | vorher | nachher | Beiträge |
    |---|---|---|---|
    | 144655 5:07 | 0,65 | 0,42 (0,36) | Gangplank 0,42, Kha'Zix 0,37, Vex 0,05 |
    | 140253 10:25 | 0,73 | 0,37 | Yasuo 0,33, Tahm Kench 0,28, Jinx 0,24, Heimerdinger 0,19 |
    | 133930 12:30 | 0,79 | 0,37 | Gwen 0,42, Zoe 0,31, Xin Zhao 0,28, Zac 0,25 |
    | 133930 15:16 | 0,67 | 0,33 | Zac 0,33, Zoe 0,33, Gwen 0,26 |

  - Nebenbei behoben: Der Merker gab dasselbe Handlungsobjekt zurück, TOT schrieb jedes Mal „Noch N Sekunden:“ davor.
    Jetzt legt er Kopien ab.
- **G3 Plan hält (140253 3:49–4:27):**
  - **Ursache:** Der Kandidat des Plans (WELLE_REIN_UND_BACK) fiel einen Takt heraus. STAPELN (242 GE schlechter)
    wurde Pflicht-Plan, und `halten_s` (8 s) sperrte die Rückkehr. Der Test sah das nicht, weil STAPELN im
    Wechsel-Takt tatsächlich der beste Kandidat war.
  - Jetzt hält der Plan eine Lücke < `luecke_s` (2 s), wenn Modus und Gefahr gleich bleiben. Dabei gibt es keinen
    Schritt-Satz. Nach einem erzwungenen Wechsel sperrt `halten_s` nicht. Eine Erinnerung kommt nur, wenn der
    Kandidat des Plans in diesem Takt da ist.
- **G4 „Gut raus“:**
  - Beurteilt wird es 10 s nach dem Rückzug-Satz: das Leben fiel um weniger als 20 Punkte, du stehst am sicheren Ort,
    und der Gegner wurde an der alten Stelle gesehen.
  - Nie in KAMPF, geprüft beim Sprechen. „er“ und „sie“ richten sich nach der Zahl.
- **G5 Rückblick:** Satz 2 richtet sich nach dem Leben beim Einstieg. Ab 0,6 (`RUECKBLICK_VOLL`) heißt er „hinter den
  Turm oder zu deinem Team“, sonst „zurück“.
- **G6 Swiftplay (133930, 140253):**
  - Das Profil steht in `wissen/mechanik.toml [swiftplay]`. Quellen: Riot Support (28.01.2026), /dev (01.12.2025),
    Wiki Swiftplay samt Patch-History V25.S1.3, V26.01, V26.02, V26.07 und Hotfix.
  - Keine Larven, kein Herold. Der erste Drache hat keinen belegten Timer, Respawn 300 s, höchstens zwei
    Elementardrachen. Der Älteste kommt ab 15:00, dann alle 6:00. Baron kommt um 12:00.
  - Die Lane-Phase dauert bis 10:00, Wellen alle 25 s ab 11:35, Kanonen ab der dritten Welle.
  - Szenario-Dateien tragen `spielmodus`. Stimmt er nicht mit der Aufnahme überein, ist die Datei rot. Das Protokoll
    und die Wellen-Eichung nennen den Modus.
  - Betroffene Szenarien:
    - 140253: `0843` (Fenster 8:34–8:55), `1025` (Lage korrigiert: keine Larven), `0000`
      (1400 Startgold).
    - 133930 und 140253: `swiftplay-keine-classic-zeiten`, `swiftplay-keine-larven`.

### Nebenbefund: Gegner-Items sind so veraltet wie ihre Level

Item-Wechsel der Gegner in der API tauchen fast nur auf, während der Gegner sichtbar ist:

| Aufnahme | Item-Wechsel (davon ungesehen) | Level-Wechsel (davon ungesehen) |
|---|---|---|
| 144655 | 18 (2) | 31 (3) |
| 164326 | 63 (11) | 82 (5) |
| 173159 | 70 (18) | 83 (15) |

Die Schätzung aus Buch 7, 3.2 (G7: Level und Item-Gold lange ungesehener Gegner) gilt deshalb für beides
(`kampf.gegner_werte`).

### Abweichungen und Entscheidungen

- `nie_back`: Ein Gegner, der vor ≤ 3 s zu sehen war (`NIE_BACK_EBEN_S`), zählt wie sichtbar. Beleg: 140253 8:04,
  „Back jetzt“ mit Yasuo 935 entfernt, der im Takt davor zu sehen war.
- `planwechsel_max` zählt Bestätigungen, Erinnerungen und Kampf-Rufe (REIN, RAUS, DREHEN) nicht als Plan.
- `satz_mit` zählt die noch geltende Kern-Ansage von vor dem Fenster mit, wie `muss_nennen_eins`.
- Die erste Swiftplay-Welle ist mit 0:30 angenommen, das ist nicht belegt.

---

## Qualitätsrunde 1 – Prüfung vom 27.09.2026, A–F (27.09.2026)

Auftrag: `buecher/protokolle/PRUEFUNG_2026-09-27.md`, A–F, noch nicht Schritt 5. Vorher committet: ef08644
(Prüfungsdatei samt Stand). Offline gemessen, der Coach wurde nicht gestartet.

### Umgesetzt

- **A. Verlorene Lane:**
  - Verloren heißt: Kräfte ≤ −1 oder zwei Tode gegen den Lane-Gegner (`modi.lane_verloren`).
  - Der Kern sagt dann **einmal** den Schutzplan `WELLE_HALTEN`: „Gangplank ist vorn: lass die Top-Welle zu
    deinem Turm kommen und farm dort, kein Trade bis Caulfields Kriegshammer.“
    - Der Plan gilt nur bei Leben ≥ `leben_kritisch` und nur, solange kein anderer Gegner beiträgt.
    - Er ersetzt FARMEN und streicht TRADE, ALL_IN und STAPELN.
  - Gefahr am sicheren Ort (≤ 4 s) wird nicht gesagt, der Plan hält. Ebenso Gefahr, zu der nur der Lane-Gegner
    einer verlorenen Lane beiträgt.
  - Nach Tod oder Basis gilt ein Plan wieder als neu (`_angesagt` geleert).
- **B. Plan-Wahl:**
  - Die Gefahr-Regel wechselt auf den besten Kandidaten, den das Gate nicht auslöst.
  - Hält die Hysterese einen schlechteren Plan, steht der Grund im Protokoll (`gehalten`).
  - Test `neuer_plan_ist_der_beste` (600 Zufallslagen).
- **C. BASIS/TOT:**
  - WOHIN kommt zuerst aus der Karten-Rechnung, dann ein Objective, wenn es nehmbar ist (`mindestens`), dann
    Seitenwelle oder Team.
  - Jedes Ziel wird mit der Gefahr **bei Ankunft** gerechnet (`gefahr.p_tod_am`; E2).
  - Ein Ziel je Aufenthalt in TOT und BASIS zusammen (`_wohin`). Es wechselt nur, wenn sich Kills, Strukturen
    oder lebende Objectives ändern.
  - Genannte Fenster sind ≥ Weg + Dauer (C3; Test `fenster_gruende_sprechen_dafuer`).
- **D. Rückzug:**
  - Ein Rückzug ist eine Episode (`RUECKZUG_EPISODE_S` = 15 s): ein Satz, einer mehr nur bei einem neu genannten
    Gegner, der Back-Schritt einmal.
  - „Jetzt back“ nur, wenn `nie_back` nichts dagegen hat. Kein „Denk dran“ in GEFAHR.
  - Neue Kennzahl `fassungswechsel`. Der erste „Jetzt back“ nach „Raus“ ist der Plan-Schritt (D2).
  - Beim Nachmessen gefunden: KAUFEN kam nach einem Teilkauf noch einmal. Die Sperre zählt ihn jetzt nach seinem
    Weiterweg (133930, 17:45/17:57; Szenario `1745-kauf-einmal`, Gegenprobe rot).
- **E. Sätze:**
  - E1: Todesrückblick in zwei Sätzen, ≤ 25 Wörter, ohne Zahlen.
    - Beteiligt ist auch, wer in der letzten Sekunde sichtbar in 2000 stand oder in den 10 s davor nah war.
    - Der Rückblick wird nicht mehr vom Strategen umformuliert. Die Fakten liegen in `lage.letzter_tod` für
      „warum bin ich gestorben?“.
  - E3: keine Wellenbefehle in BASIS.
  - E4: 20 s nach einer Gefahr keine Vorwärts-Handlung, außer die Gefahr ist sichtbar vorbei.
  - E5: das genannte Item ist mit dem Gold bezahlbar (Test `gold_reicht_fuer_das_genannte_item`).
  - E6: ohne Modus spricht keine alte Regel (nur mit Kern).
  - E7: kein AFK in KAMPF; Gegner gelten nie als AFK (die API zeigt ihr Level veraltet).
  - E8: Uhrzeiten als Wörter („acht Minuten“, „sieben siebenundfünfzig“), dazu „du bist pünktlich da“ statt
    Sekundenrechnung.
    - Gegenprobe mit edge-tts und Whisper: „7:57“ wurde vorher „sieben, fünf, sieben“ gehört.
- **4.3 auch für den Ort:** Verliert die Minimap dich kurz, hält der Plan (102112, 36:06).
- **F1** (Nachtrag Buch 1, Kapitel 7.1) und **F2**: siehe unten.

### Abnahme

| Abnahme | Soll | Ist |
|---|---|---|
| Szenarien zuerst rot | ja | **14 von 16 neuen rot** mit ef08644. Grün vorher waren 0349 (die Sätze stimmten: Rest 713 ≤ 1050, 1175 ≤ 1400) und 0900 (Riven stand 7 s vor ihrem Turm, der Gank kam 9:20) – beide bleiben als Wächter. |
| `tests/alle.py` | grün | **grün** (8 / 8) |
| alle Szenarien | grün | **29 / 30** (2 übersprungen, brauchen Claude). **Rot: `0843-todesrueckblick`** – die Daten widersprechen dem Szenario. Riven starb 8:34 (EventTime 514,1) an Yasuo allein, `Assisters []`. Brand war nicht beteiligt und stand laut Minimap etwa 4000 Einheiten weg, nicht zu sehen. `muss_nennen_eins = ["Brand", "zwei"]` kann nur ein erfundener Satz erfüllen. Der Rest des Szenarios ist grün (zwei Sätze, ≤ 25 Wörter, keine Zahlen). Ob Brand genannt werden soll, entscheidet Carlos. |
| Konstruierte Lagen | grün | **38 / 38** (`test_kern`) |
| Protokolle | 5 | `buecher/protokolle/` 102112, 133930, 140253, 144655, 145702 (neu erzeugt mit dem Endstand) |
| Abgebrochene Sätze | nur durch GEFAHR | 144655 1, 140253 0, 102112 2, 133930 9, 145702 1 – **alle** durch einen Gefahr-Satz (ZURUECK, Anlauf, „Nimm keinen Kampf an … geh zurück“). Die 9 in 133930 sind alte Regeln in OBJECTIVE/KAMPF (Schritt 5). |
| Fassungswechsel (D4) | 0 | **0** in 102112, 133930, 140253, 144655 (vor dem KAUFEN-Fix 133930: 1) |
| F1: 144655 ≥ 8 von 10 eindeutigen richtig | ja | **9 von 11 (82 %)** |
| F1: 3:13, 5:17, 5:38 sind GECRASHT_BEI_DIR | ja | **ja, alle drei** |
| F1: 133930 ≥ 8 von 10 | ja | **nicht belegbar**, s. u.: die Minimap-Bilder sind weg. Mit den live erkannten Punkten 4 von 7. |
| F2: ≥ 80 % der Sprünge erkannt, ≤ 1 falscher Flash je Partie | ja | **nicht erreicht**, s. u. |
| F2: Dashboard zeigt jeden erkannten Flash mit Restzeit | ja | **ja** (Headless-Chrome im Nachspielen, 133930 2:09: „Gwen Flash 4:45“, „Xin Zhao Flash 4:24“) |

### Kennzahlen (Kern; in Klammern Schritt 4)

| Aufnahme | ungefragt je 30 min | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | 9.4 1–4 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG |
|---|---|---|---|---|---|---|
| 2026-09-27_102112 | 53 (56) | 0,79 | 0 | 0 | 0 | 8 / 28 / 1 / 2 |
| 2026-09-27_133930 | 85 (88) | 1,25 (1,21) | 0 | 0 | 0 | 9 / 17 / 2 / 1 (11 / 17 / 3 / 0) |
| 2026-09-27_140253 | 53 (61) | 0,90 (1,04) | 0 | 0 | 0 | 2 / 13 / 0 / 1 (3 / 14 / 1 / 0) |
| 2026-09-27_144655 | 62 (56) | 1,06 (0,96) | 0 | 0 | 0 | 2 / 11 / 1 / 1 (5 / 5 / 0 / 1) |

144655 hat weniger Gefahr-Sätze und mehr Pläne: aus fünf „Raus“ sind zwei geworden, dazu der Schutzplan der
verlorenen Lane. Er wird nach jedem Tod und jeder Basis neu gesagt (1:37, 2:14, 5:39, 7:10). Um 3:34 kam er ein
fünftes Mal, weil sein Item wechselte („kein Trade bis Axiombogen“).

### F1 – Welle: Front statt Summe

Umgesetzt wie in der Prüfung (Nachtrag Buch 1, Kapitel 7.1): Gruppen entlang der Lane, die Front, nachlaufende
Wellen als `naechste_dein`/`naechste_ihr`, `GECRASHT_*` ≥ 3 in 0,08 vor dem Turm, keine Zeitpunkte mit Tod oder
Recall in der Eichung.

Die drei Fälle kamen damit **nicht** grün. Die Ursachen lagen im Bild:

- **3:13 und 5:38:** Riven farmt vor ihrem Turm, ihr Icon verdeckt die gegnerischen Vasallen. Sichtbar sind 1–2
  am Rand, 0,085 vor dem Turm.
- **5:17:** Rivens weiße Pfadlinie (1 px, dunkler Schatten) zerschneidet drei gegnerische Vasallen am Turm in
  Stücke von 16/19/53 Flächeneinheiten. Gelesen wurde einer, um 5:15 waren es drei.
- **Hysterese:** Mit ihr schaltet der Zustand erst 5:20.

Drei Zusätze, je mit Schalter in `kern.toml [welle]`:

- `SCHNITT_FLAECHE`: angeschnittene Stücke an weißen Linien zählen, Hälften einmal.
- `icon_deckung`: dein Icon in der Zone, dann reicht einer am Rand.
- `crash_dir_sofort`: GECRASHT_BEI_DIR ohne Hysterese, wie sein Spiegel.

Gegenprobe für die Regel: Test `wellen_front`, mit der alten Summenregel ZU_IHM.

**144655** (Bilder da, neu beschriftet; `buecher/wellen_eichung/2026-09-27_144655.json`):

- 22 Zeitpunkte, 11 eindeutig, 9 richtig (82 %). Vorher waren es 4 von 10.
- Falsch:
  - 5:59: Kern ZU_IHM, wahr ZU_DIR.
  - 8:59: Kern ZU_IHM, wahr MITTE. Die gegnerische Welle liegt unter Rivens Icon.
- **Umbeschriftet:** 7:00 (3 gegnerische am Turm, 1 eigener) war bis F1 ZU_DIR. Nach der F1-Definition ist das
  GECRASHT_BEI_DIR. Ohne diese Umbeschriftung: 8 von 11.

**133930:** Die Minimap-Ausschnitte wurden am 27.09. um 17:26 aufgeräumt (`lage.bilder_aufraeumen`: nur die
letzten drei Partien). Das tat Carlos' laufender Coach nach Partie 164326.

- `wellen_eichung.py` rechnet deshalb mit den **live** erkannten Punkten (`ereignisse.jsonl.gz`). Das ist der
  Leser von damals, mit Rauten- statt Ring-Maske und ohne Pfadlinie.
- Ergebnis: 4 von 7 eindeutigen (57 %).
- 4:00 (1 gegnerischer an deinem Turm, Rest unter Gwens Icon) ist nach F1 kein Crash mehr (≥ 3) und steht jetzt
  auf „unklar“.
- Eine echte Messung braucht eine neue Partie mit Bildern. Der Bilderordner lässt sich jetzt mit einer Datei
  `BEHALTEN` schützen; gesetzt für 102112, 140253, 144655.

**Grenze Vasallen unter fremden Icons:** Betroffen sind 6 Zeitpunkte ausdrücklich unter einem Icon (144655:
1:40, 5:10, 5:52; 133930: 4:00, 4:41, 8:08). Dazu kommen 5, an denen Riven und Gangplank an der Welle stehen und
keine Vasallen zu sehen sind (vermutlich darunter), und die zwei Fehler 5:59 und 8:59 (die Welle liegt unter
Rivens Icon).

### F2 – Flash: erst gemessen (`werkzeuge/flash_messung.py`)

| | 144655 | 140253 | 133930 | zusammen |
|---|---|---|---|---|
| Sprünge 300–450 in ≤ 0,25 s (Sichtungen, F2.1) | 3 | 10 | 23 | 36 |
| davon Gegner | 2 | 1 | 4 | **7** |
| davon heute als Flash erkannt | 1 | 0 | 2 | **3 (43 %)** |
| Dein Flash laut HUD (sichere Wahrheit) | 2 | 3 | 5 | **10** |
| davon als Sprung auf der Minimap zu sehen | 0 | 0 | 0 | **0** |
| Chat „<Champion> hat Blitz benutzt“ im gelesenen Text | 1 | 1 | 1 | **3**, alle 3 wurden Timer |
| Flash-Timer im Nachspielen | 1 (Minimap) | 2 (Chat, Minimap) | 3 (Chat, 2 Minimap) | 6 |

Die 7 gegnerischen Sprünge, und wo sie verloren gehen:

- Erkannt: Gangplank 1:56 (144655), Gwen 1:54 und Tristana 14:50 (133930).
- Kha'Zix 4:41: zwei Lesungen 0,2–0,25 s auseinander (die Live-Grenze ist 0,2 s).
- Tahm Kench 1:01: nicht bestätigt, bleibt keine 0,2 s am Landepunkt.
- Zoe 17:59 und 19:01: als Blink-Champion bewusst ausgenommen.

Bis auf Gangplank haben alle einen eigenen Dash oder Blink. Die Sprünge, die die Minimap sieht, sind also
überwiegend Dashes.

**Gegenprobe an den behaltenen Ausschnitten** (1 Bild/s; 133930 hat keine mehr):

- **Gangplank 1:56:** Kampf mit Riven, beide Icons übereinander. Der Flash ist echt: Carlos pingte ihn um 2:05,
  und Riven flashte laut HUD im selben Moment.
- **Kha'Zix 4:42:** Ein Ausschnitt genau im Sprung zeigt ihn am Landepunkt. Der Sprung ist echt, aber Flash und
  sein E (Sprung 700) sind nicht zu unterscheiden.
- **Tahm Kench 1:01:** Er liegt halb unter Zoes Icon; der „Sprung“ ist die wandernde Mitte des verdeckten Icons.
  Das ist ein Verfolger-Fehler, und die Live-Kette verwarf ihn zu Recht.

**Der Befund:** Ein Flash fällt fast immer in einen Kampf, und im Kampf liegen die Icons übereinander. Bei
Rivens eigenen 10 Flashs, bei denen der Zeitpunkt feststeht, sah es so aus:

- 8-mal führte der Verfolger ihr Icon nur als verdeckt (Güte 0, wird nie als Sprung gewertet) oder hatte es
  nicht.
- 2-mal sah er keinen Sprung.

Für Gegner gilt dasselbe Bild. Der Bildschirmweg sieht die Kämpfe und liest sogar Namen (Xin Zhao, Zac, Yasuo).
Er verwirft sie aber zu Recht, weil sie alle einen eigenen Dash haben („lieber stumm als falsch“).

- **Einzige sichere Quelle:** der Chat-Ping aus der Anzeigetafel. 3 von 3 kamen an, einen davon hat Carlos
  selbst gepingt.
- **Falsche Flashs:** Drei Minimap-Timer betreffen Champions mit Dash (Yasuo 10:01, Gwen 1:54, Tristana 14:50).
  Sie sind unbestätigt. Waren es Dashes, hat 133930 zwei falsche.

**Abnahme nicht erreicht.** Mit Schwellen ist das nicht zu holen: jede Lockerung macht aus Dashes Flashs.
Möglichkeiten, **Carlos' Entscheidung:**

1. Die Minimap verwirft wie der Bildschirm Sprünge von Dash-Champions. Das ergibt weniger, aber sichere Timer.
2. Den Flash-Effekt im Spielbild erkennen (gelber Blitz an Absprung und Landung). Das ist eine neue
   Wahrnehmungsaufgabe und unterscheidet Flash von Dash.
3. Carlos pingt gegnerische Flashs in der Anzeigetafel. Das kommt heute schon zu 100 % an.

### Abweichungen vom Buch und Entscheidungen

1. **F1-Zusätze:** Pfadlinie, Icon-Deckung und GECRASHT_BEI_DIR sofort (s. o.). Alle drei sind abschaltbar.
2. **Umbeschriftung 7:00** (144655) und **4:00** (133930) nach der neuen Definition. Beide sind oben genannt,
   mit Zahl ohne Umbeschriftung.
3. **Todesrückblick nicht mehr situativ:** Der Stratege formuliert ihn bis Schritt 6 nicht mehr frei. Der Weg
   zum Strategen bleibt und ist getestet (`test_stratege`).
4. **Flash-Meldungen warten auf das Briefing**, statt es zu unterbrechen (nur GEFAHR unterbricht).
5. **Gegner-AFK aus:** Die API zeigt fremde Level nur, wie zuletzt gesehen. Ein „AFK“-Gegner war ein Irrtum.
6. **Konstanten nicht im Buch:**
   - `SICHER_DORT_S` = 4 s, `NACH_GEFAHR_S` = 20 s, `RUECKZUG_EPISODE_S` = 15 s, `PUENKTLICH_S` = 5 s.
   - `[modus] ort_halten_s`.
   - `[welle] turm_toleranz` = 0,02, `icon_deckung`, `crash_dir_sofort`, `welle.SCHNITT_FLAECHE` = 10.
7. **Tests an die Prüfung angepasst:**
   - `modus_sperre_budget`: ohne Modus → stumm (E6).
   - `test_stratege`: der lange Tod gibt zwei Sätze (E1).
8. **Neue Werkzeuge:**
   - `werkzeuge/flash_messung.py` (F2).
   - `werkzeuge/dashboard_nachspielen.py`: das Dashboard mit dem Stand einer Aufnahme auf eigenem Port, neben
     einem laufenden Coach.
   - `wellen_eichung.py`: `--mit` für feste Zeitpunkte; ohne Bilder rechnet es mit den Live-Punkten.
9. **Nebenbei:** Während der Arbeit lief Carlos' Coach (Start 16:43) und eine Partie (17:31). Schwere Läufe
   liefen mit niedriger Priorität, der Coach wurde nicht angefasst. Die Minimap-Bilder von 140253 und 144655
   sind vorsorglich gesichert.

---

## Schritt 4 – SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN (27.09.2026)

### Umgesetzt

- `kern/modi/karte.py` – die Karten-Rechnung aus Buch 5, Kapitel 2:
  `EV = gewinn · p_erfolg − weg · zeitwert − p_tod(weg + dauer) · Todeskosten + folgewert`.
  - **Türme:** je Lane der vorderste stehende Turm. Verteidiger werden je Gegner gerechnet: Tote mit Respawn plus Weg aus dem Brunnen, Gesehene ≤ 15 s mit Weg ÷ Tempo, alle anderen gelten als unbekannt. Ein Turm ist Kandidat, wenn er vor dem **ersten** Verteidiger fällt oder du diesen schlägst. Für die Antwort zählt ihre gemessene Kraft.
  - **Wert eines Turms:** Platten an jedem Turm, Turmgold, `turm_extra`. Kristalle (×1,3) werden nur dort gerechnet, wo man sie sieht: am äußeren Turm deiner Lane mit allen Platten.
  - **Weitere Kandidaten:** Seitenwelle, Welle rein und rotieren (45–75 s, ohne TP), zur Gruppe bzw. TP-Spiel (Kapitel 5) und Umwandeln (Kapitel 8). Beim Umwandeln gilt die Reihenfolge aus Kapitel 8 bis zum Nexus: Inhibitor-Turm, Inhibitor, Nexus-Türme, Nexus.
- **Modi:**
  - `modi/seite.py`: Split-Regel 3.1. Nach einem gewonnenen Kampf gilt sie nicht.
  - `modi/gruppe.py`: MIT_GRUPPE, Seitenwelle auf deiner Seite; Back nur, wenn kein Objective und kein Kampf ansteht.
  - `modi/unterwegs.py`, `modi/verteidigen.py` (WELLE_KLAEREN, HALTEN_UNTER_TURM, TAUSCHEN).
  - Nach einem gewonnenen Kampf gibt es in SEITE, GRUPPE und UNTERWEGS keinen Back, solange eine Struktur erreichbar ist.
- **`kern/merkmale.py`:**
  - Wellen aller drei Lanes, `lane_hier`, Seitenwellen, woanders/unbekannt.
  - Die Antwort und ihre Kraft.
  - Teamkampf: ≥ 2 gegen ≥ 2 in 1500, dazu fällt Leben oder jemand stirbt; hält 5 s.
  - TP ihres Toplaners, Tote.
  - Das Umwandel-Fenster über die Takte.
- **Sprechen (Kapitel 2 und 6):**
  - Läufst du schon zum Ziel (≥ 500 Einheiten näher in 3 s), schweigt der Coach, und der Plan gilt als gesagt. Ausnahme ist das Umwandeln: dort sagt der Satz das Fenster und „Ruf dein Team“.
  - Einmal Erinnerung nach 20 s ohne Fortschritt außerhalb der Lane.
- **Bestätigungen (Kapitel 9):** „Genau so - Welle drin und pünktlich da.“, „Sauber umgewandelt.“, „Guter TP.“, „Welle gerettet - kein Turm verloren.“.
- **BASIS nach der Lane-Phase:** Das Ziel kommt aus der Karten-Rechnung, sonst aus der alten Bewertung. In den Kauf-Satz geht nur noch dessen Grund. Vorher stand dort 133930, 17:57: „… dann auf den Bot-Inhibitor-Turm: Geh auf den Bot-Inhibitor-Turm, …“.
- **`kern/testlage.bauen_mitte`:** baut eine echte `Partie` aus den Lagen in `mitte.toml`.
  - Wellen, Mitspieler, Gegner (gleicher Bereich wie du → im Abstand; fehlend → unbekannt), Türme und Teamkampf.
  - Die Jungler-Seite wird wie `jungle.wahrscheinlich` gerechnet.
- **`szenarien.py`:** Eine gesprochene Kern-Ansage, deren Plan im Fenster noch gilt, zählt für `muss_nennen_eins` (Kapitel 2: schweigt, solange du hinläufst).
- **Live-Default:** `kern.KERN_MODI` = LANE, BASIS, TOT, SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN. Mit `LOLCOACH_KERN_SCHRITT=3` gibt es den Stand von Schritt 3 für Gegenproben.

### Abnahme Schritt 4 (Buch 5, Kapitel 11)

| Abnahme | Soll | Ist |
|---|---|---|
| `3632-ende-statt-back` über den Kern | grün | **grün**. 36:03 bzw. 36:13 „Mid-Inhibitor-Turm jetzt: 4 von ihnen sind noch 33 Sekunden tot. Ruf dein Team.“, der Plan hält bis 36:47. Gegenprobe mit dem Schritt-3-Kern: **rot** (36:32 „Geh jetzt back, du hast 4400 Gold …“). |
| `3535-rueckzug-31s` über den Kern | grün | **grün**. 35:27 „Raus zu Brand, Corki und Tryndamere: Sett kommt.“ statt des Top-Turms in 31 s. |
| `1315-crash-dann-back` | grün | **grün** |
| Lagen in `mitte.toml` | alle grün | **13 / 13**, dazu `lane.toml` + `recall.toml` 25 / 25 (`test_kern` prüft jetzt alle 38) |
| 9.4 Punkt 1–4 ohne Verstoß | alle Aufnahmen | **0** in 102112 und in allen neuen echten Partien (133930, 140253, 144655): Das ist die Abnahme aus Buch 0, Kapitel 13. In den Aufnahmen vom 26.09. bleiben 10 (120049 2, 125902 2, 155643 1, 194524 2, 212105 2, 230520 1). Es sind alles alte Regeln an Stellen, an denen die Minimap Riven länger als 10 s nicht fand (kein Modus = keine Sperre, s. u. Punkt 12). |
| ungefragte Ansagen je 30 min ≤ 50 | ja | **nicht erreicht**: 102112 56 (Schritt 3: 57), 133930 88, 140253 61. Der Kern allein liegt darunter (102112 37, 133930 43). Der Rest ist das alte System im Modus OBJECTIVE (102112: 19 Ansagen, 133930: 26), der erst in Schritt 5 an den Kern geht. |
| echte Partie mit Mid-Game (> 20 min) ausgewertet | ja | **ja**: 133930, s. u. |
| `tests/alle.py` | grün | **grün** (neu: Viego-Übernahme, AFK-Gegner) |

Szenarien 102112 mit Kern: **13 grün / 13 geprüft** (Schritt 3: 11 / 13).

### Kennzahlen (Stand Schritt 4, Kern)

| Aufnahme | ungefragt je 30 min | Lane-Phase je 30 s | Kehrtwenden | 9.4 1–4 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG | p_da-Brier schlimmster Fall → Kern |
|---|---|---|---|---|---|---|
| 2026-09-27_102112 | 56 | 0,79 | 0 | 0 | 8 / 29 / 1 / 2 | 0,317 → 0,059 |
| **2026-09-27_133930 (echt, 21,8 min)** | 88 | 1,21 | 0 | 0 | 11 / 17 / 3 / 0 | 0,423 → 0,074 |
| **2026-09-27_140253 (echt)** | 61 | 1,04 | 0 | 0 | 3 / 14 / 1 / 0 | 0,273 → 0,044 |
| **2026-09-27_144655 (echt)** | 56 | 0,96 | 0 | 0 | 5 / 5 / 0 / 1 | 0,241 → 0,038 |

Das neue Seiten-Modell der Gefahr (Punkt 6) verschlechtert die Eichung nicht: p_da schlägt den schlimmsten Fall in allen 26 Aufnahmen, 102112 und 140253 unverändert.

**Echte Partie 133930** (Riven Top gegen Gwen, rote Seite, ab 14:00 hinten):
- Von 14:00 bis 21:55 war der Modus zu gut drei Vierteln OBJECTIVE. Der Kern entscheidet nach Schritt 4 also im kleineren Teil des Mid-Games.
- Wo er entscheidet, passt es. 20:11 „Raus zu deinem Mid-Tier-1-Turm: Tristana und Zoe kommen.“ (danach fiel Rivens Leben von 88 auf 33 %), 20:23 Back bei 33 %.
- 21:46 in ihrer Basis mit vier toten Gegnern: „Nexus-Turm jetzt: 4 von ihnen sind noch 19 Sekunden tot.“, danach „Nexus jetzt …“. Vorher stand dort „Back jetzt“, weil der Kern hinter den Inhibitor-Türmen keine Ziele kannte.
- In 102112 gilt dasselbe ab 38:17 („Nexus-Turm jetzt …“). Um 38:32 fällt er, und der Coach sagt „Sauber umgewandelt.“

### Abweichungen vom Buch und Entscheidungen

1. **Erster Verteidiger (Kapitel 2):** Geprüft wird nur der erste, der rechtzeitig kommt. Vorher wurden alle Rechtzeitigen gegen dich gerechnet (`m-split-drueck`).
2. **Split-Regel 1:** Ruft ein Objective ohne TP und gibt es „Welle rein und raus“, fallen FARMEN, SEITENWELLE, DRUECKEN und PLATTEN weg. Vorher gewann FARMEN (`m-welle-und-raus`).
3. **Zeitwert nur auf den Weg, p_tod über Weg + Dauer** (Formel in Kapitel 2). Vorher kostete auch die Zeit am Turm Zeitwert, und der innere Turm verlor gegen eine halbe Welle.
4. **Platten an jedem Turm:** Patch 26.1, `saison2026.md`: auch innen und am Inhibitor. `turm_gewinn` hatte sie nur außen.
5. **Kristalle** zählen nur, wo sie sichtbar sind (äußerer Turm deiner Lane, alle 5 Platten stehen). Sonst rechnet der Coach ohne.
6. **Gefahr, Kartenseite nach der Lane-Phase (7.5):**
   - Jeder gesehene Gegner zählt auf der Seite seiner letzten Sichtung, verblasst über 90 s wie der Jungler (`jungle.wahrscheinlich`). Vorher galt `roam_basis` für alle. 3535 war dadurch „keine Gefahr“: Kai'Sa vor 7 s unten, Sona und Sett unten, Riven allein im unteren Fluss.
   - Der Lane-Gegner zählt mit 1 nur, wenn du auf deiner Lane stehst.
7. **„Bleib an/bei …“ (ZURUECK am sicheren Ort):** Das Risiko gilt über das normale Fenster, ohne Rückzugsrabatt. Vorher schlug es mit p_tod ≈ 0 das Halten unter dem Turm (`m-verteidigen-halten`).
8. **Umwandeln (Kapitel 8):**
   - Die 15 s braucht nur der Auslöser. Danach hält das Fenster, „solange es reicht“, also solange ein Turm vor seinem ersten Verteidiger fällt. Vorher kippte der Plan um 36:32 (Sona noch 14 s tot) auf HALTEN.
   - Es gilt auch in SEITE. Vorher 36:03 auf der Bot-Lane mit vier Toten: „Bot-Welle rein, dann back“.
9. **Folgewert beim Umwandeln:** Fällt ein Turm im Fenster, zählt der nächste derselben Lane mit, wenn auch er vor seinem ersten Verteidiger fällt. Sonst schickte der Coach die Gruppe von Mid quer über die Karte zum inneren Bot-Turm, statt den äußeren Mid-Turm fünf Sekunden vor ihr zu nehmen (`m-gruppe-umwandeln`). „Mit der Gruppe“ gilt nur, wo Mitspieler am Ziel stehen.
10. **Kapitel 8, Punkte 1–2 (nicht im Buch beziffert):**
    - Positionen von Inhibitoren, Nexus-Türmen und Nexus stammen aus der Karte.
    - Werte: Inhibitor = `objective_wert.inhibitor`, Nexus-Turm = `turm_extra` + ¼ Nexus, Nexus = `objective_wert.nexus`.
    - Dauer wie `turm_dauer_s.nexus`. Nexus-Türme stehen nach 180 s wieder.
    - Nur im Umwandel-Fenster.
11. **Sprechen:** Die Regel „Läufst du schon dorthin, schweigt der Coach“ gilt nicht beim Umwandeln (der Satz trägt das Fenster). Erinnert wird nur außerhalb der Lane.
12. **Modus bei kurz unbekanntem Ort (4.3):** Der Modus bleibt bis zu 10 s (`[modus] ort_halten_s`, nicht im Buch). Vorher sprachen dann die alten Regeln ungesperrt: 133930 um 7:52–7:58 „Schieb die Welle in seinen Turm“ mitten im Modus OBJECTIVE. Länger unbekannt bleibt es wie in Schritt 2: kein Modus, die alten Regeln sprechen.
13. **Szenario-Prüfung:** Eine stehende Kern-Ansage zählt für `muss_nennen_eins`. `3632` verlangt „Mid“ oder „Inhibitor“ in 36:30–36:47. Der Kern sagt es um 36:13 und schweigt danach, weil Riven hinläuft (Kapitel 2). Das Szenario selbst ist unverändert. `darf_nicht_sagen` prüft weiter nur Gesprochenes im Fenster.
14. **`testlage`-Annahmen:**
    - Gegner im gleichen Bereich wie du stehen im angegebenen Abstand; fehlende sind unbekannt.
    - Die Gegner eines Teamkampfs stehen sichtbar am Kampfort.
    - Die Jungler-Seite kommt aus der Sichtung.
    - `m.mitspieler` kommt aus den Mitspielern der Lage (fehlte: „mit der Gruppe“ zählte nie jemanden).
15. **`kern.toml`-Schlüssel, die nicht im Buch stehen:**
    - `[mitte]`: `woanders_abstand`, `woanders_alt_s`, `seitenwelle_mitspieler_abstand`, `teamkampf_nachlauf_s`, `teamkampf_leben_faellt`, `platten_annahme`, `kampf_wert_je_gegner`, `gruppe_turm_faktor`.
    - `[modus]`: `ort_halten_s`.

### Nebenbei behoben: Partie 144655 (Carlos, 14:46, Riven Top gegen Gangplank)

- **„Partie vorbei“ um 9:24:** Der gegnerische Viego übernahm einen Toten. Die Live-API meldet ihn dann unter dessen Namen (Kha'Zix, Vex). Der Coach hielt jede Übernahme für eine neue Partie, schrieb ein Review und fing in 30 s viermal neu an. Jetzt gilt nur noch: andere Spieler oder die Spieluhr springt zurück (`aufzeichnung._spieler`). Das Practice Tool fällt weiter an der Uhr auf.
- **„Kha'Zix ist AFK … spiel deine Lane nach vorn“ (1:30, Riven starb 1:57):** Die Live-API zeigt die Items der Gegner nicht, also ist „kein einziges Item“ bei Gegnern kein Beleg. Dieselbe falsche Meldung kam in 133930 für Zac. Ein Gegner gilt jetzt nur als AFK, wenn er ab 2:30 noch Stufe 1 ist. Die AFK-Sätze nennen die Welle mit Lane (9.4 Punkt 1, 102112 1:30).
- **Hat mein halbfertiger Schritt 4 in seiner Partie mitgesprochen? Nein.** Sein Coach lud den Kern beim Partiestart um 14:46:55, mein erster Schritt-4-Patch kam um 14:49:12, und Python lädt Module nicht nach. Zur Zeit der „Wortfetzen“ (6:28–6:51 = 14:53:23–14:53:46) liefen bei mir keine Messungen.
- Das Stottern der Stimme und die fehlenden Flash-Timer auf dem Dashboard sind **nicht** untersucht (OFFEN.md).

---

## Nachtrag zu Schritt 3 – Wellen-Wahrnehmung (27.09.2026)

Auftrag Carlos: kein Umbau am Kern; `welle.py` nur Icon und Ring ausblenden, Minimap-Ausschnitte der letzten drei
Partien behalten, `1315` auch OBJECTIVE erlauben, Eichung (Buch 1, 1.4) an der nächsten echten Partie wiederholen.

- **Icon und Ring statt Raute** (`welle.py`): Der Ring eines Champion-Icons liegt bei 30–33 px (Icon-Radius 32 px,
  764-px-Minimap; gemessen an 314 freien Icons der Partie 140253), ab 34 px ist nichts mehr davon. Jetzt werden je
  Champion Icon und Ring (1,1 Icon-Radien + 1 px) in den Farbmasken geschwärzt, danach wird gezählt. Vorher: eine
  Raute 0,05 um die Icon-Mitte, am Schwerpunkt geprüft – auf den Diagonalen enger als der Ring, auf den Achsen weiter.
  An allen 613 Ausschnitten von 140253: Punkte im Ring (≤ 36 px) **vorher 14, jetzt 0**; Vasallen direkt neben dem
  Ring (37–40 px) vorher 227, jetzt 394; insgesamt 8956 → 9089. Stichprobe von 12 der neuen Punkte am Ring: 11 echte
  Vasallen, 1 auf dem hellblauen Leuchtring eines Recalls/Teleports. Test `wellenleser_ring_und_nachbar` (fällt mit
  dem alten Stand durch: Ringstück gezählt, Vasall bei 38 px verloren).
  Was das nicht kann: Vasallen **unter** einem Icon sind im Bild verdeckt – die bekommt keine Maske zurück.
- **Ausschnitte behalten:** `lage.bilder_aufraeumen` schützt die Bilder der letzten drei *Partien* – gezählt nach
  aufgenommener Spielzeit (≥ 5 min), nicht nach der Spieluhr; Coach-Neustarts und Bruchstücke schoben echte Partien
  vorher hinaus (130355 verlor seine Bilder an 132154 und 133930). Während der Partie wird nicht mehr nach 20 min
  gelöscht (`BILDER_BEHALTEN` 90 min), sonst fehlte die Lane-Phase jeder längeren Partie. ~100–180 MB je Partie.
- **`1315-crash-dann-back`:** `modus = ["SEITE", "OBJECTIVE"]`, soll/darf_nicht unverändert – jetzt grün (der
  Kern-Plan-Teil bleibt übersprungen, bis der Kern OBJECTIVE/SEITE führt).
- **Werkzeug `werkzeuge/wellen_eichung.py`:** rechnet die Welle aus den behaltenen Ausschnitten einer Aufnahme neu
  (aktuelles `welle.py` + WellenPuffer des Kerns), legt eine Bildtafel und `buecher/wellen_eichung/<stamm>.json` an;
  `--auswerten` gibt die Quote.
- **Zwischenstand an 133930** (echte Partie, Riven Top gegen Gwen, rote Seite, 1073 Ausschnitte – die erste lag vor
  dem Umbau und war bisher nicht bekannt): 13 Zeitpunkte der Lane-Phase (die ersten ~4 min hatte die alte 20-min-Regel
  schon gelöscht). **9 eindeutig, 5 richtig (56 %); GECRASHT_BEI_IHM 0 / 2.** Richtig sind nur die leichten Fälle
  („deine Welle läuft los“, ZU_IHM); falsch alle aussagekräftigen: GECRASHT_BEI_DIR (4:00), GECRASHT_BEI_IHM (6:07,
  Riven im Recall – der Leuchtring schluckt die Vasallen daneben), ZU_IHM statt gehaltenem GECRASHT_BEI_IHM (6:28 –
  die Zustands-Hysterese im WellenPuffer hält den Crash zu lange), ZU_DIR (7:09 – die gegnerischen Vasallen halb unter
  Gwen, die Zählung kippt). Abnahme weiter **nicht erreicht**. Die Eichung an der **nächsten** echten Partie steht aus.
- **Wiederholt an der nächsten echten Partie, 144655** (Riven Top gegen Gangplank, rote Seite, 797 Ausschnitte):
  - 19 Zeitpunkte, davon 10 eindeutig, **4 richtig (40 %)**. GECRASHT_BEI_IHM kam nicht vor. Abnahme weiter **nicht erreicht**.
  - Richtig waren wieder nur „deine Welle läuft los“ (ZU_IHM).
  - Der Kern sagt in 17 von 19 Fällen ZU_IHM.
  - **Die Hauptursache ist jetzt klar, und sie liegt im Kern, nicht im Bild.** Dreimal (3:13, 5:17, 5:38) stehen gegnerische Vasallen an deinem äußeren Turm, während deine nächste Welle zwischen innerem und äußerem Turm losläuft. Die Zustandsregel (`WellenPuffer._roh`, Buch 1 1.4) zählt alle Vasallen der Lane. GECRASHT_BEI_DIR verlangt `unsere ≤ 1`, und mit der nachlaufenden Welle (4–6) wird daraus `unsere − ihre ≥ 2` = ZU_IHM.
  - Dazu zweimal gegnerische Vasallen direkt am Riven-Icon, die die Ring-Maske mit ausblendet (7:00, 8:59).
  - Und zweimal wählte das Werkzeug einen Zeitpunkt, an dem Riven tot war (Auswahl prüft den Tod nicht).
  - Vorschlag, **Carlos' Entscheidung** (Umbau am Kern): nur die Vasallen um die Front zählen, die nachlaufende Welle nicht. Beschriftung: `buecher/wellen_eichung/2026-09-27_144655.json`.
- Nebenbei: `tests/test_kern.py` und `szenarien.py --konstruiert` prüfen nur Lagen in Modi, die der Kern schon führt;
  die neuen Lagen aus `mitte.toml` (Buch 5, Schritt 4) stehen als „übersprungen“ und werden mit Schritt 4 geprüft.

---

## Schritt 3 – Der Kern übernimmt LANE, BASIS, TOT (27.09.2026)

### Umgesetzt

- `lolcoach/kern/`: `handlung.py` (Ziel, Handlung, vor/zurück/stumm/sicher), `gefahr.py` (p_da, p_verliere, p_tod
  nach 7.5), `wert.py` (EV, Todeskosten 7.3, Wellenwert, Zeitwert, sechs Fragen), `plan.py` (halten / Gefahr /
  Schritt / besser mit Hysterese / Erinnerung, 8.2), `sprechen.py` (Kategorien, Budget 9.2 im Kern selbst,
  wartender PLAN), `modi/lane.py`, `modi/basis.py`, `modi/tot.py`, `testlage.py` (konstruierte Lagen, Buch 1 6.2).
- `kern/merkmale.py`: `WellenStand` (Buch 1, 1.2–1.4: Median 6 s, Trend 20 s, Nebel, vorderster stehender Turm,
  Zustände mit Hysterese 3 s, GECRASHT_BEI_IHM sofort), Kanonen-Uhr, Jungler-Seite (`jungle.wahrscheinlich`), TP,
  Kaufplan, Lane-Gegner im Brunnen, Welle beim Verlassen der Lane.
- Buch 1 (Welle): FARMEN, WELLE_REIN_UND_BACK (mit Kanone), STAPELN, WELLE_HALTEN (angreifend/schützend),
  UNTER_TURM_FARMEN, PLATTEN; Buch 3 (Recall, Tempo, Kauf): die fünf Back-Gründe, „nie back“ (2.2), die Welle
  entscheidet den Zeitpunkt (2), Gefahr schlägt Timing (2.1), KAUFEN mit Namen und Kontroll-Auge (3), WOHIN mit
  Wellen-Uhr / Objective / TP zur Lane (4), BESTAETIGUNG (5): Back im Fenster, Rückzug gelohnt, Platte mit Fenster,
  unter dem Turm gefarmt, Stapel zur Kanone, Fokus Kontroll-Auge.
- `--kern neu` ist Default. In LANE, BASIS und TOT sind die alten Regeln stumm (Sperre), außer dem
  Todesrückblick (einmal je Tod ab 14 s) und `_afk`. Stellung `schatten` rechnet mit und schreibt „würde sagen“ in
  `_kern.jsonl`, `alt` ist der Stand von Schritt 2.
- Sprechplan-Weiche (9.6): `kern:`-Ansagen laufen an Themen-, Widerspruchs- und Rückzugssperre vorbei, das Budget
  prüft der Kern. Midgame-Plan des Strategen → INFO (9.1). `minimap_gesund` → TECHNIK durch den Sprechplan.
- Dashboard (9.5): Plan mit Grund, Top-3 mit EV, Gefahr-Markierung; Claude bekommt den Plan als zweite Kopfzeile.
- `_kern.jsonl`: je Takt dazu Plan, Schritt, Ziel, EV, Top-3, Gefahr, Wellenzustand und was gesagt wurde.
- Werkzeuge: `szenarien.py` prüft `soll`/`darf_nicht` gegen den Kern-Plan (überspringt Modi, die der Kern noch nicht
  führt), `--kern`, `--konstruiert`; `kennzahlen.py` misst alt und Kern nebeneinander (Lane-Phase je 30 s,
  GEFAHR/PLAN/ERINNERUNG/BESTAETIGUNG, p_da-Brier auf denselben Proben).
- Tests: `tests/test_kern.py` (alle konstruierten Lagen + Satzlängen 9.3), `bestaetigung_back_im_fenster`,
  `minimap_farben_relativ`.
- Die drei Szenarien aus Buch 3, 7.1 liegen in `tests/szenarien/2026-09-27_102112_buch3.toml`.

### Abnahme Schritt 3

| Abnahme | Soll | Ist |
|---|---|---|
| `0517-platte-ohne-flash`, `0850-kein-hin-und-her`, `0904-drei-kommen`, `3100-basis-braucht-ziel` (Kern) | grün | **alle grün** (5:18 „Back jetzt: 38 Prozent Leben, Sett ist tot.“; 9:02 ZURUECK) |
| `3004-basis-kauf-und-ziel` ohne `frage` | grün | **grün** (KAUFEN: Letzter Atemzug + Sonnenköcher) |
| Buch 3: `0545-back-bei-40-prozent`, `0600-basis-kauf` | grün | **grün** (`1315` gehört zu Schritt 4, s. u.) |
| konstruierte Lagen `lane.toml` + `recall.toml` | alle grün | **25 / 25** |
| Kehrtwenden | 0 | **0** in allen fünf Aufnahmen und in der echten Partie (alt 102112: 3) |
| Lane-Phase: ungefragte Ansagen je 30 s | ≤ 1 im Mittel | **0,83** (102112), 0,94 / 0,65 / 0,89 / 0,00 (andere); echte Partie 140253 **1,04** (alt 1,33) |
| `p_da` schlägt den schlimmsten Fall (Brier) | ja | **ja, überall**: 102112 0,059 gegen 0,317; echte Partie 0,044 gegen 0,273 |
| mindestens eine echte Partie ausgewertet | ja | **ja**: 140253 (Riven Mid gegen Yasuo, 10,8 min, vom alten System gespielt, mit dem Kern nachgespielt) |
| `tests/alle.py` | grün | **grün** (neu: `test_kern`) |
| Buch 1, 1.4: Wellen-Eichung ≥ 80 %, GECRASHT_BEI_IHM ≥ 90 % | ja | **nicht erreicht**, s. u. |
| Generalprobe | – | **nicht gelaufen**: Carlos spielte währenddessen (eigenes Fenster mit Spieltitel) |

Szenarien 102112 mit Kern: 11 grün / 13 geprüft. Rot bleiben `3632-ende-statt-back` (UNTERWEGS/GRUPPE,
Abnahme Schritt 4; das alte System sagt dort weiter „Geh jetzt back“) und `1315-crash-dann-back` (der Modus ist
um 13:15 OBJECTIVE, das Szenario sagt SEITE; Abnahme Schritt 4).

### Kennzahlen (Stand Schritt 3; alt = `--kern alt`, Kern = `--kern neu`)

| Aufnahme | ungefragt je 30 min alt → Kern | „… bei dir“ | Lane-Phase je 30 s | Kehrtwenden | 9.4-Verstöße 1–4, 7 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG | p_da-Brier schlimmster Fall → Kern |
|---|---|---|---|---|---|---|---|
| 2026-09-26_235433 | 74 → 58 | 3 → 0 | 1,21 → 0,94 | 0 → 0 | 4 → 0 | 6 / 10 / 2 / 0 | 0,198 → 0,069 |
| 2026-09-27_001155 | 29 → 39 | 2 → 2 | 0,49 → 0,65 | 0 → 0 | 2 → 0 | 0 / 4 / 0 / 0 | 0,213 → 0,198 |
| 2026-09-27_094832 | 71 → 53 | 3 → 0 | 1,18 → 0,89 | 0 → 0 | 2 → 0 | 4 / 5 / 2 / 0 | 0,229 → 0,047 |
| 2026-09-27_101832 | 27 → 0 | 0 → 0 | 0,45 → 0,00 | 0 → 0 | 0 → 0 | 0 / 0 / 0 / 0 | 0,308 → 0,144 |
| 2026-09-27_102112 | 61 → 57 | 11 → 3 | 1,18 → 0,83 | 3 → 0 | 2 → 1 | 5 / 23 / 1 / 1 | 0,317 → 0,059 |
| **2026-09-27_140253 (echt)** | 78 → 61 | 3 → 0 | 1,33 → 1,04 | 0 → 0 | 4 → 0 | 4 / 11 / 1 / 0 | 0,273 → 0,044 |

Die ungefragten Ansagen je 30 min liegen außer in 001155 unter dem alten System, aber noch über dem Ziel 45 aus
Kapitel 9.2 – der Rest kommt außerhalb der Kern-Modi (SEITE, OBJECTIVE, UNTERWEGS: Schritte 4/5). Der eine
9.4-Verstoß in 102112 ist `_afk` (1:30, „Euer Jungle ist leer“ ohne Lane), bis Schritt 8 eine alte Regel.

**Echte Partie 140253** (Carlos, Riven Mid auf der roten Seite, Coach um 10:45 von Carlos beendet: „ich bin jetzt
gerade zweimal gestorben wegen dir“): Das alte System sagte 9:25 „Schieb die Welle rein und geh dann zum
Drachen“, 10:05 starb Riven an Yasuo. Der Kern sagt an denselben Stellen „Bleib an deinem Mid-Tier-1-Turm:
Brand und Yasuo kommen“ (8:15) bzw. „Raus zu deinem Mid-Tier-1-Turm: Brand und Yasuo kommen“ (9:50) – in beiden
Todesfenstern die Warnung, nie ein „rein“. Dazu kamen die Wahrnehmungsfehler der roten Seite (unten, Punkt 10).

### Buch 1, 1.4: Wellen-Eichung – nicht erreicht

- **102112** hat keine Minimap-Ausschnitte mehr (am Partieende aufgeräumt), nur Spielbilder mit einer Minimap von
  237 px – Vasallen 1–3 px, nicht ehrlich zu beschriften.
- **Echte Partie 140253**: 20 Zeitpunkte der Lane-Phase aus den 764-px-Ausschnitten (während der Partie gesichert,
  nur lesend kopiert). Eindeutig beschriftbar waren 6 der 20 – am Kampfort liegen die Vasallen fast immer unter den
  Champion-Icons, und `welle.py` blendet Punkte am Icon bewusst aus (der Ring hat dieselben Farben). Davon 2 richtig
  (ZU_IHM 3:48, ZU_DIR 5:30), 4 falsch (4:00 ohne jede Lesung noch ZU_IHM statt UNBEKANNT/LEER; 4:12 und 5:42
  eigene Welle kommt, Kern ZU_DIR/MITTE; 4:49 die Wellen treffen sich an Rivens Turm, Kern ZU_IHM).
- Ursachen: (1) Die rote Seite war vertauscht (Punkt 10, behoben); (2) der Trend lief über Sprünge der Front
  (behoben: nur der letzte zusammenhängende Abschnitt, `[welle] front_sprung`); (3) die gegnerischen Vasallen am
  Kampfort fehlen (unter den Icons, im Nebel) – dann gilt `unsere − ihre ≥ 2`, und fast alles ist ZU_IHM. Das ist
  Wahrnehmung, kein Kern-Fehler.
- Folge für die Entscheidungen: WELLE_REIN_UND_BACK hängt an ZU_IHM/MITTE und damit praktisch nur am Back-Grund;
  BACK_JETZT, PLATTEN und STAPELN hängen an GECRASHT_BEI_IHM/LEER/MITTE und sind seltener als sie sein sollten.
  GECRASHT_BEI_IHM ließ sich nicht getrennt eichen (in der Stichprobe einmal, ohne Bild-Wahrheit).
- Offen (OFFEN.md): `welle.py` braucht eine Zählung, die unter den Icons nur den Ring ausblendet, nicht den ganzen
  Kreis, und eine echte Partie mit behaltenen Minimap-Ausschnitten (die Aufräumung am Partieende verschieben).

### Abweichungen vom Buch und Entscheidungen

1. **Gefahr-Gate (Buch 3, 2.1):** Schlägt die Gefahr beim Bleiben an (7.5), sind nur sichere Handlungen (ZURUECK,
   BACK_JETZT) und der schützende Freeze (Buch 1, 3.7) Kandidaten – sonst gewann „Welle rein, dann back“ mit
   Sett 900 entfernt (`k-nicht-back-gegner-nah`).
2. **`p_kampf` (nicht im Buch, `[gefahr] kampf_ohne_anlauf = 0.3`):** Mit p_da = 1 für jeden sichtbaren Gegner in
   1500 war jede ausgeglichene Lane „Gefahr“ (p_tod 0,3). Ein Sichtbarer, der nicht auf dich zuläuft, kämpft nur mit
   0,3; dein Lane-Gegner, der auf dich zuläuft, ebenso – außer er ist stärker (`kraefte()[0] ≤ −1`) oder du bist
   unter 50 % (echte Partie 140253, 0:38: „Raus zu deinem Turm“ zu Spielbeginn). Wer ungesehen ankommt oder als
   Jungler/Roamer auf dich zuläuft, kommt zum Kämpfen.
3. **„Menge der Ankommenden“ (7.5):** gerechnet gegen alle, die sichtbar in 1500 stehen oder im Fenster
   wahrscheinlich da sind (p_da ≥ 0,5) – nicht nur die Sichtbaren in 1500 (9:04: einzeln gerechnet war jeder der
   drei „schwächer“).
4. **ZURUECK:** zwei Fassungen (nur raus / raus, dann back), die bessere zählt; `[gefahr] rueckzug_faktor = 0.6` auf
   den Weg; mit Back zählt der Kanal danach am sicheren Ort mit (sonst war „erst raus“ fast immer besser als
   BACK_JETZT, gegen `k-back-40-prozent`). Der Grund ist, wer dich beim Bleiben tötet; stehst du schon dort:
   „Bleib an …“.
5. **WELLE_REIN_UND_BACK bei GECRASHT_BEI_IHM** (Buch 1, 3.2 zählt es dazu) ist BACK_JETZT (Buch 3, 2 und die Lage
   `k-back-bei-crash` mit `darf_nicht`): der erste Schritt ist schon erledigt.
6. **GEGNER_ZURUECK** (Buch 3, 1) gilt auch bei ZU_IHM/MITTE, nicht nur gecrasht – sonst hat „Sett ist gebackt:
   Welle rein, Platte, dann back“ (4.3, Lage `k-gegner-gebackt`) keinen Back-Grund.
7. **TP zur Lane (4.1):** Die Regel „kein Objective innerhalb der TP-Abklingzeit“ (300 s) widerspricht dem Beispiel
   im selben Kapitel („Drache erst in 4 Minuten“) und der Lage `k-tp-zur-lane` (250 s). Entschieden: das TP muss
   zum Kampf ums Objective zurück sein – Spawn + `tp_objective_nachlauf_s` (60) ≥ Abklingzeit.
8. **Kritisches Leben** (`[recall] leben_kritisch = 0.3`, Riven-Lexikon „außer Leben < 30 %“): kein
   WELLE_REIN_UND_BACK, BACK_JETZT unabhängig von der Welle (094832, 4:26: „Welle rein“ bei 11 %).
9. **Kaufplan nach dem Kern-Build:** Bei fertigem Kern kannte der Kaufplan kein Item mehr (3004: 3007 Gold, kein
   Kauf-Satz). Jetzt die Lexikon-Zeile „Item 4–6“, bei vollem Inventar mit „Verkauf <Start-Item>“ davor
   (`kaufplan.folge`).
10. **Minimap-Farben sind relativ** (Wahrnehmung, gefunden bei der Eichung): dein Team ist blau, der Gegner rot –
    der Code las blau als Team ORDER. Auf der roten Seite waren dadurch eigene und gegnerische Vasallen vertauscht
    (samt Richtung der Front), die Platten-Ziffern wurden in der falschen Farbe gesucht, und bei doppelten Champions
    kippte die Zuordnung. Behoben an den Einstiegen (`welle.zustaende(…, mein_team)`, `Plattenleser.lies_karte(…,
    mein_team)`, `lage.zuordnen`); dahinter heißt blau weiter ORDER. Test `minimap_farben_relativ`. Alte Aufnahmen
    der roten Seite: Wellen stimmen beim Nachspielen, aufgezeichnete Platten nicht.
11. **Wiederholen:** derselbe Plan (Art + Ziel) nicht vor 60 s erneut (`[sprechen] wiederholen_s`), dieselbe Warnung
    vor denselben Gegnern nicht vor 30 s (`gefahr_wiederholen_s`); in der Basis vor 1:00 schweigt der Kern
    (Spielbeginn, Briefing). Sonst lag die Lane-Phase über 1 je 30 s (6:47/6:59 zweimal „Stapel …“).
12. **Erinnerung (8.2 Punkt 5)** nur, wo „nicht ausgeführt“ messbar ist: BACK (nicht in der Basis und du läufst herum)
    und ZURUECK (Gefahr besteht, du bist nicht am sicheren Ort, der Weg wurde nicht kürzer).
13. **Bestätigungen:** „Pünktlich zurück“ fehlt (braucht die Ankunft der Welle am Turm); die Stärken stehen im Kern
    (`Kern.staerken`) und in `_kern.jsonl`, das Review nimmt sie ab Schritt 7.
14. **STAPELN** nur vor einem Objective auf deiner Seite; der zweite Auslöser („der Plan sieht einen Back oder Roam in
    60–90 s vor“) fehlt – es gibt noch keinen Plan, der so weit vorausschaut.
15. **Welle (1.2):** Trend nur über den letzten zusammenhängenden Abschnitt (`front_sprung = 0.12`), s. Eichung.
16. **`kern.toml`-Schlüssel, die nicht im Buch stehen** (alle so markiert): `[gefahr] kampf_ohne_anlauf`,
    `rueckzug_faktor`; `[sprechen] wiederholen_s`, `gefahr_wiederholen_s`; `[welle] lane_laenge_mid`,
    `vasallen_tempo`, `freeze_stabil_s`, `leer_ab_s`, `front_sprung`; `[recall] tempo_bonus`, `voll_ab`, `rueckweg_s`,
    `leben_kritisch`, `tp_objective_nachlauf_s`, `tp_abklingzeit_s`, `basis_warten_s`, `basis_wieder_s`,
    `basis_hoechstens`, `kauf_sprung`.
17. **Einfluss auf eine laufende Partie:** Carlos spielte 140253, während Schritt 3 entstand. Sein Coach lief seit
    13:39 im Stand von Schritt 2; spät geladene Module (`sperre`, `kaufplan`, `kern.toml`) kamen im neuen Stand,
    sind aber mit dem alten Ablauf verträglich (die Sperre ohne `kern_spricht`, der Kaufplan mit mehr Items). Der
    Kern selbst sprach nicht mit.

---

## Schritt 2 – Modus und Sofortmaßnahmen am alten System (27.09.2026)

### Umgesetzt

- `lolcoach/kern/`: `Kern` (ein Objekt je Partie), `merkmale.py` (Bereich, Lane-Phase, Verlauf 20 s, Leben-Trend,
  im Kampf, alle Objectives mit eigener Laufzeit, Mitspieler an/zur Grube, Fenster der Gegner, Bedrohung eigener
  Strukturen, frische Daten), `modus.py` (neun Modi, Priorität, Hysterese 1,5 s), `sperre.py` (Kapitel 14).
  `bewertung.verteidiger_ab` aus `ziele` herausgezogen und von Kern und `ziele` gemeinsam genutzt.
- `wissen/kern.toml`: [modus], [sprechen]; dazu vorgezogen [gefahr] (nur Kill-Beleg) und [objective_wert].
- Modus auf dem Dashboard (Kasten „Modus“ mit Grund und den INFO-Zeilen), in `aufnahmen/<stamm>_kern.jsonl` (live,
  je Takt: Zeit, Modus, Grund, Bereich, Lane-Phase, Kampf, frisch) und als erste Zeile jeder Claude-Frage
  („MODUS: BASIS - du stehst in eurer Basis“).
- Modus-Sperre der alten Regeln nach Kapitel 14 (`Regelwerk.pruefe` → `sperre.entscheide`: sprechen / info / stumm);
  Einwürfe des Strategen (außer Briefing) nicht in KAMPF und nicht 10 s nach einer Gefahr.
- Objective-Fehler (1.3 Punkt 5): Auswahl nach Erreichbarkeit und Wert (`Regelwerk._objective_waehlen`), die
  Laufzeit immer zum genannten Objective (`komponist.zahlen/jungler_tot(..., weg=)`).
- Team-Befehle nur, wenn du rechtzeitig dort bist; sonst „Dein Team kann … nehmen – du bist N s weg“ + dein Ziel,
  bzw. statt „Drückt jetzt den X-Turm“ dein eigenes Ziel.
- Kill-Ruf nur mit Beleg (`denker.kill_beleg`, 6.2): Combo reicht / Leben ≤ 1 s alt / `kraefte()[0]` ≥ 3,0; sagt die
  Rechnung „reicht (knapp) nicht“, kein Kill. Gesagt wird der eine Beleg.
- Budget im Sprechplan: `abstand_s` (12 s) für alles außer SOFORT und Briefing; INFO (Flash, Items, Level, CS)
  aufs Dashboard, gesprochen nur Lane-Gegner/Jungler in LANE/SEITE.
- Claude-Kontext: Modus zuerst; „Deine letzten Ansagen“ nur, wenn die Frage darauf zeigt, dann nur die letzte;
  Lane-Gegner, Lane-Welle und Kampf-Urteil nur in LANE/SEITE oder mit dem Lane-Gegner ≤ 3500.
- `--kern schatten` geht jetzt (in Schritt 2 gleich `alt`), `--kern neu` bricht mit Hinweis ab.
- Werkzeuge: `nachspielen` fährt den Kern mit (Modus je Takt) und zählt Kehrtwenden nach der neuen Regel
  (Carlos' Entscheidung, Kapitel 9.4 Punkt 5); `szenarien.py` prüft `modus` und `[[modus_soll]]`.
- Tests: `modus_sperre_budget` (Modus, Sperre, INFO, Budget, Frage-Bezug); `denkkette` und
  `von_deiner_position_aus` an die neuen Regeln angepasst (Kill ohne Beleg ist Trade; Team-Befehl nur rechtzeitig).

### Abnahme Schritt 2 (102112)

| Abnahme | Soll | Ist |
|---|---|---|
| Modus-Sollwerte (5.3) | ≥ 90 % | **16 / 16 (100 %)** |
| `darf_nicht_sagen` 2522, 2847, 3535, 3004 | grün | **alle grün** (3004 rot nur an `muss_item` der Frage – Pflicht ab Schritt 6) |
| 2601 (Frage „To-do“, Pflicht erst Schritt 6) | sollte grün werden | **grün** („Push den äußeren Mid-Turm, in 16 s bei dir …“) |
| ungefragte Ansagen je 30 min | ≤ 70 | **61** (Stand Schritt 1: 111) |
| Kehrtwenden | ≤ 4 | **3** (Stand Schritt 1, neu gezählt: 6) |
| Generalprobe | läuft | **läuft** (Coach spricht, `_kern.jsonl` wird geschrieben) |
| `tests/alle.py` | grün | **grün** |

Szenarien 102112, altes System mit Schritt 2: ohne Claude 9 grün / 10 geprüft (rot: 3632), mit Claude 9 / 12
(rot: 3004 `muss_item`, 3632, review-102112). 3632 („Ende statt back“) ist Abnahme von Schritt 4.

### Kennzahlen (altes System, Stand Schritt 2; Kehrtwenden nach der neuen Regel)

| Aufnahme | ungefragt (je 30 min) | „… bei dir“ | Flash | Kehrtwenden | 9.4: 1 / 2 / 3 / 4 / 7 |
|---|---|---|---|---|---|
| 2026-09-26_235433 | 28 (74) | 3 | 1 | 0 | 4 / 0 / 0 / 0 / 0 |
| 2026-09-27_001155 | 9 (29) | 2 | 0 | 0 | 1 / 1 / 0 / 0 / 0 |
| 2026-09-27_094832 | 16 (71) | 3 | 1 | 0 | 2 / 0 / 0 / 0 / 0 |
| 2026-09-27_101832 | 1 (27) | 0 | 1 | 0 | 0 / 0 / 0 / 0 / 0 |
| 2026-09-27_102112 | **62 (61)** | 11 | 1 | **3** | 2 / 0 / 0 / 0 / 0 |

Zum Vergleich 102112 im Stand von Schritt 1 (fd59e03), mit denselben Werkzeugen und der neuen Kehrtwenden-Regel
gemessen: 112 (111 je 30 min), „… bei dir“ 22, Flash 23, Kehrtwenden 6, 9.4: 6 / 0 / 0 / 0 / 1.

### Abweichungen vom Buch und Entscheidungen

1. **Modus-Tabelle mit den echten Regeln nachgerechnet (5.3)** – zwei Zeitpunkte lagen daneben, entschieden nach
   der Kernfrage:
   - **5:17 KAMPF statt LANE:** Riven kämpfte 5:06–5:16 gegen Sett (94 % → 27 %); Sett starb, KAMPF lief die 3 s
     Nachlauf. Entscheidung: KAMPF endet sofort, wenn kein lebender Gegner mehr in `kampf_radius` ist – dann ist
     die Kernfrage „rein, halten, raus?“ beantwortet. `kampf_ende_s` gilt nur, solange noch einer da ist.
   - **36:32 OBJECTIVE statt GRUPPE/UNTERWEGS:** Baron lebte seit 20:00; ≤ 25 s von einer Grube ist man von der
     Mid-Lane fast immer. Entscheidung: „du stehst an der Grube“ heißt in der Grube – oder ≤ `objective_nah_s`
     **und** genug von euch können in dieser Zeit dort sein (`mindestens`: Baron 3, sonst 2), sonst stellt sich die
     Kernfrage „nehmen, bestreiten, abgeben, tauschen?“ nicht. Aus der Basis heraus nie (der Heimweg-Schub macht
     die Laufzeit klein). Ein Mitspieler an der Grube genügt weiter.
2. **Modus ohne bekannten Ort = kein Modus** (4.3 „nicht raten“): die Generalprobe sah die Minimap kaum; ohne Ort
   fiel der Modus sonst auf UNTERWEGS und die Lane-Regeln wären stumm gewesen. Ohne Modus gilt keine Sperre.
3. **`kern.toml` enthält Schlüssel, die nicht im Buch stehen** (alle als „nicht im Buch“ markiert):
   `grube_radius`, `verteidigen_radius/_weg_s/_welle_front`, `kampf_leben_trend`, `kampf_balken_faellt`,
   `minimap_frisch_s`, `kill_leben_frisch_s`, `[objective_wert].mindestens` und `.dauer_s`. [gefahr] enthält nur den
   Kill-Beleg, [objective_wert] ist vorgezogen, weil die Objective-Auswahl nach Wert ihn braucht.
4. **Objective-Auswahl:** erreichbar = dein Weg + geschätzte Tötungszeit (`dauer_s`) passen vor den ersten Gegner
   an der Grube (`verteidiger_ab`; nicht das Todesfenster der Regel), und genug von euch sind bis dahin dort.
   In 102112 um 25:22 ist dadurch **kein** Objective wählbar (Baron klar nicht, der Drache 0,5 s über dem Fenster
   gegen Sett im schlimmsten Fall) – der Coach sagt „Drückt jetzt den äußeren Mid-Turm …“. Das `soll` des
   Szenarios (Drache nehmen) kommt mit Schritt 5 (Kampflage, Buch 6), nicht über einen angepassten Startwert.
5. **Budget und Frische:** Schritt 2 verlangt `abstand_s` = 12 s, die alte Frische-Grenze erlaubt WICHTIG nur
   10 s Warten – eine Ansage direkt nach einer anderen hätte nie kommen können. Nach 9.2 („gesagt, sobald wieder
   Platz ist und er dann noch gilt“) darf, wer nur am Budget wartet, `abstand_s` länger warten; ob er noch stimmt,
   prüft weiter seine Prüfung.
6. **INFO nach der Tabelle in Kapitel 14** (Flash des Lane-Gegners/Junglers auch in SEITE), nicht nur „in LANE“
   wie in der Kurzfassung von Schritt 2. `aufbruch` (Kauf beim Verlassen der Basis) gilt als KAUFEN, nicht als
   Lane-Info von `_items`.
7. **Sicherer Ort (7.5) vorgezogen:** Rückzug zum nächsten von Turm, Basis oder eigener Gruppe (≥ 2 Mitspieler
   beieinander) – nötig für die Abnahme von 3535 („Top-Tier-3-Turm, 31 s“, drei Mitspieler 8 s entfernt).
8. **Stratege „nicht in GEFAHR“** vor dem Kern (Schritt 3) genähert: 10 s nach einer Ansage mit Thema „gefahr“.
9. **`_kern.jsonl` nur live** (neben der Aufnahme); Nachspielen schreibt keine, damit es das Live-Protokoll nicht
   überschreibt.
10. **3004 `muss_item`:** Claude nannte „Lord Dominiks Ring“ – kein Name aus der Ladenliste. Frage-Teil, Pflicht in
    Schritt 6 (Kauf aus dem Kern).

---

## Schritt 1 – Messen, nichts am Verhalten ändern (27.09.2026)

### Umgesetzt

- `werkzeuge/nachspielen.py`: gemeinsame Grundlage – Aufnahme durch `Regelwerk` + `Sprechplan` (stumm) wie live,
  je Takt Leben, sichtbare Gegner, Kills, Objectives (für Kehrtwenden), Datenlücken, Proben für die Gefahr-Eichung.
- `werkzeuge/szenarien.py`: Szenarien gegen das alte System (nur Text: `darf_nicht_sagen`, `muss_nennen_eins`,
  `muss_ziel`, `kehrtwenden_max`, `ansagen_max`). Kern-Teile (`modus`, `soll`, `darf_nicht`, `[[modus_soll]]`)
  stehen als „übersprungen“. `--mit-claude` stellt die `frage` über den alten Antwortweg (sofort, sonst Claude
  mit Spielakte und Bildschirm des Moments) und prüft das gespeicherte Review. `--lage` zeigt die nachgespielte
  Lage je Szenario.
- `werkzeuge/kennzahlen.py`: je Aufnahme ungefragte Ansagen je 30 min, Ankunfts- und Flash-Ansagen, Kehrtwenden,
  Verstöße gegen 9.4 (1, 2, 3, 4, 7; 5 = Kehrtwenden; 6 erst mit Kern), Brier des schlimmsten Falls, Datenlücken,
  Szenario-Quote. `sinnpruefung.py` geht darin auf.
- `werkzeuge/szenario_aus_notizen.py`: 18 Stubs aus 4 Aufnahmen mit Notizen in `tests/szenarien/offen/`
  (212105: 1, 230520: 5, 235433: 2, 102112: 10).
- Wachhund nach Wanduhr (`lolcoach/wachhund.py`, Kapitel 4.3): nach 20 s ohne Schnappschuss bei offenem
  Spielfenster einmal „Ich sehe das Spiel gerade nicht – ich melde mich, sobald die Daten wieder da sind.“, bei
  Rückkehr „Ich sehe das Spiel wieder.“; jede Lücke in `aufnahmen/<stamm>_luecken.jsonl`. Ein Neustart des
  Coachs mitten in der Partie (Aufnahme fortgesetzt) wird dort ebenfalls als Lücke eingetragen.
  Test: `wachhund_meldet_datenluecke`.
- `--kern alt|schatten|neu` an `live` und `abspielen`; bis Schritt 2 nur `alt` (die anderen brechen mit Hinweis ab).
- `CLAUDE.md` (Verweis auf `buecher/`, Arbeitsweise Beschwerde → Szenario → Modelländerung, `--kern`, neue
  Werkzeuge), `OFFEN.md` („In Arbeit: Buch 0, Schritt 1“, ersetzte Punkte markiert).

### Datenlücke 15:55–24:24 in 102112: geklärt

Kein API-Fehler, kein Absturz: **der Coach wurde von Hand beendet.**

- Letzter Schnappschuss 10:37:06, nächster 10:45:34 (Wanduhr). Die Spielbilder (`schirm_*.jpg`) enden 10:37:09
  und beginnen 10:45:35 – der ganze Prozess war weg, nicht nur die API.
- `aufnahmen/absturz.log` (faulthandler): kein Absturz, neue Startzeile „Coach gestartet 10:45:33“.
- Letzter Tastendruck vorher 15:38 („Wo soll ich reingehen?“ vierfach erkannt). Carlos schrieb in dieser Zeit
  „ich musste den Coach ausmachen, der hat … mal hintereinander gesagt geh rein geh rein“ – die Schleife der
  Stimme (ein unterbrochener Satz kam nach jedem Tastendruck wieder).
- Behoben ist die Ursache schon: Commit 93f4fee (10:44, eine Minute vor dem Neustart), „Sprechtaste ist
  Stummtaste“ – unterbrochene Sätze werden nicht mehr wiederholt.
- Neu: der Wachhund (oben). Für diesen Fall (Coach aus) greift der Eintrag beim Neustart.

### Grundlinie (altes System, die 5 jüngsten Aufnahmen)

| Aufnahme | Minuten mit Daten | ungefragt (je 30 min) | „… bei dir“ | Flash | Kehrtwenden | 9.4: 1 / 2 / 3 / 4 / 7 | Brier schlimmster Fall (Proben, Grundrate) | Lücken > 5 s |
|---|---|---|---|---|---|---|---|---|
| 2026-09-26_235433 (Bots) | 11,3 | 40 (106) | 4 | 7 | 0 | 4 / 0 / 0 / 0 / 0 | 0,198 (1774, 0,157) | keine |
| 2026-09-27_001155 (Bots) | 9,2 | 18 (58) | 2 | 5 | 0 | 1 / 1 / 0 / 0 / 0 | 0,213 (456, 0,636) | keine |
| 2026-09-27_094832 (Bots) | 6,8 | 22 (97) | 4 | 3 | 0 | 1 / 0 / 0 / 0 / 0 | 0,229 (1351, 0,149) | keine |
| 2026-09-27_101832 | 1,1 | 2 (54) | 0 | 2 | 0 | 0 / 0 / 0 / 0 / 0 | 0,308 (52, 0,327) | keine |
| 2026-09-27_102112 (Bots) | 30,4 | **112 (111)** | **22** | **23** | 4 | 6 / 0 / 0 / 0 / 1 | 0,317 (6307, 0,105) | 0:04–0:11, 6:53–6:59, **15:55–24:23 (508 s)** |

Ziel laut Buch: ≤ 45 ungefragte Ansagen je 30 min. GEFAHR / PLAN / ERINNERUNG und `p_da` gibt es erst mit dem
Kern (Schritt 3); der Brier des schlimmsten Falls ist die Latte, die `p_da` dann unterbieten muss.
101832 ist ein Bruchstück von einer Minute (Coach vor der Partie neu gestartet).

### Szenarien 102112, altes System

| Szenario | ohne Claude | mit `--mit-claude` | Grund |
|---|---|---|---|
| 0517-platte-ohne-flash | rot | rot | 5:17 „… nimm die Platte mit“ |
| 0850-kein-hin-und-her | grün | grün | 1 Kehrtwende im Fenster (9:00 → 9:04, erlaubt: 1) |
| 0904-drei-kommen | rot | rot | 9:24 „Bleib an deiner Welle, … zusammen schwächer als du“ |
| 2522-kein-baron-drache-lebt | rot | rot | 25:22 „Nehmt jetzt Baron Nashor“ |
| 2601-frage-to-do | übersprungen | grün | „Push den äußeren Mid-Turm, in 21 s frei …“ (kein Sett) |
| 2847-baron-statt-drache | grün | grün | kein „Baron“ im Fenster (Team-Ruf-Grenze seit 1b5b60f) |
| 3004-basis-kauf-und-ziel | übersprungen | grün | nennt Kontroll-Auge und Top-Lane – inhaltlich dünn („rüste auf“) |
| 3100-basis-braucht-ziel | rot | rot | 30:56 „Geh zurück zu deiner Basis“ – in der Basis |
| 3500-drache-solo | übersprungen | grün | „Drache: ihr 2 in 15 Sekunden dort, sie 0 – nehmen.“ (Riven steht an der Grube: „15 s“ stimmt nicht) |
| 3535-rueckzug-31s | rot | rot | 35:35 „… zu deinem Top-Tier-3-Turm, das sind 31 Sekunden“ |
| 3632-ende-statt-back | rot | rot | 36:32 „Geh jetzt back, du hast 4400 Gold.“ |
| review-102112 | übersprungen | rot | Lücke nicht genannt; Lektion 1 „Kein Kontroll-Auge“; 17:19 „während du durchgehend oben standest“ |
| **Quote** | **2 / 8** (6 rot) | **5 / 12** (7 rot) | |

Modus-Sollwerte (16 Zeitpunkte): übersprungen, der Modus kommt in Schritt 2.

### Abnahme Schritt 1

- Läufer laufen: ja (`szenarien.py`, `kennzahlen.py`, `szenario_aus_notizen.py`).
- Grundlinie eingetragen: ja (oben).
- Das alte System fällt bei mindestens 6 der 102112-Szenarien durch: **ja, 6 von 8 ohne Claude** (7 von 12 mit).
- `tests/alle.py` grün: ja.

### Abweichungen vom Buch

1. **Kehrtwenden in 102112: 4 statt 8 (Kapitel 1.2).** Gezählt nach 9.4 Punkt 5 wörtlich: vor ↔ zurück in ≤ 30 s,
   Paare mit neuem Ereignis dazwischen fallen heraus. Ohne diesen Filter sind es 13 (9 davon mit Ereignis).
   Die Zählweise hinter der 8 steht nicht im Buch. Der Filter ist großzügig: „neuer Gegner sichtbar“ trifft in
   dichten Phasen fast immer zu (9:04 → 9:24 zählt deshalb nicht). Entscheidung: Zählung nach 9.4 wörtlich
   beibehalten. Vorschlag für Schritt 2: als neues Ereignis nur einen Gegner zählen, der in ≤ 3000 um dich
   auftaucht.
   **Entschieden (Carlos, vor Schritt 2):** der Vorschlag gilt – als neues Ereignis zählt nur ein Gegner, der in
   ≤ 3000 um dich neu sichtbar wird (in den 5 s davor nicht sichtbar). Eingetragen in Kapitel 9.4 Punkt 5, umgesetzt
   in `werkzeuge/nachspielen.neues_ereignis`.
2. **Szenario-Lagen nachgespielt, vier kleine Korrekturen** in `tests/szenarien/2026-09-27_102112.toml`:
   0517 Flash noch ~59 s (HUD) statt ~48 s; 2522 Ort „unten“ (Minimap), Galio stirbt genau in diesem Takt;
   3100 um 30:30 noch 3240 Gold, Kauf gegen 31:00; 3632 Brand „unten“ statt im eigenen Jungle. Alle anderen
   Lagen stimmen (Abstände ±150, Zeiten ±1 s).
3. **3500: `muss_nennen_eins` um „nehmen“ ergänzt.** Die Antwort „… sie 0 – nehmen.“ ist inhaltlich ein Ja; die
   Liste kannte nur „Ja/nimm/mach“. Der Fehler in derselben Antwort („ihr 2 in 15 Sekunden dort“, Riven steht an
   der Grube) wird damit nicht geprüft – er gehört in Schritt 5 (`fenster_gegner`, Objective-Dauer).
4. **Review mit `--mit-claude`:** geprüft wird das gespeicherte Review der Partie, kein neu erzeugtes (spart
   ~2 min Claude je Lauf). Für Schritt 7 muss der Läufer das Review neu erzeugen.
5. **9.4 Punkt 2 ohne Modus genähert:** „Lane-/Wellenbefehl außerhalb LANE/SEITE“ = du stehst weder auf deiner
   Lane noch (nach 14:00) auf einer Seitenlane; „an deiner Welle – geh hin“ zählt als Weg. Mit dem Modus aus
   Schritt 2 wird das exakt.
6. **`p_da`-Brier:** bis Schritt 3 nur der schlimmste Fall (p = 1, wenn früheste Ankunft ≤ 10 s). Wahrheit: der
   Gegner war in den nächsten 10 s **sichtbar** in 1500 um dich – wer ungesehen kam, zählt nicht (Grenze der
   Messung). Proben: je Sekunde jeder lebende Gegner mit bekannter frühester Ankunft; `p_da` muss in Schritt 3
   auf denselben Proben gemessen werden.
7. **Stub 26:20 in 102112** zeigt einen möglichen Wahrnehmungsfehler: das Nachspielen sieht Riven „in eurem
   unteren Jungle“, Carlos sagte „ich bin in der Midlane an meiner Base“. Beim Beschriften prüfen.
   **Geklärt (Carlos, vor Schritt 2): kein Wahrnehmungsfehler** – Riven lief um 26:15 von der Mid-Lane in den
   eigenen unteren Jungle; das Nachspielen sieht sie um 26:20 richtig dort.
