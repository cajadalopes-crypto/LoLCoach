Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Stufe 3b – Wahrnehmung für die 14 offenen Entscheidungen (Auftrag 033)

Gemessen an beschrifteten Bildern aus Carlos' Aufnahmen (nur Sehen, kein Entscheidungswissen). Beschriftungen und
Stichproben: `buecher/challenger/sehen/`, Werkzeuge: `werkzeuge/sehen_eichung.py`, `ward_spur_probe.py`,
`tp_recall_probe.py`, `kopfgeld_probe.py`. Verlässlich = Treffer ≥ 90 % und Fehlalarme ≤ 5 % an einer **frischen**
Stichprobe (an Regeln und Schwellen nicht beteiligt). Urteil steht in `lolcoach/makro/wahrnehmung.py`.

| Eingabe | Weg | Treffer | Fehlalarme | Laufzeit | verlässlich |
|---|---|---|---|---|---|
| Wellen aller Lanes (W11, W14, M6) | `welle.py` auf alle Lanes; neu: Pulk-Zerlegung, Totenkopf-/Ziffer-Filter, „bei euch“ erst ab 2 Gegner-Vasallen | 26/27 (96 %) | 1/27 (4 %) | 20 ms, 1×/s | **ja** |
| Eigene Wards – Ort, Alter (S10, S14, T4, M5) | `sehen.wards`: Vorlagenabgleich (hell, matt, Kontrollauge, blass), `sehen.Wardspur` | 116/118 (98 %) | 1/117 (1 %) | 205 ms, eigener Faden alle 3 s | **ja** |
| Eigener Ward weg (S12) | Wardspur „weg“ | – | 3–7/50 (6–14 %) | – | nein |
| Trinket-Ladungen (S13) | `sehen.trinket`: Ziffer-Vorlagen im HUD-Feld | 80/80 | 0/80 | 0,05 ms, 1×/s | **ja** |
| Busch ohne Sicht (S11) | – | – | – | – | nein |
| Recall des Lane-Gegners (B5) | `Lagebild._recall` (7 s still, dann weg), nachgespielt | 18/36 bestätigt | – | – | nein |
| TP-Stand der Gegner (T9) | `Lagebild._fernsprung`, nachgespielt | nicht messbar | – | – | nein |
| Objective-Kopfgeld (O12) | `sehen.kopfgeld`: Goldrand um Turm-Symbole | Rand lesbar, Bedeutung offen | – | – | nein |
| Blitz der Mitspieler (P2) | HUD / Chat | – | – | – | nein |

**Neue Abdeckung: erkannt 105/111** (vorher 97). Stumm bleiben S11, S12, B5, T9, O12, P2 (`buecher/challenger/abdeckung.md`).

## Je Eingabe, knapp

- **Wellen.** Drei Stichproben à 60 Karten. Die erste fand die Fehler: einzelne rote Punkte waren Totenkopf-Marker,
  Turm-Ziffern und Stücke von Champion-Ringen (4 von 24 „bei euch“ falsch). Dazu übersah der Leser dichte Pulks.
  Nach Carlos' Hinweis zählt der Leser Pulks mit einer Schablone: Ein Vasall ist immer derselbe Kreis
  (Silhouette 79 px bei 570, an 490 freistehenden gemessen). Zuerst setzt er die sichtbaren hellen Kreise. Was dann
  über die Schablonen hinausragt, ist ein verdeckter Vasall. Gemessen an den Seitenlanes (238 Lane-Bilder):
  - Stichprobe 2 mit dem Endleser: 10/11 richtig, 1 übersehen (Welle in der Basis).
  - Frische Stichprobe 4: 16/16 richtig, nichts übersehen.
  - Der eine Fehlalarm ist ein Vasall mit einem Totenkopf daneben.
  - Offen: Am Karma-Pulk (6 Vasallen) findet der Leser 4. Einer liegt im ausgeblendeten Icon-Ring, einer ragt nur
    4 px über die Schablone (Schwelle: 8 px).
- **Wards.** Der erste Farbleser traf im Fluss nur 75 %: Das Ward verschwimmt mit dem Flussblau. Deshalb gleicht der
  Leser jetzt mit Vorlagen ab, in vier Formen, und blendet den Kamerarahmen aus. Die „blasse“ Form war ein
  Ward, das noch über eine Minute steht (Verlauf ±60 s). Die Formen „hell“ und „matt“ sagen **nicht**, wem das Ward
  gehört: Nur 8 von 135 hellen Wards tauchten neben Carlos' Icon auf. Wards deines Teams reichen aber für Sicht an
  der Flanke und am Objective. „Weg“ ist nicht verlässlich: Icons, Timer-Text oder Pings verdecken das Ward, auch
  nach dem Nachsehen noch in 3 bis 7 von 50 Fällen.
- **Trinket.** Die Ladungszahl unten rechts im Trinket-Feld wird mit drei Klassen-Vorlagen gelesen
  (Aufladung = 0, sonst 1 oder 2). An 80 Bildern gegengeprüft (Leave-one-out) und an 80 frischen Bildern: alle
  richtig.
- **Busch.** Nicht gebaut. Die Minimap zeigt keine Sicht im Busch (Nebelzellen sind so breit wie eine Lane), und im
  Spielbild fehlt ein Merkmal für „Busch ohne Sicht“.
- **Recall.** Nachgespielt über 10 Partien: 36 erkannte Recalls. Nur 18 davon sind bestätigt, also danach neue Items
  in der Live-API oder als Nächstes in der Basis gesehen.
- **TP-Stand.** In 10 Partien wurden nur 10 Fernsprünge erkannt. Das sind unter 50 Stichproben, und wie viele echte
  TPs es gab, zeigt keine Quelle. Deshalb ist der Treffer nicht messbar.
  - Fehler gefunden: `lage.sicht_fuer` findet bei `.jsonl.xz`-Aufnahmen die Sichtungen nicht. Im Probe-Werkzeug ist
    das umgangen, `lage.py` ist nicht geändert (Entscheidung im Auftragsbericht).
- **Kopfgeld.** Goldrand an Türmen ist lesbar. Er zeigte sich in 4 von 10 Partien, immer an allen drei eigenen
  Außentürmen ab ~14 min. Dass er das Kopfgeld bedeutet, ist nicht belegt: Die Live-API hat kein Kopfgeld-Ereignis,
  und der Goldvorsprung ist aus ihr nicht zu schätzen, weil sie gegnerische Items nur „zuletzt gesehen“ kennt.
- **Mitspieler-Flash.** Die HUD-Leiste zeigt nur Leben und Ult. Im Chat stehen 50 Blitz-Pings (11 Partien), alle über
  Gegner.

Verdrahtet: `lage.Beobachter` liest Trinket im Sekundenblock und Wards im eigenen Faden (`WARD_TAKT` 3 s). Das
`Lagebild` führt `team_wards()` und `trinket_ladungen()`. Der Minimap-Takt (60 Bilder/s) bleibt unberührt. Die
Makro-Lage live zu füllen bleibt Stufe 4.

## Reste aus 028

1. **Wiederholungskäufe.** In 134020 wurden die Stahlkappen 14:11 gekauft und 32:29 für die Schikane verkauft.
   `kaufplan` merkt sich jetzt verkaufte Stiefel und empfiehlt mit vollem Build keine Stiefel mehr. Aufgewertete
   Stiefel zählen als die Stufe darunter. Test: `auftrag_033_kein_wiederholungskauf`.
2. **Satzbug** „Jetzt, wo Baron in 34 Sekunden aufgetaucht ist“. Eine Uhr gilt nicht mehr als Ereignis
   (`stratege_live._als_ereignis`, Test in `test_kern`).
3. **Elixier-Regel** aus 3000 High-Elo-Partien (`werkzeuge/challenger/elixiere.py`):
   - Nur 9 % der Spieler kaufen ein Elixier.
   - Beim Kauf: Level 14/17/18 (10/50/90 %), Minute 26/32/40.
   - 65 % kaufen es mit ≥ 5 fertigen Items.
   - Neue Regel: ab Level 14 (vorher 9), weiter mit fünf fertigen Items und freiem Platz.
4. **Szenario 2302** folgt dem früheren Back (22:25) und ist grün.
5. **TP-Kanal** 3 s statt 4 s (seit 25.S1.1, Stand 26.19): `uhren.toml tp_s` 6 → 5, Test nachgezogen.
