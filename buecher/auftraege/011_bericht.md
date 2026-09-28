# Bericht zu Auftrag 011 – Warnungsrate nachziehen, Szenario 2522 richtigstellen

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md` („Auftrag 011“).

## Commits

- `e372a71`: beide Stellschrauben, Szenarien, Unit-Test, neun Protokolle (neu), messungen.md, OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Umgesetzt

1. **Ungesehen zählt nur gepaart:** Wer länger als 5 s ungesehen ist, zählt nur als Kopf, wenn zugleich ein
   Sichtbarer nah ist und näher kommt.
   - 101426 20:01 und 23:35 bleiben jetzt still.
   - 20:10 und 21:35 bleiben: Dort kommt ein Sichtbarer näher.
   - 20:10 ist jetzt die erste Warnung vor dem Tod (20:16); `2016-viego-zaehlt-mit` bleibt grün.
2. **Keine Wiederholung ohne neue Lage:** Dieselbe Warnung kommt nur mit neuem Kopf, anderem Ziel oder einem
   `p_tod`, das um mehr als eine Stufe steigt (Stufen 0,15 / 0,3 / 0,5 / 0,7).
   - Die Wiederholung 9 s später fällt weg: Der Doppel-Satz 20:01/20:10 ist jetzt eine Warnung (Szenario
     `2010-keine-wiederholung`).
   - Ebenso fällt 22:38 „Back jetzt“ 13 s nach dem Rückzug weg.
3. **Szenario 2522:** Es erwartet jetzt den Split (Tryndamere nimmt den Drachen, Riven den Turm). Das Verhalten ist
   unverändert, der Grund steht im Szenario.

## Warnungen je 30 min (vorher = Stand nach 010)

| 101426 | 164326 | 173159 | 133930 | 140253 | 144655 | 213624 | 102112 |
|---|---|---|---|---|---|---|---|
| 15,0 → **13,4** | 11,9 → **9,8** | 11,0 → 10,2 | 15,1 → 13,7 | 13,9 → 11,1 | 12,4 → 12,4 | 10,8 → 10,8 | 3,9 → 3,9 |

**`a1-warnungen-je-30min` ist grün:** 101426 hat 11 GEFAHR-Sätze (vorher 13). Diese sind:

- 4 der 20:16-Art (9:00, 20:10, 21:35, 22:25: ein näher kommender Sichtbarer plus ein 9–15 s Ungesehener),
- 3 echte Mehrfachgefahren,
- 3 Kampf-Raus oder Back bei wenig Leben,
- 1 wegen wenig Leben.

Die Kennzahl mit Vorsicht-Sätzen bleibt in 101426 über 10 (13,4), weil 5 „Du stehst tief“ dazukommen.

## Tests und Szenarien

- **Szenarien 240 / 244**, 3 übersprungen.
  - Rot sind nur noch die alten Fälle: 3× Wendepunkt-Probe (19 späte Sätze) und 0944.
  - `a1-warnungen-je-30min` und `2522` sind grün.
- **Nebenwirkung:** Weil 23:35 nicht mehr warnt, prüft jetzt 213624 22:09 die Form „Von der Bot-Lane zurück zu …“.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.
- Leerlauf ab 14:00 praktisch unverändert (101426 52 %).

## Offen

- **„Du stehst tief“:** Soll die Warnungs-Kennzahl diese Sätze mitzählen? Mit ihnen liegt 101426 bei 13,4, ohne sie
  bei 9,2.
- **Nächster Schritt:** Nichts blockiert Testpartie 2. Vor der Partie muss Carlos den Coach neu starten.
