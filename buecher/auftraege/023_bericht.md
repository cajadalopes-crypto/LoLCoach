# Bericht zu Auftrag 023 – Stabile Messung, eine Stimme, Pflicht-Infos, Tempo

## **TOR NICHT ERREICHT** (nicht neu gemessen – auf Carlos' Wunsch abgekürzt, das Tor misst 025)

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Die Einzelheiten stehen in
`buecher/messungen.md` („Auftrag 023“).

## Zahlen aus Runde 1 (021 alt / 021 neues Verfahren / 023)

| Größe | Tor | bekannt | neu |
|---|---|---|---|
| Soll gesagt + teilweise | ≥ 80 / 75 % | 56 / 57,4 / **59,4 %** ✗ | 70 / 69,0 / **72,5 %** ✗ |
| Flash / Jungler / Lane-Gegner weg | ≥ 95 % | 88·89·58 % → **34/34 · 71/72 · 8/8** ✓ | 89·84·43 % → **8/9 · 61/62 · 2/2** (89 % Flash) |
| Widersprüche je Partie | ≤ 1 | 2/7/4/7 · 4/9/3/11 → **4/8/2/8** ✗ | 4/2/1 · 3/2/1 → **3/2/4** ✗ |
| Füllsätze | ≤ 5 % | 4,0 · 2,8 → **2,2 %** ✓ | 3,2 · 2,5 → **2,9 %** ✓ |
| Latenz ganze Antwort (Median) | ≤ 2 s | 2,3–2,5 → **2,40–2,45 s** ✗ | → **2,26–2,39 s** ✗ |
| bis zum ersten Satz (Median) | – | **1,34–1,49 s** | **1,28–1,42 s** |
| Sicherheit | 0 | **0** ✓ | **0** ✓ |

- **Kritiker:** drei frische je Partie. Einig waren sie bei 83 % (bekannt) und 78 % (neu) der Punkte; nur drei
  Punkte brauchten den vierten.
- **Soll-Listen:** 17 Streichungen, jede mit Grund.
- **Stand der Messungen:** Runde 1 lief vor den letzten Fixes, die neue Menge vor den letzten vier.

## Gebaut

- **Messung:**
  - Soll-Listen eingefroren (`proben/soll_023/`).
  - `werkzeuge/kritik_mehrheit.py` für drei Kritiker, Mehrheit und einen vierten für strittige Punkte.
  - Neue Definition für „Lane-Gegner weg“.
- **Pflicht-Infos:**
  - höchstens 5 Wörter („Teemo oberer Fluss, 6 Sekunden.“);
  - sie unterbrechen einen Plan-Satz und warten höchstens 3 s;
  - auch im Kampf und zusätzlich zum Plan-Satz.
- **Eine Stimme:**
  - Antworten des Kerns setzen den einen Plan.
  - Eine Warnung ersetzt den Plan. Binnen 8 s nach einem anderen Plan beginnt sie mit „Stopp –“.
  - Anlässe binnen 10 s werden zusammengefasst.
  - Der Kern-Ersatz spricht nur bei einem Ausfall.
  - Eine Info mit Plan geht über den Schiedsrichter.
  - Ein nacktes „Nein“ auf einen Anlass wird verworfen, und es gibt kein Markdown mehr.
- **Tempo:**
  - Kurzer Prompt ohne Wissensblock für Lane, Fenster, Roam und Kampf.
  - Cache-Treffer und die Zeit bis zum ersten Satz werden gemessen.
  - Das Textende kommt jetzt am Anfang der stillen PLAN-Zeile statt an ihrem Ende. Das spart vermutlich ~0,9 s, gemessen ist es noch nicht.
- **xz:**
  - `aufraeumen.py` wandelt alle Aufnahmen außer den letzten drei um; eine Lesefunktion liest beide Formate.
  - Projektordner 4466 → 4334 MB, je Partie ~46 → ~12 MB.
  - Nachspiel und Szenarien sind an zwei Aufnahmen Satz für Satz gleich.

## Tests

- **`tests/alle.py`:** 10 / 10.
- **Unit-Tests:** Jeder Fix hat einen Test, der vorher rot war (`test_kern.stimme_023`).
- **Szenarien, parallel:** 313 / 317. Rot sind nur die alten (3× Wendepunkt, 0944). 0806 zählt Pflicht-Infos jetzt nicht mehr gegen `ansagen_max`.
- **Sicherheit:** Über alle sieben 023-Läufe mit dem aktuellen Prüfer liegt jede Kategorie bei 0 (nach vorn unter R1, Kill-Check, Begriffe).

## Offen (für 025)

- **Endmessung:** Tor mit dem Endstand, vor allem Widersprüche und die Latenz nach dem PLAN-Zeilen-Fix.
- **Verpasste Infos nicht einzeln angesehen:** 164809 6:19 Flash Wukong, 26:25 Jungler Vi, 183125 ein Jungler.

## Kosten

2,32 $ von 5 $:
- 1,49 $ Runde 1;
- 0,72 $ neue Menge;
- 0,11 $ die abgebrochene Runde 2.
