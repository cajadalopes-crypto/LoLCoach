# Auftrag 008 – Kritik-Runde (neue Kritiker, zwei Rollen)

Vier neue Kritiker-Agenten ohne Code, einer je Partie (164326 zusammen mit 144655). Jeder hatte zwei Rollen:

- **Challenger-Kritiker** wie in Auftrag 005: ok / schwach / falsch / gefährlich.
- **Carlos-Kritiker** (A5): hilft / neutral / nervt je ungefragter Ansage. Dazu lagen Carlos' Notizen und
  Sprechtasten-Logs aus 213624 und 101426 bei.

Neu nach Buch 4, Kapitel 6: je Satz „Ist das Warum nachvollziehbar?“ (ja/nein) und die Klasse „Info ohne Folgen“.

Grundlage waren die Protokolle nach Teil A und Teil 1 (Stand vor dem Commit, `--fragen` für 101426 und 213624). Die
Urteile liegen im Scratchpad (`k008_krit/urteile_*.jsonl`). Nach der Zählung kamen noch Kleinigkeiten dazu (unten):

- die WARUM-Antwort beginnt jetzt mit dem Plan-Satz,
- der Teamplan-Satz ist kürzer,
- sechs Befunde der Kritiker sind behoben.

Eine Nachzählung verlangt der Auftrag nicht, es gab keine.

## Zählung

| Partie | min | ok | schwach | falsch | gef. | falsch je 30 min | Warum ja | hilft | neutral | nervt | Info ohne Folgen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 101426 (echt, Carlos' Testpartie) | 35,9 | 81 | 7 | 3 | 0 | **2,5** | 91 % (71/78) | 88 % | 2 % | **10 %** | 1 |
| 164326 (echt) | 42,8 | 98 | 5 | 1 | 0 | **0,7** | 95 % (86/91) | 91 % | 5 % | 4 % | 4 |
| 173159 (echt) | 38,3 | 83 | 3 | 1 | 0 | **0,8** | 92 % (57/62) | 93 % | 5 % | 2 % | 1 |
| 144655 (echt, 10 min) | 9,7 | 11 | 1 | 0 | 0 | 0,0 | 70 % (7/10) | 83 % | 8 % | 8 % | 1 |
| 213624 (Bot, Fragen) | 25,1 | 96 | 8 | 0 | 0 | 0,0 | 89 % (79/89) | 95 % | 0 % | 5 % | 0 |

**Soll aus A5** (101426, 164326, 173159):

| Soll | 101426 | 164326 | 173159 |
|---|---|---|---|
| „nervt“ ≤ 10 % | 10 % (8/82), knapp erreicht | 4 % ✓ | 2 % ✓ |
| „hilft“ ≥ 60 % | 88 % ✓ | 91 % ✓ | 93 % ✓ |
| Warnungen ≤ 10 je 30 min (kennzahlen.py) | **12,5** ✗ | 9,1 ✓ | 8,6 ✓ |
| 0 Sätze mit verbotener oder vager Form (kennzahlen.py) | 0 ✓ | 0 ✓ | 0 ✓ |
| „falsch“ ≤ 2 je 30 min | **2,5** ✗ | 0,7 ✓ | 0,8 ✓ |
| Warum nachvollziehbar ≥ 90 % (Buch 4, 6) | 91 % ✓ | 95 % ✓ | 92 % ✓ |
| Info ohne Folgen: 0 je 30 min (Buch 4, 6) | 1 ✗ | 4 ✗ | 1 ✗ |

Kein „gefährlich“ in keiner Partie. Die Kritiker zählten auch drei Formen als vage, die `kennzahlen.py` nicht als
vage erkennt:

- „Raus, zu deinem Turm!“ auf einer fremden Lane,
- „Raus, zu Talon!“,
- „19 20“ als Uhrzeit.

## Klassen (schwach und falsch) und was danach gebaut wurde

| Klasse | Fälle (falsch) | Beispiele | Gebaut |
|---|---|---|---|
| „Du stehst tief“ auf der eigenen Lane | 5 (2) | 101426 24:47, 31:23; 173159 6:39; 213624 7:14, 9:39 | Vorsicht nur noch in ihrem Jungle oder ihrer Basis (`vorsicht_nur_jungle`). Szenarien `2447-…`, `3123-kein-tief-auf-der-lane` |
| abgebrochener Satz | 4 (0) | 101426 30:08, 164326 21:58, 173159 19:42, 213624 18:12 | nicht gebaut: Transport (Sprechplan), eigenes Thema |
| an der Frage vorbei | 4 (1) | 101426 32:17 tot, „Dann zuerst in den Shop.“; 101426 29:00 Inventar; 213624 12:14 | Respawn-Plan nennt jetzt den Kauf und die Lane. Szenario `3207-tot-respawn-mit-kauf` |
| vage Sprache | 6 (0) | „Raus, zu deinem Turm!“ auf der Top-Lane (101426 25:38, 31:43); „Raus, zu Talon!“; „19 20“ | Steht der nächste Turm auf einer anderen Lane: „Raus, zu eurem Top-Turm!“ (Szenario `2538-raus-mit-lane`). „Raus, zu Kayn!“ ist die Form aus A2, bleibt. |
| Info ohne Folgen | 4 (0) | „Caitlyn ohne Flash.“ (Carlos will die Flashs), „Gut raus.“ (Bestätigung, Buch 3) | nicht gebaut: beide Satzarten sind gewollt |
| falscher Grund | 2 (1) | 173159 22:17 „Back jetzt: 29 Prozent Leben“ bei 13 %; 101426 2:35 „Trade Aurora …“ bei 15 % | Die Leben-Zahl ist die beim Sprechen (Haken im Sprechplan). Szenario `2217-leben-von-jetzt`. Der Trade ist Mikro (Buch 2, zurückgestellt). |
| Widerspruch | 1 (1) | 164326 33:02 „Baron weg. Farm Top …“ – sie hatten den Buff | „Sie haben den Baron.“ Szenario `3302-sie-haben-den-baron` |
| Wiederholung ohne Anpassung | 2 (0) | 213624 10:19/10:26 dreimal dieselbe Inventar-Antwort | nicht gebaut |
| zu spät | 1 (0) | 144655 9:11 „Raus“ bei 18 % tief in ihrem Jungle, Kha'Zix allein ungesehen (A1 verlangt ≥ 2 Fehlende) | nicht gebaut: A1 wie beschlossen |

Neue Szenarien aus der Kritik, alle auf dem kritisierten Stand rot:

- `2026-09-28_101426_kritik008.toml` (4),
- `2026-09-27_164326_kritik008.toml` (1),
- `2026-09-27_173159_kritik008.toml` (1).
