# Bericht zu Auftrag 025 – Events und lebendige Arbeitspakete, Stufe 1

## **TOR NICHT ERREICHT**

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Die Einzelheiten stehen in
`buecher/messungen.md` („Auftrag 025“).

## Maße (Buch 15, Teil 7) auf allen 8 Testpartien inkl. 231200

| Maß | Soll | Ergebnis |
|---|---|---|
| Paket-Abdeckung (davon angesagt) | ≥ 90 % | **94 %** ✓ (55 %) |
| Abbruch-Reaktion ≤ 2 s | ≥ 95 % | 82 % ✗ |
| Budget-Treue: Fehler / gefährlich | ≤ 5 % / 0 | 13 % ✗ / **0** ✓ |
| Back-Pünktlichkeit | ≥ 80 % | 58 % ✗ |
| Chancen genutzt | ≥ 70 % | 56 % ✗ |
| Event-Abdeckung (mit Claude) | ≥ 85 % | 59 % ✗ |
| Erahnung (Eintritt bei p ≥ 0,6) | ≥ 60 % | Kampf 75 %, Rückkehr 85 %, Lane-Back 68 % ✓; Gank 8 % → bleibt still |
| Abwägung (blinder Kritiker, 23 Momente mit ≥ 2 Events) | ≥ 75 % | 61 % ✗ (vorher 35 %) |
| Soll-Liste bekannt / neu (023: 59 / 72 %) | ≥ 80 / 75 % | **55 / 59 %** ✗, 231200: 61 % |
| Widersprüche je Partie | ≤ 1 | 1–7 ✗ |
| Sicherheit / Füllsätze / Latenz / Kosten | 0 / ≤ 5 % / ≤ 2 s / ≤ 0,50 $ | 0 ✓ / 1,9–3,1 % ✓ / 1,5–1,7 s ✓ / 0,35 $ ✓ |

**Stand der Soll-Liste:** Gemessen wurde **vor** Runde 2 (Back als Voreinstellung). Für ein zweites API-Nachspiel reichte das Budget nicht.

**Rückgang gegenüber 023:** Die Soll-Liste fiel auf der neuen Menge von 72 % auf 59 %. Mögliche Ursachen:
- die neuen Kern-Sätze („warum nicht“, Countdown, „Kampf vorbei“), die die Kritiker teils als Füllsätze zählten;
- Streuung zwischen den Läufen.

Die Ursache ist nicht sauber getrennt.

## Gebaut

- **`kern/events.py`:**
  - Erkennung aller Gruppen aus 0.1, jede Erkennung eine kleine Funktion.
  - Vier Erahnungen mit p und ETA, an den Aufnahmen geeicht (`wissen/events.toml`). Unter 60 % bleiben sie still.
- **`kern/uhren.py`:** die vier Uhren (Gefahr, Welle, Objective, Ressourcen).
  - Wege laufen über Karte × gemessenes Tempo.
  - `wissen/wege.toml` ist gemessen, aber lückenhaft: Nur Top-blau und Mid-rot kamen in den Aufnahmen vor.
- **`kern/pakete.py`:**
  - Ein aktives Paket mit Frist aus den Uhren, Erledigt- und Abbruch-Prüfung sowie gesprochenen Übergängen (≤ 8 Wörter, ohne Sprechsperre).
  - Das Plan-Objekt aus 021 hängt als `plan_text` am Paket.
  - Chancen-Scanner HILFE (Kampfrechner, nie bei „klar hinten“) und „warum nicht“.
- **Werkzeuge:** `werkzeuge/pakete_messen.py` (die automatischen Maße, 45 s für 8 Partien) und `werkzeuge/mehrfach_events.py`.
- **Tests:**
  - 24 Szenarien aus echten Aufnahmen (`tests/szenarien/*_auftrag025.toml`).
  - Unit-Test `test_kern.pakete_025`; er war vorher rot, weil die Module fehlten.
  - Szenarien gesamt 330 / 343. Rot sind die 4 alten und 9 Abwägungs-Momente.

## Zehn Beispiel-Pakete (Stub-Nachspiel, Endstand)

1. **120049, 21:37 OBJECTIVE:** „Drache allein: Level 17 gegen 9.“ → 21:39 „Raus jetzt: Rakan in 7 Sekunden.“
2. **120049, 21:40 OBJECTIVE:** „Drache jetzt: … ihr seid vier gegen eins.“ → 21:43 „Drache genommen.“
3. **120049, 22:11 HILFE:** „Planwechsel: Alistar kämpft mit Varus auf der Mid-Lane, du bist in 4 Sekunden da: hilf. Danach zur Top-Welle.“ → 22:15 „Kampf vorbei.“
4. **120049, 23:02 TURM:** „Ihr Mid-Inhibitor jetzt …“ → 23:09 „Ihr Mid-Inhibitor fällt.“
5. **120049, 15:54 TURM:** „Ihr Top-Inhibitor-Turm jetzt“ → 15:56 „Raus jetzt: Brand in 18 Sekunden.“
6. **164809, 12:28 TURM:** „Drück ihren inneren Top-Turm: 22 Sekunden, bis einer kommt.“ → 12:29 „Platte.“ → 12:32 „Raus jetzt: Wukong ist da.“
7. **164809, 18:33 TURM:** „Mit der Gruppe zu ihrem inneren Mid-Turm: 18 Sekunden …“ → 18:47 „Noch 5 Sekunden.“ → 18:49 „Ihr inneren Mid-Turm fällt.“ Der falsche Kasus ist behoben (jetzt „Ihr innerer …“), nachgemessen ist das nicht.
8. **120049, 4:03 BACK:** „Back jetzt: 1250 Gold für Caulfields Kriegshammer.“ → 4:22 still beendet (Kampf).
9. **120049, 8:16 WELLE:** „Top-Welle rein, dann back: 1000 Gold für Eklipse …“ → 8:23 still beendet (Kampf).
10. **125902, 27:46 KAUF:** „Verkauf Dorans Klinge, dann kauf Der Brutalisierer …“ → 27:59 still beendet (Tod).

## Offen

- **Widersprüche:** Der Kern-Satz „X kämpft: nicht hin“ kann einem Stratege-Satz widersprechen (120049 24:08/24:26). „Warum nicht“ muss den aktiven Plan von Claude kennen.
- **Back-Pünktlichkeit:** Der Kern ruft Back nicht nach der Back-Frist der Wellen-Uhr. Die Uhr wird gerechnet, aber noch nicht genutzt.
- **Abbruch-Reaktion:** Es fehlen die Gründe „Partner in anderem Kampf“ und „Überzahl aus der Gefahr-Uhr“.
- **Gank-Erahnung:** trifft nur zu 8 % ein, braucht eine neue Regel.
- **Wege-Messung:** Für Bot/Mid-blau und Lane → Grube fehlen Aufnahmen.
- **Nächste Messung:** Das Tor misst eine erneute Messung nach Runde 2 (API ~2,8 $).

## Kosten

2,77 $ von 4 $. Carlos sollte vor der nächsten Tor-Messung nachladen.
