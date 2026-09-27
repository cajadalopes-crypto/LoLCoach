# Buch 7 – Kampf und Teamkampf (als Bruiser)

Stand 27.09.2026. Dieses Buch füttert:

- `kern/kampf.py` (neu): **das eine** Kampfurteil, das Gefahr, Objectives, Duelle und der Todesrückblick benutzen
- `kern/modi/kampf.py` (Schritt 5)
- die Handlung `ANNEHMEN` in den anderen Modi
- den Todesrückblick nach Kampftoden

**Für Claude Code:**

- Lies zuerst Buch 0, Kapitel 5, 7.5, 8 und 9, Buch 6, Kapitel 3 und die Qualitätsrunde
  (`buecher/protokolle/PRUEFUNG_2026-09-27.md`).
- Champion-Werte (Reichweiten, Fähigkeiten) stehen hier nur als Startwerte für Riven. Die Bücher 8–10 ersetzen sie.
- Stellen, die andere Bücher ändern, sind mit **„Ändert …“** markiert.
- Jede Zahl steht in `kern.toml` (Kapitel 9).

---

## 0. Befund

1. **Im Kampf wird vorgelesen.** 144655, 9:15, Modus KAMPF, 19 % Leben:
   „Geh jetzt zurück zu deinem Top-Tier-1-Turm, das sind 10 Sekunden: Vex kann in 7 Sekunden da sein – du hast nur
   18 Prozent Leben.“

   Das sind 25 Wörter, etwa 8 Sekunden Sprechzeit, in einem Kampf, der in 3 Sekunden entschieden ist.

   Auch der Kern würde heute so reden. `_kandidaten` hängt in jedem Modus `ZURUECK` an. Schlägt die Gefahr an,
   bleibt nur `SICHER` übrig, also `ZURUECK` mit einem Satz bis 10 Wörter.
2. **Vor dem Kampf zu lang, im Kampf nichts.** 102112, 25:01: „Sona kommt auf dich zu, von unten. Nimm den Kampf an:
   Sona ist 5 Level und 3400 Gold unter dir.“ Der Inhalt stimmt, aber es sind drei Sätze.
3. **Kampftode ohne Lehre.** „Solo gegen Yasuo verloren. Dagegen sprach: Yasuo tötet dich schon mit einem Combo,
   mindestens 690 Schaden …“ Diesen Schaden hat niemand gemessen, und über die Entscheidung sagt der Satz nichts.
4. **Drei Kampfmodelle, keins geeicht.**
   - `gefahr.p_verliere` rechnet `kraft_gegen` mit Flucht-Faktoren.
   - `Kampflage.urteil` zählt Köpfe.
   - Buch 6 bräuchte ein drittes.
   - Ob eines davon Kämpfe vorhersagt, hat niemand an Aufnahmen gemessen.

**Nebenbefund Gegner-Werte** (Qualitätsrunde 1, bestätigt):

- Die Live-API meldet das Level der Gegner als Stand der letzten Sichtung. Belege: Kha'Zix springt in 144655 um
  3:34 von Level 1 auf 4, Brand in 140253 von 3 auf 5 und dann auf 7.
- Die AFK-Meldung „Kha'Zix ist AFK“ war deshalb falsch, und dass Claude Code die Gegner-AFK abgeschaltet hat, ist
  richtig.
- **Offen ist, ob die Items ebenso veraltet sind.** Prüfung: Ändern sich die API-Items eines Gegners bei einem Back,
  während er nicht auf der Minimap zu sehen ist (sein Brunnen ist nie sichtbar)? Wenn ja, sind sie live.
- **Folge für die Kampfkraft:** Ein lange nicht gesehener Gegner wird unterschätzt. Kapitel 3.2 schätzt deshalb nach.

## 1. Prinzipien

1. **Der Wert liegt vor dem Kampf.** Ob man einen Kampf annimmt oder vermeidet, zählt mehr als alles, was man im Kampf
   sagen kann. Der Coach sagt es, **bevor** die Gegner in Reichweite sind: `ANNEHMEN` oder `ZURUECK`, nie beides.
2. **Im Kampf: höchstens fünf Wörter, nur wenn es den Ausgang ändert.** Ein Satz im Kampf muss nach Sprechzeit plus
   Reaktion (etwa 2 s) noch stimmen. Also nur: rein, raus, umdrehen, auf wen. Als Grund höchstens ein Wort
   („fast tot“).
3. **Kein Mikro.** Combos, Animation-Cancel und Ausweichen kann der Coach nicht sehen und nicht rechtzeitig sagen.
   Nie „Flash jetzt“, nie „Q–W“.
4. **Ein Urteil für alle.** `kampf.p_gewinn` entscheidet Duell, Objective-Kampf (Buch 6), Gefahr (Buch 0, 7.5) und
   Todesrückblick. Es wird an Aufnahmen geeicht (Kapitel 3.3). Wo die Eichung nicht reicht, bleiben die Startwerte.
5. **Als Bruiser taucht man nur mit Beleg.** Riven gewinnt Kämpfe, wenn sie ein erreichbares Ziel tötet oder die Front
   zerlegt, während ihr Team folgt. Allein unter dem Turm oder gegen vier Gegner gewinnt sie nicht.
6. **Ohne Champion-Kurven ist Vorsicht Pflicht.** Solange die Bücher 8–10 fehlen, sind Riven und Gangplank auf
   gleichem Level und mit gleichem Gold gleich stark. Das stimmt oft nicht. Deshalb gibt es gegen den Lane-Gegner kein
   `ANNEHMEN` (Kapitel 4), und kein Satz behauptet, „die Zahlen sprachen für dich“.

## 2. Was der Coach im Kampf weiß

| Wissen | Quelle | Verlässlich? |
|---|---|---|
| dein Leben, Level, Items, Gold | Live-API | ja |
| deine Q W E R D F bereit | HUD (gelbe Buchstaben) | ja |
| Leben und Ult der Mitspieler | HUD-Leiste über der Minimap | ja |
| Kills, Tode, Assists aller | Ereignisse der Live-API | ja |
| Level der Gegner | Live-API | nur Stand der letzten Sichtung (Nebenbefund) |
| Items der Gegner | Live-API | ja oder nur letzte Sichtung – prüft der Nebenbefund |
| Orte aller Gesehenen | Minimap, 60 Bilder/s | ja, mit Verdeckung |
| Leben der Gegner | Lebensbalken im Spielbild (`lage.gegner_leben`) | nur auf dem Bildschirm, bis zu drei, ≤ 2,5 s alt (`lage.gegner_leben_jetzt`) |
| Flash und Ult der Gegner | `zauber`, Minimap-Sprünge, Chat | lückenhaft (Qualitätsrunde F2) |
| Klasse eines Champions | Data Dragon `tags` (Marksman, Mage, Tank, Fighter, Assassin, Support) und Angriffsreichweite | ja |
| Abklingzeiten der Gegner außer Flash und Ult; wer wen angreift | – | nein |

**Folge:**

- Ein Urteil beruht nur auf den Zeilen mit „ja“ oder „lückenhaft“.
- Unbekannt heißt neutral (Faktor 1), nie „schlimmster Fall“.
- Beide Seiten werden **gleich** behandelt. Was bei euch bekannt ist, aber beim Gegner fast nie, darf das Urteil nicht
  einseitig verschieben (Kapitel 3.2, Ult).

## 3. Das Kampfurteil (`kern/kampf.py`)

### 3.1 Eine Funktion

```python
def p_gewinn(m, ort, fenster_s: float, gewichte: dict | None = None) -> tuple[float, dict]:
    """Wahrscheinlichkeit, dass eure Seite einen Kampf um `ort` gewinnt, und die Aufschlüsselung
    (wer auf welcher Seite, mit welcher Kraft) für Satz, Protokoll und Todesrückblick."""
```

- **Eure Seite:** du, dazu jeder lebende Mitspieler, der in `fenster_s` bei `ort` sein kann. Mitspieler zählen zu
  `mitspieler_anteil`.
- **Ihre Seite:**
  - Jeder Gegner mit Gewicht. Standard ist `p_da(g, fenster_s, ort)` (Buch 6, 3.1).
  - Sichtbare Gegner in `kampf_radius` um `ort` zählen mit 1.
  - `gewichte` überschreibt das, zum Beispiel für „nur dieser eine Gegner kommt“.
- `fenster_s`:
  - Kampf, Duell, ANNEHMEN: `[kampf].fenster_s` (6 s)
  - an einer Grube: `[objective].kampf_fenster_s` (15 s)

**Ändert `gefahr.py` (Buch 0, 7.5):**

- `p_verliere(S) = 1 − p_gewinn(m, ort = dein Ort, fenster_s = T, gewichte = {g: 1 für g in S})`, also bedingt
  darauf, dass die Menge S wirklich kommt. Das `p_da` steckt schon in der äußeren Formel von `p_tod`. Es wird nicht
  ein zweites Mal gewichtet.
- `flucht_flash` bleibt als Faktor auf `p_tod`.
- `flucht_turm` fällt weg, weil der Turm jetzt in `K` steckt (`turm_faktor`). Sonst zählt er doppelt.

### 3.2 Die Formel

```
kraft_i = kraft(s, leben)                 # heute: 1,10^(Level−1) · (1 + Item-Gold/2500) · Leben (unbekannt 0,9)
          · ult_faktor                    # für BEIDE Seiten gleich: bekannt weg (Level ≥ 6) 0,8; sonst 1,0
          · flash_faktor                  # bekannt weg 0,95; sonst 1,0
          · faehigkeiten_faktor           # nur du: Kern-Fähigkeiten laut HUD weg (Riven: E und W) → 0,75
K       = Σ_wir kraft_i · anteil_i / Σ_die kraft_j · gewicht_j
K      *= turm_faktor,   wenn ort ≤ turm_radius von EUREM stehenden Turm
K      /= turm_faktor,   wenn ort ≤ turm_radius von IHREM stehenden Turm
p_gewinn = K^k / (1 + K^k)                # k = [kampf].k (Start 2, wie gefahr.kampf_exponent – EIN Wert)
```

- `leben`: für dich aus der API, für Mitspieler aus der HUD-Leiste, für Gegner der Balken, wenn er ≤ 2,5 s alt ist.
- **Veraltete Gegnerwerte:** Wurde ein Gegner seit > `unsichtbar_s` (60 s) nicht gesehen, geht er mit
  `level = max(API-Level, Median-Level eures Teams − level_abschlag)` in `kraft` ein. Sind auch die Items veraltet
  (Nebenbefund), gilt entsprechend `item_gold = max(API, Median-Item-Gold eures Teams · item_anteil)`. Das gilt auch
  für `bewertung.kraefte()` gegen den Lane-Gegner.
- `turm_radius` = `bewertung.TURM_REICHWEITE` (775). Es gibt keinen zweiten Radius.
- Die Faktoren 0,8, 0,95, 0,75 und 1,5 sind Schätzungen. Kapitel 3.3 eicht sie oder setzt sie auf 1.

### 3.3 Eichen an den Aufnahmen (`werkzeuge/kampf_eichung.py`, neu; Pflicht vor der Abnahme)

1. **Entscheidungspunkte, nicht Kampfbeginn.**
   - Eine Probe entsteht, wenn sich ein Gegner und du (oder ein Mitspieler ≤ 1500 von dir) erstmals auf ≤ 1500
     nähern, nach ≥ 10 s ohne solche Nähe.
   - `p_gewinn` wird **dort** gerechnet, vor dem Einstieg, genau wo ANNEHMEN und ZURUECK entscheiden.
2. **Ausgang in den nächsten 15 s:**
   - Kill-Gold eurer Kills minus Kill-Gold eurer Tode (`bewertung.kill_gold`).
   - Gewonnen ist > 0, verloren < 0.
   - Ohne Tod auf beiden Seiten ist die Probe „offen“. Offene Proben werden gezählt und als Anteil ausgewiesen, sie
     gehen aber nicht in den Brier-Wert ein.
3. **Nur echte Partien** (`bots = false`).
4. **Arten** nach Gesamtzahl der Beteiligten: 2 (Duell), 3–6, ≥ 7.
5. **Faktoren wählen** (`k`, `ult_faktor`, `turm_faktor`, `mitspieler_anteil`):
   - Ein Parameter wird nur verändert, wenn ≥ `eichung_min` (30) entschiedene Proben vorliegen.
   - Liegt ein Faktor nicht messbar besser als 1, bleibt er 1.
6. **Ergebnis in messungen.md:** Brier je Art, Fallzahl und Anteil „offen“. Soll: Brier < 0,20 und besser als die
   Grundrate.
   Dazu eine Tabelle aller entschiedenen Proben mit Uhrzeit, damit Carlos und ich einzelne nachsehen können.

## 4. Vor dem Kampf: `ANNEHMEN` oder `ZURUECK`

Kommt ein sichtbarer Gegner oder eine Gruppe auf dich zu (`kommt_naeher`, ≤ `annehmen_abstand` 2500), wird **eine**
Frage gestellt:

```
p = kampf.p_gewinn(m, dein Ort, [kampf].fenster_s)     # alle, die in 6 s dazukommen können, beide Seiten
p ≥ annehmen_p_min und alle Bedingungen unten  →  ANNEHMEN ist Kandidat, ZURUECK wegen dieser Gegner NICHT
sonst                                          →  ZURUECK wie bisher (Gefahr-Modell), ANNEHMEN nicht
```

**Bedingungen für ANNEHMEN**, alle müssen gelten:

- Nicht gegen deinen Lane-Gegner in LANE. Das bleibt `TRADE` bzw. `ALL_IN` mit Kill-Beleg (Buch 0, 6.2) und kommt mit
  Buch 2.
- Nicht, wenn deine Lane verloren ist (`kraefte()[0] ≤ −1` oder ≥ 2 Tode gegen ihn).
- Nicht, wenn die Kampfmitte in `turm_radius` ihres stehenden Turms liegt. Tauchen gibt es nur als `REIN` im Kampf
  (Kapitel 6).
- Ihr Jungler ist tot, wurde vor ≤ `jungler_sicher_s` (20 s) auf der anderen Kartenseite gesehen, oder
  `p_da(Jungler, 10 s) < jungler_p_max` (0,2).
- Dein Leben ist ≥ `annehmen_leben_min` (0,5).
- Deine Kern-Fähigkeiten sind laut HUD bereit (Riven: E und W).

**Handlung:**

- `Handlung("ANNEHMEN", Ziel("gegner", name, pos, weg), p_erfolg=p, gewinn=kill_gold(g), daten={"kampf_mit": g})`
- Der EV kommt aus `wert.bewerte`, wie bei jeder Handlung.
- Kategorie **GEFAHR**: Die Ansage darf unterbrechen, zählt nicht zum Budget und braucht kein `halten_s`. Das ist die
  Umkehrung derselben Frage.

**Ändert:** `ANNEHMEN` und `DREHEN` kommen in `handlung.VOR` und in Buch 0, 9.4, Punkt 5.

**Satz:**

- Höchstens 8 Wörter, der Name zuerst: „Sona allein: nimm den Kampf.“ „Zu zweit gegen Fiddlesticks: rein.“
- Ein Grund nur, wenn er in drei Wörtern geht: „… sie ist fast tot“.
- Level und Gold stehen auf dem Dashboard, nicht im Satz.
- Höchstens einmal je Gegner und `annehmen_wiederholen_s` (60 s).

## 5. Im Kampf: Modus KAMPF (`kern/modi/kampf.py`)

**Ändert Buch 0, 6.3 und `Kern._kandidaten`:**

- In KAMPF gibt es kein `ZURUECK`, dafür `RAUS`.
- Der Gefahr-Filter (`gefahr_schlaegt_an` → nur `SICHER`) gilt in KAMPF nicht.
- Gewählt wird nach der Tabelle 5.1, nicht nach EV und nicht über den PlanFuehrer.
- Der Kampf hat einen eigenen Zustand: aktuelle Ansage, Ziel, Zeit und Zahl der Ansagen in dieser Episode.

### 5.1 Handlungen

| Art | Wann | Satz (≤ 5 Wörter) |
|---|---|---|
| `REIN` | `p_gewinn ≥ rein_p_min` (0,65) **und** ein Ziel in Reichweite (5.2) | „Rein auf Jinx!“ · „Rein, Yasuo fast tot!“ |
| `RAUS` | `p_gewinn ≤ raus_p_max` (0,35) **und** Flucht möglich (5.3) | „Raus, zum Turm!“ · „Raus zu Tryndamere!“ |
| `DREHEN` | du bewegst dich weg, genau ein Verfolger ≤ `drehen_abstand` (1000), sein Leben ≤ `drehen_gegner_leben` (0,4, Balken), deins ≥ `drehen_eigen_leben` (0,35), `p_gewinn` gegen ihn allein ≥ `drehen_p_min` (0,65), kein zweiter Gegner sichtbar in `drehen_frei` (1500) und `p_da(Jungler, 6 s) < 0,2` | „Dreh um, Yasuo fast tot!“ |
| `HALTEN` | alles andere | – (stumm) |

**Kein Fluchtweg:** Ist die Flucht nach 5.3 nicht möglich, gilt `REIN` auf das tötbarste Ziel, auch bei kleinem
`p_gewinn`. Wer ohnehin stirbt, soll dabei etwas mitnehmen. Satz: „Rein auf Jinx!“

### 5.2 Ziel-Wahl (Bruiser)

Reichweite: `reichweite_rein` des Champions (Riven 650), mit Flash bereit plus `flash_zusatz` (400). Die Werte stehen
in `[kampf.champion]`, die Bücher 8–10 ersetzen sie.

1. **Tötbar:** Leben laut Balken ≤ `toetbar_leben` (0,3; bei Tag `Tank` 0,2).
2. **Sonst ein Carry:** ein sichtbarer Gegner mit Tag `Marksman` oder `Mage`, in Reichweite, höchste `kraft`.
   - Er zählt nur, wenn er näher an dir ist als jeder ihrer `Tank`/`Fighter` plus `hinter_front` (300), also nicht
     hinter seiner Front steht.
   - Das Abstandskriterium gilt nur, wenn die Icons auf der Minimap getrennt sind (Verdeckung).
   - `bewertung.carry` bricht nur einen Gleichstand.
3. **Sonst der Nächste** in Reichweite.

Der Zielname wird **einmal** je Episode gesagt. Ein zweites Mal nur, wenn das Ziel stirbt oder aus der Reichweite geht
und ein anderes tötbar wird.

### 5.3 Flucht

- **Ziel:** der sichere Ort aus Buch 0, 7.5 (eigener Turm, Basis, eigene Gruppe mit ≥ 2).
- **Möglich** ist die Flucht, wenn beides gilt:
  1. Deine Laufzeit zum Ziel ist kürzer als die Zeit, in der der schnellste Verfolger dich einholt. Das ist
     `(Abstand − seine Angriffsreichweite − 150) ÷ max(1, sein Tempo − dein Tempo)`. Mit Flash bereit kommen 400
     Einheiten dazu, mit Riven-E oder -Q bereit je ihre Distanz (`[kampf.champion]`).
  2. Kein Verfolger steht jetzt schon in seiner Angriffsreichweite + 150 (Data Dragon `attackrange`).
- **Satz:** der Ort in einem Wort: „Turm“, „Basis“ oder der Name des Mitspielers.

### 5.4 Sprechen im Kampf

- **Kategorie GEFAHR**, darf unterbrechen. In KAMPF spricht **nichts** anderes, weder Kern noch alte Regel, außer
  TECHNIK.
  - **Ändert Buch 0, 14:** `_afk` und alle Regeln mit „alle Modi“ sind in KAMPF stumm.
- Höchstens `max_woerter_kampf` (5) Wörter.
  - Satzanfänge vorgewärmt (`komponist.anfaenge`): „Rein auf“, „Raus, zum“, „Dreh um“.
  - Kampf-Ansagen haben `gueltig = 1,0 s`. Was dann nicht gesprochen ist, fällt weg.
- **Wechsel** von REIN zu RAUS oder zurück nur mit einem **Kampf-Ereignis**:
  - Tod auf einer Seite,
  - ein Gegner oder Mitspieler neu in `kampf_radius`,
  - Flash oder Ult eines Beteiligten erkannt,
  - dein Leben −15 % seit der letzten Ansage.

  Diese Liste kommt auch in `neues_ereignis` (für `Kern._kehrtwende`). Ohne Ereignis gibt es keinen Wechsel, auch nicht
  bei großer Änderung von `p_gewinn`.
- **Abstand** ≥ `kampf_abstand_s` (4 s), höchstens `max_je_episode` (3) Ansagen je Kampf.
- **Stumm**, wenn Carlos schon tut, was die Ansage sagen würde: REIN, während er sich dem Ziel nähert; RAUS, während er
  sich entfernt (wie Buch 5, 2).
- **Ändert die Qualitätsrunde E.4** („20 s keine Vorwärts-Handlung nach GEFAHR“): gilt nicht in KAMPF. Sonst wären
  DREHEN und REIN nach einem RAUS nie möglich.

## 6. Türme

- **Unter ihrem Turm** (Kampfmitte ≤ `turm_radius` von ihrem stehenden Turm) gibt es `REIN` nur, wenn eins zutrifft:
  - **Allein:**
    - Das Ziel ist tötbar (5.2) und dein Leben ≥ `dive_leben_min` (0,6).
    - Kein zweiter Gegner ist sichtbar in 1500, und `p_da(Jungler, 6 s) < 0,2`.
    - Vor 14:00 steht deine Welle am Turm (`GECRASHT_BEI_IHM` oder ≥ 3 eigene Vasallen dort).
    - `p_gewinn ≥ dive_allein_p_min` (0,8).
  - **Zu zweit oder mehr:** Ein Mitspieler mit mehr Leben als du kann den Turm auf sich ziehen, und
    `p_gewinn ≥ dive_team_p_min` (0,75).
- Sonst gilt beim Hinterherlaufen `RAUS` in der Form „Lass ihn, Turm!“.
- **Unter deinem Turm** zählt `turm_faktor` für euch. `ANNEHMEN` gegen den Lane-Gegner gibt es trotzdem nicht
  (Kapitel 4).

## 7. Nach dem Kampf

- **Gewonnen** (Kill ohne eigenen Tod): Der Plan wird sofort neu geprüft. Weiter geht es mit Umwandeln (Buch 5, 8),
  einem Objective (Buch 6) oder Back nach Buch 3 (`[recall]`-Schwellen). Es gibt keinen „Gut gemacht“-Satz.
- **Bestätigung** (Buch 3, `[bestaetigung]`) nur, wenn Carlos einer Kampf-Ansage gefolgt ist und es aufging:
  „Sauber, genau so.“ Höchstens einmal je 180 s.
- **Verloren und überlebt:** Der Plan wird neu geprüft, Gefahr bleibt Gefahr. Im Spiel gibt es keinen Rückblick, das
  macht das Review.

## 8. Todesrückblick nach einem Kampf

**Abgrenzung:**

- Die Qualitätsrunde (E.1) stellt die Sätze jetzt schon auf das Format um: zwei Sätze, keine Schadenszahlen, kein
  Kopfgeld, kein „hieß es“.
- Schritt 5 ergänzt die Lage-Erkennung aus der Kampf-Episode (Tabelle unten).
- Schritt 6 (Fragen, Buch 11) macht daraus das Gespräch im Review.

**Neue Kategorie `RUECKBLICK`:** gesprochen in TOT, einmal je Tod, ≥ 14 s Todeszeit, nicht im Budget
(`sprechen.zaehlt` nimmt sie aus). Höchstens `max_woerter_rueckblick` (25) Wörter, zwei Sätze:

1. Was entschied, aus der Probe am letzten Entscheidungspunkt vor dem Tod (3.3): wer da war, dein Leben, ob eine
   Ansage kam.
2. Was nächstes Mal, als Handlung.

| Lage (erkannt) | Satz 1 | Satz 2 |
|---|---|---|
| Einstieg mit `p_gewinn` < 0,35, keine Ansage | „Du bist mit 40 Prozent gegen Brand und Yasuo geblieben.“ | „Gegen zwei erst mit vollem Leben oder mit deinem Jungler.“ |
| RAUS oder ZURUECK wurde gesagt, Carlos blieb | „Raus kam, du bist geblieben – Brand und Yasuo haben dich erreicht.“ | „Bei zwei Gegnern sofort raus.“ |
| Überfall (`p_da` des Täters war < 0,3) | „Kha'Zix kam aus dem Nebel, keiner hatte ihn gesehen.“ | „Ohne Sicht auf ihren Jungler nicht so tief stehen.“ |
| Duell gegen einen einzelnen Gegner | „Duell gegen Gangplank verloren.“ | „Schau es dir im Review an.“ |
| Allein unter ihrem Turm | „Allein unter seinem Turm – der Turm hat entschieden.“ | „Tauch nur, wenn er fast tot ist und du mehr als die Hälfte Leben hast.“ |

Nie: Schadenszahlen, Kopfgeld-Rechnungen, „hieß es“, Vorwürfe, „die Zahlen sprachen für dich“.

## 9. Parameter (`wissen/kern.toml`, neu)

```toml
[kampf]
stand = "Buch 7, 27.09.2026 - Startwerte (Schaetzung), an Aufnahmen kalibrieren (Kapitel 3.3)"
fenster_s = 6
kampf_radius = 1000
k = 2.0                          # ersetzt gefahr.kampf_exponent (ein Wert fuer alles)
mitspieler_anteil = 0.8
ult_faktor_weg = 0.8             # beide Seiten; bereit oder unbekannt = 1
flash_faktor_weg = 0.95
faehigkeiten_faktor_weg = 0.75   # nur du; welche Faehigkeiten: [kampf.champion].kern
turm_faktor = 1.5
# turm_radius = bewertung.TURM_REICHWEITE (775), kein eigener Wert
eichung_min = 30
unsichtbar_s = 60
level_abschlag = 1
item_anteil = 0.8
annehmen_abstand = 2500
annehmen_p_min = 0.7
annehmen_leben_min = 0.5
annehmen_wiederholen_s = 60
jungler_sicher_s = 20
jungler_p_max = 0.2
rein_p_min = 0.65
raus_p_max = 0.35
drehen_abstand = 1000
drehen_gegner_leben = 0.4
drehen_eigen_leben = 0.35
drehen_p_min = 0.65
drehen_frei = 1500
toetbar_leben = 0.3
toetbar_leben_tank = 0.2
hinter_front = 300
dive_leben_min = 0.6
dive_allein_p_min = 0.8
dive_team_p_min = 0.75
kampf_abstand_s = 4
max_je_episode = 3
max_woerter_kampf = 5
max_woerter_annehmen = 8
max_woerter_rueckblick = 25
ereignis_leben_faellt = 0.15

[kampf.champion]                 # Startwerte; Buecher 8-10 ersetzen sie je Champion
Riven = { reichweite_rein = 650, flash_zusatz = 400, kern = ["E", "W"], flucht = { E = 250, Q = 260 } }
standard = { reichweite_rein = 550, flash_zusatz = 400, kern = [], flucht = {} }
```

`gefahr.kampf_exponent` und `gefahr.flucht_turm` fallen weg (Kapitel 3.1).

## 10. Szenarien

In `tests/szenarien/<aufnahme>_buch7.toml`. Jede Lage wird beim Anlegen durch Nachspielen geprüft und festgeschrieben.
Die Schlüssel `max_woerter`, `alte_regeln_max` und `soll_ziel` kommen aus Buch 6, Kapitel 13.

| id | Aufnahme | zeit / fenster | Soll | darf nicht |
|---|---|---|---|---|
| `0915-raus-kurz` | 144655 | 9:15 / 9:13–9:20 | modus KAMPF; soll RAUS oder HALTEN; max_woerter 5; alte_regeln_max 0 | sagen „das sind“, „Sekunden“ |
| `2501-sona-allein` | 102112 | 25:01 / 24:58–25:10 | ANNEHMEN; max_woerter 8; muss_nennen_eins „Sona“ | sagen „3400 Gold“, „Level“ |
| `2613-fiddlesticks-allein` | 102112 | 26:13 / 26:10–26:25 | ANNEHMEN oder REIN; max_woerter 8 | sagen „6800 Gold“ |
| `2631-zu-zweit-rein` | 102112 | 26:31 | ANNEHMEN oder REIN; max_woerter 8 | – |
| `0622-tod-gegen-gangplank` | 144655 | 6:22 / 6:22–6:40 | RUECKBLICK nach Tabelle 8; max_woerter 25 | sagen „mindestens“, „Schaden“, „Kopfgeld“, „Zahlen“ |
| `0338-keine-info-im-kampf` | 144655 | aus der Qualitätsrunde | erweitert: alte_regeln_max 0 in KAMPF | sagen „AFK“ |
| `0843-todesrueckblick` und `1005-tod-ohne-kopfgeld` | 140253 | aus der Qualitätsrunde | erweitert: Satz 1 nach Tabelle 8 | – |

- **102112 ist eine Bot-Partie.** 2501, 2613 und 2631 prüfen dort nur die Verdrahtung (Form, Länge, Art). Geeicht wird
  an ihnen nichts.
- Zusätzlich gehen je echter Partie bis zu drei Proben aus 3.3 mit dem **größten** Fehler (sicher gewonnen geglaubt
  und verloren, oder umgekehrt) als offene Szenarien nach `tests/szenarien/offen/`. Ihr Soll setze ich nach Durchsicht.

## 11. Abnahme Schritt 5 (Teil Kampf)

1. Die Szenarien aus Kapitel 10 sind grün über den Kern.
2. `kampf_eichung.py` ist gelaufen. Brier je Art, Fallzahlen, Anteil „offen“ und die gewählten Faktoren (oder
   „Startwert, zu wenige Proben“) stehen in messungen.md.
3. In allen Protokollen gilt in KAMPF:
   - keine alte Regel,
   - kein Satz mit mehr als 5 Wörtern (außer TECHNIK),
   - höchstens 3 Ansagen je Episode,
   - kein Wechsel ohne Kampf-Ereignis.

   `kennzahlen.py` bekommt die Spalte „Kampf-Verstöße“, Soll 0.
4. Der Umbau von `gefahr.p_verliere` auf `kampf.p_gewinn` (3.1) bricht nichts:
   - `0517`, `0850`, `0904`, `3535` und alle konstruierten Lagen (`lane.toml`, `recall.toml`, `mitte.toml`) bleiben
     grün.
   - Kehrtwenden bleiben 0.
   - Jede Lage, deren Plan sich ändert, steht mit Begründung in messungen.md.
