# Auftrag 013 – Probe: Claude als Makro-Stratege (Claude, Chat, 28.09.2026 22:50)

012 ist geprüft, die drei Fehler sind behoben. Dieser Auftrag baut **nichts am Live-Coach**. Er ist ein Versuch, der
eine Richtungsfrage klärt.

## Warum

In 192113 hat Carlos 79 Fragen gestellt. 62 beantwortete der Kern, 17 Claude.

- **Claude:** kam nach 1,3–3,0 s an die Stimme (`_sprechtaste.log`) und passte sich an seine Einwände an. Beispiel
  20:19: „Lass die Lane jetzt einfach los und bleib bei der Gruppe an der Baron-Grube … eine verlorene Welle oben ist
  da völlig egal.“
- **Kern:** Die starren Sätze („Farm deine Top-Welle“, 20:09, 20:30, 21:45) kamen alle von ihm.
- **Meine Vermutung:** Der Kern hat eine feste Auswahl von rund einem Dutzend Handlungen. Echtes Makro verknüpft
  mehrere Dinge, etwa „Top ist gepusht und Kai'Sa farmt dort, also Mid nehmen und in 90 s zum Drachen“. Das kann der
  Kern nur, wenn jemand genau diese Regel schreibt. Deshalb fühlt sich jede Verbesserung für Carlos wie null an.
- **Die Probe klärt:** Ist Claude mit dem Lagebild als Makro-Stratege klar besser als der Kern, bei Fakten, die
  stimmen, und in brauchbarer Zeit?
- 012 hat die Claude-Antworten von 23 auf 10 gesenkt. Das bleibt vorerst so. Entschieden wird nach der Probe.

## Aufbau

1. **`werkzeuge/stratege_probe.py`** (offline, nachgespielt):
   - Für gewählte Momente einer Aufnahme baut es den Kontext, den `antworten.mit_claude` live bekäme: Kopfzeile,
     `kern.kontext()`, Spielakte über `gehirn`.
   - Dazu kommen die Kandidaten des Kerns mit EV und Grund, als Fakten, nicht als Vorgabe.
   - Das geht über `llm.frage` (Abo, wie live, Modell `sonnet`), mit einem **neuen Systemprompt `STRATEGE`**.
2. **`STRATEGE`**, kurz und hart:
   - Du bist Challenger-Makro-Coach. Ein bis zwei Sätze. Der nächste Schritt, danach der Schritt danach, und der
     **entscheidende Grund** aus der Lage. Liegen zwei Wege nah beieinander, nenn beide.
   - Nur Fakten aus der Lage: Namen, Zeiten, Zahlen, Orte. Nichts erfinden. Weißt du etwas nicht, sag es.
   - Nie nach vorn, wenn der Kern „stumm“ oder R1 meldet (Leben < 40 %, p_tod ≥ 0,3).
   - Widerspricht der Spieler mit einer Beobachtung („Welle ist leer“), glaub ihm und plane neu.
   - Deutsch, gesprochen. Keine Listen, keine Floskeln.
3. **Momente**, höchstens 70 Aufrufe:
   - **192113:** jede echte Frage von Carlos (reine Beschimpfungen und Notizen ausgenommen), dazu jeder Wendepunkt ab
     10:00 (Turm, Kill, Objective).
   - **101426:** die 10 Leerlauf-Fenster aus 009 und die Wendepunkte ab 14:00.
   - Am Wendepunkt fragt die Probe: „Was jetzt, und warum?“
4. **Faktenprüfer** (automatisch):
   - Markiere jeden Champion-Namen, jede Zeitangabe und jede Zahl in der Stratege-Antwort, die nicht aus dem Kontext
     stammt oder ihm widerspricht.
   - Markiere jeden Vorwärts-Rat trotz R1.
5. **Latenz:** Zeit bis zum ersten Satz (Strom) und bis zum Ende, je Aufruf. Median und p90. Kamen Grenzen oder
   Ablehnungen vom Abo? Wie viele Aufrufe gingen in welcher Zeit durch?

## Ausgabe für Carlos

`buecher/protokolle/STRATEGE_PROBE.md`, eine Tabelle je Partie:

| Zeit | Lage in einem Satz | Carlos' Frage (falls eine) | Coach live (Kern) | Stratege (Claude) | Latenz | Fakten-Flag |

Lesbar, ohne Code. Carlos entscheidet damit selbst.

## Blind-Kritik

Die zwei Kritiker (Challenger, Carlos) bekommen je Moment beide Antworten, **gemischt als A und B**, ohne zu wissen,
welche von wem ist. Je Moment gibt es ein Urteil: A besser, B besser oder gleich. Dazu „falsch“ oder „gefährlich“ je
Antwort.

Im Bericht stehen:
- die Gewinnquote des Strategen,
- „falsch“ und „gefährlich“ je Seite,
- die Fakten-Flags,
- die Latenz.

## Nicht tun

- Den Live-Coach nicht ändern, kein neuer Sprechweg. Das kommt erst nach Carlos' Entscheidung.
- Den Systemprompt nicht nach den Kritik-Ergebnissen hinbiegen. Ein Durchlauf, dann eine zweite Fassung nur, wenn
  der erste Lauf einen klaren handwerklichen Fehler zeigt (z. B. zu lange Sätze). Beide Läufe berichten.

## Ende

1. `STRATEGE_PROBE.md`, `013_bericht.md` mit Gewinnquote, Fehlern, Latenz und Abo-Grenzen.
2. Committen. Starte den Coach nicht.
