# Bericht zu Auftrag 026 – Buch 15, Stufe 1 fertig machen

## **TOR NICHT ERREICHT**

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Die Fälle im Einzelnen und die geänderten
Messdefinitionen stehen in `buecher/messungen.md` („Auftrag 026“).

| Maß | Soll | vorher (025) | nachher (026) |
|---|---|---|---|
| Paket-Abdeckung | ≥ 90 % | 94 % | 91 % ✓ |
| … davon angesagt | – | 55 % | 68 % |
| Abbruch-Reaktion | ≥ 95 % | 82 % | 100 % ✓ (16/16) |
| Budget-Treue: Fehler / gefährlich | ≤ 5 % / 0 | 13 % / 0 | 0 % / 0 ✓ (n = 9) |
| Back-Pünktlichkeit | ≥ 80 % | 58 % | 2/2 ✓, dazu 22 Backs erzwungen oder abseits der Lane |
| Chancen genutzt | ≥ 70 % | 56 % | 64 % ✗ |
| Event-Abdeckung (mit Claude) | ≥ 85 % | 59 % | 61 % ✗ (nur Kern 66 %) |
| Erahnung | ≥ 60 % | Kampf 75, Rückkehr 85, Lane-Back 68, Gank 8 | unverändert; Gank bleibt still |
| Abwägung (blinder Kritiker) | ≥ 75 % | 61 % gemeldet, nachgemessen 50 % | 47 % ✗ |
| Soll-Liste bekannt / neu / 231200 | ≥ 80 / 75 % | 55 / 59 / 61 % | 62 / 66 / 60 % ✗ |
| Widersprüche je Partie | ≤ 1 | 1–7 | 2–4 ✗ |
| Füllsätze | ≤ 5 % | 2–3 % | 0,6–1,0 % ✓ |
| Sicherheit | 0 | 0 | 0 ✓ |
| Latenz ganze Antwort / erster Satz | ≤ 2 s | 1,5–1,7 / 1,3–1,5 s | 1,6–1,9 / 1,4–1,7 s ✓ |
| Kosten API-Nachspiel | ≤ 3,50 $ | 2,77 $ | 2,82 $ ✓ |

**Messdefinitionen:**
- Die Schärfung jeder Definition ist in `messungen.md` offengelegt.
- Die Kritiker haben neue Regeln (Übergänge sind keine Füllsätze, ein begründeter Planwechsel ist kein Widerspruch). Füllsätze und Widersprüche sind deshalb nur bedingt vergleichbar.
- Die Abwägung aus 025 (61 %) ließ sich am committeten Stand nicht wiederholen, dort sind es 50 %.

## Gebaut

1. **Back zur Frist:**
   - 10 s vorher sagt der Kern: „In 10 Sekunden Welle rein, dann Back: pünktlich zur Kanone um …“.
   - Ein Back nur fürs Gold wartet in der Lane-Phase, wenn die Frist vorbei ist und die Welle nicht bei ihm liegt.
2. **Abbruch:** Jeder Gegner, der neu auf 1000 herankommt, bricht ab, außer bei eigener Überzahl. Dazu kommen Überzahl aus der Gefahr-Uhr (auch Ungesehene), „Partner weitergezogen“ und eine 15-s-Sperre für abgebrochene Ziele.
3. **Gefahr-Uhr:**
   - Lange Ungesehene zählen mit höchstens 5 s, TP aus der Basis mit 6 s.
   - Die Marge steigt auf 8 s; die Paket-Abdeckung bleibt dabei bei 91 %.
   - Die Wege sind gespiegelt.
4. **FARMEN:** hat einen Start-Satz. HALTEN bleibt bewusst still, weil es sonst gegen das Szenario 3451 sprach.
5. **Eine Stimme:** „X kämpft: nicht hin“ schweigt gegen den aktiven Plan von Kern oder Claude. Die Begründung nennt das Ziel („Top-Welle bringt mehr“).
6. **Chance „Lane-Gegner weg oder tot“:** Der Kern sagt „Welle rein, dann Platten“.
7. **Kritiker:** Die Anweisung ist fair gemacht, wie der Auftrag es verlangt.
8. **Gank-Erahnung:** nicht gebaut. Sie bleibt still, die Zeit ging an 1–7.

**Tests:**
- `tests/alle.py` 10/10.
- `test_kern.pakete_026` ist neu; er war vorher rot.
- Zwei neue Szenarien in 231200 (Platten-Chance, Back zur Frist) waren vorher rot.
- Alle Szenarien 332/346. Rot sind die 4 alten und 10 Abwägungs-Momente.

## Offen

- **Abwägung (47 %):**
  - Der blinde Kritiker will fast überall „Back“. Der Kern farmt, oft ohne Gold für ein Item oder mit der Back-Frist dagegen.
  - Die Back-Frist aus Teil 1 und das Kritiker-Urteil ziehen hier gegeneinander. Das sollte Carlos entscheiden.
- **Soll-Liste:** Sie fehlt vor allem bei Objectives (Herold, Drache, Baron als Ziel).
- **Widersprüche:** Sie liegen meist zwischen zwei Antworten auf Carlos' nachgespielte Fragen. Die Fragen beziehen sich auf die Live-Sätze, nicht auf die Sätze des Nachspiels.
- **Event-Abdeckung:** Objective-Events bleiben ohne Satz.

## Kosten

2,82 $ von 3,50 $.
