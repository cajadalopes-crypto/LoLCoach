# Auftrag 016 – Carlos' Pflichtenheft: sagen, was er sieht, und Ketten statt Schweigen (Claude, Chat, 29.09.2026 14:10)

**Grundsatz ab jetzt: Carlos macht keine Testpartien mehr.** Geprüft wird nur noch an Aufnahmen. Die Partien sind echt,
das Nachspielen läuft durch denselben Code wie live. Frag Carlos nie nach einer Partie. Starte den Coach nicht.

## Was schiefging

Die Partie `aufnahmen/2026-09-29_133448` (Riven gegen Poppy, nach 17 min abgebrochen) und Carlos' Notizen darin sind
jetzt das Pflichtenheft. Seine Hauptklage: **Der Coach schweigt.**
- Er sagt nicht, wo der Jungler ist.
- Er sagt nicht, wessen Flash weg ist.
- Er sagt nicht, was nach dem Back kommt.
- In der Lane gibt es keine Tipps.

Das ist die Folge meiner Aufträge 009 bis 011. Ich habe die Menge gedrosselt und dabei genau diese Infos
herausgeschnitten. Die alten Ziele „Warnungen ≤ 10“ und „nervt ≤ 10 %“ sind deshalb **nicht mehr Hauptmaß**. Hauptmaß
ist jetzt die **Abdeckung** (Teil 6).

## 1. Informationspflicht (ungefragt, kurz, immer)

1. **Flash:** Jeder gegnerische Flash, den der Coach sieht, wird gesagt, egal wie weit weg: „Poppy Flash weg.“
   - Die Einschränkung aus 010 („nur nahe Gegner“) fällt weg.
   - Kommt eine Flash-Frage, antwortet der Kern vollständig, mit Restzeit je Gegner.
2. **Jungler:** Taucht der gegnerische Jungler nach ≥ 20 s ohne Sicht wieder auf, sagt der Coach den Ort: „Teemo oben
   im Fluss.“
   - Kann er in ≤ 8 s bei dir sein, kommt „bei dir in N Sekunden“ dazu.
   - Die Sperre aus 009 (Lagebild nur mit Handlung) gilt dafür nicht.
3. **Lane-Gegner weg:** Wird dein Lane-Gegner weit weg gesehen (andere Lane, Basis, ≥ 30 s von dir), gibt es die Info
   mit Folge: „Poppy unten gesehen: drück deine Welle.“
   - Nach vorn nur, wenn R1 es erlaubt.
   - Das ist Carlos' Notiz 11:35: „Das entscheidet doch alles, dass ich jetzt hier durchpushen kann.“
4. **Kampf in der Nähe:** Kämpft ein Mitspieler in ≤ 6 s Weg von dir (Leben fällt, Gegner sichtbar dabei), entsteht
   ein Anlass für den Strategen (Teil 3).
   - Das ist Notiz 6:23: „hilf Volibear, der ist neben dir, du bist volles Leben“.

## 2. Ketten statt Einzelbefehle

- **Jeder Back-Ruf** nennt Kauf und Ziel danach: „Back jetzt: Axiombogen, dann zu Yorick nach Mid, weil …“.
- **Ankunft in der Basis:** Die komplette Kette kommt ungefragt: Kauf (passend zu Gold **und** freien Plätzen), dann
  Ziel, Grund.
- **Nach jedem Turm, Objective oder Kampf:** der nächste Schritt und der danach.
- Das gilt für den Strategen und für den Kern-Ersatz.

## 3. Stratege auch in der Lane

- **Leerlauf-Anlass** ab 1:30 statt ab 14:00. Nach 35 s ohne Plan-Satz und ohne Warnung fragt der Coach den
  Strategen, solange du lebst.
- **In der Lane-Phase** bekommt der Stratege die Aufgabe „Wellen- und Lane-Tipp mit Grund“. Das sind Carlos' Beispiele
  (Notiz 5:54):
  - „push die Lane aus, Teemo ist nicht da“,
  - „such ein 1 gegen 1“,
  - „freeze die Welle“,
  - „die Welle läuft zu dir, weil …“.
- **Dazu die Lage:** Wellenstand der eigenen Lane (Vasallen beider Seiten, Richtung), Ort des Lane-Gegners und des
  Junglers, Leben beider.
- **Neuer Anlass:** „Kampf in der Nähe“ aus 1.4.

## 4. Sicherheit, die in 133448 durchrutschte

1. **12:10:** Bei **5 % Leben**, mit Lux und Sona voll daneben, kam „Schieb kurz die Top-Welle rein“ durch
   `pruefe`.
   - Unter R1 zählt jede Welle, die man zum Gegner schiebt oder reindrückt, als Vorwärts-Rat.
   - Seit 015 sind nur „Welle holen/farmen auf der eigenen Seite“ erlaubt.
   - Unit-Test mit genau diesem Satz.
2. **9:29:** „Poppy ist sichtbar und schwach … geh sie jetzt an“, obwohl sie volles Leben hatte.
   - Angriffs-Aufrufe des Strategen („geh an“, „greif an“, „trade“, „all-in“) gibt es nur, wenn der Combo-Check des
     Kerns jetzt einen Kill sagt und R1 nicht greift.
   - „Schwach“ über einen Gegner nur unter 50 % Leben.
   - Unit-Test.

## 5. Kaufen

- **13:19–13:48:** „Kauf Caulfields, Spitzhacke, Langschwert für die Eklipse“ bei vollem Inventar, dann zweimal
  „verkauf Dorans Klinge“.
  - Der Kaufplan zählt freie Plätze.
  - Bauteile, die zu einem Item im Inventar verschmelzen, belegen keinen neuen Platz.
  - Verkaufen nur, wenn es ohne nicht geht, und dann einmal mit Grund.
- **Kontroll-Auge:** höchstens einmal je Back vorschlagen. Nie „zurück nur für das Auge“. Sagt Carlos Nein
  (14:29), fällt es für 5 min weg.

## 6. Messen ohne Carlos

1. **Nachspielen** von 133448, 192113 und 101426 durch den Live-Weg:
   - mit echtem Strategen über das Abo;
   - mit Carlos' echten Fragen zur echten Zeit, aus `_sprechtaste.log` bzw. den Protokollen.
2. **Lesbares Protokoll je Partie:** `buecher/protokolle/NACHSPIEL_<partie>.md`, Minute für Minute, was der Coach jetzt
   sagen würde, ungefragt und auf jede Frage.
3. **Abdeckung (neues Hauptmaß)**, je Partie:
   - gesehene gegnerische Flashes, angesagt (Soll 100 %);
   - Jungler-Wiedersichtungen nach ≥ 20 s, angesagt (Soll ≥ 90 %);
   - Backs mit Kette (Kauf + Ziel) (Soll 100 %);
   - längste Stille in der Lane-Phase, solange du lebst (Soll ≤ 45 s);
   - Carlos-Notizen, die jetzt erfüllt wären.
4. **Sicherheit bleibt hart:**
   - 0 Vorwärts-Sätze unter R1;
   - 0 Angriffs-Aufrufe ohne Kill-Check;
   - 0 innere Begriffe.
5. **Carlos-Kritiker:** Ein frischer Agent bekommt Carlos' Notizen aus 133448 und 192113 als Maßstab. Er urteilt
   Minute für Minute: „Wäre Carlos hier zufrieden?“ Dazu ein Challenger-Kritiker für „stimmt es?“.

## Ende

1. Szenarien und Unit-Tests zuerst rot, dann die Fixes. Voller Lauf. Die alten Szenarien, die Stille verlangen
   (Warnungsrate, „Info ohne Folgen“), dürfen angepasst werden. Jede Anpassung wird im Bericht begründet.
2. `016_bericht.md` mit Abdeckung vorher und nachher, Sicherheit, Kritik und den drei NACHSPIEL-Protokollen.
3. Committen. Starte den Coach nicht.
