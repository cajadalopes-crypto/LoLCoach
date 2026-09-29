# Auftrag 017 – Inhalt statt Takt: ein Plan, ganze Sätze, keine Füllsätze (Claude, Chat, 29.09.2026 17:45, ersetzt die Fassung von 14:30)

Lies zuerst `buecher/13_challenger_coach.md`. **Keine Testpartien, geprüft wird nur an Aufnahmen. Frag Carlos nie nach
einer Partie. Starte den Coach nicht.**

Ich habe `NACHSPIEL_2026-09-29_133448.md` selbst gelesen:
- **Was jetzt stimmt:** Flash, Jungler und Back-Ketten kommen.
- **Was nicht stimmt:** der Inhalt und die Form. Das hat Vorrang vor allem Neuen.

## Teil 0 – Was ich im Nachspiel 133448 gefunden habe (zuerst)

1. **Zerstückelte Sätze:** Aus einer Stratege-Antwort werden drei Ansagen über 8 s, z. B.:
   - 1:32 „Farm deine Welle weiter,“
   - 1:35 „Poppy ist mit 24 Prozent schwach …“
   - 1:40 „Danach nimm die Kanone …“

   **Fix:** Stratege-Antworten werden ganz geprüft und **als ein Satz am Stück** gesprochen, nie in Teilen mit Pausen.
2. **Latenz 6–7 s:**
   - Ziel: erster gültiger ganzer Satz im Median ≤ 3 s, p90 ≤ 5 s.
   - Miss zuerst, wo die Zeit hingeht: Prozessstart, Promptlänge, Warteschlange mehrerer Anlässe, Warten auf das
     Satzende.
   - Dann beheben:
     - vorgewärmter Prozess;
     - Kontext kürzen (nur was die Frage braucht);
     - nur ein Aufruf zur Zeit;
     - veraltete Anlässe verwerfen statt anstellen.
   - Latenz je Schritt in `messungen.md`.
3. **Füllsätze:** „Nimm die Kanone mit, weil sie extra Gold bringt“, „Farm deine Welle weiter“ (ohne Grund) oder
   „Weiter deine Top-Welle“.
   - **Fix:** `pruefe` verwirft Sätze ohne neue Info und ohne Entscheidung. Liste in `wissen/`, erweiterbar.
   - Hat der Stratege nichts Substanzielles, schweigt er.
   - **Die 35-s-Pflicht aus Buch 13, Teil 3, gilt NICHT als Zwang zu Füllsätzen.** Stattdessen gibt es Anlässe mit
     Inhalt (Teil 1.2).
4. **Widersprüche Kern gegen Stratege:** 10:17 „Back jetzt“ → 10:35 „Schieb rein, dann back“ → 10:47 „Drück ihren
   inneren Top-Turm“ → 10:52 „Poppy unten: drück deine Welle“ → 10:59 „Back jetzt“. **Fix:** Teil 1.5, ein aktiver
   Plan als einziger Schiedsrichter.
5. **Kauf:**
   - „Kauf jetzt …“ gibt es nur in der Basis oder im Back-Ruf (4:17 kam es mitten auf der Lane).
   - Käufe werden aus dem Inventar verfolgt: kein „noch 225 Gold bis Axiombogen“ nach dem Kauf, kein „vergiss den
     Axiombogen“, wenn er schon gekauft ist (13:12).
   - Kein „nichts zu kaufen“ bei 4130 Gold.
6. **Top-Wellen-Reflex:** Stehen oder farmen Mitspieler an deiner Welle, ist sie nicht dein Ziel. Dann kommt das nächste
   Ziel mit Grund.
7. **„Poppy schwach“** kam zwar nicht mehr als Angriffsgrund, aber noch als Beschreibung bei 24 % (1:35). Das ist nur
   korrekt, wenn es stimmt und eine Folge hat. Sonst weg.

## Teil 1 – Buch 13 umsetzen (über 016 hinaus)

1. **Jungler-Vorhersage (I2)** aus `jungle.wahrscheinlich`:
   - nur früh im Spiel, nach ≥ 45 s ohne Sicht, immer mit „vermutlich“, höchstens alle 60 s;
   - an allen Aufnahmen nachgeprüft (Trefferquote der nächsten Sichtung);
   - unter 65 % Trefferquote stumm, mit Bericht.
2. **Lane-Anlässe mit Inhalt** statt Zeittakt. Der Stratege wird gefragt „Freeze, Slow Push oder Crash, und warum?“, mit
   `wissen/wellen_regeln.md` (aus Buch 13, Teil 3, mit Stand) und dem Wellenstand (Vasallen je Seite, Richtung,
   Kanone). Anlässe:
   - Die Welle kippt die Richtung.
   - Die Kanonenwelle ist ≤ 20 s entfernt.
   - Der Lane-Gegner geht weg (Back, Roam) oder kommt zurück.
   - Der Jungler wird gesehen oder vorhergesagt.
   - Dein eigener oder ihr Flash ist weg.
   - Du kannst den nächsten Spike kaufen.
3. **Objective-Vorlauf:**
   - 60 s vor dem Spawn die Vorbereitungskette (crashen, back, zum Pit mit Team).
   - 40 s vorher loslaufen.
   - Ohne Prio den Tausch-Satz (ABGEBEN_TAUSCHEN).
4. **Respawn-Kette:** 12 s vor dem Respawn Kauf und Ziel.
5. **Ein aktiver Plan (Schiedsrichter):**
   - Kern und Stratege schlagen nur vor. Gesprochen wird ein Plan-Satz nur, wenn er den aktiven Plan setzt oder
     ändert.
   - Eine Änderung innerhalb von 30 s gibt es nur bei einer echten Lageänderung (Gefahr, Kill, Objective, Sichtung,
     die das Ziel betrifft). Sie beginnt mit der Änderung („Jetzt, wo …“).
   - Warnungen und Infos (I1–I5) dürfen immer sprechen, löschen den Plan aber nicht, außer die Warnung macht ihn
     unmöglich.
   - „Und dann?“ beantwortet der Plan (sein nächster Schritt).

## Teil 2 – Messen

1. **Blinde Soll-Liste:**
   - Ein frischer Challenger-Kritiker bekommt je Minute nur die Lage (133448, 192113, 101426), ohne die Coach-Sätze.
   - Er schreibt je Minute höchstens zwei Dinge, die ein Coach sagen müsste.
   - Ein zweiter Agent vergleicht mit dem Nachspiel: gesagt, teilweise oder fehlt.
   - Soll: ≥ 80 % gesagt oder teilweise.
2. **Füllsatz-Quote** (Sätze ohne neue Info oder Entscheidung, von einem Kritiker gezählt): Soll ≤ 5 %.
3. **Widersprüche:** Plan-Wechsel in < 30 s ohne Lageänderung. Soll 0.
4. **Latenz:** wie in Teil 0.2.
5. **Weiter aus 016:**
   - Abdeckung I1–I4 ≥ 90 %;
   - Sicherheit hart (0 / 0 / 0).
6. **Protokolle:** `NACHSPIEL_*.md` neu erzeugen und „fehlt“-Minuten markieren.

## Ende

1. Unit-Tests und Szenarien zuerst rot, dann die Fixes. Voller Lauf.
2. `017_bericht.md`:
   - Soll-Liste-Treffer vorher (Stand 016) und nachher;
   - Füllsätze, Widersprüche, Latenz, Abdeckung, Sicherheit;
   - die zehn schlimmsten „fehlt“-Minuten mit Grund.
3. Committen. Starte den Coach nicht.
