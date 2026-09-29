# Bericht zu Auftrag 021 – Gehirn mit Plan und Freigabe-Tor (Buch 14, Schritt C)

Fertig am 29.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Einzelheiten stehen in
`buecher/messungen.md` („Auftrag 021“), die Protokolle in `stratege_probe_021/`.

## **TOR NICHT ERREICHT**

| Größe | Tor | bekannt (101426, 192113, 133448, 183125) | neu (125902, 164809, 120049) |
|---|---|---|---|
| Soll-Liste gesagt + teilweise | ≥ 80 / ≥ 75 % | **56 %** ✗ | **70 %** ✗ |
| Sicherheit (R1 / Kill-Check / Begriffe) | 0 / 0 / 0 | 0 ✓ | 0 nach Fix ✓ (vorher 1) |
| Flash / Jungler / Lane-Gegner weg | je ≥ 90 % | 88 / 89 / 58 % ✗ | 89 / 84 / 43 % ✗ |
| Füllsätze (Kritiker) | ≤ 5 % | 4,0 % ✓ | 3,2 % ✓ |
| Widersprüche je Partie | ≤ 1 | 2 / 7 / 4 / 7 ✗ | 4 / 2 / 1 ✗ |
| Latenz ganzer Satz, Median | ≤ 2 s | 2,3–2,5 s ✗ | 2,3–2,5 s ✗ |
| Kosten je 30 min | ≤ 0,50 $ | 0,45 $ ✓ | 0,34 $ ✓ |

**Fehlende Punkte:** Soll-Liste, Abdeckung (vor allem „Lane-Gegner weg“), Widersprüche, Latenz. Carlos sollte noch
**nicht** wieder mit dem Coach spielen.

## Gebaut

- **Plan-Objekt:** Claude hält Ziel, zwei Schritte, Grund, „gilt bis“ und Abbruch in einer stillen PLAN-Zeile. Sie
  beantwortet „Und dann?“.
- **Plan-Sätze:** Jeder Plan-Satz des Kerns geht als Entwurf an Claude. Der Kern spricht ihn nur als Ersatz.
- **Wissensblock** mit ~5000 Tokens je Partie, zwischengespeichert: Buch 13, Wellen-Regeln, Objectives, die zehn
  Champions und Carlos' Build.
- **Neue Anlässe:**
  - Timer mit Aufgabe (90 s, 30 s, Spawn);
  - Fenster nach einem gegnerischen Tod;
  - Roam-Gefahr;
  - Gegner in deinem Jungle.
- **Kampfansage:** nur „Nicht rein“ bei „klar hinten“ vom Rechner, sonst zwei Optionen.
- **Zwei Sicherheitsfixe:** erneute Prüfung direkt vor dem Sprechen, und „schwach“ gilt nur für den eigenen
  Satzteil.

## Zehn Beispielminuten (Stand 019 → 021, Urteil des Kritikers)

| Partie, Min. | Soll | 019 | 021 |
|---|---|---|---|
| 101426, 19 | Baron in 30 s, drei tot: Team zum Baron | fehlt (Team Mid) | gesagt (19:41 Gruppe zum Baron) |
| 101426, 18 | Viego tot: der Baron ist eurer | fehlt | gesagt (19:10 zum Baron) |
| 101426, 17 | Baron in 151 s, vorher Sicht | fehlt | teilweise (17:03 Baron in 140 s) |
| 183125, 6 | Garen in deinem Jungle: Büsche nicht blind | fehlt | gesagt (6:25) |
| 183125, 11 | 1851 Gold: Langdolch + Mantel | fehlt (stumm) | gesagt (11:08) |
| 183125, 18 | Nach Respawn Lord Dominiks fertig | teilweise | gesagt (18:36) |
| 133448, 13 | Top-Welle, dann Herold in 92 s | teilweise | gesagt (13:28) |
| 192113, 19 | Teemo Flash weg (19:11) | gesagt | **fehlt** |
| 192113, 15 | Nicht Top-Welle, erst Herold | teilweise | **fehlt** (15:22 Top-Welle) |
| 133448, 2 | nicht zu weit vor, Twitch im Jungle | gesagt | **fehlt** (1:47–3:13 still) |

## Kosten

- **Nachspiele:** 5,46 $ von höchstens 6 $, danach Schluss mit den Runden.
- **Wie viele Runden:** Runde 2 wurde nur auf der bekannten Menge gerechnet, die neue Menge danach einmal. Für eine
  dritte Runde reichte das Budget nicht.
- **Im Spiel:** 0,34–0,45 $ je 30 min.
- **Guthaben:** Nachladen sollte Carlos, wenn es weitergeht.

## Was ich daraus schließe

- **Die Kritiker streuen stark.** Zwischen Runde 1 und 2 kippten viele Urteile, ohne dass sich der Satz grundlegend
  änderte.
- **Ein Teil der Soll-Punkte verlangt, was die harten Regeln verbieten:** All-in ohne Kill-Check oder Wards.
- **Die 80 % brauchen mehr als Prompts:**
  - verlässliche Info-Pflichten (Lane-Gegner weg: 43–58 %);
  - weniger Stimmen, die sich widersprechen (Kern-Warnung, Antwort, Anlass);
  - eine kürzere Antwort, damit die Latenz unter 2 s fällt.

## Tests

- **Unit-Tests:** `gehirn_021` war vor 021 rot, weil `Plan`, der Wissensblock und die Anlässe fehlten.
- **`tests/alle.py`:** 10 / 10.
- **Szenarien:** 313 / 317. Rot sind nur die alten (3× wendepunkt-ansage, 0944). 0449 war durch die neue
  Jungle-Meldung kurz rot und ist behoben.

## Nachtrag zu 020

Der Riot-Download ist fertig (2000 Partien, Schlüssel gültig). Die Eichung ergibt Schwelle 0,60, Tor ja
(`wissen/kampf_eichung.toml`).
