# Bericht zu Auftrag 020 – Kampfrechner, geeicht an Riot-Partien (Buch 14, Schritt B)

Fertig am 29.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Einzelheiten stehen in
`buecher/messungen.md` („Auftrag 020“).

## Quelle und Abgleich

- **Meraki `lolstaticdata` ist veraltet:** Stand Patch 25.15; Graves Q dort 45–125 + 80 %, im Spiel 50–150 + 55 %.
- **Genommen: CommunityDragon** (Patch 16.19, 173 Champions), jetzt in `wissen/faehigkeiten/` mit `stand.toml`.
- **Abgleich mit `combo.py` (Wiki):**
  - Riven Q/W/R2, Camille W/E und Graves Q/R sind **gleich**.
  - Die Daten kennen weder Rivens drei Q noch Passiv, Camilles Q oder Graves' Q-Detonation. Dort wird zu wenig
    Schaden gerechnet, also zur vorsichtigen Seite.

## Rechner und Eichung

- **`lolcoach/kampf_rechner.py`:**
  - rechnet den Burst je Champion gegen jeden Gegner und daraus einen Ablauf in 0,25-s-Schritten;
  - gibt `klar_vorn` / `knapp` / `klar_hinten` mit zwei Zahlen und den Annahmen aus;
  - **Unit-Test:** `kampf_rechner_020`, rot auf ce3abc9.
- **Riot-Daten:** 1095 Partien (EUW, Challenger bis Master), 35 157 Kämpfe.
  - Der Download lief beim Commit noch (~1100 / 2000).
  - Der Schlüssel war gültig.
  - Die Eichung wird in 021 mit dem vollen Satz wiederholt.

| Menge (Schwelle 0,50) | klar vorn | klar hinten | Abdeckung |
|---|---|---|---|
| alle Kämpfe | 97,0 % | 96,6 % | 67,6 % |
| Teamkämpfe (je Seite ≥ 2) | 93,6 % | 92,1 % | 49,0 % |
| gleich viele Beteiligte | 80,1 % | 80,5 % | 15,3 % |

**Tor: ja.** Die Schwelle liegt bei 0,50. Sie ist so hoch gewählt, dass auch bei gleich vielen Beteiligten beide
klaren Urteile mindestens 80 % treffen.
- **Grund:** Die Beteiligten kommen aus den Kill-Ereignissen. Deshalb trifft schon „mehr Köpfe gewinnt“ 96 %.
- **Grenzen:** Die Daten kennen kein Leben zu Kampfbeginn, keine Abklingzeiten und keine Beteiligten ohne Treffer
  auf ein Opfer.

## Anschluss

Das Lagebild (Anlass I6) bekommt `RECHNER mit dir: klar vorn: ihr 840 Burst gegen Kog'Maws 1120 Leben; ihr Burst
310 gegen dein 1710`.
- „Mit dir“ zählt nur, wenn du in 12 s dort bist.
- Dazu steht, wie viele Gegner niemand sieht.
- Gesprochen wird davon noch nichts; das kommt in 021.

## Fünf Kämpfe aus deinen Aufnahmen

| Kampf | Urteil | Ausgang (15 s) |
|---|---|---|
| 183125 13:52 – Zyra + du gegen Kog'Maw | klar vorn (840 Burst gegen 1120 Leben) | Kog'Maw stirbt ✓ |
| 183125 22:15 – Udyr + du gegen Garen | klar vorn (1160 gegen 1190) | Garen stirbt ✓ |
| 101426 20:13 – Yunara + du gegen Twitch | klar vorn (1350 gegen 1490) | du stirbst ✗ |
| 192113 29:38 – Sona + du gegen Master Yi (einer unsichtbar) | klar vorn | Sona stirbt ✗ |
| 101426 15:01 – Kayn + du gegen Viego, dein Leben 190 | knapp | Kayn stirbt |

An allen vier Aufnahmen:
- **klar vorn:** 13 richtig, 11 falsch.
- **klar hinten:** 10 richtig, 2 falsch.
- **knapp:** 20-mal gewannen sie, 10-mal wir.

Live zählen nur sichtbare Gegner. **Deshalb ist „klar vorn“ live nicht belegt** und steht in
`wissen/kampf_eichung.toml` auf `sprechen = false`. „Klar hinten“ („Nicht rein“) darf in 021 gesprochen werden.

## Tests

- **`tests/alle.py`:** 10 von 10.
- **Szenarien:** 313 von 317. Rot sind nur die alten (3× wendepunkt-ansage, 0944).
