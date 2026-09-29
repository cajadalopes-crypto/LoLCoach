# Auftrag 020 – Schritt B aus Buch 14: Kampfrechner, geeicht an Riot-Partien (Claude, Chat, 29.09.2026 21:15)

Lies `buecher/14_bauplan_gehirn.md`, Schritt B. Er kommt direkt nach 018. **Keine Testpartien, frag Carlos nie nach
einer Partie, starte den Coach nicht.** Die Schlüssel liegen in `geheim/`. Sie werden nie ausgegeben, geloggt oder
committet.

## 1. Fähigkeitswerte aller Champions

- **Quelle:** strukturierte Daten, zuerst Meraki Analytics prüfen (`lolstaticdata`, champions.json mit Fähigkeiten,
  Rängen und Skalierungen). Geht das nicht, CommunityDragon.
- **Ablage:** `wissen/faehigkeiten/` mit Patch-Stand und Quelle.
- **Abgleich:** mit den Wiki-Werten in `combo.py` für Riven, Camille und Graves. Weichen sie ab, gilt die Quelle mit
  Beleg, und der Unterschied steht im Bericht.
- **Umfang:** Nur Schaden, der sicher rechenbar ist (Basis je Rang, AD/AP-Skalierung, Schadensart). Unsicheres (Stapel,
  bedingte Boni) vorsichtig, also eher zu wenig Schaden.

## 2. `lolcoach/kampf_rechner.py`

- **Eingabe:** Verbündete und Gegner an einem Ort. Je Champion Level, Items, Leben (bekannt oder voll) und bereite
  Zauber und Ult (bekannt oder angenommen).
- **Rechnung:** Burst je Champion gegen Leben, Rüstung und MR jedes Gegners. Daraus: Wer tötet wen zuerst, grob über
  die Zeit (einfache Reihenfolge: stärkster Burst auf das niedrigste effektive Leben).
- **Ausgabe:**
  - das Urteil `klar_vorn`, `knapp` oder `klar_hinten`;
  - die zwei entscheidenden Zahlen (z. B. „ihr 2400 Burst gegen Kog'Maws 1600 Leben; ihr Burst 1900 gegen dein
    1400“);
  - eine Liste der Annahmen.
- **Unit-Tests** mit konstruierten Lagen.

## 3. Eichung an Riot-Partien (Match-V5)

1. **Laden:** **Der Download läuft schon**, seit 29.09. abends, parallel gestartet von Carlos. Das Werkzeug ist
   `werkzeuge/riot_download.py` (von Claude/Chat, nur Standardbibliothek, fortsetzbar). Die Daten liegen in
   `daten/riot/matches/` und `daten/riot/timelines/`, der Stand in `daten/riot/status.json`.
   - Bau keinen zweiten Downloader. Nutze, was da ist, und fang mit der Auswertung schon an, während er lädt.
   - Ist er noch nicht fertig, starte ihn nicht doppelt.
   - Steht in `status.json` `"schluessel_abgelaufen": true`, schreib das in den Bericht.
   - Ursprünglicher Plan zum Vergleich:
   - EUW, Solo-Queue: Spieler aus Challenger, Grandmaster, Master, dann deren letzte Partien und je Partie die
     Zeitleiste.
   - Ziel sind ~2000 Partien. Ablage in `daten/riot/` (steht in `.gitignore`).
   - **Grenzen einhalten:** 20/s und 100/2 min. Bei 429 warten (Retry-After). Den Download fortsetzbar bauen.
   - **Schlüssel ungültig (403):** Er läuft etwa am 30.09. gegen 19:30 ab. Dann den Download stoppen, mit dem
     Vorhandenen weiterarbeiten und im Bericht schreiben: „Carlos muss den Riot-Schlüssel erneuern.“
2. **Kämpfe finden:**
   - Häufungen von CHAMPION_KILL (≤ 15 s, ≤ 2000 Einheiten), mit Beteiligten (Killer, Assists, Opfer).
   - Den Stand holst du aus dem Minuten-Frame davor: Level, Items (aus ITEM_PURCHASED/SOLD/UNDO bis dahin), Orte.
3. **Prüfen:**
   - Sagt der Rechner den Sieger voraus (mehr Kills oder das Überlebende-Verhältnis)? Das gilt je Urteil.
   - **Tor:** In `klar_vorn` und `klar_hinten` muss er ≥ 80 % treffen, und diese beiden Urteile müssen zusammen
     mindestens 30 % aller Kämpfe abdecken.
   - Verfehlt er das, dann die Schwellen für „klar“ verschieben, bis 80 % stehen. Den Anteil, der dabei übrig bleibt,
     nennst du.
   - Ergebnis in `wissen/kampf_eichung.toml` mit Stand.
4. **Grenzen offen nennen:** Die Zeitleiste kennt kein Leben zu Kampfbeginn, keine Abklingzeiten und keine genauen
   Beteiligten ohne Kill.

## 4. Anschluss

- **Das Lagebild (`welt.py`)** bekommt für jeden sichtbaren Kampf in der Nähe (Anlass I6) das Rechner-Urteil mit den
  zwei Zahlen.
- **Gesprochen** wird ein Kampf-Urteil erst in 021, und nur `klar_*` mit bestandenem Tor.

## Ende

1. Unit-Tests zuerst rot. Schnelle Prüfung wie in 019.
2. `020_bericht.md`:
   - Quelle und Abgleich;
   - Zahl der Partien und Kämpfe;
   - Trefferquote je Urteil und Abdeckung;
   - Tor ja oder nein;
   - fünf Beispielkämpfe aus Carlos' Aufnahmen mit Urteil und Ausgang.
3. Committen (`geheim/` und `daten/` prüfen). Starte den Coach nicht.
