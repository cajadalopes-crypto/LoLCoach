# Auftrag 009 – Letzte Sperren vor Testpartie 2 (Claude, Chat, 28.09.2026 13:30)

Ich habe `buecher/protokolle/2026-09-28_101426.md` (Stand 122431c) und die Aufnahme dazu gelesen. Die Zahlen aus 008
tragen. Ein Fall ist aber gefährlich und muss vor der nächsten Testpartie weg. Das ist ein kleiner Auftrag, danach
sofort Bericht.

## 1. Gefährlich: „Trade“ bei 15 % Leben

**101426, 2:35:** „Trade Aurora: dein Combo macht etwa 400, Aurora hat nur 330 Leben.“ Riven hatte **15 %** Leben
(Plan TRADE, p_tod 0.20) und war um 2:43 tot.

- R1 hätte den Satz sperren müssen: Leben < 40 %. `TRADE` und `ALL_IN` fehlen aber in der R1-Liste. Außerdem hängen
  beide am Lane-Duell (Buch 2), und das ist zurückgestellt.
- **Fix:**
  - `TRADE` und `ALL_IN` sind **stumm**, bis Buch 2 kommt. Berechnet werden sie weiter, im Protokoll mit „stumm: Buch 2
    zurückgestellt“.
  - Beide kommen in die R1-Liste.
  - Prüf, ob noch andere Vorwärts-Handlungen außerhalb der R1-Liste liegen.
- **Szenario** `0235-kein-trade-bei-15` (101426): darf_nicht_sagen „Trade“, „Combo“.
- **Suche:** Durchsuch alle neun Protokolle nach gesprochenen Vorwärts-Handlungen mit Leben < 40 % oder p_tod ≥ 0.3.
  Jeder Fund kommt in messungen.md. Soll: 0.

## 2. Entscheidungen zu 008_bericht.md

1. **Ungesehene Gegner als Köpfe (Tod 20:16):** Ja, wenn der Gegner seit ≤ 20 s (`kopf_ungesehen_s`) ungesehen ist
   **und** er von seiner letzten Sichtung aus in ≤ 5 s bei dir sein kann (Weg ÷ Tempo, abzüglich der Zeit seit der
   Sichtung, wie `verteidiger_ab`). Wer zuletzt weit weg war, zählt nicht.
   - 20:16 muss warnen.
   - 14:00 bleibt still, wenn Viego weit weg war.
   - Beides kommt als Szenario.
2. **Lagebild:** Es kommt nach 30 s Stille, aber höchstens alle 90 s. Die Folgerung muss eine Handlung oder Grenze sein
   („nicht allein nach vorn“, „oben ist frei: Welle drücken“). „Aurora steht nah bei dir“ allein reicht nicht.
3. **Jetzt bauen, was in 008 offen blieb:**
   - **Drache vor Inhibitor:** Der EV entscheidet, mit Weg und Fenster. `karte.ORDNUNG` gilt nur noch bei Gleichstand.
   - **Recall-Warnung im Kanal:** nur, wenn der erste Gegner vor Kanal-Ende + 1 s bei dir sein kann.

## 3. Fragen: „Was soll das bedeuten?“

**101426, 32:17.** Carlos fragt: „Raus zum Turm ist auch eine super schwammige Aussage. Was soll das überhaupt
bedeuten? Soll ich zu meinem Turm zurücklaufen, zu meinem Tier 1?“ Die Antwort war „Du lebst in 29 Sekunden wieder:
kauf Langschwert …“. Das geht an der Frage vorbei.

- **Neue Absicht `KLAEREN`:** Die Frage bezieht sich auf den letzten gesprochenen Satz („was heißt das“, „welcher Turm“,
  „macht keinen Sinn“, „was meinst du“). Die Antwort erklärt diesen Satz konkret: welches Ziel, welcher Turm, warum
  damals. Beispiel: „Zum Top-Außenturm, weil Twitch und Aurora 3 Sekunden weg waren.“
  - Diese Antwort gilt auch, wenn Carlos schon tot ist.
  - Der Satz muss höchstens 60 s alt sein, sonst antwortet der Coach wie bisher.
- **Szenario** (Frage-Szenario) 101426 32:17: soll „Top“ und „Twitch“ enthalten, darf_nicht_sagen „lebst in“.

## 4. Kleine Sprachfehler aus 101426

- **Kein Possessiv vor Champion-Namen:** „Ihr Aurora ist Level 6“ (64) und „Ihr Aurora hat drei Items“ (531) heißen
  „Aurora ist Level 6“ und „Aurora hat drei Items“.
- **Items im Schutzplan:** „kein Trade bis Langschwert“ (12:11) ist unsinnig. Im Schutzplan steht nur ein **fertiges**
  Item aus Carlos' Build (Caulfields Kriegshammer, Axiombogen, …).
- **Bauteile beim Kaufen:** Ein Bauteil wird immer mit dem Ziel genannt, zum Beispiel „Kauf Langschwert für die
  Hydra“.
- **Nachgeprüft, kein Fehler:** „Kauf Tiamat“ um 28:39 war richtig, weil Slot 2 frei war.

## 5. Nur messen: Leerlauf

Leerlauf ab 14:00 liegt bei 52–59 %. Zieh aus 101426 zehn zufällige Leerlauf-Fenster. Schreib zu jedem den einen Satz,
den ein Challenger-Coach dort gesagt hätte, oder „nichts – Stille ist richtig“. Das kommt in `009_bericht.md`. Hier
nichts bauen, ich entscheide danach, ob das Maß oder der Coach falsch ist.

## Ende

1. Szenarien zuerst rot, dann die Fixes. Am Ende einmal der volle Lauf.
2. Neues Protokoll 101426 mit `--fragen`.
3. **Eine** Nachzählung für 101426, mit einem frischen Carlos-Kritiker und einem frischen Challenger-Kritiker. Das
   Ergebnis kommt in `009_bericht.md`.
4. Committen. Starte den Coach nicht.
