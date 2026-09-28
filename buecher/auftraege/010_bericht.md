# Bericht zu Auftrag 010 – Plan nach dem Wendepunkt

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten in `buecher/messungen.md` („Auftrag 010“).

## Commits

- `efbe05f`: alle Fixes, 10 Szenarien, 2 offene Fälle, 2 Unit-Tests, neun Protokolle (neu), messungen.md, OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Was besser wurde

1. **Plan nach dem Wendepunkt:**
   - Bliebe sonst nur HALTEN, sucht der Kern ein Wellen-Ziel, z. B. „Drück die Mid-Welle: 4 gegen 1 Vasallen.“
   - Die Welle der eigenen Lane geht vor; 45 s bleibt es dieselbe Lane.
   - Der Kern bleibt still nach einer Warnung, einem Rückzug, einem Back-Ruf oder einem frischen Turm- oder
     Objective-Ruf.
   - Von den 6 Stichproben aus 009 haben jetzt 4 ein Ziel: 14:13 Mid-Welle (Beispiel 1), 17:55, 24:43, 33:47.
   - Die 3 Gegenbeispiele bleiben still.
2. **Info ohne Folgen:**
   - „Gut raus.“ und „Sauber umgewandelt.“ kommen nur noch vor dem nächsten Plan-Satz (6-mal, nie allein).
   - Flash-Meldungen kommen ungefragt nur für nahe Gegner. „Aurora ohne Flash.“ kommt jetzt 10:38, als sie 1190 vor
     dir steht.
3. **Rückzug auf eine andere Lane:** 23:35 „Von der Bot-Lane zurück zu deinem inneren Mid-Turm: zwei kommen.“
4. **Wackelnde Einschätzung:** Der Anteil am Objective wird über 1,5 s gemittelt (102112 25:22: 0,57 statt 1,0).
   Unit-Test dazu.
5. **Die 41-%-Stelle** steht in OFFEN.md.

## Leerlauf ab 14:00 (Ziel: deutlich unter 51–59 %)

| 101426 | 133930 | 164326 | 173159 | 102112 | 213624 |
|---|---|---|---|---|---|
| 59 → **51 %** | 62 → **44 %** | 51 → **44 %** | 51 → 52 % | 32 → 33 % | 31 → 31 % |

**Was nicht besser wurde, und warum:**
- **Stummes FARMEN:** Den größten Rest macht FARMEN auf der Seite als stummer Grundplan (80–220 s je Partie). Das ist
  kein HALTEN-Fall und bleibt still.
- **Riskante Wellen:** Viele Wellen liegen in Gefahr (`p_tod` ≥ 0,3, R1).
- **173159:** Frische Turm- und Objective-Rufe halten den Kern dort 382 Takte still. Ohne diese Sperre lag der
  Leerlauf tiefer (101426 42 %, 164326 40 %), aber es gab doppelt so viele Widersprüche und „Drück die Top-Welle“
  15 s nach „Baron bestreiten“.
- **Zwei offene Stichproben** (`offen/2026-09-28_101426_leerlauf.toml`):
  - 17:03: Der Turm ist stumm (Kampfmodell), der Back gesperrt (3 in 10 min), und keine Welle ist nah.
  - 30:21: 46 % Leben und 900 Gold sind kein Back-Grund.

**Kosten:**
- Ungefragt je 30 min +3 bis +13 (101426 68 → 77).
- Widersprüche +1 bis +2 je Partie.
- Die Welle wird 12–15-mal je Partie gesagt.

## Tests und Szenarien

- **Szenarien 236 / 242**, 3 übersprungen. Rot sind nur die bekannten Fälle: 3× Wendepunkt-Probe (18 späte Sätze, in
  009: 24), 0944, 2522 und die Warnungen je 30 min (beide offen aus 009).
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.
- Vorwärts-Sätze bei < 40 % oder `p_tod` ≥ 0,3: weiter 0.

## Testpartie oder erst klären?

Aus meiner Sicht kann **Testpartie 2** jetzt kommen: Die gefährliche Stelle ist seit 009 weg, und die neuen Wellen-Sätze
lassen sich nur live beurteilen (helfen sie, oder nerven 12–15 je Partie?). Offen bleiben die zwei Entscheidungen aus
009:

- Warnungen 11–15 je 30 min, der Preis der Regel zu ungesehenen Köpfen.
- 2522: Drache oder Turm, wenn ein Mitspieler den Drachen allein nimmt.

Beide lassen sich mit der Testpartie besser entscheiden. Vor der Partie muss Carlos den Coach neu starten.
