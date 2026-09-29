# Auftrag 022 – Speicher: Der Projektordner wächst nicht mehr unkontrolliert (Claude, Chat, 29.09.2026 21:35)

Klein, und direkt nach 021 dran. **Keine Testpartien, starte den Coach nicht.**

## Stand (gemessen am 29.09. um 21:25)

Der Projektordner hat ~5,6 GB:

| Was | Größe |
|---|---|
| `aufnahmen/*_bilder` (32 Partien, ~24 000 Dateien) | 2,35 GB |
| `daten/whisper` (large-v3-turbo 1,6 GB, small 0,5 GB) | 2,1 GB |
| `aufnahmen_probe` (Generalproben) | 0,40 GB |
| `aufnahmen/*_flashclips` | 0,28 GB |
| `aufnahmen/*.jsonl.gz` (33 Partien) | 0,23 GB |
| `daten/riot` (am Ende ~2000 Partien) | ~0,15 GB |

## Regeln (Carlos: „nicht wie ein Geschwür immer weiter wachsen“)

1. **Immer behalten** (klein): je Partie `.jsonl.gz`, `_ansagen.json`, `_kern.jsonl`, `_stratege.jsonl`, `_notizen.md`,
   `_sprechtaste.log`, Bericht und Review. Das sind ein paar MB je Partie.
2. **Bilder** (`_bilder`) bleiben nur:
   - für **Testpartien**, also jede Aufnahme, die ein Szenario in `tests/szenarien/`, ein Unit-Test, ein
     Nachspiel-Satz oder das Freigabe-Tor aus 021 braucht (automatisch ermitteln, dazu eine Liste
     `wissen/testpartien.toml`);
   - für die **letzten drei Partien**, damit eine neue Partie mit Fehlern noch zum Testfall werden kann.

   Alle anderen Bilder werden nach dem Spiel gelöscht. Prüf, ob `bilder_aufraeumen` das schon tun sollte und warum
   noch Bilder von 32 Partien da sind.
3. **Flash-Clips:** höchstens die 40 neuesten (für die spätere Flash-Erkennung), der Rest weg.
4. **`aufnahmen_probe`:** Die Generalprobe räumt ihre Ausgabe am Ende selbst auf, nur das letzte Log bleibt.
5. **Whisper:** Wird `faster-whisper-small` noch benutzt? Wenn nicht, löschen.
6. **`stratege_probe_0xx/`** im Wurzelordner: nach `buecher/protokolle/` verschieben oder, wenn nur Zwischenspeicher,
   löschen.
7. **Werkzeug** `werkzeuge/aufraeumen.py`: zeigt, was es löschen würde (Trockenlauf), löscht mit `--ja`. Es wird nach
   jeder Partie automatisch aufgerufen. Testpartien und die letzten drei Partien fasst es nie an.

## Ende

- Einmal ausführen, erst trocken.
- Im Bericht: Größe vorher und nachher und was pro neuer Partie dauerhaft bleibt. Ziel: ≤ 10 MB je Partie ohne
  Testpartie-Status.
- Committen. Starte den Coach nicht.
