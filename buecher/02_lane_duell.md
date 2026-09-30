# Buch 2 – Lane-Duell: wann traden, wann nicht (mit Riven-Teil)

> **ZURÜCKGESTELLT** (Carlos, 28.09.2026 03:25): erst Makro (Buch 4), Mikro später. Nicht umsetzen, bis ein Auftrag es ausdrücklich verlangt.

Stand 28.09.2026. Dieses Buch füttert:

- `kern/duell.py` (neu), das Urteil Du gegen deinen Lane-Gegner
- die Handlungen `TRADE`, `ALL_IN` und `MEIDEN` in LANE und SEITE
- die Gefahr durch den Lane-Gegner (ersetzt die Behelfsregel R5)
- die Lane-Sätze, das Matchup-Wissen in Antworten und im Rückblick

Den Riven-Teil (Kapitel 6) hätte eigentlich Buch 8 gebracht. Er steht hier, weil Carlos fast nur Riven Top spielt.
Camille und Graves folgen später nach demselben Muster.

**Für Claude Code:**

- Lies zuerst Buch 0, Kapitel 6.2 (Kill-Beleg) und 7.5, Buch 7, Kapitel 1–3, und `lolcoach/denker.py`
  (`kampf_faktoren`, `urteil`, `_combo`, `_combo_er`, `_matchup`).
- Vieles davon gibt es schon im alten System. Dieses Buch holt es in den Kern, misst es und stellt die Sprache um.

---

## 0. Befund

1. **Der Kern kennt das Matchup nicht.** `kraefte()` vergleicht nur Level, Item-Gold und Leben. Riven gegen Gangplank
   ist damit dasselbe wie Riven gegen Cho'Gath.
   - Folgen: „Raus: Cho'Gath kommt“ bei vollem Leben (173159). „Raus, zum Turm!“ in einem Level-2-Kampf, den Riven
     gegen Rumble gewann (213624). Aber auch umgekehrt: Gangplank tötet Riven zweimal allein (144655), und niemand
     warnt vor dem Matchup.
2. **Das alte System weiß viel mehr,** aber der Kern nutzt es nicht:
   - `denker.kampf_faktoren` rechnet deinen Combo gegen sein Leben (`combo.py`, für Riven von Hand geprüft) und
     seinen Combo gegen dein Leben.
   - Dazu die Siegquote des Matchups (Lexikon), die Lane-Kurve je Phase (`wissen/lane_kurve.toml`), den Jungler,
     einen dritten Gegner, den Turm und die Zone (Teemo-Pilze, Heimerdinger-Geschütze).
3. **Niemand hat gemessen, ob diese Faktoren Lane-Duelle vorhersagen.** Das Kampfmodell aus Buch 7 hat es für alle
   Kämpfe nicht geschafft (AUC 0,30 für Gold). Lane-Duelle sind aber die häufigsten Kämpfe in echten Partien und die
   einfachsten: zwei Spieler, gleiche Welle, sichtbares Leben.
4. **Die Lane-Sätze sind entweder stumm oder Mikro.** „Trade Yasuo: dein Combo macht etwa 1280, Yasuo hat nur 810
   Leben.“ Der Grund ist richtig, aber ein Riven-Main braucht keinen Combo erklärt. Er braucht das **Wann**.

## 1. Prinzipien

1. **Wann, nicht wie.** Der Coach sagt, **wann** ein Trade oder All-in richtig ist und **warum**. Die Tastenfolge
   sagt er nie; die kennt Carlos.
2. **Fenster entstehen durch Ereignisse:**
   - Spike: Level 2, 3, 6, ein fertiges Item.
   - Sein Leben fällt.
   - Sein Flash ist weg.
   - Sein Jungler ist weit weg.
   - Deine Fähigkeiten sind wieder da.

   Nur beim Aufgehen eines Fensters wird gesprochen, einmal.
3. **Das Matchup ist Wissen, keine Zahl im Satz.** Ein Lehrsatz je Partie zur richtigen Zeit reicht: „Gegen
   Gangplank: dein W erst nach seinem W, sein W reinigt den Stun.“ Die Siegquote bleibt auf dem Dashboard.
4. **Eigene Fähigkeiten sind Pflicht:** Kein Trade-Ruf ohne die Kern-Fähigkeiten (Riven: Q und E, siehe Kapitel 6).
   Das ist sichtbar (HUD) und einer der häufigsten echten Fehler: traden ohne Flucht.
5. **Messen vor Sprechen.** Das Duell-Urteil spricht Angriffe erst, wenn es an echten Lane-Duellen besser trifft als
   der Zufall (Kapitel 5). Vorher bleiben nur Rufe **gegen** einen Kampf und die Spike-Sätze, die ohne Modell gelten.

## 2. Das Duell-Urteil (`kern/duell.py`)

```
duell.urteil(m) -> (art, wert, faktoren)       # art in ALL_IN | TRADE | NEUTRAL | MEIDEN
```

- **Eingang:** `denker.kampf_faktoren(b)`, unverändert als Rechnung. Neu ist:
  - Die Gegnerwerte laufen über die Schätzung aus Buch 7, 3.2, wenn sie veraltet sind. Der Lane-Gegner ist meist
    frisch gesehen, das trifft also selten.
  - Die Kern-Fähigkeiten aus dem HUD (Kapitel 6) sind ein eigener Faktor: Fehlt eine, gilt „nicht bereit“ (−2).
- **Wert:** Die Summe der Faktoren ohne „turm“, wie in `denker.urteil`.
- **Arten:**

| Art | Bedingung (Startwerte, `[duell]`) |
|---|---|
| `ALL_IN` | Kill-Beleg aus Buch 0, 6.2: `combo_kill`, **oder** Wert ≥ `all_in_ab` (3,0). Dazu: kein Jungler oder Dritter mit `p_da(10 s)` ≥ 0,2, nicht unter seinem Turm (Buch 7, 6), Kern-Fähigkeiten bereit. |
| `TRADE` | Wert ≥ `trade_ab` (1,2), sein Combo tötet dich nicht (`combo_er` fehlt), Kern-Fähigkeiten bereit, Jungler wie oben. |
| `MEIDEN` | Wert ≤ `meiden_ab` (−1,2) **oder** `combo_er` **oder** Lane verloren (Qualitätsrunde A). |
| `NEUTRAL` | alles andere |

**Ersetzt R5 (Lane-Gegner allein ist keine Gefahr):**

- Kommt nur der Lane-Gegner, entscheidet das Duell-Urteil.
- Bei `MEIDEN` greift die Gefahr bzw. der Schutzplan wie gehabt.
- Bei `NEUTRAL` oder besser gibt es keine GEFAHR.
- Kommt ein zweiter Gegner, gilt wieder Buch 0, 7.5.

## 3. Handlungen und Sätze in LANE (und SEITE gegen den Lane-Gegner)

| Handlung | Kandidat, wenn | Satz (≤ 14 Wörter, Grund aus dem Fenster) |
|---|---|---|
| `ALL_IN` | Art `ALL_IN` **und** ein Fenster ging gerade auf (Kapitel 4) | „All-in jetzt: Gangplank hat 40 %, sein Jungler ist unten.“ |
| `TRADE` | Art `TRADE` **und** ein Fenster ging gerade auf | „Kurzer Trade jetzt: du hast 6, er nicht.“ |
| `MEIDEN` | Art wechselt zu `MEIDEN` (einmal je Wechsel) | „Kein Trade: dein E ist weg.“ / „Er hat 6, du nicht: kein Trade bis 6.“ |
| `WELLE_HALTEN` (Schutzplan) | Lane verloren (bleibt wie in Qualitätsrunde A) | bleibt |

**Regeln:**

- Ein Trade-Satz nur beim **Aufgehen** eines Fensters, höchstens einer je `trade_abstand_s` (45 s). Kein Satz, wenn
  Carlos schon kämpft, dann gilt Buch 7.
- `MEIDEN` wird gesagt, wenn Carlos auf den Gegner zuläuft (≤ 800, Abstand sinkt) und die Art `MEIDEN` ist. Sonst
  bleibt es stumm.
- Die Zahl im Satz ist das **Leben in Prozent** („hat 40 %“), nie Schadenszahlen.

## 4. Fenster in der Lane

| Fenster | Erkennung | Satz-Grund |
|---|---|---|
| **Dein Level-Spike** (2, 3, 6) vor ihm | Levels aus der API; sein Level, wenn er ≤ 10 s gesehen ist | „du hast 6, er nicht“ |
| **Sein Level-Spike** vor dir | wie oben | MEIDEN: „er hat 6, du nicht“ |
| **Dein Item fertig**, er ohne vergleichbares | eigene Items (API) gegen sein Item-Gold (frisch gesehen) | „Brutalisierer fertig, er hat noch nichts“ |
| **Sein Leben** ≤ `leben_fenster` (0,5), deins ≥ 0,7 | Balken (≤ 2,5 s alt) und API | „er hat 40 %“ |
| **Sein Flash weg** | `zauber` (Chat-Ping, bestätigter Sprung) | „ohne Flash“ |
| **Sein Jungler weit weg** | Jungler gesehen auf der anderen Kartenseite ≤ 20 s | „sein Jungler ist unten“ |
| **Deine Kern-Fähigkeiten wieder bereit** nach einem Trade | HUD | nur als Grund, kein eigener Satz |

Jedes Fenster wird nur als **Übergang** gesprochen, von zu nach offen. Ein Fenster, das offen bleibt, wird nicht
wiederholt.

## 5. Messen (`werkzeuge/duell_eichung.py`, Pflicht vor den Angriffs-Sätzen)

1. **Lane-Duelle finden**, nur in echten Partien (`bots = false`, CLASSIC und SWIFTPLAY getrennt).
   - Du und dein Lane-Gegner sind ≤ 800 voneinander, beide nehmen in 5 s Schaden (dein Leben fällt, sein Balken
     fällt), und kein weiterer Champion ist in 1500. Das Ende ist 5 s ohne Schaden.
2. **Ausgang:**
   - Sieg: er stirbt, oder sein Leben fällt um ≥ 15 Punkte mehr als deins.
   - Niederlage: umgekehrt.
   - Sonst offen.
3. **Urteil am Anfang:** `duell.urteil` 0,5 s vor dem ersten Schaden. Gemessen wird AUC und Brier, je Art.
4. **Soll für Angriffs-Sätze:** AUC ≥ 0,65 bei ≥ 30 entschiedenen Duellen. Vorher sind `ALL_IN` und `TRADE` stumm
   (berechnet, im Protokoll „stumm: Duell nicht geeicht“). `MEIDEN` und Spike-Sätze dürfen sprechen, sie verhindern
   Kämpfe und schicken nicht hinein.
5. **Kill-Beleg separat:** Trat `combo_kill` auf, starb der Gegner dann, wenn Carlos einstieg? Der Anteil kommt nach
   messungen.md. Liegt er ≥ 70 % (bei ≥ 10 Fällen), darf `ALL_IN` mit `combo_kill` auch ohne bestandene Eichung
   sprechen.

## 6. Riven (Parameter; eigentlich Buch 8)

Quelle: `wissen/lexikon/champions/Riven.md` (Stand 26.19) und `wissen/build_carlos.toml`.

**Kern-Fähigkeiten und Flucht:**

- Kern: **Q** (irgendeine Ladung bereit laut HUD) und **E**. Fehlt eine, gibt es kein TRADE und kein ALL_IN.
- Flucht: E 250, Q 3 × 225 (Q3 springt über dünne Wände), Flash 400. Das geht in `[kampf.champion].Riven.flucht`
  (Buch 7) und ersetzt den Startwert dort.
- Fehlen Q **und** E und steht der Gegner ≤ 600 mit mehr Leben als du: „Raus: Q und E sind weg.“ (MEIDEN, einmal je
  Vorfall). Das ist der häufigste Riven-Fehler und in echten Partien der Satz mit dem meisten Lehrwert.

**Spikes** (für Kapitel 4):

- Level 3 (alle drei Grundfähigkeiten), Level 6 (R: +20 % AD, Windschnitt), Level 11 und 16 (R-Abklingzeit).
- Items in Carlos' Reihenfolge (`build_carlos.toml`): Axiombogen → Eklipse oder Endloser Hunger → Hydra. Das erste
  fertige Item zählt als Spike.
- Der **Windschnitt** richtet ab ≤ 25 % Leben am meisten Schaden an. Liegt sein Leben ≤ 30 % und dein R ist bereit
  bzw. aktiv, ist das der Kill-Grund: „Windschnitt: er hat 25 %.“

**Reichweite fürs Einsteigen:** 650 (E + Q), mit Flash 1050. Bleibt wie Buch 7.

**Matchups:** Leg `wissen/matchups/Riven.toml` an, aus dem Abschnitt „Matchups“ des Lexikons. Je Gegner:

```toml
[Gangplank]
siegquote = 49.1                     # lolalytics Emerald+, Stand im Kopf der Datei
fenster = "dein W erst nach seinem W, sein W (Skorbut entfernen) reinigt deinen Stun"
gefahr = "Fässer zwischen dir und ihm"
all_in = "Level 3 mit Entzünden, wenn sein W weg ist"
lehrsatz = "Gegen Gangplank: dein W erst nach seinem W, sein W reinigt den Stun."
```

- Nur, was im Lexikon steht. Nichts dazuerfinden.
- `lehrsatz` höchstens 14 Wörter, gebaut aus `fenster` oder `gefahr`.
- **Gesprochen wird er** einmal kurz vor dem ersten Trade-Fenster oder bei Level 3, und noch einmal bei Level 6, wenn
  `all_in` etwas zu Level 6 sagt.
- **In Antworten:** Bei WARUM- und SOLL_ICH-Fragen zum Lane-Gegner steht der Lehrsatz als Grund zur Verfügung.
- **Im Rückblick:** Beim Duell-Tod (Buch 7, Kapitel 8) wird „Schau es dir im Review an“ durch den Lehrsatz ersetzt,
  wenn er zum Tod passt.

## 7. Parameter (`wissen/kern.toml`)

```toml
[duell]
stand = "Buch 2, 28.09.2026 - Startwerte, an Lane-Duellen eichen (Kapitel 5)"
all_in_ab = 3.0
trade_ab = 1.2
meiden_ab = -1.2
jungler_p_max = 0.2
leben_fenster = 0.5
leben_eigen_min = 0.7
trade_abstand_s = 45
meiden_abstand = 800
eichung_min = 30
eichung_auc_min = 0.65
combo_kill_anteil_min = 0.7
combo_kill_faelle_min = 10
riven_kern = ["Q", "E"]
```

## 8. Szenarien und Abnahme

**Szenarien** (zuerst rot):

| Aufnahme | Zeit | Soll |
|---|---|---|
| 173159 | 7:45 und 9:18 | „Cho'Gath kommt“ nur bei `MEIDEN` |
| 144655 | 1:37 | Lehrsatz Gangplank statt nur „Gangplank ist vorn“; Ort und Form des Satzes beim Nachspielen festlegen |
| 164326 | ein Moment, in dem Riven ohne Q und E vor Teemo stand und Leben verlor | „Raus: Q und E sind weg.“ (Stelle beim Nachspielen suchen, begründen) |
| 213624 | 1:11 und 1:17 | kein Rückzug im gewonnenen Level-2-Duell; Bot-Partie, nur Verdrahtung |

**Abnahme:**

1. `duell_eichung.py` ist gelaufen. Anzahl, AUC und Brier stehen in messungen.md, dazu die Entscheidung, ob
   `ALL_IN`/`TRADE` sprechen.
2. `wissen/matchups/Riven.toml` für alle Gegner aus dem Lexikon. Ein Test prüft, dass jedes Feld im Lexikon belegt ist.
3. Die Kritik läuft wie in Auftrag 005, eine Runde. In den Lane-Phasen der echten Partien gibt es kein „falsch“ zu
   Lane-Sätzen.
