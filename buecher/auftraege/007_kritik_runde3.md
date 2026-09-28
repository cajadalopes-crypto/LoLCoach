# Auftrag 007 – Kritik, Runde 3 (und Nachzählung)

Drei neue Kritiker-Agenten, ohne Code und mit derselben Rolle wie in Auftrag 005. Sie bekamen die Protokolle nach
Teil A–C (`9487b8e`). Die Urteile liegen im Scratchpad (`k007_r3/urteile_*.jsonl`).

## Zählung Runde 3 (Stand `9487b8e`)

| Partie | min | ok | schwach | falsch | schwach je 30 min | falsch je 30 min |
|---|---|---|---|---|---|---|
| 164326 (echt) | 42,8 | 69 | 25 | 6 | 17,5 | 4,2 |
| 173159 (echt) | 38,3 | 66 | 19 | 9 | 14,9 | 7,0 |
| 144655 (echt) | 9,7 | 13 | 4 | 1 | 12,4 | 3,1 |
| 213624 (Bot, Fragen) | 25,1 | 56 | 30 | 10 | 35,9 | 12,0 |
| 102112 (Bot) | 30,4 | 51 | 13 | 4 | 12,8 | 3,9 |

**Freigabe-Schwelle** (echte Partien ≤ 2 falsch je 30 min, kein „gefährlich“): **nicht erreicht.** Dazu kam ein
gefährlicher Fall: 173159 35:09 „Nexus-Turm jetzt: Yasuo und Olaf sind noch 32 Sekunden tot.“ Kai'Sa und Cho'Gath
standen 35:06/35:07 an ihrem Brunnen auf, Tod 35:21.

## Klassen (falsch) und was gebaut wurde (`de4500c`)

| Klasse | falsch | Beispiele | Fix |
|---|---|---|---|
| Halte-Satz „Warte hier: …“ am Wendepunkt (neu in 007) | 6 | 173159 26:07 (20 % Leben), 27:55, 32:11; 144655 7:15; 102112 13:41; 213624 23:57 | Ein Halte-Plan sagt am Wendepunkt nur noch, was danach kommt, kein Warten auf ein Ereignis und kein „Bleib bei deinem Team“ |
| Farm- oder Warte-Satz gegen ein eben gesagtes Back | 3 | 164326 16:28 (14 s nach „Back jetzt“), 173159 32:11, 213624 23:57 | Kein Farm- oder Halte-Satz ≤ 30 s nach einem Back-Ruf ohne Recall |
| Wiederbelebte gelten als „lange ungesehen“ (gefährlich) | 1 | 173159 35:09 | Wer ≤ 25 s wiederbelebt und seitdem nicht gesehen ist, steht an seinem Brunnen (Ort, Abstand, Ankunft) |
| Objective-Ziel springt zu einem Turm | 2 | 164326 35:34 (28 s nach „zum Drachen“), 35:01 | Ein eben gesagtes Objective-Ziel (≤ 60 s, lebt oder spawnt in ≤ 45 s) wechselt ohne Wendepunkt nicht zu einem Turm. 35:01 bleibt: Dort ist der Turmfall ein Wendepunkt, und Buch 6, 8 stellt den Inhibitor vor den Drachen |
| Kauf-Antwort nach dem Kauf | 2 | 213624 10:38, 10:54 „Kauf Spitzhacke …“, schon gekauft | Nach dem Kaufschritt nennt die Antwort nur das Ziel danach |
| „Raus“ während des Recalls | 3 | 102112 13:22, 213624 4:29, 164326 24:14 | **nicht gebaut:** Das würde Rückzugswarnungen unterdrücken (Schranke), Frage in `007_bericht.md` |
| An der Frage vorbei (Bot, Fragen) | 4 | 213624 5:05, 12:14, 13:18, 16:42 | nicht gebaut: vier verschiedene Ursachen |
| Einzelfälle | 5 | 173159 12:43, 23:11, 28:22, 33:20; 213624 19:12 | unter der Schwelle |

**Unterwegs gefunden:**
- Der Sprechplan verlangte vor einem Hinweis 8 s Stille. „X ohne Flash“ gilt aber nur 8 s: Nach jedem Satz kurz davor
  erklang die Meldung nie und galt trotzdem als gemeldet (213624 8:41). Jetzt reichen 1,5 s, und die Meldung fällt
  nicht unter das Budget.
- Ein Turmziel verfällt jetzt mit seinem Fenster, spätestens nach 120 s. Vorher hielt in 102112 ein Nexus-Turm von
  33:02 noch um 36:32.

Szenarien, alle zuerst rot auf `9487b8e`: `3509-respawn-am-nexus`, `2607-kein-warte-hier`, `1341-kein-warte-hier`,
`1628-kein-farm-nach-back`, `3534-drache-bleibt`, `2357-kein-warte-nach-back`, `1038-schon-gekauft`.

## Nachzählung (Stand `de4500c`, neue Kritiker, nur echte Partien)

| Partie | min | ok | schwach | falsch | falsch je 30 min | Runde 3 → Nachzählung |
|---|---|---|---|---|---|---|
| 164326 (echt) | 42,8 | 71 | 21 | 4 | **2,8** | 4,2 → 2,8 |
| 173159 (echt) | 38,3 | 60 | 28 | 2 | **1,6** | 7,0 → 1,6 |
| 144655 (echt) | 9,7 | 6 | 11 | 0 | **0,0** | 3,1 → 0,0 |

- **Kein „gefährlich“ mehr.**
- **Schwelle ≤ 2:** 173159 und 144655 erreicht, **164326 nicht (2,8).**
- **Was in 164326 falsch bleibt:**
  - 35:01 „Euer Bot-Turm ist weg. Top-Inhibitor jetzt …“ und 35:06 „Zum Drachen …“ (5 s später, der Widerspruch
    dazu): Riven steht Bot, der Drache spawnt in 40 s neben ihr. Nach Buch 6, 8 geht der Inhibitor (Rang 3) im
    Umwandel-Fenster vor den Drachen (1,5), das Buch sagt also Inhibitor. Die Kritiker sagen Drache →
    Entscheidung in `007_bericht.md`.
  - 33:02 „Baron weg. Farm Top …“: Der Gegner hat den Baron-Buff, 5 s später kommt die Belagerung. Der
    Belagerungs-Auslöser (c) verlangt ≥ 3 von ihnen in eurer Hälfte, und die waren erst 5 s später da.
  - 26:54 „Back jetzt: 1700 Gold für Stahlsiegel.“ 28 s nach dem Verlassen der Basis, ein Einzelfall.
- **173159:** zwei „Raus“ gegen einen einzelnen Gegner, den Riven dann tötet (2:27, 27:01). Das ist das Gefahr-Modell,
  dort ist nichts gelockert.

