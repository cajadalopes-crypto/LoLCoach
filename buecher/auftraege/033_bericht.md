Guthaben: 0,00 $ (Abo-Aufrufe: 0)

# Bericht 033 – Stufe 3b: Wahrnehmung für die 14 offenen Entscheidungen

Der vollständige Bericht steht in `buecher/challenger/phase3b_bericht.md`.

**Commit:** Auftrag 033. Den Coach nicht gestartet.
- **Neu:** `lolcoach/sehen.py` (Wards, Wardspur, Trinket, Goldrand), `wissen/ward_vorlagen.png`,
  `wissen/trinket_ziffern.png`, `werkzeuge/sehen_eichung.py`, `ward_spur_probe.py`, `tp_recall_probe.py`,
  `kopfgeld_probe.py`, `werkzeuge/challenger/elixiere.py`, Beschriftungen in `buecher/challenger/sehen/`.
- **Geändert:**
  - `welle.py`: Pulk-Schablone, Totenkopf-Filter, `stand()`.
  - `lage.py`: Trinket im Sekundenblock, Ward-Faden, `team_wards()`, `trinket_ladungen()`.
  - `makro/wahrnehmung.py`, S12 braucht jetzt `ward_weg`.
  - `kaufplan.py`: verkaufte Stiefel, Stiefelstufe, Elixier ab Level 14.
  - `stratege_live.py`: Uhr ist kein Ereignis.
  - `uhren.toml`: TP 5 s.
  - Szenario 2302.

**Tests:**
- `tests/alle.py` 11/11 grün, `tests/makro/alle.py` 4/4 grün.
- Szenarien: 362/376 grün. Die 14 Roten sind alle aus 028 bekannt: 7× „mehrere Events“, 3× wendepunkt-ansage,
  0944, wohin-kurz, s23, a4. 2302 ist wieder grün, kein neues Rot.

**Kennzahlen:**

| | |
|---|---|
| Wellen aller Lanes | Treffer 26/27, Fehlalarme 1/27 – verlässlich |
| Wards deines Teams (Ort) | Treffer 116/118, Fehlalarme 1/117 – verlässlich |
| Trinket-Ladungen | 80/80 an frischen Bildern – verlässlich |
| Nicht verlässlich | Ward weg, Busch, Recall, TP-Stand, Kopfgeld, Mitspieler-Blitz |
| Abdeckung | erkannt **105/111** (vorher 97); stumm: S11, S12, B5, T9, O12, P2 |

**Offene Entscheidungen:**
1. `lage.sicht_fuer` findet bei `.jsonl.xz`-Aufnahmen die Sichtungen nicht (alle Partien bis 29.09.). Nachgespielt
   wird dann ohne Protokoll. Der Fix ist eine Zeile, ändert aber die Eingaben der Szenarien. Soll er rein?
2. Die Makro-Lage live füllen (Stufe 4): Die Leser liefern jetzt, `MakroLage` wird aber noch nirgends live gebaut.
3. Wem ein Ward gehört, ließe sich aus einem Trinket-Abzug plus einem neuen Ward neben dem eigenen Icon schließen.
   Nicht gebaut, weil S12 auch an „weg“ scheitert.
