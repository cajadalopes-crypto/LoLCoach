# Auftrag 007 – Entscheidungen, die restlichen Fehlerklassen, Live-Tauglichkeit (Claude, Chat, 28.09.2026 03:30)

Ziel dieses Auftrags: Danach darf Carlos die erste Testpartie spielen. Dafür müssen die Kritiker in den echten Partien
auf höchstens **2 „falsch“ je 30 min** kommen, und der Live-Weg muss auf seinem Bildschirm laufen.

## Teil A – Entscheidungen zu 004_frage.md und 005_frage.md

1. **Wendepunkt und FARMEN:** B, aber nie ohne Grund. Am Wendepunkt kommt immer ein Satz.
   - Ist der Plan FARMEN, nennt der Satz den Grund **und** was als Nächstes kommt, also `danach`, ein Ereignis der
     Zeitleiste oder eine Bedingung. Beispiele:
     - „Turm ist down: Farm Top, Rumble ist 40 Sekunden weg.“
     - „Turm ist down: Farm Top, bei 1300 Gold back für Eklipse.“
     - „Turm ist down: Farm Top; taucht Xin unten auf, Platten am inneren Turm.“
   - Die Wendepunkt-Probe bleibt so, wie sie ist.
2. **Wächter 16:21:** bestätigt. Mit Team und klarer Überlegenheit kommt kein „Raus“.
3. **Warten am Inhibitor-Turm (005, 1):** A mit Bedingung. In der Lane-Phase ist das Respawn-Ziel der **äußere**
   Turm, außer ≥ 2 Gegner waren in den letzten 10 s sichtbar ≤ 2000 davon. Dann gilt B mit ehrlichem Grund:
   „Bleib am inneren Turm: Gangplank und Kha'Zix stehen an deinem äußeren.“
4. **Belagerung der eigenen Basis (005, 2):** Ja, das ist eine neue Regel für Buch 5, Kapitel 7. Trag sie dort als
   Nachtrag ein.
   - **Auslöser:** ≥ 3 Gegner sichtbar in 3000 um euren Inhibitor-Turm, Inhibitor oder Nexus-Turm, **oder** ≥ 2
     eigene Türme in 30 s, **oder** Baron- bzw. Ältesten-Buff beim Gegner und ≥ 3 von ihnen auf einer Lane in eurer
     Hälfte.
   - **Wirkung:** VERTEIDIGEN bzw. ZUR_GRUPPE gilt dann auch aus der Ferne, mit dem Weg als Kosten. Ausnahme: Du bist
     selbst in ihrer Basis und der Nexus fällt vor ihrer Ankunft an eurem (Nexus-Rennen, mit Beleg).
5. **Lange Objectives (005, 3):** Ja. Für Baron, Ältesten und jedes Objective mit Tötungszeit > 25 s gilt „klar
   überlegen“ nur, wenn höchstens **ein** lebender Gegner länger als 20 s ungesehen ist.
6. **W3 Flash im Spielbild:** Stufe 1 bauen, also nur sammeln. Nach jedem erkannten Sprung (und nach jedem Chat-Ping
   „Blitz“) speichert der Coach live 1,5 s Spielbild rund um den Sprung nach `aufnahmen/<stamm>_flashclips/`
   (Bildrate wie live, platzsparend). Die Erkennung baut ab jetzt niemand, erst wenn 20 echte Clips da sind.

## Teil B – Die offenen Fehlerklassen aus 005_kritik_runde2.md

Wie immer: erst ein Szenario aus dem echten Fall, zuerst rot, dann der Fix.

- **Klasse 6, Antwort und Ansage zählen verschieden.**
  - Es gibt **eine** Zählfunktion für „ihr seid X“: wer in `kampf_fenster_s` an der Grube sein kann. Ansage und
    Antwort benutzen dieselbe.
  - Wo „schon dort“ zählt, sagt der Satz das ausdrücklich: „zwei stehen schon dort, zwei kommen“.
- **Klasse 9, Back ohne Anlass.**
  - Kein Back-Ruf in GEFAHR, das ist ZURUECK. Keiner in der Basis. Keiner, wenn seit dem letzten Back-Ruf nichts
    passiert ist.
  - Fälle: 173159 6:39 und 34:59, 164326 39:49, 213624 17:11.
- **Klasse 10, Ziel springt oder zieht weg vom offenen Fenster.**
  - Ein Turmziel wechselt nur mit Ereignis. Im Umwandel-Fenster bleibt das erste erreichbare Ziel, bis es fällt oder
    das Fenster zu ist.
  - Fälle: 164326 18:27, 35:14, 35:54, 41:26, 42:09, 42:33; 173159 20:17.
- **Klasse 11, Farmen statt Back.**
  - Bei Gold ≥ nächste Stufe + 500 oder Leben < 40 % ist BACK Kandidat vor FARMEN. Ausnahme: Ein Objective oder ein
    Fenster steht in ≤ 30 s an, dann wird das gesagt.
  - Fälle: 164326 16:23, 25:56, 28:37.
- **Einzelfälle:**
  - Dieselbe Flash-Meldung zum selben Gegner höchstens einmal je Verbrauch (164326 4:18).
  - Ein Ziel je Basis-Aufenthalt (102112).

## Teil C – Live-Tauglichkeit auf Carlos' Bildschirm (7680 × 2160)

Der Kamera-Test in `test_bausteine` scheitert, weil der Bildschirm jetzt 7680 × 2160 groß ist.

1. **Klären:**
   - Kopiert der Coach je Takt den ganzen Bildschirm, oder nur die Ausschnitte (Minimap, HUD, Spielbild-Streifen)?
   - Wie viel CPU und Speicher braucht der Beobachter bei dieser Größe?
   - Wo liegt das Spielfenster? Randlos im Vollbild auf 7680 × 2160, oder kleiner?
2. **Generalprobe** (`werkzeuge/generalprobe.py`) mit einem nachgebauten Fenster in dieser Größe, dazu 2,5 Minuten
   Live-Weg: Minimap gefunden, HUD gelesen, Takt ≥ 10/s, keine Ausnahmen. Den Befund kommt nach messungen.md.
3. Den Kamera-Test so anpassen, dass er die Bildschirmgröße nicht fest erwartet.

## Teil D – Kritik Runde 3

Wie Auftrag 005: drei neue, unabhängige Kritiker ohne Codekenntnis auf den neuen Protokollen. Gezählt wird je Partie
„falsch“ und „schwach“ je 30 min. Ergebnis nach `007_kritik_runde3.md`.

- **Freigabe-Schwelle für mich:** echte Partien (164326, 173159, 144655) ≤ 2 „falsch“ je 30 min, und kein „falsch“ der
  Sorte gefährlich (Vorwärts-Ruf vor einem Tod).
- Liegt es darüber, baust du die neuen Klassen mit ≥ 2 Fällen noch in diesem Auftrag und zählst einmal nach, mit einem
  neuen Kritiker.

## Ende

Committen und `007_bericht.md` schreiben. Wenn danach `008_auftrag.md` im Ordner liegt, machst du direkt damit weiter.
Starte den Coach nicht.
