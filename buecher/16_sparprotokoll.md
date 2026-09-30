# Buch 16 – Sparprotokoll (30.09.2026)

Anlass: Am 29. und 30.09. gingen 21,35 $ API-Guthaben weg. Davon waren 19,68 $ Nachspiele von Aufnahmen zum Messen
und nur 1,67 $ Carlos' echte Spiele.

**Grundsatz (Carlos, 30.09.2026 12:48, verbindlich):** Guthaben (die Claude-API) wird nur verbraucht, wenn Carlos
den Coach wirklich benutzt. Die Entwicklung nutzt die API nicht: Tests, Nachspiele, Proben, Eichungen, Kritiker.
Das gilt immer, nicht nur bei knappem Budget.

## 1. Wer die API nutzen darf

| Lauf | Weg |
|---|---|
| Carlos startet den Coach selbst (`Coach starten.cmd`), echtes Spiel | API: Haiku live, Sonnet für freie Fragen |
| Alles, was Claude Code startet: `tests/alle.py`, `nachspielen`, `generalprobe`, `stratege_probe`, `latenz_probe`, `szenarien --mit-claude`, Kritiker, Eichungen | **nie API**, nur Stub oder Abo |

## 2. Technische Sperre, nicht nur eine Regel

- `llm_api.aktiv()` ist nur wahr, wenn die Umgebungsvariable `LOLCOACH_API=1` gesetzt ist. Ohne sie läuft alles über
  das Abo, auch wenn ein Schlüssel in `geheim/` liegt.
- Zweite Sicherung: `llm_api._anfrage` wirft `APIFehler`, wenn die Variable fehlt. So kann kein Werkzeug die API
  um `aktiv()` herum aufrufen.
- Nur Carlos' Startdateien setzen die Variable, etwa `Coach starten.cmd` mit `set LOLCOACH_API=1`. Claude Code setzt
  sie nie, auch nicht „kurz zum Prüfen“. Die einzige Ausnahme steht in Abschnitt 4.
- Die `generalprobe` und alle Werkzeuge starten Unterprozesse ohne `LOLCOACH_API`. Die Variable wird aus der
  Umgebung entfernt, nicht nur nicht gesetzt.
- Test in `tests/alle.py`: Ohne die Variable gibt es keine API, auch mit Schlüssel. `generalprobe` und
  `nachspielen` reichen die Variable nicht weiter.

## 3. Messen ohne Guthaben

Die Messung geht nur so weit wie nötig, eine Stufe nach der anderen:

1. **Stub, kostenlos.** Prüft die Mechanik: wann, ob und wie oft der Coach spricht, Lücken, Stillstand, Basis,
   Abbrüche, Budget-Treue, Hin und Her, Füllsätze. Jede Code-Änderung wird zuerst und fast immer nur hier geprüft.
2. **Abo, 3 Partien** (231200, 091311 und eine Holdout-Partie). Prüft, was Claude wirklich sagt, und den Trend der
   Soll-Liste. Höchstens eine Runde je Auftrag.
3. **Abo, alle Partien.** Nur als Tor-Prüfung, wenn Stufe 2 nah am Tor liegt (bekannt ≥ 75 %). Höchstens einmal
   je Auftrag.

Dazu gilt:
- **Zwischenspeicher:** Kommt dieselbe Frage (gleicher Prompt, gleiche Lage) noch einmal, wird die gespeicherte
  Antwort genommen. Nie zweimal fragen.
- **Spielzeit steht still:** Nachspiele über das Abo warten auf die Antwort. Dafür hält die Spielzeit an, damit die
  langsamere Antwort über das Abo das Ergebnis nicht verfälscht.
- **Latenz und Kosten je Partie** kommen nur aus Carlos' echten Spielen (Live-Protokoll, `aufnahmen/*_kosten.json`),
  nie aus Nachspielen. Die Tor-Werte „Latenz ≤ 2 s“ und „≤ 0,50 $ je 30 min“ werden dort abgelesen.
- **Modell:** Über das Abo antwortet nur Sonnet, denn Haiku lief über die Kommandozeile nicht (Auftrag 017). Live
  läuft Haiku. Im Blindvergleich war Sonnet nicht besser als Haiku, die Messung bleibt also aussagekräftig. Weicht
  ein echtes Spiel deutlich ab, zählt das echte Spiel.
- **Das Abo ist auch nicht umsonst,** es kostet Carlos' Nutzungsvolumen. Deshalb gelten die Stufen oben auch fürs
  Abo. Kritiker laufen weiter nur einmal am Ende.

## 4. Ausnahmen

Eine Ausnahme gibt es nur mit Carlos' ausdrücklichem Ja im Chat, vorher mit Betrag und Grund. Im Auftrag steht dann
eine Zeile: „Ausnahme Guthaben: höchstens X $ für Y (Carlos, Datum)“. Nur für diesen Lauf darf Claude Code
`LOLCOACH_API=1` und `LOLCOACH_API_BUDGET=X` setzen. Der Code hält bei X hart an. Ohne diese Zeile gilt 0 $.

## 5. Nachweis in jedem Bericht

Die erste Zeile jedes Berichts lautet: **„Guthaben: 0,00 $ (Abo-Aufrufe: N)“**. Den Betrag rechnet
`werkzeuge/guthaben.py` aus allen `*_kosten.json`, die seit Auftragsbeginn außerhalb von Carlos' echten Partien
entstanden sind. Liegt er ohne Ausnahme über 0: Das ist ein Fehler, und er steht oben im Bericht.

## 6. Umsetzung

Auftrag 028, Teil 0, vor allem anderen. Die früheren Zeilen „API-Budget: höchstens N $“ in den Aufträgen sind damit
abgelöst.
