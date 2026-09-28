# Auftrag 006 – Wahrnehmung: Welle, Quest-Anzeige, Flash im Spielbild (Claude, Chat, 28.09.2026 00:15)

Nur nach Auftrag 005. Es geht um Wahrnehmung, das Entscheiden bleibt unangetastet.

## W1. Welle in 173159 (heute 7 von 12)

- Die Fehlerursachen je Zeitpunkt stehen schon in messungen.md (Qualitätsrunde 2). Behebe, was im Bild behebbar ist.
- **Soll:** ≥ 8 von 10 eindeutigen Zeitpunkten in 173159, ohne dass 144655 (9/11) oder 164326 (13/15) schlechter
  werden.
- Jede Änderung braucht einen Schalter in `kern.toml [welle]`. Die Wirkung steht je Partie in messungen.md.

## W2. Quest-Fortschritt im HUD

- Prüf an den Bildern von 164326 und 173159, ob der Fortschritt der Top-Quest **ohne Tastendruck** irgendwo im HUD
  zu sehen ist.
- **Harte Grenze aus CLAUDE.md:** Der Coach drückt keine Taste, auch nicht V. Ist die Anzeige nur mit V sichtbar,
  wird sie nur gelesen, wenn Carlos V selbst drückt.
- Der Befund kommt nach messungen.md. Ist die Anzeige passiv lesbar: Quest-Ende erkennen, damit das Quest-TP ab
  dann als bereit gilt, nicht erst ab 13:35.

## W3. Flash im Spielbild: nur eine Machbarkeitsprüfung, kein Umbau

- Welche Bildausschnitte außer der Minimap werden aufgenommen, und mit welcher Rate? Ist ein gelber Flash-Blitz am
  Absprung oder an der Landung darin überhaupt zu sehen?
- Such in 164326 und 173159 fünf Flashs von Gegnern (Chat-Ping oder bestätigte Sprünge) und schau nach, ob sie im
  Spielbild erkennbar wären.
- Das Ergebnis als Abschnitt in messungen.md, mit Bildern in `buecher/flash_pruefung/`. Ob wir das bauen, entscheide
  ich danach.

## Ende

Committen, `006_bericht.md` schreiben. Starte den Coach nicht.
