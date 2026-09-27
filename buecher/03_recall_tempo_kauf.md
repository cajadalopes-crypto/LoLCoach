# Buch 3 – Recall, Tempo, Kauf

Stand 27.09.2026 · für Claude Code, Umbau-Schritt 3 (Modi `LANE`, `BASIS`, `TOT`) · setzt Buch 0 und Buch 1 voraus ·
Wissen dazu: `wissen/lexikon/grundlagen.md` (Recall und Gold, Top-Lane im Detail) und die Champion-Lexika
(`Recall-Schwellen`, `Build`).

---

## 0. Worum es geht

Ein Back ist die teuerste Routine-Entscheidung der Lane. Er kostet:

- ~8 s Kanal,
- Einkauf,
- ~20–30 s Rückweg,
- oft eine Welle.

Er bringt:

- Items,
- Leben,
- und, richtig getimt, Tempo: Du bist vor dem Gegner zurück, du bist vor dem Objective bereit.

In 102112 war der Back fast nie das Problem. Das Problem war der Coach: Er sagte

- „nimm den Kampf an“ bei 40 % Leben mit 1500 Gold im Beutel (5:54),
- „schieb die Welle in seinen Turm“ in der eigenen Basis,
- „kauf den Rest deines Golds“.

Dieses Buch legt fest, wann Back, was kaufen und wohin danach.

---

## 1. Warum zurück? Die Back-Gründe

Ein Back ist nur Kandidat, wenn mindestens ein Grund vorliegt. Alle Gründe fließen als Gewinn ins EV:

| Grund | Bedingung | Gewinn (GE) |
|---|---|---|
| `GOLD_STUFE` | `kaufplan` liefert einen Kauf, der sich lohnt (`denker.kauf` → lohnt; vorhanden: fertiges Item oder Bauteile ≥ `KAUF_LOHNT_AB`) | Kaufwert: gekaufte Kosten × `kauf_faktor` + `spike_bonus`, wenn ein Kern-Item fertig wird |
| `GOLD_HORTEN` | ungenutztes Gold ≥ `horten_ab` (1500) | wie oben + `horten_zuschlag` je 500 darüber (gehortetes Gold kämpft nicht mit) |
| `LEBEN` | Leben < `leben_back` (0,4) **oder** Mana reicht nicht für eine Combo (API `resourceValue`) | fehlendes Leben × `heil_faktor`, dazu sinkt p_tod für alle folgenden Lane-Handlungen |
| `OBJECTIVE_VORLAUF` | Objective auf deiner Seite spawnt in 60–100 s, du wärst mit Back rechtzeitig und voll zurück | `vorlauf_bonus` × Objective-Wert |
| `GEGNER_ZURUECK` | Lane-Gegner ist gerade gebackt (Brunnen) oder tot, deine Welle ist gecrasht | Tempo-Bonus: gleichzeitiger Back ohne Verlust |
| `KEINER` | keiner der oben | kein Back-Kandidat |

**Riven** (Lexikon, Zeile „Recall-Schwellen“): „1337 g (Brutalisierer) oder 1050 g (Caulfields) +
Kontroll-Auge. Nicht mit < 800 g zurück, außer Leben < 30 %.“ Solche Zeilen liest der Kern je Champion als
`back_schwelle` und `back_nie_unter` mit. Fehlt die Zeile, gilt `KAUF_LOHNT_AB` aus `denker`.

---

## 2. Wann genau? Die Back-Handlungen

Die Welle entscheidet den Zeitpunkt (Buch 1, Zustände):

| Zustand der Welle | Handlung | Warum |
|---|---|---|
| `GECRASHT_BEI_IHM` | `BACK_JETZT` | bestes Fenster: Die Welle kommt dir entgegen (Bounce), du verlierst fast nichts |
| `ZU_IHM`, `GROSS_ZU_IHM`, `MITTE` mit Überzahl | `WELLE_REIN_UND_BACK` (Buch 1, 3.2) | erst crashen, sonst verlierst du die Welle |
| `LEER` | `BACK_JETZT` | beide Wellen weg, kein Verlust |
| `ZU_DIR`, `GROSS_ZU_DIR`, `GECRASHT_BEI_DIR` | `UNTER_TURM_FARMEN` (Buch 1, 3.5), dann `BACK_JETZT` | ein Back jetzt verschenkt den Stapel |
| `UNBEKANNT` | `BACK_JETZT` nur bei `LEBEN` oder Gefahr | ohne Welle kein Timing-Rat |

### 2.1 Gefahr schlägt Timing

Ist p_tod(bleiben) × Todeskosten ≥ Gefahr-Schwelle, gewinnt `BACK_JETZT` oder `ZURUECK`, **egal wie die Welle
steht**. Ein toter Riven verliert alle Wellen.

Beispiel 5:45 in 102112: 39 % Leben, 1537 Gold, Flash weg, Fiddlesticks vor 8 s oben gesehen. Das ergibt
`BACK_JETZT`.

**Satz:** „Back jetzt: 40 Prozent Leben, 1500 Gold im Beutel.“ Das Item nennt erst der Kauf-Satz in der
Basis, aus `kaufplan`.

**Nicht:** „Nimm den Kampf an“ (5:54 alt).

### 2.2 Nie back

- In `KAMPF`.
- Wenn ein sichtbarer Gegner ≤ 1500 entfernt ist und dich im Kanal (8 s) erreicht. Dann erst raus, dann back:
  `ZURUECK` mit Folge `BACK_JETZT`.
- Wenn ein Objective auf deiner Seite in < 40 s spawnt und du voll bist. Dann bleiben und helfen, Buch 6.

### 2.3 Der Satz nennt immer den Grund mit Zahl

- „Back jetzt: …“
- „Top-Welle rein, dann back: …“
- „Farm unter dem Turm, back danach: …“

---

## 3. Was kaufen? `KAUFEN`

**Quelle:** `kaufplan.plan` und `denker.kauf`, beide vorhanden, dazu die Ladenliste aus Data Dragon. Der Kern
**erfindet keine Items**. Claude bekommt die Kaufliste fertig.

**Regeln:**

1. **Namen, nicht Kategorien.** „Kauf den Brutalisierer und ein Kontroll-Auge.“ Nicht „rüste auf“, nicht „den
   Rest deines Golds“ (30:15 alt).
2. **Höchstens drei Dinge** im Satz. Der Rest steht auf dem Dashboard.
3. **Kontroll-Auge** kommt dazu, wenn keins im Inventar ist, ein Platz frei ist und nach dem Kern-Kauf ≥ 75 Gold
   übrig sind.
   - Ist das Kontroll-Auge der **Fokus des Tages** (`profil`), steht es **zuerst** im Satz: „Kontroll-Auge und
     Brutalisierer“.
4. **Trank verkaufen**, wenn es dadurch für ein Bauteil mehr reicht. Das ist vorhanden: `denker.kauf`.
5. **Kein Kauf-Satz außerhalb von BASIS/TOT.** Ausnahme ist der Grund eines Back-Plans („… für den
   Brutalisierer“).

**Zeitpunkt:**

- In `BASIS` sofort beim Eintritt.
- In `TOT` 8 s vor dem Respawn (Buch 0, 6.3). Der Kern ruft `KAUFEN` und `WOHIN` zusammen **einmal** auf.

---

## 4. Wohin danach? `WOHIN` und Tempo

### 4.1 In der Lane-Phase (bis 14:00)

Der Normalfall ist **zurück auf die Lane**. Wichtig ist der Zeitpunkt:

- Der Kern rechnet deinen Weg zur Lane (Einheiten / Tempo; Heimweg-Schub bis 14:00 +80 % → +40 % über 4 s,
  `saison2026.md`).
- Er vergleicht ihn mit der Ankunft der nächsten Welle an deinem Turm (Wellen-Uhr plus Zustand vor dem Back).

**Satzformen, jeweils mit einer Zahl:**

- „Zurück nach Top: deine Welle ist in 20 Sekunden an deinem Turm.“
- Wenn ein Objective näher ist: „Zu den Larven: Spawn 8:00, du bist 7:40 dort, crash vorher nicht nötig.“

**Teleport zurück (Top)** ist Kandidat `WOHIN_TP_LANE`, wenn alles gilt:

- TP bereit,
- auf der Lane stehen ≥ 1,5 Wellen oder Platten auf dem Spiel (verlorene Welle ≥ `tp_lane_wert_min`),
- **und** kein Objective, für das du TP brauchst, spawnt innerhalb der TP-Abklingzeit (bis 10:00 300 s,
  `saison2026.md`).

Ohne das gilt: laufen. **Satz:** „TP auf deine Welle: zwei Wellen stehen vor deinem Turm, Drache erst in
4 Minuten.“

### 4.2 Nach der Lane-Phase

`WOHIN` nimmt das beste Ziel aus Buch 5 (Seite, Gruppe, Objective). Bis Buch 5 umgesetzt ist (Schritt 4), gilt
`bewertung.ziele` (vorhanden). Die Warteregel BASIS aus Buch 0, 6.3 gilt: Steht Carlos nach dem Kauf > 20 s
in der Basis, wird das Ziel wiederholt.

### 4.3 Tempo gegen den Lane-Gegner

„Wer zuerst eine freie Aktion hat, hat Tempo“ (Reasoning, Abschnitt 8/9). Messbar sind drei Fälle:

| Lage | Rat | Satz |
|---|---|---|
| Lane-Gegner backt (Brunnen erkannt), deine Welle ist `ZU_IHM`/`MITTE` | `WELLE_REIN_UND_BACK` oder `PLATTEN`: er verliert Vasallen am Turm, du backst gleich danach ohne Verlust | „Sett ist gebackt: Welle rein, Platte, dann back.“ |
| Du backst, er bleibt mit großer Welle bei dir | Back nur bei Gefahr oder `LEBEN`; sonst `UNTER_TURM_FARMEN` | – |
| Du bist vor ihm zurück (er noch im Brunnen oder auf dem Weg) | `STAPELN` oder `PLATTEN`, wenn die Welle passt; mit Objective in ≤ 100 s: `VORBEREITEN_OBJECTIVE` | – |

---

## 5. `BESTAETIGUNG`: der Coach lobt, was richtig war

Neue Sprech-Kategorie. Sie ergänzt Buch 0, Kapitel 9.1. Ein Coach, der nur warnt und befiehlt, bringt nichts
bei. Richtiges muss sich festsetzen.

**Regeln:**

- **Nur für Plan-Handlungen, die Carlos wirklich ausgeführt hat**, und nur, wenn sie etwas gebracht haben.
  Die Auslöser stehen in Buch 1, Kapitel 4, und in der Tabelle unten.
- **Häufigkeit:** höchstens 1 je `bestaetigung_abstand_s` (180 s), nie in `KAMPF` oder `GEFAHR`, nie bei vollem
  Budget. Zählt zum Budget (Buch 0, 9.2).
- **Kurz:** ≤ 8 Wörter, ohne „super“ und „toll“. Die Handlung wird benannt: „Sauber: Welle drin, dann back.“
- **Am liebsten angehängt, nicht allein.** Beim Eintritt in die Basis steht die Bestätigung vor dem Kauf-Satz:
  „Sauber gebackt. Kauf den Brutalisierer, dann Top: …“. Das spart eine Ansage.
- **Ins Review.** Jede Bestätigung wird als Stärke mit Zeit gespeichert. Das Review nutzt sie für den Block
  „Stärken“ statt freier Claude-Sätze.
- **Fokus des Tages:** Wird der Fokus erfüllt (z. B. Kontroll-Auge gekauft), bestätigt der Coach es **einmal**:
  „Kontroll-Auge gekauft – genau der Fokus.“

| Moment | Erkennbar an | Satz |
|---|---|---|
| Back im Fenster | Recall startet ≤ 10 s nach `GECRASHT_BEI_IHM` oder bei `LEER`, mit lohnendem Kauf | „Sauber: Welle drin, dann back.“ |
| Rückzug hat sich gelohnt | Plan `ZURUECK` wurde ausgeführt, und ≤ 10 s danach taucht der Gegner, vor dem gewarnt wurde, ≤ 1500 von deinem alten Ort auf – du lebst | „Gut raus – da war er.“ |
| Pünktlich zurück | Ankunft an der Lane ±5 s zur Welle am Turm | „Pünktlich – kein Vasall verloren.“ |
| Platten mit Fenster | Plan `PLATTEN` erfüllt, Back vor Rückkehr des Gegners | „Platte geholt und weg – genau so.“ |

**Wie der Recall erkannt wird:** Das eigene Icon steht still und landet dann im Brunnen. Das nutzt heute schon
`lage.brunnen_seit` für Gegner. Für dich reicht: Eintritt in `BASIS` ohne Tod, und die letzte Position vor ≤ 12 s
lag außerhalb der Basis.

---

## 6. Parameter für `wissen/kern.toml`

```toml
[recall]
stand = "Buch 3, 27.09.2026 - Startwerte (Schaetzung), an Szenarien kalibrieren"
leben_back = 0.4
horten_ab = 1500
horten_zuschlag = 100           # GE je 500 Gold ueber horten_ab
spike_bonus = 300               # GE, wenn ein Kern-Item fertig wird
vorlauf_bonus = 0.3             # Anteil am Objective-Wert
kanal_s = 8
einkauf_s = 3
tp_lane_wert_min = 180          # GE, verlorene Welle/Platten, ab dem TP zur Lane lohnt
nie_back_gegner_abstand = 1500

[bestaetigung]
stand = "Buch 3, 27.09.2026"
abstand_s = 180
max_woerter = 8
```

---

## 7. Szenarien

### 7.1 Aus Aufnahmen

Diese Szenarien gehören in `tests/szenarien/2026-09-27_102112.toml`. Die Lagen sind am 27.09. nachgespielt und
geprüft.

| id | Zeit | Lage | soll | darf nicht |
|---|---|---|---|---|
| `0545-back-bei-40-prozent` | 5:45 (Fenster 5:40–5:58) | 39 % Leben, 1537 Gold, Flash weg, Fiddlesticks 5:37 oben gesehen, Welle 7:0 deine, Sett lebt ~900 entfernt | `ZURUECK` (erst raus, Sett erreicht dich im Kanal) / `BACK_JETZT` / `WELLE_REIN_UND_BACK` | sagen: „Kampf an“; Pläne `TRADE`, `ALL_IN` |
| `0600-basis-kauf` | 6:00, BASIS | 1567 Gold, voll, im Inventar Dorans Klinge und 2 Langschwerter | `KAUFEN` | – |
| `1315-crash-dann-back` | 13:15, Modus SEITE: Sein äußerer Top-Turm ist gefallen, deshalb ist die Lane-Phase vorbei. Abnahme erst mit Schritt 4. | 47 % Leben, 1899 Gold, 11 eigene Vasallen an seinem **inneren** Top-Turm (s ≈ 0,80), Sett lebt 4200 entfernt | `BACK_JETZT` / `WELLE_REIN_UND_BACK` | `PLATTEN` (47 % mit Sett in der Nähe) |

Zusätzlich:

- **`0600-basis-kauf`:** `muss_ziel`. Welches Item, entscheidet `kaufplan` aus dem Lexikon-Build.
  Riven hatte 2 Langschwerter, der Kern-Build führt über den Axiombogen, also ist nicht zwingend der
  Brutalisierer gemeint. Der Test prüft den Plan `KAUFEN` und dass der Satz ein Ziel nennt. Dass ein echter
  Item-Name fällt, prüft die Fabrik-Lage `k-basis-kauf-und-ziel`.
- **`1315-crash-dann-back`:** Beim Eintritt in die Basis (~13:23) ist eine `BESTAETIGUNG` erlaubt, aber keine
  Pflicht.

### 7.2 Konstruiert

`tests/szenarien/konstruiert/recall.toml`, Format wie `lane.toml` (Buch 1, 6.2).

**Bestätigungen** hängen an einer Abfolge (Crash → Recall → Basis) und lassen sich nicht mit einer einzelnen
Lage prüfen. Claude Code schreibt dafür einen Folgetest mit drei Takten in `tests/test_bausteine.py`
(`bestaetigung_back_im_fenster`). Dazu kommt `1315-crash-dann-back` in Schritt 4.
