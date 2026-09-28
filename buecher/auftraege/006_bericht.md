# Bericht zu Auftrag 006 – Wahrnehmung: Welle, Quest-Anzeige, Flash im Spielbild

Fertig am 28.09.2026. Der Coach wurde nicht gestartet, und das Entscheiden ist unverändert. Die Einzelheiten stehen in
`buecher/messungen.md`, Abschnitt „Auftrag 006“.

## Commits

- `957fbbf`: W1, Welle mit drei Schaltern in `[welle]`, einzeln gemessen; `wellen_eichung.py --neu --schalter`
- `e7c4aa8`: W2 (Quest-Platz V passiv gelesen), W3 (Flash-Machbarkeit, Bilder in `buecher/flash_pruefung/`),
  messungen.md, OFFEN.md, drei Protokolle
- dazu der Commit mit Auftrag und Bericht

## Tests und Szenarien

- `tests/alle.py` **9 / 10**. Neu ist `test_quest_ende_aus_dem_hud`. Weiter scheitert nur `kamera_gibt_nur_einmal_frei`
  an der Umgebung (Bildschirm 7680 × 2160, seit 004).
- Szenarien **163 / 167** (unverändert), konstruierte Lagen **40 / 40**.

## Kennzahlen

| | Soll | vorher | nachher |
|---|---|---|---|
| Welle 173159, eindeutige richtig | ≥ 80 % | 7 / 12 (58 %) | **10 / 12 (83 %)** |
| Welle 144655 | nicht schlechter | 9 / 11 | 9 / 11 |
| Welle 164326 | nicht schlechter | 13 / 15 | 13 / 15 |
| Quest-TP bereit (213624 / 102112 / 173159 / 164326) | ab Quest-Ende | 13:35 überall | 9:51 / 11:36 / 11:46 / 12:12 |

- **W1:** Nur `hysterese_zu_mitte_s = 1` hilft ohne Schaden. `icon_deckung_zone` kostet 144655 drei Treffer,
  `trend_farbwechsel` gleicht sich aus. Beide stehen auf aus, ihre gemessene Wirkung steht im Kommentar.
- **W2:** Der Quest-Platz V ist **ohne Tastendruck** sichtbar.
  - Ein türkiser Ring wächst mit dem Fortschritt, ab dem Quest-Ende ist das Symbol violett.
  - Das erste violette Schirmbild liegt in allen vier Partien im Fenster der Handmessung.
  - Der Coach liest nur, er drückt nie V.
- **W3:** Mit den gesicherten Bildern (alle 5 s) ist ein Flash-Blitz (~0,3 s) nicht zu prüfen. In den fünf Beispielen
  ist keiner zu sehen, in dreien ist der Flashende nicht einmal im Bild.

## Offen und zu entscheiden

1. **Flash im Spielbild bauen?** Live liegt das Spielbild mit ~12 / s vor. Sichtbare Flashs findet aber schon die
   Balkenspur (Quelle „Bildschirm“: 4 von 12 in 164326, 5 von 9 in 173159). Ein gelber Blitz brächte vor allem die
   Bestätigung „Flash statt Dash“. Mein Vorschlag vor jedem Bau: nach einem Sprung der Balkenspur 1–2 s mit 12 / s
   sichern und an 20 echten Flashs zählen.
2. **Welle:** 173159 7:33 (Icon am Zonenrand) und 9:25 (übereinanderliegende Vasallen) sind Bildwahrnehmung
   (`Wellenleser.punkte`), keine Schwelle.
3. **Aus 004 und 005 weiter offen:** `004_frage.md` (Wendepunkt-Probe, Wächter 1621), `005_frage.md` (Inhibitor-Turm,
   Belagerung, Baron) und die Klassen 6, 9, 10 und 11 der Kritik.
