# Buch 11 – Führen: nächster Schritt, Vorausschau, Antworten

Stand 27.09.2026. Dieses Buch füttert:

- `kern/zeitleiste.py` (neu): was in den nächsten 3 Minuten passiert.
- `kern/plan.py`: Jeder Plan bekommt ein `danach`.
- `kern/sprechen.py`: Wendepunkte, Vorschau und Optionen.
- `kern/fragen.py` (Schritt 6, Buch 0 Kapitel 10): Antworten aus demselben Plan.

Das Review nach dem Spiel („wie ein Coach lehrt“) war früher als Buch 11 geplant. Es wird Buch 12.

Für Claude Code: Lies zuerst Buch 0, Kapitel 8, 9 und 10, Buch 5, Kapitel 2 und Buch 6, Kapitel 3. Stellen, die ein
anderes Buch ändern, sind mit **„Ändert …“** markiert. Jede Zahl gehört in `kern.toml` (Kapitel 9).

---

## 0. Befund: Partie 213624 (Carlos, Riven gegen Rumble, 27.09.)

Carlos lag 29/1/3 vorn. Er hat trotzdem **fünfzehn Mal** gefragt, was er jetzt tun soll:

- 9:44 und 9:55: „Der erste Tower ist down, was jetzt?“
- 12:05 bis 12:56: „Warum Top und nicht Drache?“, „Zum Drachen oder zum Turm? Du widersprichst dich.“
- 13:12, 13:36, 13:48, 14:37, 16:40: „Was mache ich jetzt?“, „Drache ist tot, wo gehe ich jetzt hin?“, „Was mache
  ich, nachdem der Tower tot ist?“

Seine Notizen sagen dasselbe:

> 17:08: „Du musst die nächsten Schritte schon ein bisschen früher kommunizieren … man hat ständig einen Leerlauf,
> man wartet auf Anweisungen … Du musst in der Lage sein, zwei, drei Minuten in die Zukunft zu gucken.“
>
> 20:32: „Du sagst nicht, was die nächsten Schritte sind … Wenn das und das passiert, machst du das und so. Also so,
> dass man weiß, wo man die nächsten Moves hinmacht, damit man sich effizient bewegen kann.“

Nach dem Spiel (22:12) hat er präzisiert:

> „Er soll, wenn nichts zu sagen ist, gerne still sein. Aber wenn es darum geht, meine nächsten Moves zu machen und
> warum ich sie tue, basierend auf dem aktuellen Spielstand, erst recht im hektischer werdenden Mid- und Late-Game,
> da gibt es eigentlich immer was zu sagen: Gegner X hat Flash genutzt, diese Option könntest du machen, weil es
> unwahrscheinlich ist, dass du gestört wirst … kein Mist erzählen, sondern mehr Qualität über den Game State und
> die nächsten besten Schritte.“

**Die Antworten waren schlecht:**

- 12:56: „Drache lebt.“ als einzige Antwort auf „Zum Drachen oder zum Turm?“
- 13:16: „Drache lebt.“ auf „Welche Welle, auf welcher Lane?“
- 13:36: „Drache in 4 Minuten 57.“ auf „Drache ist tot, wo gehe ich jetzt hin?“
- 12:05 bis 12:38: drei Antworten, drei Richtungen (Top, Drache, „zurück Richtung Turm“)
- 1:19: „Geh rein auf Rumble“, während der Kern gerade „Raus, zum Turm!“ gesagt hatte

**Die Ursachen:**

1. **Leitsatz 7 aus Buch 0 („Schweigen ist ein Rat“) ist zu weit gefasst.** Er stimmt, solange Carlos einen Plan
   ausführt. Ist der Plan erledigt (Turm fällt, Drache fällt, Back vorbei, Respawn), ist Schweigen **Leerlauf**.
2. **Der Plan kennt nur den nächsten Schritt**, nie den übernächsten. „Was danach?“ kann er deshalb nicht beantworten,
   und der Übergang kommt zu spät.
3. **Es gibt keine Zeitleiste.** Was in 1–3 Minuten kommt (Herold, Respawns, Flash zurück, Back-Bedarf), weiß der
   Kern nur einzeln, nie zusammen.
4. **Die Fragen laufen noch über das alte System** (Schritt 6 fehlt). `sofort` antwortet mit Stichworten, Claude
   bekommt die Rohlage statt des Plans. Deshalb widersprechen sich Ansage und Antwort.

## 1. Prinzipien

1. **Carlos hat immer einen gesagten Plan im Kopf:** was jetzt, was danach, worauf achten. Ist er erledigt oder
   ungültig, kommt der nächste **sofort**, auch ohne Frage.
2. **Vorausschau 1–3 Minuten.** Ein Challenger-Kollege denkt ständig voraus: „Herold in 90 Sekunden, vorher back“,
   „Rumble ist 40 Sekunden tot, das reicht für den inneren Turm“, „Ihr Top hat kein TP bis 24:10, Split ist sicher“.
3. **Bedingte Pläne:** „Wenn X, dann Y.“ Höchstens eine Bedingung je Satz. So kann Carlos handeln, ohne auf den
   Coach zu warten.
4. **Optionen offen legen:** Liegen zwei Handlungen dicht beieinander, nennt der Coach beide mit ihrem Unterschied.
   Das entspricht auch Riots Linie: Entscheidungen zeigen, nicht diktieren.
5. **Still ist gut, Leerlauf nicht.** Still bleibt der Coach, während Carlos einen gesagten Plan ausführt und nichts
   Neues passiert. Nie nach einem Wendepunkt.
6. **Jeder Satz: Handlung und Grund aus dem Spielstand.** „Geh Top“ allein gibt es nicht. „Top, dort nimmt die Welle
   sonst niemand“ ist ein Grund.
7. **Eine Wahrheit.** Ungefragte Ansagen und Antworten kommen aus demselben Plan und derselben Zeitleiste. Eine Antwort,
   die dem Plan widerspricht, gibt es nicht. Ändert sich der Plan, sagt die Antwort das: „Neu: …, weil …“.
8. **Kein Mist.** Was der Coach nicht sicher weiß, sagt er nicht, oder er sagt ehrlich „unsicher“.

## 2. Die Zeitleiste (`kern/zeitleiste.py`)

Die Zeitleiste wird in jedem Takt neu gebaut. Sie ist eine sortierte Liste von Ereignissen in den nächsten
`zeitleiste_s` (180 s):

| Ereignis | Quelle | Beispiel |
|---|---|---|
| Objective spawnt | Buch 6, Kapitel 2 | „Herold 15:00“ |
| Gegner steht wieder auf | Respawn | „Rumble lebt ab 12:31“ |
| Gegner-Zauber zurück | `zauber` (Flash, TP), nur bekannte | „Sona Flash ab 13:10“ |
| Euer Fenster endet | Tote plus Weg aus dem Brunnen (Buch 5, Kapitel 8) | „Fenster Mid bis 17:02“ |
| Buff endet | Baron-Buff 180 s, Ältester | „Baron-Buff bis 26:40“ |
| Inhibitor steht wieder auf | Ereignisse | „euer Mid-Inhibitor ab 38:18“ |
| Deine Welle kommt an | Wellentakt (Buch 1) | „Top-Welle an deinem Turm 12:48“ |
| Dein Back-Bedarf | Gold zur nächsten Stufe (Buch 3), Leben | „Eklipse kaufbar ab ~12:40“ |
| Dein TP zurück | Quest-TP, Auftrag 002 | „TP ab 19:30“ |

Nur bekannte Ereignisse kommen hinein. Ein Flash ohne Beleg erscheint nicht.

Die Zeitleiste steht auf dem Dashboard und in `kern.kontext()` für Claude.

## 3. Der Weg: `jetzt` → `danach` (Ändert Buch 0, 8.1)

Der Plan bekommt ein Feld `danach: Handlung | None`.

**Rechnung:**

1. **Projektion.** Nimm den Zustand, der nach der jetzigen Handlung erwartet wird:
   - Zeit = jetzt + Weg + Dauer.
   - Ort = das Ziel der Handlung.
   - Die Zeitleiste ist bis dahin fortgeschrieben (wer lebt wieder, was ist gespawnt).
   - Dein Gold = jetzt + Gewinn der Handlung.
2. **Beste Handlung im projizierten Zustand.** Dieselbe Kandidatenrechnung wie im Kern (Karten-Rechnung Buch 5,
   Objectives Buch 6, Back Buch 3), aber aus der projizierten Lage.
3. Das Ergebnis ist `danach`. Es wird **nicht** gespielt, nur gesagt und angezeigt. Ist die jetzige Handlung
   erledigt, wird `danach` normal neu geprüft und kann sich ändern.

`danach` fällt weg bei GEFAHR, in KAMPF und wenn die jetzige Handlung kürzer als 5 s dauert.

**Beispiel 213624, 9:55** (Turm fällt, Drache lebt, vier von euch sind unten):

- `jetzt` = `WELLE_REIN` (8 s).
- `danach` = `NEHMEN` Drache mit Pantheon, Mundo und Karma.
- Der Satz: „Turm ist down: Welle rein, dann zum Drachen, ihr seid dort zu viert.“

## 4. Wann der Coach spricht (Ändert Buch 0, 9.1 und 9.2)

In dieser Rangfolge:

| Anlass | Wann | Budget |
|---|---|---|
| **GEFAHR** | wie bisher (Buch 0, 7.5; Buch 7) | frei |
| **WENDEPUNKT** | die jetzige Handlung ist erledigt oder ungültig: Struktur fällt, Objective fällt (egal wer), Kill oder Tod in ≤ 2000 um dich oder dein Ziel, Back beendet (du verlässt die Basis), Respawn, dein Rückzug ist sicher angekommen | frei, aber höchstens 1 je 8 s |
| **FENSTER** | eine neue Information öffnet eine Option (Tabelle unten) | Budget |
| **VORSCHAU** | ab 14:00; ≥ `vorschau_ruhe_s` (45 s) ohne Ansage **und** ein Ereignis der Zeitleiste in ≤ 90 s, das deinen Plan ändert | Budget, höchstens 1 je 60 s |
| **INFO_FLASH** | Auftrag 002 | eigenes Budget |

**WENDEPUNKT, Satzform** (höchstens 14 + 6 Wörter):

- „<Was passiert ist, 2–4 Wörter>: <Handlung> <Ziel>, <Grund>. Danach <danach>.“
- „Turm ist down: Welle rein, dann Drache, ihr seid zu viert.“
- „Drache drin: Mid-Welle nehmen. Danach back, Herold in 90 Sekunden.“
- „Du bist raus: Eklipse kaufen, dann zum Drachen, dein Team ist dort.“

Fehlt eine sinnvolle Handlung (alles zu gefährlich), sagt er auch das: „Turm ist down: Welle rein, dann zurück, Xin
fehlt seit 40 Sekunden.“

**FENSTER** (neue Information, die eine Option öffnet):

| Information | Satz |
|---|---|
| Jungler auf der anderen Kartenseite gesehen | „Xin unten gesehen: 30 Sekunden frei für Platten oben.“ |
| Lane-Gegner tot oder im Brunnen | „Rumble ist 40 Sekunden weg: das reicht für den inneren Turm.“ |
| Ihr Toplaner ohne TP (`tp_gegner_top`) | „Ihr Top hat kein TP bis 24:10: Split oben ist sicher.“ |
| Zwei oder mehr Gegner tot | Umwandeln (Buch 5, 8), schon vorhanden |
| Flash eines Gegners weg, der in deiner Nähe ist | „Ziggs ohne Flash: er ist dein Ziel, wenn er vorn steht.“ |

Ein FENSTER-Satz braucht eine Handlung, die **jetzt** besser wird, sonst schweigt der Coach. Er zählt als PLAN,
wenn er den Plan ändert.

**VORSCHAU** (Mid- und Late-Game, mit Bedingung):

- „Drache in 80 Sekunden: bis dahin Bot-Welle, dann zur Grube. Stirbt Caitlyn, sofort Drache.“
- „Baron-Buff noch 60 Sekunden: jetzt Mid-Inhibitor, danach back.“
- „Rumble lebt in 20 Sekunden wieder: Turm noch schnell, dann raus.“

Die Bedingung („stirbt X“, „taucht X unten auf“, „fällt der Turm“) steht nur dabei, wenn der Kern sie wirklich
auswerten kann. Dann wird sie zum Auslöser eines WENDEPUNKT.

**Optionen** (nur in WENDEPUNKT und VORSCHAU):

- Liegen die zwei besten Handlungen innerhalb von `optionen_abstand` (15 % oder 150 GE), nennt der Satz beide:
  „Zwei Wege: Drache mit Team, sicher. Oder Top-Turm allein, mehr Gold, aber Xin fehlt.“
- Höchstens 20 Wörter. Die Empfehlung steht zuerst.

**Stille:**

- Während Carlos den gesagten Plan ausführt und sich der Plan nicht ändert. „Ausführen“ heißt: Er nähert sich dem
  Ziel oder arbeitet daran (Buch 5, 2).
- Wiederholungen: gleicher Satz oder gleiches Ziel in 60 s.
- Ohne sichere Grundlage.

**Budget:**

- Das Ziel ≤ 50 ungefragte Ansagen je 30 Minuten gilt weiter, ohne INFO_FLASH (Carlos will die Flashs) und ohne
  WENDEPUNKT, die er ausdrücklich will.
- Neu ist eine **Untergrenze**. Ab 14:00 soll es keine Lücke > 60 s ohne gültigen, gesagten Plan geben, während Carlos
  lebt und nicht im Kampf ist (Kennzahl „Leerlauf“, Kapitel 7).

**Nachtrag 4.1 (Auftrag 008, A1, 28.09.2026):** GEFAHR nur noch nach Buch 0, Nachtrag 7.5.1 (sichtbar, nah, robust
unterlegen, nicht schon auf dem Rückzug, nicht dieselbe Menge in 60 s); ungesehene Gefahr höchstens als Vorsicht-Satz
je 90 s. Warnungen (GEFAHR und VORSICHT) ≤ 10 je 30 min und ≤ 25 % der ungefragten Ansagen - Kennzahl in
`werkzeuge/kennzahlen.py`. Dazu (A4) ab 14:00 höchstens einmal je 90 s ein Lagebild in einem ruhigen Moment (Buch 4,
Kapitel 5).

## 5. Fragen (Schritt 6; ergänzt Buch 0, Kapitel 10)

`kern/fragen.py` ordnet jede Frage einer Absicht zu. Die Tabelle aus Buch 0, 10.1 gilt, mit diesen Ergänzungen:

| Absicht | Erkennen (Beispiele aus 213624) | Antwort |
|---|---|---|
| `JETZT` | „was mache ich jetzt“, „was jetzt“, „wo gehe ich hin“, „und jetzt?“, „Tower ist down, was jetzt?“ | `jetzt` + Grund + `danach`: „Welle rein, dann Drache, ihr seid zu viert. Danach back.“ |
| `DANACH` | „was mache ich, nachdem …“, „und danach?“ | `danach` aus der Projektion (Kapitel 3), mit Grund |
| `WARUM` | „warum soll ich …“, „warum nicht Drache?“ | Grund des Plans + Vergleich mit der genannten oder nächstbesten Handlung: „Top bringt mehr: der Drache ist 35 Sekunden weg, dein Team schafft ihn allein.“ |
| `ENTWEDER` | „zum Drachen oder zum Turm?“ | beide Handlungen gerechnet, Empfehlung mit Grund: „Drache: dein Team ist dort. Der Turm läuft nicht weg.“ |
| `SOLL_ICH` | „soll ich meinem Team beim Drachen helfen?“ | die Handlung gegen den Plan gerechnet: „Ja, …“ / „Nein, weil …“ |
| `LAGE` | „wie macht sich mein Team?“, „wie steht's?“ | Kills, Türme, Drachen, Gold-Vorsprung, dann die größte Gefahr oder Chance, in höchstens 2 Sätzen |
| `TIMER` | „Flashes?“, „wann kommt der Herold?“ | Flash-Tabelle bzw. Zeitleiste |
| `WO` | „wo ist Xin?“ | wie bisher |
| `KAUF` | „was soll ich kaufen?“, „kein Platz im Inventar“ | Kaufplan (R3), bei vollem Inventar: „Kein Platz: verkauf Dorans Klinge, dann Spitzhacke.“ |
| `NOTIZ` | „notier …“, Beschwerden | „Notiert.“ und die Notiz. **Enthält die Notiz eine Frage** („Warum sagst du, ich soll zurückgehen?“), kommt zusätzlich deren Antwort. |
| `OFFEN` | alles andere, Erklärungen („was macht Rumbles Kit?“) | Claude mit `kern.kontext()` (Kapitel 6) |

**Regeln für jede Antwort:**

1. **Ohne Claude, in ≤ 1 s:** `JETZT`, `DANACH`, `WARUM`, `ENTWEDER`, `SOLL_ICH`, `LAGE`, `TIMER`, `WO`, `KAUF`.
2. **Mindestform:** Handlung + Ziel + Grund. Eine Antwort aus nur einem Stichwort („Drache lebt.“) ist verboten, genauso
   ein Timer ohne Handlung auf eine JETZT-Frage.
3. **Kein Widerspruch.**
   - Die Antwort entspricht dem aktuellen Plan.
   - Weicht sie von der letzten Ansage ab (anderes Ziel innerhalb von 60 s), beginnt sie mit „Neu:“ und nennt das
     Ereignis, das es geändert hat.
   - Ohne Ereignis ist ein Widerspruch ein Fehler (Kennzahl, Kapitel 7).
4. **Nach einer Antwort gilt sie als gesagter Plan.** Die ungefragte Ansage wiederholt sie nicht.
5. **Wiederholt Carlos eine Frage** (gleiche Absicht innerhalb von 30 s), war die erste Antwort offenbar unbrauchbar.
   Dann kommt eine **andere** Formulierung mit mehr Grund, nicht dieselbe.
6. **Aussagen von Carlos** („ich bin in der Base“, „Drache ist tot“, „ich habe keinen Platz“) sind Korrekturen
   (Buch 0, 10.4). Sie überschreiben das Merkmal 30 s lang und lösen eine neue Antwort aus. Beispiel 213624, 12:23:
   „Ich war in der Base, der Drache war kürzer.“ Die Antwort hätte sein müssen: „Stimmt, dann Drache: Eklipse kaufen
   und hin, dein Team ist dort.“

## 6. Claude für offene Fragen (Ändert Buch 0, 10.2 und 10.3)

**`kern.kontext()`** höchstens 30 Zeilen, in dieser Reihenfolge:

1. Modus, Ort, Leben, Gold.
2. Plan: `jetzt`, Grund, `danach`.
3. Die Top-3-Handlungen mit Grund.
4. Zeitleiste der nächsten 3 Minuten.
5. Flash-Tabelle.
6. Kills, Türme, Drachen, Gold-Vorsprung.
7. Gegner und Mitspieler mit Ort und Zeit, soweit sie für diese Frage zählen.

**Regeln im Systemprompt:**

- „Der Plan ist entschieden. Erkläre ihn. Widersprich nur mit einem Grund aus dem Kontext und nenne dann beides.“
- „Fehlender Flash oder fehlende Ult beim Gegner ist eine Chance, nie ein Grund gegen den Kampf.“
- „Zahlen als gesprochene Wörter; Kill-Bilanz ‚sechs null‘, nie ‚6/0‘.“
- „Höchstens zwei Sätze, der erste ist die Handlung.“

## 7. Messen

Neue Kennzahlen in `kennzahlen.py`:

| Kennzahl | Definition | Soll |
|---|---|---|
| `leerlauf_anteil` | ab 14:00, lebend, nicht in KAMPF: Anteil der Zeit ohne gültigen, gesagten Plan (gesagt = ungefragt oder als Antwort) | ≤ 10 % |
| `wendepunkt_verzug` | Median der Zeit zwischen Wendepunkt und dem nächsten Plansatz | ≤ 3 s |
| `widersprueche` | Antwort oder Ansage mit anderem Ziel innerhalb von 60 s ohne Ereignis | 0 |
| `stichwort_antworten` | Antworten ohne Handlung | 0 |
| `antwortzeit` | Median von Frage-Ende bis Antwortbeginn, getrennt nach „ohne Claude“ und „mit Claude“ | ohne Claude ≤ 1 s |

**Fragen-Probe:** Alle 40 Fragen aus 213624 werden Szenarien mit `frage` und der Zeit aus dem Log. Beispiele:

| Zeit | Frage | Prüfung |
|---|---|---|
| 9:55 | „Okay, der erste Tower ist down, was jetzt?“ | `muss_ziel`; Handlung vorhanden; keine Claude-Pflicht |
| 12:56 | „Zum Drachen oder zum Turm?“ | ENTWEDER: nennt eins von beiden mit Grund; darf_nicht_sagen die Antwort „Drache lebt.“ |
| 13:16 | „Welche Welle, auf welcher Lane?“ | nennt eine Lane; darf_nicht_sagen „Drache lebt.“ |
| 13:36 | „Drache ist tot, wo gehe ich jetzt hin?“ | JETZT mit Korrektur; `muss_ziel`; darf_nicht_sagen „Drache in“ |
| 16:31 | „Alle sind tot. Warum sagst du, ich soll zurückgehen?“ | NOTIZ + WARUM: nennt einen Plan (Turm, Welle), nicht nur „Notiert.“ |
| 23:15 | „Wie sieht's mit den Flashes aus?“ | TIMER: nennt jeden Gegner mit bekanntem Stand |

Die Wortwahl prüft `muss_nennen_eins`. Wo die Frage aus dem Log nicht passt, weil die Bot-Partie nur Verdrahtung
prüft, steht ein Kommentar.

**Wendepunkt-Probe:** In 164326, 173159 und 213624 folgt auf jeden Turmfall, jeden Objective-Kill und jedes
Verlassen der Basis innerhalb von 3 s ein Plansatz. Neuer Prüfschlüssel `wendepunkt_ansage = true` je Aufnahme
(`kennzahlen`).

## 8. Grenzen

- **`danach` ist eine Vorhersage.** Sie stimmt nur, wenn die Welt sich wie projiziert verhält. Deshalb wird sie am
  Wendepunkt neu gerechnet und nie als sicher verkauft.
- **Bedingte Pläne** nur mit Bedingungen, die der Kern selbst sieht: Tod, Sichtung, Struktur, Objective. Nie „wenn
  er Flash benutzt“, solange F2 Lücken hat.
- **In Bot-Partien** stimmt die Kampfstärke nicht. Die Sätze werden dort nur auf Form und Verdrahtung geprüft.

## 9. Parameter (`wissen/kern.toml`, neu)

```toml
[fuehren]
stand = "Buch 11, 27.09.2026 - Startwerte"
zeitleiste_s = 180
wendepunkt_abstand_s = 8
wendepunkt_kill_radius = 2000
danach_min_dauer_s = 5
vorschau_ab_s = 840
vorschau_ruhe_s = 45
vorschau_horizont_s = 90
vorschau_abstand_s = 60
optionen_abstand_anteil = 0.15
optionen_abstand_ge = 150
max_woerter_wendepunkt = 20
max_woerter_optionen = 20
leerlauf_max_s = 60
antwort_wiederholung_s = 30
widerspruch_fenster_s = 60
korrektur_gilt_s = 30
```

## 10. Umsetzung (Auftrag 003)

1. **Zeitleiste** mit Dashboard-Anzeige.
2. **`danach`** über die Projektion.
3. **Sprechanlässe** WENDEPUNKT, FENSTER, VORSCHAU, Optionen.
4. **Fragen** (`kern/fragen.py`) mit allen Absichten und Regeln aus Kapitel 5 und dem neuen `kern.kontext()`. Die
   alten Wege `antworten.sofort` und `mit_claude` bleiben nur als Rückfall für `OFFEN`, dann mit dem neuen Kontext.
5. **Kennzahlen und Szenarien** aus Kapitel 7, zuerst rot.
6. **Protokolle** für 213624, 164326 und 173159:
   - Die Protokolle zeigen zusätzlich `danach`, die Zeitleiste zur Ansage und die Antworten auf die Fragen aus 213624.
   - `werkzeuge/protokoll.py` bekommt dafür `--fragen`: Es spielt die Fragen aus `_sprechtaste.log` zur Zeit ein.
