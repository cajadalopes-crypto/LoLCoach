# Bericht zu Auftrag 019 – Lagebild und Claude über die API (Buch 14, Schritt A)

Fertig am 29.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md`
(„Auftrag 019“), die Nachspiele je Variante in `stratege_probe_019/`, die gewählte Variante in
`buecher/protokolle/NACHSPIEL_*.md` (mit Soll-Liste und „fehlt“-Minuten).

## Gebaut

- **Lagebild `lolcoach/welt.py`:**
  - feste Reihenfolge, eindeutige Ortsformen, dazu „seit dem letzten Aufruf (30 s)“;
  - der Stratege liest es statt des alten Kontexts;
  - im Median ~1200 Tokens je Aufruf.
- **`lolcoach/llm_api.py`:**
  - Claude über die API mit Streaming, zwei Modellen und Kostenzähler;
  - Ersatz ist das Abo;
  - Schalter `[llm] weg`.
  - Der Schlüssel funktioniert (Mini-Aufruf). `geheim/` ist in `.gitignore` und nicht im Commit.
- **Schneller prüfen:**
  - Szenarien parallel;
  - Nachspiele aller Partien parallel über die API;
  - Antwort-Zwischenspeicher.

## Messung (4 Partien, echte Fragen)

| Größe | Abo (Stand 017) | Abo, neues Lagebild | API schnell (Haiku) | API stark (Sonnet) |
|---|---|---|---|---|
| ganze Antwort, Median / p90 | 6,2 / 11,4 s | 6,8 / 12,2 s | **1,6 / 2,6 s** | 2,6 / 5,5 s |
| Kosten je 30 min | – | – | **0,25 $** | 0,51 $ |
| Soll-Liste gesagt + teilweise | 60 % | 63 % | 61 % | 61 % |
| Füllsätze (Kritiker) / Widersprüche | 7,9 % / 4 | 7,8 % / 6 | 8,0 % / 6 | 11,8 % / 7 |
| Sicherheit | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

**Gewählt:** Haiku für Lane-Anlässe, Fragen und Plan-Wechsel. Sonnet ist nicht besser, aber langsamer und teurer.
- **Kosten für Carlos:** etwa **0,25 $ je 30 min Spiel**, also rund 0,50 $ je Stunde. Das liegt weit unter der Grenze
  von 1,50 $.
- **Latenz-Soll ≤ 1,5 s:** knapp verfehlt (1,58 s).
- **Soll-Liste:** Mit ~61 % in allen Varianten liegt sie klar unter 80 %. Lagebild und Modell allein heben sie
  nicht; das ist Aufgabe von Schritt C (Plan, Wissen).
- **Füllsätze** laut Kritikern ~8 %, davon gut die Hälfte „Notiert.“ auf Carlos' Notizen.
- **Abdeckung (Kern):** I4 „Lane-Gegner weit weg“ 6/12 und Flash in 183125 9/13 liegen unter dem Soll ≥ 90 %.

## Drei Beispielminuten, vorher (Abo, Stand 017) und nachher (API schnell)

1. **192113, Minute 10.** Carlos fragt, ob er zum Drachen soll. Soll: nicht hin, sie sind zu viert unten und sein
   Flash ist weg.
   - Vorher dreimal „Geh mit Sett zu Kai'Sa und Sona, dann Drache.“
   - Nachher, 10:24: „Jetzt, wo Brand tot ist … geh zum Drachen.“ 10:26 dann „Drache ist zu riskant, geh nach Top“,
     mit Grund (Pantheon in 4 s). Der Kritiker wertet das als gesagt. Es bleibt aber ein Hin und Her.
2. **183125, Minute 14.** Garen und Tryndamere sind tot.
   - Vorher: „farm deine Top-Welle, danach halt dich für Baron oder Inhibitor bereit“.
   - Nachher: „Herold in 16 Sekunden mit Udyr nehmen, dann sofort Mid pushen …“ – das Soll.
3. **133448, Minute 14.** Soll: Herold in 28 s mit Volibear, Teemo ist unten.
   - Vorher nur ein Kanonen-Satz.
   - Nachher 14:43: „Herold in 16 s zusammen“.

## Tests

- **Unit-Tests:** neu `lagebild_019`, auf 7277f1b rot (Module fehlten). Alle 28 grün.
- **`tests/alle.py`:** 10 / 10. Ein alter Abo-Test erzwingt jetzt `weg = "abo"`, damit Tests nie die echte API
  rufen.
- **Szenarien:** 305 / 309, nur die alten Roten. Konstruierte Lagen 40 / 40.

## Rechenzeit

| Teil | Zeit |
|---|---|
| Bauen | ~2 h |
| Szenarien | 106 s (vorher ~23 min) |
| Nachspiele | API 4–7 min für alle 4 Partien, Abo 15–16 min; zwei Abo-Läufe nur für den Vergleich |
| Kritik | ~7 min (eine Soll-Liste, vier Vergleiche parallel) |

## Offen

- **Riot-Schlüssel:** nicht angefasst, das kommt in Schritt B. Er läuft nach 24 h ab und braucht dann einen neuen.
- **Caching:** greift bei Haiku erst mit dem Wissensblock (Mindestlänge 4096 Tokens).
