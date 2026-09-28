# Bericht zu Auftrag 012 – Wellen-Endlosschleife, ignorierte Fragen, Timer-Fehler

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten und alle Fragen stehen in `buecher/messungen.md`
(„Auftrag 012“).

## Commits

- `1c3a3cd`: Fixes, 2 Szenario-Dateien für 192113, 2 Unit-Tests, zehn Protokolle (neu, 192113 mit `--fragen`),
  messungen.md, OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Umgesetzt

1. **Welle:** Eine Welle ist kein Ziel, wenn sie leer ist, tief bei ihnen ohne ihre Vasallen steht oder ein
   Mitspieler an ihr steht. Gedrückt wird nur mit ihren Vasallen. „Kein Minion“ oder „reingepusht“ per Sprechtaste
   setzt die Welle 60 s auf leer. Ohne ein anderes Ziel heißt es „Geh nach Top: dort kommt ihre nächste Welle“, nicht
   mehr „sie läuft sonst in deinen Turm“.
2. **Fragen:** Die Frage wird Satz für Satz aus langen, wütenden Sätzen gezogen. Füllwörter stören die Erkennung
   nicht mehr. Neue Absichten:
   - RISIKO: Wer fehlt, dann der Plan.
   - AUGE: Ort für das Kontroll-Auge.
   - COACH: was der Coach coacht.

   Erweitert:
   - „wenn der Turm down ist“ und „sobald ich im Fountain bin“ fragen jetzt nach danach.
   - „Soll ich … kaufen“ ist eine Kauf-Frage.
   - „Ich soll …“ stellt eine Ansage in Frage.
   - „Warum nicht?“ meint die Frage davor.
   - „Du antwortest nicht“ beantwortet die letzte Frage.

   „Notiert.“ allein kommt nur noch bei reinen Beschwerden.
3. **Timer:** Der Satz wurde um 4:29,7 gewählt und um 4:37,1 gesprochen, weil die Stimme noch sprach. Die Zahl kam
   2 s nach dem ersten Ton, also rund 10 s zu hoch. Jetzt wird die Zahl beim Sprechen neu gerechnet: „Drache in
   28 Sekunden“. Unit-Test dazu.
4. **Cassiopeia (Befund):** Sie war 22:06–22:22 durchgehend sichtbar und 22:24–22:29 verloren; ihr Icon lag
   vermutlich auf Rivens. Der Satz „kam aus dem Nebel“ nutzte die Probe von 22:05, als sie noch weit weg war.
   Kleiner Fix: Wer seit der Probe sichtbar war, kam nicht aus dem Nebel.

## Wellen-Wiederholungen und Notiert-Antworten in 192113

| live | vorher | jetzt |
|---|---|---|
| 19:40 zwei Leute farmen oben | Drück die Top-Welle | Stimmt. Back jetzt: 1050 Gold für Gefräßige Hydra. |
| 19:48 reingepusht | (Claude) geh trotzdem hoch | Stimmt. Geh nach Top: dort kommt ihre nächste Welle. |
| 20:05 / 20:09 / 20:19 | Drück die Top-Welle / Claude | (Stimmt.) Bleib nah an deinem Team, auf Top ist keine Welle. |
| 20:30 warum nicht Mid? | Geh zur Top-Welle | Geh nach Top …, auf Mid wartet gerade keine Welle, die sich lohnt. |
| 20:47 kein Minion | (Claude) | Stimmt. Drück die Bot-Welle: 4 gegen einen Vasallen. |
| 23:45 an deren Nexus | (Claude) | Stimmt. Geh nach Top: dort kommt ihre nächste Welle. |
| 2:40 Notiz Kontrollauge | Notiert. | Notiert. Stell das Kontroll-Auge in den Fluss-Busch oberhalb deiner Top-Lane … |
| 4:00, 8:28, 15:55, 28:42 „antwortest nicht“ | Notiert. | Zu deiner Frage: (die Antwort auf die Frage davor) |
| 14:38 „wenn der down ist“ | Notiert. | Danach: Herold spawnt in 18 Sekunden, dann dorthin. |
| 21:11 Drache über Top? | Notiert. | Notiert. Drache spawnt erst in 256 Sekunden. … |
| 21:57 ADC farmt oben | Notiert. | Stimmt. Back jetzt: 2200 Gold für Riesenschwert. |

| 192113 | vorher | jetzt |
|---|---|---|
| nur „Notiert.“ | 11 | 5 (reine Beschwerden) |
| an Claude | 23 | 10 |
| Top-Welle ungefragt | 14 | 3 (alle außerhalb der leeren Phase) |
| Top-Welle in Antworten | 21 | 6 |

## Tests und Szenarien

- **Neu:** 65 Szenarien aus 192113. Auf dem alten Stand waren 49 rot, jetzt sind alle grün.
- **Gesamt:** 305 / 309 grün, 3 übersprungen. Rot sind nur die alten Fälle: 3× Wendepunkt-Probe und 0944.
- **Andere Partien (2b):** Die Fragen-Szenarien aus 213624 und 101426 sind bis auf das alte 0944 grün.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.
- **Angepasst:** Szenario 101426 1400 erwartete „Drück die Mid-Welle“ bei 4 gegen 0 Vasallen. Das ist genau der
  Satz, den Carlos ablehnt; die Notiz steht im Szenario.

## Kennzahlen

- **Warnungen:** unverändert (101426 13,4; 164326 9,8; 173159 9,4).
- **Leerlauf ab 14:00:** leicht höher (101426 52 → 54 %, 164326 45 → 50 %), weil das leere Drücken wegfällt.
- **192113:** Leerlauf 34 %, Warnungen 17,4 je 30 min.

## Offen

- **Ziel ohne Welle:** Braucht dich deine Welle nicht und gibt es kein anderes Ziel, sagt der Kern „Geh nach Top: dort
  kommt ihre nächste Welle“. Das stimmt, aber Carlos will dann ein Makro-Ziel. Zu entscheiden: Soll der Kern dann das
  Team oder das nächste Objective vorziehen, auch wenn deren EV klein oder ungeeicht ist?
- **Warnungen in 192113:** 17,4 je 30 min; das ist nicht untersucht.
- **Nächster Schritt:** Nichts blockiert eine Testpartie. Vorher muss Carlos den Coach neu starten.
