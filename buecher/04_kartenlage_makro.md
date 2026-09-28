# Buch 4 – Kartenlage und Makro: alles im Blick, jeder Rat mit Warum

Stand 28.09.2026. Dieses Buch füttert:

- `kern/kartenlage.py` (neu): wo die Gegner sind und was daraus folgt
- `kern/teamplan.py` (neu): wer will das Spiel wann entscheiden
- die Makro-Sätze in `kern/fuehren.py` (Buch 11)
- die Warum-Regeln für alle Ansagen und Antworten

**Carlos, 28.09. 03:25:**

> „Lass uns erstmal darum kümmern, dass wir einen Makro-Challenger-Coach haben, der alles im Blick hat und mich mit
> wertvollen Infos und den nächsten Schritten füttert und warum ich diese tun soll. Das Warum ist wichtig, damit ich
> sehe, dass dahinter Reasoning ist und kein Geschwafel.“

Mikro-Themen (Trades, Matchups, Combos, Buch 2) sind **zurückgestellt**, bis die Makro-Ebene steht.

**Für Claude Code:**

- Lies zuerst Buch 0, Kapitel 7.5, Buch 5, Kapitel 2, Buch 6, Kapitel 3, Buch 11 und `lolcoach/jungle.py`.
- Stellen, die andere Bücher ändern, sind mit **„Ändert …“** markiert.
- Jede Zahl gehört nach `kern.toml [makro]`.

---

## 1. Prinzipien

1. **Makro-Sätze schließen in drei Schritten:** Beobachtung, Folgerung, Handlung.
   - „Xin unten gesehen: oben 30 Sekunden frei, nimm die Platten.“
   - „Vier von ihnen am Drachen: den gebt ihr ab, nimm den Top-Turm.“
   - „Ihr Top hat kein TP bis 24:10: Split oben ist sicher.“

   Die Beobachtung ist das Warum. Carlos soll sie auf der Minimap wiederfinden können.
2. **Nur Gesehenes, mit Alter:** „vor 10 Sekunden unten“, „seit 40 Sekunden nicht gesehen“. Eine Folgerung ist als
   Folgerung erkennbar („wahrscheinlich unten“), nie als Tatsache.
3. **Information ist Treibstoff, kein Nachrichtenticker.** Eine Info wird nur gesagt, wenn sie
   - den besten nächsten Schritt ändert,
   - eine Option öffnet,
   - oder vor etwas warnt.

   „Sona ist unten“ allein ist Geschwafel. „Sona und Caitlyn unten: Mid-Turm ist frei“ ist Makro.
4. **Der entscheidende Grund zuerst.** Genannt wird der Grund, der die Wahl entschieden hat, nicht irgendeiner
   (Kapitel 4).
5. **Die Lage über 1–3 Minuten.** Makro heißt vorausdenken: Timer, Respawns, Spikes und die Frage, wer das Spiel wann
   entscheiden will (Kapitel 3).

## 2. Kartenlage (`kern/kartenlage.py`)

Die Kartenlage wird in jedem Takt gebaut, aus Minimap, API und Ereignissen. Je Gegner:

| Feld | Bedeutung |
|---|---|
| `zuletzt` | Ort, Kartenseite (oben/Mitte/unten/Basis) und Alter der letzten Sichtung |
| `vermutlich` | wahrscheinliche Kartenseite jetzt: Jungler über `jungle.wahrscheinlich` (geeicht), andere über `p_seite` (Buch 0, 7.5), Tote „Basis“ bis Respawn |
| `mia` | Laner in der Lane-Phase: ≥ `mia_s` (15 s) ungesehen und nicht tot oder in der Basis |
| `tot_bis` | Respawn-Zeit |
| `zauber` | Flash und TP, wenn bekannt (Zeitleiste) |
| `stand` | Level und Item-Gold, mit Schätzung aus Buch 7, 3.2 bei veralteten Werten |

Zusammenfassung: **wie viele von ihnen oben, in der Mitte, unten, unbekannt, tot.** Das Dashboard zeigt sie ständig,
und sie steht in `kern.kontext()`.

**Das Fenster je Kartenseite** ist die Zeit, bis der erste Gegner dort sein kann. Das ist die Laufzeit aus seiner
letzten Sichtung bzw. dem Brunnen nach dem Respawn, für Unbekannte mit `p_seite`. Das ist dieselbe Rechnung wie
`karte.verteidiger`, nur für die ganze Seite statt für einen Turm.

## 3. Teamplan (`kern/teamplan.py`)

„Wer will das Spiel wann entscheiden?“

- **Kurve je Team:** die Summe aus `wissen/lane_kurve.toml` [frueh, sechs, spaet] der fünf Champions.
- **Stand:** Gold-Vorsprung (Item-Gold beider Teams, geschätzt), Türme, Drachen und Seelenpunkt, Baron,
  Level-Durchschnitt.
- **Plan-Satz,** einer von vier:

| Lage | Plan | Beispiel-Satz |
|---|---|---|
| vorn und jetzt stärker | erzwingen: Objectives und Türme mit der Gruppe, Kämpfe annehmen | „Ihr seid vorn und jetzt stärker: Drache und Türme erzwingen, als Gruppe.“ |
| vorn, aber sie skalieren besser | beenden, bevor es kippt: Baron oder Inhibitor, kein Farm-Spiel | „Ihr seid vorn, aber sie skalieren: vor Minute 30 Baron oder Inhibitor.“ |
| hinten, aber ihr skaliert besser | Zeit gewinnen: Wellen halten, keine erzwungenen Kämpfe, Objectives tauschen | „Ihr skaliert besser: nichts erzwingen, Wellen halten, ab 30 Minuten seid ihr stärker.“ |
| hinten und sie sind stärker | Chancen suchen: Picks, Seitenwellen, Tausch statt Kampf | „Sie sind vorn und stärker: kein 5 gegen 5, Picks und Seitenwellen.“ |

**Carlos' Rolle darin** (Riven Top, Buch 5): Split oder Gruppe. Die Split-Regel aus Buch 5, 3.1 gilt weiter. Der
Teamplan setzt ihr die Richtung: Erzwingen heißt Gruppe, Zeit gewinnen heißt Seitenwellen.

**Gesagt wird der Plan-Satz**

- einmal um 14:00, am Übergang ins Mid-Game,
- bei einem Umschwung: Gold-Vorsprung ändert sich um ≥ 2000 seit dem letzten Plan-Satz, Inhibitor fällt, Baron,
  Seele,
- höchstens einmal je `teamplan_abstand_s` (300 s).

Der Plan ist die Richtung für `danach` und die Vorschau (Buch 11). Beim Gleichstand zweier Handlungen gewinnt die,
die zum Teamplan passt.

## 4. Das Warum (ändert Buch 0, 9.3 und Buch 11, Kapitel 4 und 5)

**Jede gesprochene Handlung hat einen Grund der Form Beobachtung → Folgerung.**

- **Der entscheidende Grund:** Von den Größen, die den EV der gewählten Handlung gegenüber der zweitbesten tragen,
  wird die mit dem größten Beitrag gesagt. Sie steckt in den sechs Fragen aus Buch 0, 7.6 (wer kann stören, wie
  lange, was bringt es …).
  - Gesagt wird sie als Beobachtung („Xin unten gesehen“), nicht als Zahl („EV 340“).
  - Messen: Die Handlung wird ohne diese Größe neu gerechnet. Kippt dadurch die Wahl, war sie entscheidend.
- **Höchstens zwei Gründe** je Satz. Der zweite nur, wenn er allein nicht reicht („… und euer Jungler ist oben“).
- **Verbotene Gründe** (Test über alle Satzbausteine):
  - Floskeln: „bis sich etwas öffnet“, „Danach rechne ich neu“.
  - Tautologien: „weil es sich lohnt“, „das ist gut“.
  - Gründe ohne Beobachtung: „dort nimmt sie sonst niemand“ nur, wenn dazu gesagt wird, wo dein Team ist („dein Team
    ist unten“).

**WARUM-Antworten** (Buch 11, 5), zwei Sätze:

1. Die entscheidenden Beobachtungen.
2. Der Vergleich mit der Alternative, die Carlos nennt (oder der zweitbesten), mit deren konkretem Nachteil.

Beispiel: „Drache, weil drei von ihnen unten tot sind und euer Team dort steht. Der Turm oben hätte Rumble in 15
Sekunden bei dir.“

## 5. Makro-Infos: wann welcher Satz (ergänzt Buch 11, 4 FENSTER und VORSCHAU)

| Anlass | Bedingung | Satz |
|---|---|---|
| **Jungler-Sichtung, weit weg** | Ihr Jungler gesehen auf der anderen Seite, und dein Plan kann das Fenster nutzen (Platten, Turm, Seitenwelle, Invade) | „Xin unten gesehen: oben 30 Sekunden frei, Platten jetzt.“ |
| **Jungler-Sichtung, nah** | Ihr Jungler gesehen auf deiner Seite, du stehst vor der Mitte deiner Lane | „Xin oben gesehen: zurück hinter die Welle.“ (GEFAHR-Regeln gelten) |
| **MIA** | Dein Lane-Gegner oder ihr Mid fehlt seit ≥ 15 s, kann in ≤ 10 s bei dir sein, du stehst vorn | „Rumble fehlt seit 20 Sekunden: nicht weiter vor.“ |
| **Tausch quer über die Karte** | ≥ 3 Gegner an einem Ort (Objective, Belagerung), dein Fenster anderswo ≥ Dauer + Weg | „Vier von ihnen am Drachen: nimm den Top-Turm, 40 Sekunden.“ |
| **Gruppierung** | ≥ 3 Gegner sichtbar zusammen in der Mitte oder auf deiner Seite, Mid-Game | „Vier von ihnen Mitte: Seitenwelle nur bis zum Fluss.“ |
| **Spike beim Gegner** | Ihr stärkster Kämpfer (Kills plus Item-Gold) schließt ein Item ab oder erreicht Level 6/11/16, frisch gesehen | „Ihr Yone hat zwei Items: Kämpfe nur noch mit Team.“ |
| **Teamplan** | Kapitel 3 | wie dort |
| **Objective-Vorlauf** | Buch 11 VORSCHAU mit Warum | „Drache in 80 Sekunden: jetzt Bot-Welle, ihr habt dort Prio.“ |

**Grenzen:**

- **Budget:** Makro-Infos teilen sich das Budget mit FENSTER und VORSCHAU, höchstens eine je `makro_abstand_s`
  (45 s). GEFAHR und WENDEPUNKT gehen vor.
- **Nur mit Wirkung:** Eine Info ohne Wirkung auf deinen Plan wird nicht gesagt, sie steht auf dem Dashboard.
- **Keine Doppelung:** Dieselbe Info (Gegner, Seite) wird höchstens einmal je 60 s gesagt, außer die Folgerung ändert
  sich.

## 6. Messen

- **Neue Kritiker-Frage:** Ist das Warum nachvollziehbar, also mit einer Beobachtung, die auf der Minimap oder in der
  Lage stimmt? Die Kritiker (wie in Auftrag 005) bewerten das je Satz mit ja oder nein. **Soll: ≥ 90 % ja** in den
  echten Partien.
- **„Info ohne Folgen“** ist eine eigene Klasse. Soll: 0 je 30 min.
- **Leerlauf** (Buch 11, 7) bleibt die Kennzahl für „er füttert mich“, Soll ≤ 10 %.
- **Szenarien aus den Partien:**
  - 164326 und 173159: Um 14:00 kommt ein Teamplan-Satz. Er passt zum Stand (Gold, Kurven); die Kurven-Summe steht
    im Szenario.
  - 213624, 16:35 (alle tot): ein Makro-Satz mit Beobachtung, zum Beispiel „Drei von ihnen tot: Mid-Inhibitor
    jetzt“.
  - 173159: eine Jungler-Sichtung auf der anderen Seite, die ein Fenster für Platten oder Seitenwelle öffnet. Die
    Stelle wird beim Nachspielen gesucht und begründet.

## 7. Parameter (`wissen/kern.toml`)

```toml
[makro]
stand = "Buch 4, 28.09.2026 - Startwerte"
mia_s = 15
mia_nah_s = 10
tausch_min_gegner = 3
gruppe_min_gegner = 3
makro_abstand_s = 45
info_wiederholen_s = 60
teamplan_abstand_s = 300
teamplan_umschwung_gold = 2000
teamplan_ab_s = 840
max_gruende = 2
```

## 8. Was zurückgestellt ist

Buch 2 (Lane-Duell, Matchups, Riven-Kit) liegt in `buecher/02_lane_duell.md` und bleibt zurückgestellt.

Bis es kommt, gelten für den Lane-Gegner die Behelfsregeln:

- R5 und die Überlegenheits-Regel (Aufträge 002, 004)
- der Schutzplan bei verlorener Lane (Qualitätsrunde A)
