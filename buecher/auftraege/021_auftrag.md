# Auftrag 021 – Schritt C aus Buch 14: Gehirn mit Plan und Freigabe-Tor (Claude, Chat, 29.09.2026 21:15)

Lies `buecher/14_bauplan_gehirn.md` (Schritt C) und `buecher/13_challenger_coach.md`. Er kommt direkt nach 020.
**Keine Testpartien, frag Carlos nie nach einer Partie, starte den Coach nicht.**

Am Ende dieses Auftrags steht die Frage, ob Carlos wieder mit dem Coach spielen kann. Die Antwort gibt allein das
**Freigabe-Tor** unten, gemessen an Aufnahmen.

## 1. Plan-Objekt, von Claude geführt

- **Inhalt:** Ziel, nächste zwei Schritte, Grund, gültig bis, Abbruch-Bedingungen.
- **Ablauf:**
  - Claude (Haiku, Modellwahl aus 019) setzt und ändert den Plan bei Ereignissen: Wendepunkt, Sichtung, die das Ziel
    betrifft, Kampf in der Nähe, Objective in 60 s oder 40 s, Back, Respawn, Carlos' Frage.
  - Der Schiedsrichter aus 017 bleibt: keine Kehrtwende ohne Ereignis, eine Änderung beginnt mit „Jetzt, wo …“.
  - „Und dann?“ und „was mache ich danach?“ beantwortet der Plan.
- **Kern:**
  - Er baut keine eigenen Plan-Sätze mehr, nur noch als Ersatz, wenn die API ausfällt.
  - Er bleibt für Warnungen, Jungler-, Flash- und Lane-Gegner-Meldungen, Timer und `pruefe` (R1, Kill-Check, innere
    Begriffe, Fakten).

## 2. Wissen je Partie (zwischengespeicherter Block, ≥ 4096 Tokens, damit der Zwischenspeicher bei Haiku greift)

- Makro-Regeln aus Buch 13, `wissen/wellen_regeln.md`, dazu Objectives und Rotationen.
- **Für die zehn Champions der Partie:** Powerspikes, Stärken und Schwächen, Roam-Gefahr, Matchup-Notizen aus
  `wissen/lexikon/`.
- Carlos' Build und der Teamplan.

## 3. Was in der Soll-Liste fehlte (NACHSPIEL-Protokolle aus 019, „fehlt“-Minuten)

Neue Anlässe oder Lagebild-Punkte, jeweils mit Szenario aus der Minute, in der der Punkt fehlte:
1. **Objective-Timer mit Aufgabe:** „Drache in 31 s, Tryndamere tot: mit Udyr und Bot zum Drachen.“ Dasselbe gilt für
   die Larven und den Herold.
2. **Roam-Gefahr:** Ein gegnerischer Laner fehlt auf seiner Lane und ist stark (Kill gerade, Level 6, Powerspike):
   „Fizz fehlt Mid, gerade Level 6: oberen Fluss im Blick.“
3. **Gegner in deinem Jungle oder Büschen:** „Garen in deinem oberen Jungle: Büsche nicht blind betreten.“
4. **Fenster nach gegnerischem Flash oder Tod:** „Garen ohne Flash bis ~6:10: hart traden“ geht nur mit Kill-Check und
   R1. Sonst gibt es die Option ohne Befehl.
5. **Kauf in der Back-Kette:** immer mit konkretem Item, passend zu Gold und Plätzen.

## 4. Kampfansagen

Nur mit dem Kampfrechner aus 020 und nur, wenn dessen Tor erreicht ist.
- **Klar vorn:** „Nehmt den Kampf: …“ mit zwei Zahlen.
- **Klar hinten:** „Nicht rein: …“.
- **Knapp:** zwei Optionen mit Grund, kein Befehl.
- Unter R1 nie nach vorn.

## 5. Freigabe-Tor (alles muss gelten)

**Mengen:**
- **Bekannt:** 101426, 192113, 133448, 183125.
- **Neu:** drei Aufnahmen aus `aufnahmen/`, die in keinem Auftrag zum Bauen benutzt wurden. Wähle die längsten, echte
  Gegner bevorzugt. Die neuen Aufnahmen werden nur gemessen, nicht zum Nachbessern benutzt.

| Größe | Tor |
|---|---|
| Soll-Liste gesagt + teilweise | bekannt ≥ 80 %, neu ≥ 75 % |
| Sicherheit (Vorwärts unter R1 / Angriff ohne Kill-Check / innere Begriffe) | 0 / 0 / 0 |
| Abdeckung Flash, Jungler, Lane-Gegner weg | je ≥ 90 % |
| Füllsätze (Kritiker) | ≤ 5 % |
| Widersprüche (Plan-Wechsel < 30 s ohne Ereignis) | ≤ 1 je Partie |
| Latenz ganzer Satz, Median | ≤ 2 s |
| Kosten | ≤ 0,50 $ je 30 min |

- **Tor verfehlt:** Bis zu drei Runden nachbessern, nur mit der bekannten Menge, die neue danach neu messen.
- **Danach:** Ist es erreicht, schreib „**TOR ERREICHT**“ in den Bericht. Ist es nicht erreicht, schreib „**TOR NICHT
  ERREICHT**“ mit den fehlenden Punkten.

## Budget (Claude-API, Carlos' Guthaben)

- 019 hat für die Nachspiele ~3,10 $ verbraucht (4 Partien × 2 Modelle).
- **In 021 höchstens 6 $ für API-Nachspiele.**
- **Sparen:**
  - nur Haiku;
  - Antwort-Zwischenspeicher je (Lage, Frage);
  - in Wiederholungsrunden nur Momente neu fragen, deren Lage oder Prompt sich geändert hat;
  - Szenarien immer mit Stub.
- **Kostenstand** nach jeder Runde in `messungen.md`.
- **Budget droht zu reißen oder das Guthaben ist leer** (API-Fehler): auf das Abo ausweichen (langsamer). Im Bericht
  sagen, dass Carlos Guthaben nachladen sollte.

## Ende

1. Unit-Tests zuerst rot. Schnelle Prüfung wie in 019. Kritiker blind und frisch.
2. `021_bericht.md`:
   - die Tor-Tabelle für beide Mengen;
   - zehn Beispielminuten vorher (Stand 019) und nachher;
   - Kosten je 30 min.
3. Committen. Starte den Coach nicht.
