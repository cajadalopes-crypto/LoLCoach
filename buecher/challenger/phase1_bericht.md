Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Challenger-Gehirn, Stufe 1 – Datenbasis der Entscheidungsmomente (Auftrag 030, 30.09.2026)

Neue Werkzeuge:
- `werkzeuge/challenger/phase1.py` baut die Momente, fortsetzbar; neue Downloads kommen mit.
- `phase1_pruefen.py` prüft sie.
- `test_kein_maphack.py` beweist, dass keine Gegnerposition in eine Lage kommt.

Einzelheiten:
- [merkmale.md](merkmale.md): jedes Feld mit Bedeutung, Quelle und B/G/U;
- [phase1_pruefung.md](phase1_pruefung.md): alle Tabellen;
- [aufteilung.json](aufteilung.json): die feste Aufteilung.

Riot-Abrufe: keine. Claude: keine.

## Was entstanden ist

**2.565.410 Entscheidungsmomente** aus 3504 Partien (alle Rollen; der Download lief während der Arbeit weiter).

**Ablage** in `daten/challenger/phase1/`:
- 24 Teile `.npz`, unkomprimiert, 1,5 GB;
- `phase1.lade()` holt alles in **0,8 s**;
- **Bau:** alles neu in etwa 2,5 min (20 Prozesse), Nachschub nur für neue Partien.

| Teil | Form | Inhalt |
|---|---|---|
| `X` | 105 Spalten | Lage, nur Wissbares: Uhr; du (Ort, Abstände, tot und Restzeit, Level, CS, Gold in der Tasche, Items, Leben, TP, seit Back); Mitspieler (Minimap); Scoreboard beider Teams (Kills, Türme, offene Inhibs, Platten, Drachen, Seele, Larven, Herold, Baron, Elder, Buffs, Items, Level, CS, Tote); Unterschiede Team und Lane; **Lane-Gegner nahe sichtbar** (≤ 1200); je Gegner tot + Restzeit und „zuletzt gesehen“ (Ort, Alter); Objective-Timer |
| `aktion` | 8 | Aktion der nächsten 60 s und **die drei danach** (60–120, 120–180, 180–240 s); alle zutreffenden als Bitmaske; Ziel (Monster oder Zone), Objective-Zustand, TP (sicher / unbekannt / kein TP-Zauber) |
| `folge` | 36 | nach 30/60/120 s: eigenes Gold und XP, Team-Gold-Abstand, Tod, Kills, Platten, Gebäude und Monster für und gegen |
| `meta` | 10 | Partie, Spieler, Team, Rolle, Liga, Zeit, Anlass, Aufteilung, Sieg, Dauer |
| `obj` | je Monster | Zeit, Art, Team, **frei/bestritten/umkämpft** |

**Zeitpunkte je Spieler:**
- jede volle Minute;
- jedes angesagte Ereignis: Kill, Gebäude, Monster, Monster-Spawn;
- eigene Ereignisse: Tod, Respawn, Back.

Liegen Zeitpunkte ≤ 5 s beieinander, zählt nur der letzte, also die Lage nach dem Bündel. Nach Anlass: Kill 866 k,
Minute 445 k, Gebäude 282 k, Back 234 k, Monster 232 k, Tod 194 k, Respawn 171 k, Spawn 143 k.

**Aufteilung** (fest, [aufteilung.json](aufteilung.json)):
- **Prüfspieler:** `sha1(Salz + PUUID) % 5 == 0`, also 20 % der Spieler.
- **Stichtag:** 26.09.2026 23:51 (80 % der Zeit davor).
- **Ergebnis:** Training 1,68 Mio., Prüfung Spieler 421 k, Prüfung Zeit 377 k, beides 91 k.
- Prüfspieler kommen als Entscheider im Training nie vor. Als Mitspieler in fremden Lagen bleiben sie drin, sonst
  fielen 89 % der Partien weg.
- **Später geladene Partien** liegen hinter dem Stichtag und sind damit „Prüfung Zeit“. Die Datei wird nie neu
  gerechnet.

## Prüfung (Abschnitt 3 des Auftrags)

**Zahlen:** Alle Tabellen stehen in [phase1_pruefung.md](phase1_pruefung.md). Im Training unter 200 Fälle haben 29
von 150 Zellen (Rolle × Phase × Aktion):
- **TP:** in jeder Zelle. Nur sichere Sprünge zählen (Entscheidung 2: TP wird ein Rechner in Stufe 3).
- **Split:** spät bei Jungle, Mid, ADC und Support.
- **Jungle:** bei Laner und Support.
- **Lane:** spät bei ADC und Support.
- **Warten:** früh beim Jungler.

Strukturelle Nullen sind markiert: Split erst ab 14:00, Jungler ohne Lane und Rotation.

**Rohdaten-Abgleich** mit einem eigenen, schlichten Leser der Riot-JSON:
- **30 Momente:** alle Felder stimmen.
- **300 Momente:** Kills, Türme, Level, Item-Wert, Back im Fenster, Folge-Kills und Sieg stimmen je 300/300. Position,
  Gold nach 60 s und tot zur Minute stimmen je 167–169 von 167–169.

**Drei Fehler, die der Abgleich fand und die behoben sind:**
1. Bei gleichem Zeitstempel (Kauf und Bauteile verbraucht) galt der größte statt der letzte Item-Wert.
2. Die Riot-Minuten liegen 0–0,4 s nach der vollen Minute. Jetzt sind sie auf die Minute gelegt, und die Werte zur
   Minute sind exakt.
3. Die Todeszeit-Formel stimmte nur in 89 %. Jetzt ist sie an den Minuten mit Leben 0 bzw. > 0 gekappt. Die Restzeit
   steht im Spiel auf dem Scoreboard, das ist also Wissbares.

**Warten war ein Sammelbecken.** Beim Nachsehen von Hand hieß ein Support „Warten“, der zum Kampf lief und dort einen
Assist bekam. Deshalb:
- Warten gilt jetzt nach der Phase-0-Regel: im Bereich bleiben, ≤ 2500 bewegt, an keinem Ereignis beteiligt.
  Das ist in High-Elo selten (1,5 %).
- Der Rest heißt **„Unterwegs“** (19,6 %).

**Nullprobe je Aktions-Label:** dieselbe Regel mit falschem Ort (gespiegelt bzw. fremde Lane) oder falscher Zeit
(+300 s), an 300 Partien.

| Aktion | Nullprobe | trifft trotzdem zu |
|---|---|---:|
| Lane | fremde Lane | 0 % |
| TP | Zeit | 0 % |
| Warten | Zeit | 3 % |
| Objective | Ort | 10 % |
| Split | Ort | 12 % |
| Rotation | Zeit | 13 % |
| Jungle (Laner) | Zeit | 18 % |
| Unterwegs | Zeit | 22 % |
| Tot | Zeit | 26 % |
| Back | Zeit | 28 % |
| Gruppe | Ort | 36 % (Mid bleibt beim Spiegeln Mid) |
| Jungle (Jungler) | Zeit | 69 % |

Jedes Label hängt am Moment. Einzige Ausnahme ist „Jungle“ beim Jungler (69 %): Er farmt fast immer, dort sagt das
Label wenig. Stufe 2 sollte es beim Jungler nicht als Entscheidung werten.

**Kein Maphack:** `test_kein_maphack.py` baut 30 Partien zweimal, einmal mit Zufallspositionen für ein Team.
- 21.461 Lagen: 0 Spalten verändert, außer dem Lane-Gegner nahe sichtbar. Dessen Ort steht nie weiter als 1200 weg.
- Die Zufallspositionen kamen in 2.934 Lagen bei den erlaubten Spalten an, der Test sieht also etwas.
- **Sabotage-Gegenprobe:** Die Jungler-Position in eine Spalte geschrieben, verletzt alle 3.269 Lagen, und der Test
  fällt durch.

## Befunde für die Planung

- **Objective-Zustand nach Entscheidung 3:**

  | Monster | frei | bestritten | umkämpft |
  |---|---:|---:|---:|
  | Drache | 60 % | 3 % | 37 % |
  | Larven | 72 % | 1 % | 27 % |
  | Herold | 68 % | 2 % | 31 % |
  | Baron | 52 % | 2 % | 46 % |
  | Elder | 42 % | – | 58 % |

- **„Bestritten“ ist fast leer.** Phase 0 hatte 40 % „frei, aber Gegner da“ gemessen, mit der Minute davor oder
  danach und 4000 Umkreis. Auf den Kill-Zeitpunkt interpoliert und mit 3000 Umkreis sind es 1–3 %. Die 40 % waren
  die Unschärfe der Minute, nicht die Wirklichkeit.
- **Nahe sichtbar ist selten:** Der Lane-Gegner ist bei Lanern in der Lane vor 14:00 nur in **31 %** der Lagen
  ≤ 1200 entfernt, weil die Positionen linear zwischen Minuten liegen. Im Spiel sieht Carlos ihn öfter. Die Lage
  unterschätzt hier, was er weiß.
- **Gegner-Jungler:** im Median vor 27 s zuletzt gesehen, in 8 % der Lagen noch nie.

## Was Stufe 2 davon braucht

1. **Lernen nur auf Training** (`aufteilung == 0`). Geprüft wird getrennt nach Spielern und nach Zeit; beides
   zusammen ist die härteste Prüfung.
2. **Aktionsziel:**
   - `a0` mit Vorrang, besser die Bitmaske, denn Back+TP, Objective+Gruppe usw. treffen zusammen zu.
   - **„Tot“** (19 %) ist keine Entscheidung. Solche Momente fallen aus der Policy und bleiben für Siegchance und
     Gefahr.
   - **„Unterwegs“** (20 %) ist ein Rest, keine Entscheidung. Er braucht entweder eine Zielangabe (wohin in 60 s:
     Zone, Grube, Mitspieler) oder er bleibt als „anderes“ stehen.
3. **Siegchance:** `sieg` plus die Scoreboard-Spalten. Die Lagen hängen stark zusammen: 730 Momente je Partie. Die
   Kalibrierung also je Partie gewichten oder eine Stichprobe nehmen, sonst zählen lange Partien mehr.
4. **Aktionswert:** Folge nach 60/120 s, bei Fensterende NaN. Das betrifft 2–9 % der Momente und fällt dort weg.
   Dazu die Siegchance-Änderung aus Modell 1.
5. **Dünne Zellen:**
   - TP überall, weil TP ein Rechner wird (Stufe 3).
   - Split spät außer bei Top; Lane spät bei ADC und Support.
   - Diese Zellen bekommen kein eigenes Modell, sondern gehen in die Rolle bzw. Phase darüber auf.
6. **Jungler:** „Jungle“ ist bei ihm Grundrauschen (Nullprobe 69 %). Für ihn zählen Objective, Gruppe, Back und
   der Weg (die Zone bei +60), nicht das Jungle-Label.
