# Rückfragen zu Auftrag 005

Drei Befunde der Kritiker bräuchten eine Grundsatzentscheidung. Sie sind deshalb **nicht gebaut**.

## 1. Warten am Inhibitor-Turm nach dem Tod (Klasse 7, 3 × falsch)

Beispiel 144655 1:59: „Noch 8 Sekunden: zurück nach Top, bleib am Inhibitor-Turm: Gangplank war zuletzt oben.“
Ebenso 173159 23:11 und 164326 12:59.

Der Kern schickt dich nach dem Respawn nur dorthin, wo p_tod bei Ankunft unter `wohin_p_tod_max` liegt (G2 aus
Qualitätsrunde 2). Liegen der äußere und der innere Turm darüber, bleibt der Inhibitor-Turm. Die Kritiker sagen: In
der Lane-Phase kostet das die ganze Welle, und der Grund („war zuletzt oben“) erklärt es nicht.

- **A:** In der Lane-Phase ist der äußere Turm immer erlaubt, er schützt dich ja. Das lockert G2 und ist deshalb nicht
  gebaut.
- **B:** Es bleibt dabei, nur der Grund wird ehrlich: „am äußeren Turm wäre es zu riskant: Gangplank und Kha'Zix
  können dort sein“.

## 2. Top-Welle, während das Team den Ältesten bestreitet oder die Basis verteidigt (Klasse 8, 3 × falsch)

173159 28:22 „Dann Top-Welle.“, der Älteste spawnte in 18 s. 36:50 „Zwei eurer Türme weg: Dann Top-Welle.“, ihr
Ältesten-Buff lief und die Basis wurde belagert.

VERTEIDIGEN (Buch 5, 7) gilt nur, wenn du nah bist (`verteidigen_weg_s`). Buch 6 kennt den Weg zum Ältesten nur als
Objective-Handlung mit Chance. Die Top-Welle als Tausch widerspricht keinem Buch. Nach Carlos' und der Kritiker
Maßstab ist sie hier aber falsch.

- **Frage:** Soll eine Belagerung der eigenen Basis (≥ 2 Türme in 30 s oder Ältesten-Buff beim Gegner) dich auch aus
  der Ferne zurückholen? Das wäre eine neue Regel für Buch 5, 7.

## 3. Baron mit drei ungesehenen Gegnern (Klasse 1, Rest)

164326 21:01 „Baron jetzt: Level 16 gegen 14, ihr seid drei gegen eins.“ Nach der Regel aus Auftrag 004 ist das auch
mit `p_da_min = 0,1` klar überlegen: drei gegen zwei, zwei Level und über 2000 Gold vorn. Drei Gegner waren aber
lange nicht zu sehen, und ein Baron dauert 45 s. Die Kritiker nennen das gefährlich.

- **Frage:** Soll die Überlegenheit bei Objectives mit langer Dauer (Baron, Ältester) zusätzlich verlangen, dass
  höchstens einer der lebenden Gegner ungesehen ist?
