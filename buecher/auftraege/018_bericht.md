# Bericht zu Auftrag 018 – Was Carlos' Graves-Partie zeigt

Fertig am 29.09.2026. Keine Testpartie, der Coach wurde nicht gestartet. Geprüft an Aufnahmen, nachgespielt mit dem
fertigen 017/019 (API, Haiku). Zahlen in `buecher/messungen.md` („Auftrag 018“).

## Gebaut

1. **Objective-Symbole:** Die Minimap-Gruben werden gelesen (`lolcoach/objsymbole.py`), live jede Sekunde, im
   Nachspiel aus den Bildern. Treffer an 8 Partien gegen die API: **oben 99,5 %, unten 97,7 %**. Claude liest jetzt
   „Herold lebt (Symbol auf der Karte zu sehen)“.
2. **Respawn:** „Du lebst in 10 Sekunden wieder: du lebst in 10 Sekunden.“ ist behoben – die Kette wird vor der
   Zeitangabe gekürzt. Die Prüfung verwarf „Verkauf Dorans Klinge, kauf Sonnenköcher“ als „kein Platz“; das ist
   behoben. Neu: Stehst du 20 s still in der Basis, kommt der Plan noch einmal („Los: …“), höchstens zweimal.
3. **Turm:** immer mit Stufe („unter eurem äußeren Mid-Turm“). Gewartet wird am vordersten stehenden Turm.
4. **Kaufen:**
   - Einzigartige Gruppen kommen aus den Spieldaten (CommunityDragon, `wissen/item_gruppen.json`). Schwarzes Beil
     und Lord Dominiks teilen `LastWhisper`, statt Beil kommt jetzt Schutzengel.
   - **Elixier:** ab Level 9, wenn sonst nichts passt. Hier weicht die Umsetzung vom Auftrag ab: Es braucht einen
     freien Platz. Laut Spieldaten wird es erst beim Trinken verbraucht, und du konntest es 36:47 mit sechs Items
     nicht kaufen. Bei vollem Inventar nennt der Coach den Grund.
5. **Kampf in der Nähe:**
   - Claude bekommt die Zahlen des Kerns: wer dort lebt, Leben, Level, Flash, Tote, dein Weg und der Kill-Check
     deines Combos. Er sagt zuerst „Hilf“ oder „Nicht hin“.
   - Der Anlass greift jetzt bis 15 s Weg (vorher 6 s, deshalb kam 26:15 nichts).
   - Nachspiel 26:52: „Geh sofort zum unteren Fluss zu deinen vier, nehmt den Drachen …“.
6. **Tod:**
   - Der laufende Satz bricht sofort ab.
   - Der Tod-Satz hat höchstens 12 Wörter, z. B. 38:09 „Am Baron kamen zwei von ihnen zusammen.“
   - Kein „geh zurück“ und kein „hinter den Turm“ an einen Toten.
7. **Top-Welle:** Ab 20:00 steht sie in 11 von 35 Plan-Sätzen (vorher 17 von 37). Ohne Grund noch 3 Mal: der Grund
   fällt der Wortgrenze zum Opfer, oder die Kette endet mit „Danach nach Top.“ Das ist offen.

## Nachspiel 183125

| Größe | 019 | 018 |
|---|---|---|
| Soll-Liste gesagt + teilweise (blinder Kritiker) | 54 % | 55 % |
| Sicherheit | 2 | **0** |
| Stratege, Median / p90 | 1,6 / 2,8 s | 1,3 / 2,5 s |
| Flash / Jungler / Backs mit Kette | 9/13 · 27/29 · 8/10 | 10/13 · 25/29 · 9/10 |
| Stille in der Lane | 104 s | 73 s |
| Widersprüche / Füllsätze (Kritiker) | – | 5 / 17 |

- Die Soll-Liste steigt kaum: Die Fixes treffen einzelne Momente, die Liste misst den Plan über die ganze Partie
  (Schritt C).
- **26:15:** Der Coach sagte 25:58 „Nicht hin: 7 s Weg, 41 % Leben“. Der Challenger würde auf Kog'Maw gehen.
  Das erlaubt die Regel „kein Angriff ohne Kill-Check“ nicht, denn Kog'Maws Leben war nicht zu sehen.

## Tests

- **Szenarien:** 313 / 317 grün. Rot sind nur die alten (3× wendepunkt-ansage, 0944).
- **Neue Szenarien:** 8 / 8 grün, 5 davon auf 4b3f1f0 rot. 26:15 steht als Szenario ohne Prüfteil drin, denn dort
  antwortet nur der Stratege.
- **`tests/alle.py`:** 10 / 10, darin die konstruierten Lagen.
- Ein alter Test hielt „Elixier geht immer“ fest; er ist an die Spieldaten angepasst.

## Offen

- **Elixier ohne freien Platz:** Bitte bei Gelegenheit live prüfen, ob Spieldaten und deine Beobachtung stimmen.
- **Minimap-Symbole:**
  - „Symbol fehlt, also genommen“ sagt der Coach bewusst nicht; im Kampf an der Grube liest die Minimap sonst
    falsch.
  - Unten ist die Grube in 11 % der Bilder von Portraits verdeckt. Dann gilt der letzte Stand.
- **Kosten:** API-Kosten dieses Auftrags rund 0,60 $ (zwei Nachspiele). Gemessen: 0,26 $ je 39-Minuten-Partie.
