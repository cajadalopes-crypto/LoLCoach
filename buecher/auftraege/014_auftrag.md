# Auftrag 014 – Claude als Makro-Stratege: erst die Schutzschicht, dann live (Claude, Chat, 28.09.2026 23:40)

Die Probe aus 013 ist klar: Im Blindvergleich gewinnt der Stratege gegen den Kern rund 70 %, bei Fragen, an
Wendepunkten und im Leerlauf. Er macht aber mehr gefährliche Fehler (3 gegen 1), und die folgen Mustern. Teil A behebt
diese Muster im Code und prüft neu. **Teil B (live) nur, wenn Teil A das Tor schafft.**

## Teil A – Schutzschicht

**A1. Lage ohne Doppeldeutung** (`kern.kontext()` / `lage_text`, was der Stratege bekommt):
- **Unsichtbare Gegner:** „Master Yi: zuletzt gesehen vor 288 s in seiner Basis, jetzt unbekannt, kann überall sein“
  statt „vor 288 s“. Sichtbare heißen „jetzt sichtbar …“.
- **Deine eigenen Zauber:** „Dein TP: bereit“ oder „in 56 s“, dazu Flash und Ult. Wo der Stratege keinen Zustand
  hat, schreibt er nichts dazu.
- **Wenn R1 greift, eine eigene Zeile:** „Nach vorn verboten (Leben 36 %). Erlaubt: …“ mit den erlaubten Handlungen
  des Kerns.

**A2. Harte Prüfung im Code** (`stratege.pruefe(satz, lage)`), bevor ein Satz an die Stimme geht:
1. **Nach vorn trotz R1:** Enthält der Satz eine Vorwärts-Handlung (drücken, pushen, erzwingen, Richtung
   Baron/Drache/Turm/Inhibitor, rein, Kampf nehmen, …), wird er verworfen.
2. **Innere Begriffe:** R1, EV, p_tod, Todesrisiko als Zahl, Kern, Kandidat, gesperrt, Modell, Hysterese. So etwas
   darf nie gesprochen werden (Lauf 2, 19:06: „36 Prozent Leben ist R1“). Satz verwerfen.
3. **Entwarnung ohne Sicht:** „kein Gank-Risiko“, „weit weg“ oder „in seiner Basis“ über einen Gegner, der länger als
   20 s nicht zu sehen war (9:42), wird verworfen.
4. **Fakten:** Champion-Namen müssen in der Partie sein. TP, Flash und Ult nur so, wie die Lage sie nennt. „Porten“
   geht nur mit bereitem TP.
5. **Fallback:** Beim ersten Verwerfen neu fragen, mit dem Grund. Beim zweiten gilt der Kern-Satz. Jedes Verwerfen
   kommt mit Grund ins Protokoll.

**A3. Kein Hin und Her.** Die Probe zeigte um 10:24 „Ja, geh zum Drachen“ und um 10:34 „Top bringt mehr als der
fünfte Mann am Drake“.
- Der Stratege bekommt seine letzten zwei Sätze (≤ 60 s) und den aktuellen Plan.
- **Regel:** Innerhalb von 30 s dreht er keine Empfehlung um, außer die Lage hat sich geändert. Dann sagt er, was
  sich geändert hat: „Jetzt, wo Yi unten aufgetaucht ist: …“.

**A4. Ton.**
- Nie von oben herab. „Da diskutier ich nicht mit dir“ darf so nicht kommen.
- Eine Beobachtung von Carlos gilt als Tatsache.
- Unsicherheit wird kurz zugegeben.
- Weiterhin höchstens 25 Wörter.

**A5. Neue Probe mit Tor:**
- **Momente:** dieselben 70 aus 013, dazu **30 neue** aus 164326 und 173159 (Wendepunkte und Leerlauf). Die 30 dienen
  als Prüfung, am Prompt wird nicht auf sie hin gebaut.
- **Blind-Kritik:** frische Kritiker, je Rolle zwei Durchgänge (die Streuung aus 013). Gezählt wird der Mittelwert.
- **Tor, alles muss gelten:**
  - „gefährlich“ beim Strategen ≤ beim Kern, in beiden Mengen;
  - nach der Prüfung (A2) 0 Vorwärts-Sätze trotz R1 und 0 innere Begriffe (automatisch gezählt);
  - „falsch“ beim Strategen höchstens 2 mehr als beim Kern;
  - Gewinnquote des Strategen ≥ 65 % in der neuen Menge (164326/173159).
- **Tor nicht geschafft:** Aufhören, Bericht schreiben, **kein Teil B**.

## Teil B – Live-Einbau (nur mit geschafftem Tor)

**B1. Fragen:**
- Jede echte Frage geht an den Strategen (Strom, erster Satz sofort an die Stimme, wie `mit_claude` heute).
- **Beim Kern bleiben:** Faktfragen mit exakter Antwort (Timer, wer hat Flash, wann lebt X, Stand/Gold) und KLAEREN
  (die letzte Ansage erklären).
- Widerspricht Carlos mit einer Beobachtung („Welle ist leer“), geht das an den Strategen. Die 60-s-Markierung aus
  012 bleibt.

**B2. Wendepunkte:**
- **Anlässe:** Turm oder Objective gefallen, zwei oder mehr Kills in 10 s, Respawn, Ankunft in der Basis.
- An diesen Stellen ersetzt der Stratege den Plan-Satz des Kerns.
- Warnungen des Kerns gehen immer vor und dürfen unterbrechen.
- **Fallback:** Braucht der erste Satz länger als 4 s oder wird er verworfen, spricht der Kern.

**B3. Leerlauf:** Ab 14:00 fragt der Coach den Strategen „Was jetzt, und warum?“, wenn 45 s lang kein Plan-Satz und
keine Warnung kam. Höchstens einmal je 45 s.

**B4. Wellen-Sätze (010):** Die Wellen-Sätze des Kerns („Drück die …-Welle“) kommen nur noch als Fallback.

**B5. Messen:**
- **Szenarien:** Die bestehenden Szenarien laufen weiter mit dem Kern. Die Stratege-Wege laufen im Nachspielen mit
  einem Aufzeichnungs-Stub, damit der Lauf nicht vom Abo abhängt.
- **Generalprobe** (`--breite 3840 --links 1920`) mit echtem Claude-Aufruf an zwei Wendepunkten. Zu messen sind die
  Latenz bis zum ersten Ton und das Verhalten, wenn Claude ausfällt.
- **Sprechmenge:** ungefragt je 30 min in den Protokollen, Soll wie heute (≤ ~75).

**B6. Protokoll:** Stratege-Sätze haben die Quelle „stratege“. Verworfene Sätze stehen mit ihrem Grund darin.

## Ende

1. Der Bericht nennt für Teil A das Tor mit allen Zahlen und für Teil B, was eingebaut und gemessen ist.
2. Committen. Starte den Coach nicht.
