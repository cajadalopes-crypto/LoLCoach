# Buch 1 – Die Welle

Stand 27.09.2026 · für Claude Code, Umbau-Schritt 3 (Modus `LANE`) · setzt Buch 0 voraus · Wissen dazu:
`wissen/lexikon/grundlagen.md` (Wellenmanagement) und `saison2026.md`. Dieses Buch macht aus diesem Wissen
**Entscheidungen**, die der Kern mit dem rechnen kann, was die Minimap wirklich liefert.

---

## 0. Was die Welle für den Coach bedeutet

Die Welle ist die Uhr der Lane. Fast jede gute Entscheidung eines Toplaners in den ersten 14 Minuten
lautet „erst die Welle, dann …“:

- erst crashen, dann back,
- erst stapeln, dann Larven,
- erst die Welle zu dir ziehen, dann sicher farmen, solange der Jungler oben ist.

Der alte Coach sah die Welle nur als Momentaufnahme („eure 6 gegen seine 2“). Er wusste nicht, wohin sie
läuft, und hat sie nie als Plan-Schritt benutzt. Der neue Coach macht zwei Dinge:

1. Er liest die Welle **über Zeit** (Kapitel 1).
2. Er macht sie zum **ersten Schritt** fast jedes LANE-Plans (Kapitel 3).

---

## 1. Was wir messen können – und was nicht

`welle.py` liefert je Lane und etwa 1× je Sekunde:

- `blau`, `rot`: gezählte Vasallen-Punkte,
- `front`: wo sich die Wellen treffen, `s` von 0 = blaue Basis bis 1 = rote Basis,
- `schiebt`: wer gerade schiebt.

`Lagebild.welle(lane, zeit)` gibt den letzten Stand zurück, wenn er jünger als 4 s ist.

### 1.1 Grenzen, gemessen an 102112 nachgespielt

- **Die Front springt.** Stirbt eine Welle, ist die nächste an der eigenen Basis die „Front“. Beispiele:
  - 1:35 s = 0,50, 1:40 s = 0,16, 1:45 s = 0,60
  - 9:15 s = 0,24, 9:20 s = 0,32, 9:25 s = 0,32, 9:30 s = 0,49

  Jede **einzelne** Lesung ist unzuverlässig.
- **Gegnerische Vasallen im Nebel fehlen.** `rot` ist oft 0, obwohl eine Welle da ist. Rote Punkte gibt es nur,
  wo Sicht ist, also nahe an deinen Vasallen oder an dir.
- **Keine Nah-/Fernkampf-Unterscheidung, kein Vasallenleben.** Die Kanone kennen wir nur aus der Uhr (1.3).
- **„Welle crasht in X s“ ist nicht verlässlich vorhersagbar.** Ein Versuch in `OFFEN.md` ergab: Nur 6–9 % der
  Vorhersagen kommen überhaupt an. Der Coach **nennt keine Crash-Zeiten**, sondern die Kanonen-Uhr.

### 1.2 `WellenStand` – die geglättete Welle (neu in `kern/merkmale.py`)

Der Kern hält für die eigene Lane einen Puffer der letzten 20 s mit allen Lesungen. Alle Werte sind aus
**deiner** Sicht: `front` 0 = deine Basis, 1 = seine. Für Rot also `1 - front`.

```python
@dataclass
class WellenStand:
    lane: str
    unsere: int | None        # Median der letzten 6 s (nur Lesungen mit front != None)
    ihre: int | None          # Median der letzten 6 s; None, wenn nicht messbar (siehe unten)
    front: float | None       # Median der letzten 6 s
    trend: float | None       # Steigung der Front in s je 10 s (lineare Regression über 20 s); > 0 = zu ihm
    zustand: str              # siehe 1.4
    seit: float               # seit wann dieser Zustand gilt
    frisch: bool              # >= 3 Lesungen in den letzten 6 s
```

**`ihre` ist unbekannt (None)**, wenn `front > 0.55` ist **und** du weiter als 1500 Einheiten von der Front weg
bist. Dann liegt ihre Welle im Nebel, und 0 hieße nur „nicht gesehen“.

### 1.3 Die Wellen-Uhr (vorhanden: `entscheider.wellen_spawns`, `naechste_kanone`)

- Spawn bei 0:30, danach bis 14:00 alle 30 s, bis 30:00 alle 25 s, danach alle 20 s.
- Kanone:
  - bis 14:00 jede dritte Welle (die erste ist Welle 3 um 1:30),
  - bis 25:00 jede zweite,
  - danach jede Welle.
- Quelle ist `wissen/mechanik.toml [wellen]`.

Daraus kennt der Kern jederzeit `naechste_kanone` (Ankunft in der Lane-Mitte) und `naechste_welle`. Diese
Zeiten sind **sicher**. Deshalb sagt der Coach Zeiten nur so: „Kanone kommt 7:31“.

**Geometrie** (Top, aus `welle.LANES`): Die Lane ist ≈ 20.000 Einheiten lang, Δs = 0,1 ≈ 2000 Einheiten ≈ 6 s
Vasallenweg bei 350 Tempo.

| Punkt | Lage auf `s` aus deiner Sicht |
|---|---|
| dein Außenturm | ≈ 0,35 |
| sein Außenturm | ≈ 0,65 |
| Turmreichweite | ± 0,06 um den Turm |

Die Werte stehen in `welle.TURM_AUSSEN`.

**`turm_dein` und `turm_ihr` sind immer der vorderste stehende Turm der Seite auf dieser Lane.** Der Kern
projiziert die Turmposition aus `bewertung.stehende_tuerme` mit `welle._projektion` auf `s`. Fällt der
Außenturm, rückt der innere nach. Ohne das würde eine Welle am inneren Turm (s ≈ 0,80, 102112 um 13:15) nie als
„gecrasht“ erkannt.

### 1.4 Zustände der Welle

Der Kern bestimmt den Zustand mit **Hysterese**: Ein neuer Zustand gilt erst, wenn er 3 s lang Kandidat war.
Ausnahme ist `GECRASHT_BEI_IHM`, der sofort gilt, weil er ein Plan-Schritt ist. Geprüft wird von oben nach
unten:

| Zustand | Bedingung (Startwerte in `kern.toml [welle]`) | Bedeutung |
|---|---|---|
| `UNBEKANNT` | nicht `frisch` | nichts sagen, was die Welle braucht |
| `LEER` | `unsere == 0` und (`ihre == 0` oder None) seit ≥ 4 s | beide Wellen weg, z. B. nach Crash + Turm |
| `GECRASHT_BEI_IHM` | `front ≥ turm_ihr − 0,06` und `unsere ≥ 1` und `ihre ≤ 1` (oder None) | deine Welle schlägt an seinen Turm |
| `GECRASHT_BEI_DIR` | `front ≤ turm_dein + 0,06` und `ihre ≥ 1` und `unsere ≤ 1` | seine Welle am Turm – farmen unter dem Turm |
| `GROSS_ZU_IHM` | `unsere ≥ gross_ab` (7) und `trend ≥ 0` | Stapel – der Crash wird groß |
| `GROSS_ZU_DIR` | `ihre ≥ gross_ab` und `trend ≤ 0` | sein Stapel kommt zu dir |
| `GEHALTEN_BEI_DIR` | `turm_dein + 0,03 ≤ front ≤ turm_dein + 0,12`, `|trend| ≤ 0,01`, 15 s stabil, `ihre ≥ unsere + 2` | Freeze vor deinem Turm |
| `ZU_IHM` | `trend ≥ trend_schwelle` oder (`unsere − ihre ≥ 2` und `ihre` bekannt) | die Welle wandert zu ihm |
| `ZU_DIR` | `trend ≤ −trend_schwelle` oder `ihre − unsere ≥ 2` | die Welle wandert zu dir |
| `MITTE` | sonst | neutral |

> **Nachtrag (Qualitätsrunde 1):** `unsere`/`ihre` zählen nur noch die **Front**, und die beiden
> `GECRASHT_*`-Zeilen gelten in der Fassung aus Kapitel 7.1.

**Eichung (Schritt 3):** Claude Code beschriftet in 102112 und einer echten Partie je 20 Zeitpunkte von Hand
mit dem Zustand. Grundlage sind die Minimap-Bilder, die in `_bilder/` liegen, solange sie nicht aufgeräumt
sind. Abnahme: ≥ 80 % Treffer, und `GECRASHT_BEI_IHM` ≥ 90 %, weil es Plan-Schritte auslöst.

---

## 2. Die Wertrechnung der Welle (für `kern/wert.py`)

| Größe | Formel | Quelle |
|---|---|---|
| **Wellenwert** | 3 × `vasall_nah` + 3 × `vasall_fern` (+ Kanone) in Gold, dazu dieselben Vasallen in XP × `xp_ge` | `mechanik.toml [gold]`, `[xp]` |
| **Stapelwert** | Wellenwert × (unsere / 6), höchstens 3 Wellen | – |
| **verlorene Welle** | Welle, die an **deinem** Turm stirbt, während du weg bist: voller Wellenwert. Welle an **seinem** Turm, während du weg bist: 0 für dich, aber `gegner_farmt_unter_turm` = er verliert etwa 30 % davon. | – |
| **Abwesenheit** | Wellen, die in `dauer` an deinem Turm ankommen, laut Wellen-Uhr und Zustand: `GECRASHT_BEI_IHM` → die erste zählt halb (Bounce), `MITTE` → voll, `ZU_DIR`/`GROSS_ZU_DIR` → voll + `gross_zuschlag` | – |

Die Rollenquest Top zählt als kleiner Zuschlag (Startwert `quest_je_s_lane = 1,5 GE/s`). Dahinter stecken
7,5 Punkte je 5 s in der Lane und Vasallen à 2 Punkte, für ein früheres Ende der Quest mit +600 XP und TP-Ausbau.
Die Quelle ist `saison2026.md` [Rollenquests].

---

## 3. Die Handlungen der Welle (für `kern/modi/lane.py`)

Neu gegenüber Buch 0, Kapitel 6.3: `STAPELN` und `UNTER_TURM_FARMEN`. Beide gelten bei den Kehrtwenden
(Buch 0, 9.4 Punkt 5) als **neutral**.

### 3.1 `FARMEN` (Grundplan, stumm)

Gilt immer, wenn keine andere Handlung mehr EV hat. Der Coach sagt dazu nichts. Einzige Ausnahme ist der
Satz aus 3.6, wenn die Welle **zu dir** gehört.

### 3.2 `WELLE_REIN_UND_BACK`

**Kandidat, wenn alles gilt:**

- Zustand ∈ {`ZU_IHM`, `GROSS_ZU_IHM`, `MITTE`} mit `unsere ≥ (ihre or 0)`, **oder** Zustand
  `GECRASHT_BEI_IHM`,
- ein Grund zum Back aus Buch 3 liegt vor: Gold, Leben, Objective-Vorlauf, Gegner gerade zurückgekommen,
- geschätzte Crash-Dauer ≤ `crash_max_s` (Startwert 15 s). Sie ergibt sich als
  `(turm_ihr − front) × lane_laenge / vasallen_tempo + (ihre or 0) × 1,0 s`. Das ist eine grobe Schätzung und
  wird nur **intern** zur Auswahl benutzt, nie gesagt.

**Schritte:**

1. `["Welle rein", "back", <Kauf>, <Ziel>]`.
2. Der Schritt „Welle rein“ ist erfüllt, sobald `GECRASHT_BEI_IHM` gilt **oder** 15 s vergangen sind.
3. Danach kommt eine PLAN-Ansage: „Welle ist drin – jetzt back.“

**Satz:** „Top-Welle rein, dann back: 1500 Gold für den Brutalisierer.“

**Kanone mitnehmen:**

- Kommt die nächste Kanone in ≤ `kanone_warten_s` (Startwert 15 s) **und** p_tod bleibt klein, wartet der Plan
  auf die Kanone: „Kanone kommt 6:31 – die noch rein, dann back.“
- Die Kanone ist der beste Crash, weil sie am Turm lange lebt. Das verlängert dein Fenster.

**Abbruch:**

- p_tod steigt: dann `ZURUECK` oder `BACK_JETZT`,
- Zustand wird `GROSS_ZU_DIR`: dann `UNTER_TURM_FARMEN`.

### 3.3 `STAPELN` (Slow Push)

**Kandidat, wenn:**

- ein Objective auf **deiner Kartenseite** spawnt in 45–100 s (Larven 8:00, Herold 15:00; Top-Seite) **oder**
  der Plan einen Back oder Roam in 60–90 s vorsieht,
- und Zustand ∈ {`MITTE`, `ZU_IHM`, `LEER`},
- und `p_da(Jungler, 30 s)` < `stapeln_gefahr_max` (Startwert 0,4). Wer stapelt, steht vorn.

**Ziel:** die Kanonenwelle, die 15–30 s vor dem Objective ankommt, oder die nächste Kanone vor dem geplanten
Back.

**Schritte:** `["stapeln bis Kanone <Zeit>", "crashen", <Folge>]`.

**Satz:** „Stapel die Top-Welle bis zur Kanone um 7:31: dann crashen und zu den Larven.“

**Warum:** Der Gegner muss wählen, ob er CS und Platten verliert oder zu spät zum Objective kommt. Das ist
Tempo.

### 3.4 `WELLE_HALTEN` (Freeze vor deinem Turm)

**Kandidat, wenn:**

- Zustand ∈ {`GEHALTEN_BEI_DIR`, `ZU_DIR`} **und** die Front liegt ≤ `turm_dein + 0,15`,
- **und** eine der beiden Lagen trifft zu:
  - **angreifend:** `kraefte()[0] ≥ 1` (du stärker) – er muss zum Farmen nach vorn, wo du ihn schlägst oder
    sein Jungler weit ist, **oder**
  - **schützend:** p_da des gegnerischen Junglers auf deiner Seite ≥ 0,5 **oder** du bist schwächer
    (`kraefte()[0] ≤ −1`).
- **Nicht**, wenn ein Objective auf deiner Seite in ≤ 60 s spawnt. Dann gilt `STAPELN`, oder die Welle gehört
  wenigstens nicht an deinen Turm.

**Satz:**

- angreifend: „Lass die Welle vor deinem Turm stehen: Sett muss zum Farmen nach vorn.“
- schützend: „Lass die Welle zu dir kommen: Fiddlesticks ist wahrscheinlich oben.“

**Was der Coach nicht sagt:** Er erklärt keine Freeze-Technik („nur Last Hits, Aggro ziehen“). Das gehört ins
Review oder in eine Antwort auf „Wie freeze ich?“ (Buch 11).

**Abbruch:**

- Zustand `GECRASHT_BEI_DIR`: Der Freeze ist gebrochen, es gilt `FARMEN` oder `UNTER_TURM_FARMEN`.
- Objective-Vorlauf beginnt.

### 3.5 `UNTER_TURM_FARMEN`

**Kandidat, wenn:**

- Zustand ∈ {`GECRASHT_BEI_DIR`, `GROSS_ZU_DIR`} und du bist ≤ 20 s von deinem Turm,
- **und** ein Back jetzt würde den Stapel kosten (verlorene Welle ≥ `stapel_verlust_min`, Startwert 150 GE).

**Satz:** „Farm unter deinem Turm, back erst, wenn die Welle weg ist: sonst verlierst du 8 Vasallen.“

Ist das Leben kritisch, gewinnt `BACK_JETZT` oder `ZURUECK` über die EV-Rechnung. Genau dafür gibt es sie.

### 3.6 `PLATTEN` (Präzisierung zu Buch 0)

**Kandidat, wenn:**

- Zustand `GECRASHT_BEI_IHM` mit `unsere ≥ 3`, damit deine Vasallen den Turm tanken,
- **und** dein Lane-Gegner ist tot, im Brunnen (`lage.brunnen_seit`) oder > 3000 entfernt mit Ankunft >
  `platten_dauer`,
- **und** p_tod(Dauer) ist klein.

**Wichtig seit 2026:**

- Platten bleiben bis zum Turmfall (nicht mehr bis 14:00). `PLATTEN` ist deshalb auch in `SEITE` Kandidat
  (Buch 5).
- Kristall-Aufwuchs: Hat niemand den Turm lange angefasst, bringt **dein erster Treffer** Echtschaden. „Hau den
  Turm selbst zuerst an“ gehört als Zusatz in den Satz, wenn der Turm seit ≥ 60 s unberührt ist. Das ist
  messbar über die Platten-Ziffer und Treffer-Ereignisse. Ist es nicht messbar, weglassen.

**Satz:** „Platte am äußeren Top-Turm: Sett ist noch 20 Sekunden tot.“

### 3.7 Welle und Gefahr

Das Gefahr-Modell (Buch 0, 7.5) entscheidet über den Rückzug. Die Welle ändert zwei Dinge:

- **Wo du stehst, bestimmt die Welle.** `ZU_IHM` bedeutet, du stehst vorn. Liegt p_da(Jungler) auf deiner Seite
  hoch, verschiebt sich das EV von `FARMEN` am Punkt der Front hin zu `WELLE_HALTEN` (schützend). Dann gilt:
  - kein Satz „Geh zurück“, solange nichts kommt,
  - stattdessen **einmal** „Lass die Welle zu dir kommen“.

  Das ersetzt die 22 „… bei dir“-Warnungen durch einen Plan.
- **Ein Rückzug kostet die Welle.** Die Todeskosten enthalten die eigene Welle (Buch 0, 7.3). Der Rückzug
  enthält sie auch. Wer bei `GROSS_ZU_DIR` zurückgeht, verliert den Stapel.

---

## 4. Bestätigen (Pädagogik, siehe Buch 0 Kapitel 9 und die Kategorie `BESTAETIGUNG` in Buch 3)

Welle ist das, was man am schnellsten falsch lernt. Diese Momente bekommen **einmal** eine kurze Bestätigung,
höchstens 8 Wörter. Die Regeln für Bestätigungen stehen in Buch 3, Kapitel 5.

| Moment | erkennbar an | Satz |
|---|---|---|
| Crash vor dem Back | `GECRASHT_BEI_IHM` in den 10 s vor dem Start des Recalls | „Sauber: Welle drin, dann back.“ |
| Stapel zur Kanone vor dem Objective | Plan `STAPELN` erfüllt, Crash 15–30 s vor dem Spawn | „Genau so – er muss jetzt wählen.“ |
| Unter dem Turm gefarmt statt gebackt | Plan `UNTER_TURM_FARMEN` erfüllt, danach Back mit `LEER` | „Gut – nichts verloren.“ |

---

## 5. Parameter für `wissen/kern.toml`

```toml
[welle]
stand = "Buch 1, 27.09.2026 - Startwerte (Schaetzung), an Szenarien und Handbeschriftung kalibrieren"
median_s = 6
trend_fenster_s = 20
zustand_hysterese_s = 3
turm_dein = 0.35                # s aus deiner Sicht, nur Rueckfall: gilt ist der vorderste stehende Turm (1.3)
turm_ihr = 0.65
turm_reichweite_s = 0.06
lane_laenge = 20000             # Einheiten, Top/Bot; Mid ~ 10500 (welle.LANES)
gross_ab = 7
trend_schwelle = 0.02           # s je 10 s
nebel_ab = 0.55                 # front, ab der "ihre = 0" unbekannt heisst ...
nebel_abstand = 1500            # ... wenn du weiter als das von der Front weg bist
crash_max_s = 15
kanone_warten_s = 15
stapeln_gefahr_max = 0.4
stapel_verlust_min = 150        # GE
gross_zuschlag = 60             # GE je Welle ueber 6 Vasallen
quest_je_s_lane = 1.5           # GE, Top-Rollenquest (saison2026.md)
platten_dauer = 8               # s fuer eine Platte mit Vasallen (grob)
```

---

## 6. Szenarien

### 6.1 Aus Aufnahmen

Neu in `tests/szenarien/2026-09-27_102112.toml`, siehe Buch 3, Kapitel 7, dort mit Recall-Bezug:
`0545-back-bei-40-prozent`, `0600-basis-kauf`, `1315-crash-dann-back`.

### 6.2 Konstruierte Lagen (neu, `tests/szenarien/konstruiert/`)

Echte Partien gibt es noch fast keine. Die Regeln dieses Buchs lassen sich aber ohne Aufnahme prüfen: mit
**konstruierten Lagen**. Das sind handgeschriebene Merkmale, die direkt in `kern/modi/lane.py` gehen.

- **Format:** siehe Datei `tests/szenarien/konstruiert/lane.toml`, Kopfkommentar.
- **Umsetzung:** Claude Code baut dazu `kern/testlage.py`, eine Fabrik, die aus den Feldern `Merkmale` samt
  minimaler `Bewertung` baut. `werkzeuge/szenarien.py` bekommt `--konstruiert`, und `tests/alle.py` lässt sie
  mitlaufen.
- **Abnahme Schritt 3:** alle Lagen aus `lane.toml` und `recall.toml` grün.

Konstruierte Lagen ersetzen keine echten Partien. Sie verhindern aber, dass eine Regel still kaputtgeht, und
halten die Absicht dieses Buchs als Test fest.

---

## 7. Nachträge

### 7.1 Front statt Summe (Qualitätsrunde 1, 27.09.2026; Prüfung F1)

**Anlass.** In 144655 standen dreimal (3:13, 5:17, 5:38) gegnerische Vasallen an deinem äußeren Turm, während
deine nächste Welle zwischen innerem und äußerem Turm loslief. 1.4 zählte alle Vasallen der Lane:
`GECRASHT_BEI_DIR` verlangte `unsere ≤ 1`, die nachlaufende Welle (4–6) machte daraus `ZU_IHM`.

**Regel** (`welle._front`, `merkmale.WellenPuffer`):

1. Die Vasallen-Punkte einer Lane werden entlang der Lane projiziert (0 = dein Brunnen, 1 = seiner) und in
   Gruppen geteilt. Eine Lücke > `[welle] front_luecke` (0,06) trennt.
2. **Die Front:**
   - Eine Gruppe mit beiden Farben ist die Front (der Zusammenstoß; bei mehreren die größte).
   - Sonst: die vorderste eigene Gruppe und die dir nächste gegnerische Gruppe.
3. **Nachlaufende Gruppen** zählen nicht für den Zustand: eigene hinter der Front auf deiner Seite, gegnerische
   hinter der Front auf seiner. Die nächste davon steht im `WellenStand` als `naechste_dein` / `naechste_ihr`
   (Lage ihrer Spitze, 0–1 aus deiner Sicht) – für „deine nächste Welle ist gleich da“.
   `unsere`/`ihre` zählen nur die Front.
4. `GECRASHT_BEI_DIR`: ≥ `crash_mindestens` (3) gegnerische Front-Vasallen in der Zone vor deinem vordersten
   Turm, und ≤ 1 eigener Front-Vasall dort – egal, was dahinter läuft. `GECRASHT_BEI_IHM` spiegelbildlich.
   - Zone: von `turm_toleranz` (0,02) hinter dem Turm bis `crash_zone` (0,08) davor. Wer den Turm schlägt, steht
     auf der Karte auch knapp dahinter.
5. `wellen_eichung.py` wählt keine Zeitpunkte, an denen du tot bist oder recallst. Recall heißt: dein Icon taucht
   binnen 9 s im Brunnen auf, ohne dass du stirbst.

**Drei Zusätze, nicht im Auftrag, nötig für die Abnahme** (je mit Schalter in `kern.toml [welle]`):

- **Pfadlinie** (`welle.SCHNITT_FLAECHE`):
  - Befund: dein weißer Laufweg auf der Minimap (1 px, mit dunklem Schatten) zerschneidet Vasallen in Stücke
    unter der Mindestfläche. 144655, 5:16–5:17: drei gegnerische am Turm, gelesen wurde einer.
  - Regel: Ein Stück ab 10 (statt 22) Flächeneinheiten, das eine weiße Linie berührt, zählt als Vasall. Zwei
    Hälften desselben Vasallen (näher als 7 px bei 570) zählen einmal.
- **Icon-Deckung** (`icon_deckung`):
  - Befund: Steht dein eigenes Icon in der Zone, verdeckt es die Vasallen darunter. 144655, 3:13 und 5:38: Riven
    farmt vor ihrem Turm, am Rand ihres Icons sind 1–2 gegnerische zu sehen.
  - Regel: Dann reicht einer. Gezählt wird bis knapp hinter den Rand des Icons (Icon-Radius + `turm_toleranz`).
  - Vasallen unter FREMDEN Icons bleiben eine Grenze (s. u.).
- **Sofort** (`crash_dir_sofort`): `GECRASHT_BEI_DIR` gilt wie `GECRASHT_BEI_IHM` ohne 3 s Hysterese. Mit der
  Regel „≥ 3 an deinem Turm“ ist er so scharf wie sein Spiegel. Mit Hysterese kam 5:17 erst um 5:20.

**Grenze:** Vasallen unter einem fremden Icon (Gegner oder Mitspieler an der Lane) sind nicht zu sehen. In der
Eichung ist das der häufigste Grund für „unklar“; die Zahl steht in `messungen.md`, Qualitätsrunde 1.

**Ergebnis:** siehe `messungen.md`, Qualitätsrunde 1, F1.
