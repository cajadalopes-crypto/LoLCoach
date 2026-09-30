# Auftrag 027 – Der Herzschlag: immer eine gesprochene Anweisung (Claude, Chat, 30.09.2026 10:10, ersetzt die Fassung von 09:15)

**Keine Testpartien, frag Carlos nie nach einer Partie, starte den Coach nicht.** Beim Bauen nur automatische Maße,
Kritiker und API-Nachspiel einmal am Ende. API-Budget: höchstens 3 $, danach das Abo.

## Warum diese Fassung

Carlos hat von sich aus gespielt: `aufnahmen/2026-09-30_091311` (Riven gegen Malphite, 37 min). Sein Urteil:
**„extrem passiv, gibt keine Kommandos, von lebendigen Arbeitspaketen keine Spur“**. Er hat absichtlich still
gestanden und auf Anweisungen gewartet. Es kam nichts.

Die Aufnahme bestätigt das:
- **190 Ansagen,** davon 51 Antworten auf seine Fragen.
- **Ungefragte Handlungsanweisungen:** nur eine Handvoll (DRUECKEN 3, NEHMEN 2, WOHIN 2, BACK 1, GRUPPE 1,
  Stratege 28).
- **„Warum nicht“-Sätze** („Yorick kämpft: nicht hin …“): 26. Er hörte also vor allem, was er **nicht** tun soll.
- **Respawn:** „Du lebst in 11 Sekunden.“ ohne Kauf und Ziel.
- **Basis:** mit 1700 Gold im Brunnen „geh Top“, statt zuerst den Einkauf.
- **Hin und Her:** 23:21 „Top-Welle crashen“, eine Sekunde später „Bot-Turm“.
- **Falsche Lage:** 20:17 „Baron jetzt“ bzw. „dein Team startet den Baron“, das Team kämpfte aber am Drachen.

**Warum unsere Maße das nicht gesehen haben (Fehler von Claude/Chat):** „Paket-Abdeckung 91 %“ zählt ein *internes*
aktives Paket, nicht das, was Carlos *hört*. Ab jetzt misst das Hauptmaß, was gesprochen wird.

## 0. Hotfix Mikrofon (von Claude/Chat am 30.09. 09:15 direkt eingespielt, noch nicht committet)

`lolcoach/sprache.py` hat `PushToTalk._oeffne`: Geht das gewählte Gerät nicht, probiert es den Windows-Standard und
dann alle Eingänge außer WDM-KS. Gibt es kein Mikrofon, entfällt die Frage, und der Coach läuft weiter.
- Unit-Test mit einer `sounddevice`-Attrappe schreiben und mitcommitten.
- Prüfen, warum ein WDM-KS-Pfad benutzt wurde.

## 1. Der Herzschlag (Hauptteil)

**Regel:** Solange du lebst und nicht kämpfst, hast du **immer eine gesprochene, gültige, positive Anweisung**:
was jetzt, und was danach.

1. **Auslöser für eine neue Anweisung** (Kern, sofort, ≤ 2 s):
   - das alte Paket ist erledigt, ungültig oder durch ein besseres Play ersetzt;
   - **Stillstand:** Du bewegst dich ≥ 5 s nicht (eigene Position auf der Minimap), außerhalb von Kampf, Recall
     und Kanal;
   - **Basis:** Ankunft oder Respawn im Brunnen, dann sofort Kauf (ganzes Gold, Kette), danach das Ziel;
   - **Tot:** 12 s vor dem Respawn Kauf (im Laden geht das schon im Tod) und Ziel;
   - **Auffrischung:** 25 s ohne gesprochene Anweisung, dann die aktuelle Anweisung mit neuer Info oder eine neue.
2. **Positiv zuerst:**
   - „Warum nicht“ steht **nie allein**. Es ist höchstens ein Nachsatz zu einer positiven Anweisung („Crash die
     Welle, dann Drache mit Braum. Nicht zu Yorick: 10 s weg.“).
   - Das gilt ebenso für „Du stehst tief“, „jemand fehlt“ und „Vorsicht“: immer mit dem, was du stattdessen tun
     sollst.
3. **Ohne Claude verlässlich:**
   - Der Kern hat für jede Lage eine brauchbare Vorlage-Anweisung aus den Paketen (Welle, Turm, Back, Objective,
     Gruppe, Hilfe).
   - Claude formuliert besser, wenn er innerhalb von 2 s liefert, sonst spricht die Vorlage.
4. **Kein Hin und Her:**
   - Eine Anweisung gilt, bis sie erledigt oder ungültig ist.
   - Ein Wechsel innerhalb von 20 s nur mit echtem Event und „Jetzt, wo …“.
   - Zwei Plan-Sätze in < 5 s mit verschiedenem Ziel sind verboten; der zweite wird verworfen.
5. **Spielende:**
   - Liegen Nexus-Türme oder Inhibitoren offen und sind ≥ 3 Gegner tot (Respawn ≥ 15 s): „Jetzt beenden: alle auf den
     Nexus“, per TP oder Quest-TP, wenn bereit.
   - Das ist ein Event mit höchstem Wert.

## 2. Kauf (aus Carlos' Notizen dieser Partie)

- **Ganzes Gold ausgeben:** Bauteile kaufen, bis das Gold nicht mehr reicht (21:54, mit fast 1000 Gold raus). Mit
  Kette: „Kauf Tiamat und Langschwert, dann …“.
- **Stiefel aufwerten:** 10:33, „er weiß nicht, was ausgebaute Schuhe sind“. Stiefel-Stufe 2 gehört zum Build, mit
  passendem Vorschlag (Riven: Ionische Stiefel o. ä., aus `wissen/build_carlos.toml` oder dem Laden).
- **Verkaufen:** zuerst Tränke oder Trinkflasche, dann Dorans (16:00 verkaufte er Dorans statt des Tranks).
- **Kaufen im Tod** (25:31): Im Brunnen kann man schon tot einkaufen. Die Kauf-Anweisung kommt also im Tod.

## 3. Fakten-Prüfung für Objectives

20:17 hieß es „dein Team startet den Baron“, das Team kämpfte aber am Drachen.

- `pruefe` prüft Aussagen über Objectives gegen die Minimap-Positionen der Mitspieler (wer steht an welcher Grube)
  und gegen die Symbole.
- Stimmt eine Aussage nicht, wird der Satz verworfen.
- **Szenario** 20:17–21:19.

## 4. Back-Regel (entschieden von Claude/Chat, aus der Fassung von 09:15)

- **Welle gecrasht:** Back, auch ohne Gold für ein ganzes Item, mit Kauf-Kette. Ausnahme: ein Objective oder
  Kampf-Event in ≤ 20 s.
- **Welle läuft zu dir:** farmen, bis sie am Turm ist. Ausnahmen: R1 (dann Back sofort) oder ein Objective in ≤ 90 s
  (dann Back, sobald der Verlust höchstens eine halbe Welle beträgt).
- **Die Back-Frist** sagt nur, wann du spätestens zurück sein musst.

## 5. Neues Hauptmaß: was Carlos hört (automatisch, aus dem Nachspiel)

| Maß | Soll |
|---|---|
| **Anweisungs-Lücke:** Zeit, in der du lebst, nicht kämpfst und keine gültige, gesprochene, positive Anweisung hast (gültig bis erledigt, ungültig oder 30 s alt) | p90 ≤ 20 s, nie > 35 s |
| **Stillstand-Reaktion:** ≥ 5 s still außerhalb von Kampf, Recall und Kanal → Anweisung in ≤ 2 s | ≥ 95 % |
| **Basis-Reaktion:** Brunnen mit Gold ≥ billigstes sinnvolles Bauteil → Kauf-Anweisung in ≤ 2 s | ≥ 95 % |
| **Negativ allein:** Sätze, die nur sagen, was man nicht tun soll | 0 |
| **Hin und Her:** zwei Plan-Sätze mit verschiedenem Ziel in < 5 s | 0 |
| Sicherheit, Latenz, Kosten | wie bisher |

**Messen auf allen Testpartien, vor allem den vier von Carlos selbst gespielten: 133448, 183125, 231200, 091311.**
091311 wird Testpartie. Seine Notizen werden Szenarien, und das Stillstehen ab 15:41 ist Pflicht-Szenario.

## Ende

1. Nach jeder Änderung die automatischen Maße.
2. **Einmal am Ende:** API-Nachspiel der Testpartien und die Kritiker (Soll-Liste, Mehrheit).
3. **`027_bericht.md`:**
   - beginnt mit „TOR ERREICHT“ oder „TOR NICHT ERREICHT“;
   - für 091311 zehn Minuten vorher/nachher: was Carlos gehört hat und was er jetzt hören würde;
   - die Kosten.
4. Committen. Starte den Coach nicht.
