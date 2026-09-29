# Bericht zu Auftrag 022 – Speicher: Der Projektordner wächst nicht mehr unkontrolliert

Fertig am 29.09.2026. Keine Testpartie, der Coach wurde nicht gestartet.

## Größe

| | vorher | nachher |
|---|---|---|
| Projektordner | **5,54 GB** | **4,35 GB** |
| Bilder ohne Testpartie (13 Partien) | 91 MB | 0 |
| Flash-Clips | 280 MB (5705 Dateien) | 32 MB (die 40 neuesten) |
| `aufnahmen_probe` | 397 MB | 52 KB (nur `generalprobe.log`) |
| Whisper `small` | 464 MB | 0 |

Es bleiben:
- die Bilder der 18 Testpartien (2,2 GB);
- Whisper `large-v3-turbo` (1,6 GB), das der Coach auf der Grafikkarte nutzt.

## Gebaut

- **`werkzeuge/aufraeumen.py`** (Logik in `lolcoach/aufraeumen.py`): Ohne Schalter macht es einen Trockenlauf,
  `--ja` löscht.
  - Es läuft nach jeder Partie automatisch; das ersetzt `bilder_aufraeumen`.
  - Testpartien und die letzten drei Partien fasst es nie an.
  - Die kleinen Daten zum Nachspielen bleiben immer: Sichtungen, Ereignisse, `gruben.json`.
- **Testpartien werden automatisch ermittelt:** Szenarien, Unit-Tests und Soll-Listen der Nachspiele, einschließlich
  des Freigabe-Tors aus 021. Die Liste steht in `wissen/testpartien.toml`: 18 Partien, je Partie mit Quelle.
- **Generalprobe:** Sie räumt am Ende selbst auf, nur das letzte Log bleibt.
- **Warum noch Bilder von 32 Partien da waren:**
  - `bilder_aufraeumen` löschte nur die Minimap-Bilder. Spielbild und Chat (`schirm_`, `chat_`) blieben immer.
  - Es lief nur nach einer Live-Partie.
  - Es hätte zudem Bilder von Testpartien ohne `BEHALTEN` gelöscht, etwa 213624.
- **Whisper `small`** war nur der Ersatz ohne Grafikkarte. Gelöscht; fällt CUDA je aus, lädt der Coach es selbst neu
  (einmal 0,5 GB).
- **`stratege_probe_016`–`021`** liegen jetzt unter `buecher/protokolle/proben/`. Die Werkzeuge schreiben dorthin.
  Die Pfade in älteren Berichten sind nicht angepasst.

## Was je neuer Partie dauerhaft bleibt (ohne Testpartie-Status)

| Datei | 39-min-Partie (183125) |
|---|---|
| `.jsonl.gz` | **34 MB** |
| `_verlauf.json` | 5,6 MB |
| `_kern.jsonl` | 3,8 MB |
| Sichtungen und Ereignisse | 2,0 MB |
| Rest | < 0,2 MB |
| **zusammen** | **~46 MB** |

**Ziel ≤ 10 MB nicht erreicht.** Die Aufnahme ist gzip, und gzip sieht nur 32 KB zurück. Dieselbe Datei als xz hat
**0,49 MB** statt 34 MB (gemessen; 3 s zum Packen mit gzip, 22 s mit xz). Nach der Partie xz zu packen brächte jede
Partie unter 10 MB.

**Zu entscheiden:** Das ändert das Aufnahmeformat. Alle Leser und viele Werkzeuge suchen `*.jsonl.gz`. Soll ich
umstellen?

## Tests

- **Unit-Test:** `aufraeumen_022` prüft, dass keine Testpartie und keine der letzten drei Partien im Plan steht.
- **`tests/alle.py`:** 10 / 10.
- **Szenarien:** 313 / 317. Rot sind nur die alten.
