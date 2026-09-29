# Bericht zu Auftrag 024 – Grundlagen aus der Udyr-Partie

Fertig am 30.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Das Tor misst 025. Einzelheiten stehen in
`buecher/messungen.md` („Auftrag 024“).

## Gebaut

- **Tot oder lebendig nur aus der API (2):**
  - `stratege.fakten` verwirft Sätze, die einen Lebenden tot, einen Toten lebend oder den Lane-Gegner weg nennen. Die Prüfung läuft beim Bauen **und** direkt vor dem Sprechen.
  - „Jetzt, wo X tot ist“ gilt nur, solange die API X tot meldet (`Schiedsrichter.gilt`).
- **Lane-Gegner weg (3):** Weg gilt nur mit Beleg, das ist `ereignisquellen.anwesenheit`. Belege sind:
  - er wurde zuletzt außerhalb seiner Lane gesehen;
  - oder er ist ≥ 20 s ungesehen, obwohl du dort stehst, wo du ihn sehen müsstest (400–1200 Einheiten).

  Das Lagebild sagt Claude ausdrücklich „nicht weg“. Die Ursache bei 5:56 war kein Minimap-Überdecken: Riven war noch 6700 Einheiten weg.
- **TP (4):**
  - „Xerath TP weg.“ ist jetzt eine Pflicht-Info wie beim Flash. Erkannt wurde der TP schon vorher, gesagt wurde er nie.
  - Das Quest-TP heißt im Lagebild so.
  - Der Wissensblock plant damit. Die Werte (390 s, Patch 26.19) stammen aus `wissen/lexikon/saison2026.md` und `kern.toml [quest_tp]`.
- **Satz- und Kauffehler (5):**
  - Eine Notiz mit Frage wird beantwortet und notiert.
  - Ein Kontroll-Auge im vollen Inventar wird zuerst gestellt, dann folgt das fertige Item. Ein fertiges Item verkauft der Coach nicht, sonst bricht die Regel aus 164326.
  - Beim Farmen gibt es keine Kauf-Vorschau mehr.
  - Nach „Jetzt, wo …“ kommen nur echte Ereignisse.
  - Ein „kein Back“ ohne Grund wird verworfen, wenn das Gold für ein Item reicht.
- **Event-Quellen für 025:** `lolcoach/kern/ereignisquellen.py` enthält `TodQuelle`, `LaneQuelle` und `ZauberQuelle`. Jede liefert Events mit Typ, Ort, Beteiligten, Zeit und Sicherheit.
- **Aus 023 nachgeschärft:** „Stopp –“ steht nur noch vor einem Rückzug. Im Nachspiel stand es auch vor „Rein, Gragas fast tot!“.

## Tests und Nachspiel

- **`tests/alle.py`:** 10 / 10.
- **`test_kern.udyr_024`:** vorher rot, jetzt grün.
- **`test_kaufplan`:** ergänzt um den Fall „Auge stellen, dann ein fertiges Item“.
- **Szenarien:**
  - `2026-09-29_231200_auftrag024.toml` mit 8 Szenarien aus den Notizen: 3 waren vorher rot (TP, Notiz-Frage, volles Inventar), 5 sind Wächter.
  - Alle Szenarien parallel: 321 / 325, rot sind nur die alten (3× Wendepunkt, 0944).
- **Ein API-Nachspiel von 231200:** Jede Notiz ist Satz für Satz geprüft, siehe Tabelle in `messungen.md`. Sicherheit 0 / 0 / 0.

| Größe | live 231200 | Nachspiel 024 | Ziel |
|---|---|---|---|
| ganze Antwort, Median | 2,4 s | **1,57 s** | – |
| erster Satz, Median | – | **1,44 s** | ≤ 1,5 s ✓ |
| Kosten je 30 min | 0,80 $ (inkl. 0,16 $ Sonnet) | **0,38 $** | ≤ 0,50 $ ✓ |

Sonnet lief live nur außerhalb des Coachings: für die Spielakte vor der Partie sowie für Bericht und Review danach.

## Offen

- **Für 025:** Die Arbeitspakete (Notizen 18:37, 29:39) und die Stille bei 30:59.
- **Einhängen:** Die Event-Quellen hängen noch nicht im Kern-Takt, das macht 025 in `kern/events.py`.
- **Ein fertiges Item für ein besseres verkaufen?** Das wäre eine Regeländerung gegen den Test aus 164326. Das kann Carlos entscheiden.

## Kosten

0,44 $ von 1 $.
