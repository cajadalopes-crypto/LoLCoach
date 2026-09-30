Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 036 – Die Warnungsflut abstellen: Gefahr aus dem Modell

Der vollständige Bericht steht in `buecher/challenger/phase6_bericht.md`.

**TOR NICHT ERREICHT – noch nicht gemessen.** Der Umbau steht. Gemessen wird bei Carlos ohne Claude Code:
```
python werkzeuge\challenger\gefahr_schwelle.py
python werkzeuge\abnahme_035.py
```

**Commit** auf Zweig `stufe6-gefahr`, gepusht, kein Pull Request. Vorher `origin/main` geholt: `main` enthielt
`stufe5-abnahme` schon. Den Coach nicht gestartet, Claude nicht aufgerufen.

- **Teil 1:**
  - Eine Gefahr-Entscheidung warnt nur, wenn das Gefahr-Modell sie bestätigt: `Hirn.tod60 >= gefahr_schwelle`,
    über `vorrang.bestaetigt`.
  - Die Handregel ist nur noch Zusatzbedingung. Ohne Modellwert warnt nur B4 (wenig Leben).
  - Fällt die Warnung weg, spricht die beste andere Anweisung.
  - `gefahr_schwelle = 0.40` ist vorläufig. `werkzeuge/challenger/gefahr_schwelle.py` wählt sie an den
    Prüfpartien (Tod nach Warnung ≥ 2 × ohne, Warnungen ≤ 15 %) und schreibt sie nach `kern.toml`.
- **Teil 2:**
  - **Stillstand:** Die Ursachen waren im Code zu finden. Nach Einkauf, Recall-Kanal und Kampf begann der Coach das
    Stehen nicht neu, 027 schon: Im Brunnen nach dem Kauf kam nie ein „Los“.
  - **Basis:** Der Kauf kam erst am Brunnen statt beim Betreten der Basis, wartete auf einen Grund oder aufs Budget,
    und im Tod ging B7 vor B8.
  - Alle behoben. Die Fehlfälle stehen ab jetzt je Zeile in `makro_messen.py` und `phase5_messung.md`. Der Lauf aus
    035 hatte nur Summen.
- **Teil 3:** alle 121 roten Szenarien je eine Zeile.
  - W 50 (Warnungsflut, neu messen), G 4 (Gefahr-Prüfsteine für die Schwelle), T2 7 (Teil 2).
  - U 11: umgeschrieben, die makro-Fassung ergänzt, die alte bleibt.
  - F 15: alte Formulierung oder Kategorie, nach dem Neumessen umschreiben.
  - B 34: Befunde, vor allem Fragen ohne Ja/Nein oder ohne die gefragte Alternative, Carlos' Einspruch zur Lage und
    der fehlende Todesrückblick.
  - `szenarien.py --json` schreibt jetzt den Grund jedes Rots.

**Tests:**
- `tests/makro/alle.py` 7/7 grün.
- `tests/einzeln.py --basis` 86/34, **neu rot: keine**.
- Konstruierte Lagen 37/40, wie vorher.
- Bot-Nachspiel: Verdrahtung im Soll, Warnungen 61 → 0 (ohne Gehirn).

**Offen / zu entscheiden (Carlos):**
- Die zwei Befehle oben; die G-Szenarien müssen danach grün sein.
- Befunde B: welche zuerst? Vorschlag: Fragen (13) und Einspruch (11), weil sie Carlos direkt treffen.
- Annehmen-Rufe im Kampf (2501, 2613, 2631): Soll makro im KAMPF „Rein!“ sagen?
- a4/lagebild-Szenarien (Kategorie LAGEBILD des alten Systems): umschreiben oder streichen?
