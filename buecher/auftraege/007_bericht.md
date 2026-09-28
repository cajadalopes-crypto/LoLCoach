# Bericht zu Auftrag 007 – Entscheidungen, Fehlerklassen, Live-Tauglichkeit

Fertig am 28.09.2026. Gegen ein Spiel wurde der Coach nicht gestartet, nur die verlangte Generalprobe lief gegen einen
nachgebauten Client. Die Einzelheiten stehen in `buecher/messungen.md`, Abschnitt „Auftrag 007“, die Klassen in
`007_kritik_runde3.md`.

## Commits

- `9487b8e`: Teil A–C. Entscheidungen, Klassen 6/9/10/11, Einzelfälle, Belagerung (Buch 5, Nachtrag 7.1), Flash-Clips,
  Live-Weg 7680 × 2160, Kamera-Test, Generalprobe.
- `de4500c`: Teil D. Klassen der Kritik Runde 3.
- dazu der Commit mit Messungen, Kritik, Bericht und Auftrag.

## Tests und Szenarien

- `tests/alle.py` **10 / 10**; der Kamera-Test ist wieder grün.
- Szenarien **190 / 194**, 2 übersprungen. Konstruierte Lagen **40 / 40**.
- **30 neue Szenarien aus echten Fällen, alle zuerst rot.**
  - Ausnahmen: `1711` war schon grün und bleibt als Wächter.
  - `2411-rueckzug-episode` war am Zwischenstand rot.
- Rot bleiben die Wendepunkt-Probe (3 Dateien, 29 späte oder fehlende Sätze, vor 007 rund 70) und die Frage 9:44.

## Kennzahlen

| „falsch“ je 30 min | vor 005 | nach 005 | 007 Runde 3 | 007 Nachzählung | Soll |
|---|---|---|---|---|---|
| 164326 (echt) | 11,9 | 9,8 | 4,2 | **2,8** | ≤ 2 |
| 173159 (echt) | 7,0 | 3,9 | 7,0 | **1,6** | ≤ 2 |
| 144655 (echt) | 6,2 | 3,1 | 3,1 | **0,0** | ≤ 2 |

„Gefährlich“ gab es in Runde 3 einmal (173159 35:09, behoben), in der Nachzählung nicht mehr.

**Unterwegs gefunden und behoben:**
- **Rückzug:** Ein stiller Back-Plan hielt eine Rückzugs-Episode 9 min offen. Dadurch wurde eine GEFAHR nicht gesagt
  (213624 24:11).
- **Wiederbelebte:** Sie galten als „lange ungesehen“ statt „an ihrem Brunnen“ (der gefährliche Fall).
- **Flash-Meldung:** „X ohne Flash“ verfiel im Sprechplan (8 s Ruhe verlangt) und galt trotzdem als gemeldet.
- **Dashboard:** Der Kern-Kasten war seit 003 kaputt (TypeError).
- **Messung:** Die Wendepunkt-Messung übersah den Satz, der das Ereignis beantwortet.

## Freigabe für die erste Testpartie

- **Kritik:** 173159 und 144655 liegen unter der Schwelle, **164326 knapp darüber (2,8)**.
- **Live-Weg:** Minimap 904/906 gefunden, HUD 137/137 gelesen, keine Ausnahmen.
  - **Der Takt ≥ 10/s ist nicht nachgewiesen:** Der Bildschirm war aus, und dxcam lieferte kein Bild. Über GDI kamen
    6/s.
  - Vor der Testpartie bitte einmal mit eingeschaltetem Bildschirm laufen lassen: `python werkzeuge/generalprobe.py
    --ohne-gehirn --ohne-review`.
- **Annahme für 32:9:** Die Minimap sitzt am rechten Bildschirmrand. Stimmt das nicht, meldet der Coach eine blinde
  Minimap.

## Zu entscheiden

1. **Buch 6, 8 gegen die Nähe** (164326 35:01/35:06): Im Umwandel-Fenster geht der Inhibitor (Rang 3) vor den Drachen
   (1,5), auch quer über die Karte, wenn der Drache in 40 s neben dir spawnt. Die Kritiker sagen Drache. Soll ein
   erreichbares Objective in ≤ 45 s einen Inhibitor schlagen, der weiter weg ist als der Spawn?
2. **„Raus“ während des Recalls** (3 Fälle): Nach „Back jetzt“ kommt 9–20 s später „Raus zum Turm: X kommt“. Das
   bricht den Recall ab. Das zu unterdrücken lockert eine Rückzugswarnung, deshalb nicht gebaut.
3. **Belagerung, Auslöser (c):** Der Baron-Buff beim Gegner allein (ohne ≥ 3 in eurer Hälfte) löst noch nichts aus
   (164326 33:02 „Baron weg. Farm Top“).
