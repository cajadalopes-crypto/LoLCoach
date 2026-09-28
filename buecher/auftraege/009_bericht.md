# Bericht zu Auftrag 009 – Letzte Sperren vor Testpartie 2

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md` („Auftrag 009“).

## Commits

- `3ad5f40`: alle Fixes, 11 Szenarien, 2 Unit-Tests, neun Protokolle (neu erzeugt), messungen.md, OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Umgesetzt

1. **Trade bei 15 %:**
   - TRADE und ALL_IN stehen in der R1-Liste. Sie sind stumm („stumm: Buch 2 zurückgestellt“).
   - WELLE_REIN_UND_BACK und STAPELN sind ab `p_tod` 0,3 kein Kandidat mehr.
   - Suche in neun Protokollen: vorher 3 Funde, jetzt **0**.
2. **Entscheidungen:**
   - Ungesehene ≤ 20 s zählen als Köpfe: 20:01/20:10 warnen, 14:00 bleibt still.
   - Das Lagebild spricht nur mit einer Handlung oder Grenze.
   - Drache vor Inhibitor:
     - Der Rang gilt nur noch bei Gleichstand; jedes Ziel im Fenster bekommt denselben Bonus.
     - Ein Objective ≤ 10 s neben euch geht vor die Türme, mit „danach“, z. B. 33:21 „Drache zuerst, der liegt neben
       euch; danach ihr Bot-Inhibitor-Turm, der Baron-Buff hält noch 120 Sekunden.“
   - Recall-Kanal: Gewarnt wird nur, wenn der erste Gegner vor Kanal-Ende + 1 s da ist.
   - Nebenbei: Ohne Ort wählt der Kern nach einem Kampf bis zu 2 s keinen neuen Plan.
3. **KLAEREN (32:17):** jetzt „Zu eurem inneren Top-Turm, weil Aurora und Twitch 2 Sekunden weg waren.“ Das gilt auch im
   Tod. 31:07 („Was soll damit Welle heißen?“) beantwortet jetzt der Kern, nicht mehr Claude.
4. **Sprache:**
   - „Aurora ist Level 6“,
   - „kein Trade bis zum Axiombogen“,
   - „Kauf Langschwert für die Eklipse“.

## Tests und Szenarien

- **Szenarien 226 / 232**, 3 übersprungen.
  - Rot sind die alten Fälle: 3× Wendepunkt-Probe (24 späte Sätze, im letzten 008-Lauf 28) und 0944.
  - Neu rot: `a1-warnungen-je-30min` und `2522-kein-baron-drache-lebt` (unten, 1 und 2).
- **Neu:** 11 Szenarien und 2 Unit-Tests, auf `122431c` alle rot außer den drei Wächtern.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.

## Nachzählung 101426 (frischer Challenger- und frischer Carlos-Kritiker)

| | 008 | 009 |
|---|---|---|
| falsch je 30 min (≤ 2) | 2,5 | **0,8** (1 falsch, 0 gefährlich) |
| Warum nachvollziehbar (≥ 90 %) | 91 % | 95 % |
| hilft / nervt (≥ 60 % / ≤ 10 %) | 88 % / 10 % | 86 % / 10 % |
| Antworten beantwortet | – | 9 von 10 |
| Warnungen je 30 min (≤ 10) | 11,7 | **15,0** |
| vage Sätze (0) | 0 | 0 |

- **Einziges „falsch“:** 23:35 „Zurück unter deinen inneren Mid-Turm“, gesagt auf der Bot-Lane.
- **Was nervt:** abgebrochene Sätze (3), „Mid-Welle“ ohne Zustand (2).

## Leerlauf (nur gemessen)

Von 10 zufälligen Leerlauf-Fenstern ab 14:00 ist die Stille in 3 richtig: ein Rückzug oder Back-Ruf gilt noch. In 7
fehlt ein Satz. In 6 davon hat der Kern nach einem Wendepunkt keinen Plan mit Ziel, nur HALTEN, etwa nach einem Turm, dem
Drachen oder drei Kills. Das Maß ist also meist richtig, der Coach nicht. Die Tabelle mit je einem Challenger-Satz steht
in messungen.md.

## Zu entscheiden

1. **Warnungen wieder über 10 je 30 min** (101426 15,0; 164326 11,9; 173159 10,2). Das ist der Preis von 2.1.
   - Die vier neuen Warnungen in 101426 (20:01, 20:10, 21:35, 23:35) passen zur Lage; 20:10 wiederholt 20:01.
   - Mögliche Stellschrauben: Ein Ungesehener zählt nur, wenn ein Sichtbarer näher kommt; oder 15 s statt 20 s.
2. **2522 (102112 25:22):** Tryndamere nimmt den Drachen allein zu 86 %. Darum sagt der EV „äußerer Mid-Turm“; Buch 6
   sagte „Drache“.
   - Soll ein freies Objective mit Mitspieler dort Vorrang behalten?
   - Oder gilt der Split, Tryndamere auf den Drachen und Riven auf den Turm?
3. **Leerlauf:** Soll der nächste Auftrag den Plan nach Wendepunkten füllen?
