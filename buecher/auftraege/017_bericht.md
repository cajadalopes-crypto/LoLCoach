# Bericht zu Auftrag 017 – Inhalt statt Takt (abgekürzt)

Stand 29.09.2026. Carlos hat 017 abgekürzt: Die laufenden Nachspiele wurden abgebrochen, **die Messung aus Teil 2
fehlt und kommt mit 019**. Der Coach wurde nicht gestartet.

## Gebaut

**Teil 0:**
- **Ganze Sätze:** Die Antwort des Strategen wird ganz geprüft und als EIN Stück gesprochen, bei Fragen wie bei
  Anlässen. Auch Teilsätze bis zum Komma werden erst am Satzende geprüft.
- **Latenz:**
  - gemessen, wohin die Zeit geht (`werkzeuge/latenz_probe.py`, `stratege_probe_017/latenz_*.json`);
  - der Stratege bekommt einen kurzen Prompt mit dem Entwurf des Kerns;
  - gesprochen wird beim Textende statt beim Abschluss-Ereignis;
  - zwei Prozesse werden vorgehalten;
  - Anlässe während eines Aufrufs verfallen.
- **Füllsätze:** Muster in `wissen/fuellsaetze.toml`. Der Stratege darf „NICHTS“ sagen und schweigt dann.
  Kern-Füllsätze wie „Weiter deine Top-Welle.“ werden gestrichen. Der 35-s-Takt in der Lane ist weg.
- **Kauf:**
  - „Kauf jetzt“ gibt es nur in der Basis oder im Back-Ruf.
  - Kein Satz über schon gekaufte Items.
  - Bei vollem Inventar mit Trank wird der Trank verkauft (192113 28:24 „nichts zu kaufen“ bei 4130 Gold).
  - „Noch 225 Gold bis Axiombogen“ um 7:55 war kein Fehler: Es waren Bauteile gekauft.
- **Top-Wellen-Reflex:** Eine Welle, an der Mitspieler stehen, ist nach der Lane-Phase kein Ziel mehr, weder für
  Kern noch für Stratege.
- **„Schwach“:** nur noch mit Folge.

**Teil 1:**
- **Jungler-Vorhersage (I2):** gebaut, aber abgeschaltet. An allen 32 Aufnahmen traf keine Vorhersage ≥ 65 % (andere
  Seite 53 %, gleiche Seite 47 %, n = 51; `stratege_probe_017/jungler.json`).
- **Lane-Anlässe mit Inhalt:** Welle kippt, Kanone ≤ 20 s, Lane-Gegner weg oder zurück, Jungler gesehen, Flash weg,
  Spike kaufbar. Frage dazu „Freeze, Slow Push oder Crash, und warum?“ mit `wissen/wellen_regeln.md`.
- **Objective-Vorlauf:** 60 s vorher die Kette, 40 s vorher loslaufen, ohne Prio der Tausch-Satz. Beachtet die
  Back-Grenze und R1.
- **Respawn-Kette:** 12 s vor dem Respawn Kauf und Ziel.
  - Nebenfund: Das Gedächtnis „ein Ziel je Tod“ merkte sich ein leeres Ziel, dann blieb der ganze Tod stumm.
- **Ein aktiver Plan (Schiedsrichter):**
  - Plan-Sätze von Kern und Stratege sprechen nur, wenn sie den Plan setzen oder ändern.
  - Eine Änderung in < 30 s gibt es nur nach einem Ereignis, dann mit „Jetzt, wo …“.
  - Warnungen und Infos sprechen immer.
  - „Und dann?“ bekommt den aktiven Plan als Entwurf.

## Geprüft (grün)

- **Unit-Tests:** neu `inhalt_017`, alle 27 grün. Auf dem Stand von 016 waren sie rot: Füllsätze, schon Gekauftes,
  „schwach“ ohne Folge, besetzte Welle, Trank, Antwort in 3 Stücken, Schiedsrichter fehlte. „Kauf jetzt auf der Lane“
  war auf 016 schon verworfen, aber nur wegen Gold.
- **`tests/alle.py`:** 10 / 10.
- **Szenarien:**
  - voller Lauf 305 / 309, nur die alten Roten (3× Wendepunkt-Probe, 0944);
  - die geänderten Teile nach den letzten Fixes nachgeprüft (8 Dateien, nur dieselben alten Roten).
- **Sicherheit:** über alle vorhandenen 017-Läufe (8 Läufe, 876 Sätze): 0 nach vorn unter R1, 0 Angriffe ohne
  Kill-Check, 0 innere Begriffe.

## Nicht gemessen (kommt mit 019)

- **Soll-Liste:**
  - Die blinden Soll-Listen und der Vergleich für den Stand 016 liegen vor: 97 von 148 gesagt oder teilweise (66 %).
  - Der Vergleich nachher fehlt.
- **Füllsatz-Quote, Widersprüche, Abdeckung I1–I4:** nicht auf dem Endstand gemessen. Werkzeug fertig:
  `werkzeuge/nachspiel_abdeckung.py` mit `lage` und `auswerten`.
- **Latenz:**
  - **Sonde:**
    - Mit Entwurf und Pause zwischen den Aufrufen (wie live) kommt das erste Token nach 1,0–1,2 s, die ganze
      Antwort nach 3,3–4,0 s (Median). p90 ~7 s.
    - Soll ≤ 3 / ≤ 5 s: verfehlt.
    - Ursache: Das adaptive Nachdenken von Sonnet lässt sich über die CLI nicht abschalten. Haiku und ältere Modelle
      antworten dort nicht.
  - **Nachspiel:** Dort kamen Aufrufe dicht hintereinander, deshalb ~7 s. Seitdem werden zwei Prozesse vorgehalten.
- **Die NACHSPIEL-Protokolle** sind noch die von 016.
