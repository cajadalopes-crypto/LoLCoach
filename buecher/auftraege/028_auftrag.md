# Auftrag 028 – Eine Stimme, ein Plan, richtig kaufen (Claude, Chat, 30.09.2026 13:40, ergänzt 14:40)

**Keine Testpartien, frag Carlos nie nach einer Partie, starte den Coach nicht.**
**Guthaben: 0 $.** Ab jetzt gilt das Sparprotokoll (`buecher/16_sparprotokoll.md`). Die API ist in diesem Auftrag
ganz tabu. Wo echter Claude-Text nötig ist, läuft er über das Abo (`LOLCOACH_LLM_WEG=abo`). Die Kritiker laufen
einmal am Ende und nur für die Abo-Partien.

## Warum

027 hat den Herzschlag gebracht: Lücke, Stillstand und Basis sind erfüllt. Jetzt reden aber mehrere Stimmen
gegeneinander. Herzschlag, Kern-Plan, Pakete, Events, Stratege und Antworten auf Fragen planen jede für sich.

Die Kritiker zählen 7–20 Widersprüche je Partie (026: 2–4). Ein Challenger-Coach, der sich widerspricht, ist
schlechter als einer, der schweigt. Beispiele aus dem 091311-Nachspiel in `027_bericht.md`:
- 16:03 „Zu Yorick auf die Bot-Lane“, drei Sekunden später „räum die Welle bei dir, dann drück den inneren
  Top-Turm“.
- 22:50 „Farm Top“, sieben Sekunden später „Geh auf ihren inneren Top-Turm“, ohne Event und ohne Grund.
- 21:03–21:30: fünf Antworten in 27 s mit fast derselben Kauf-Kette, dazu „Mein Fehler.“ und „Tut mir leid.“
- 22:43: zwei Antworten in derselben Sekunde auf eine Frage.
- 20:19 „Jetzt, wo Plan: Welle gerettet …“, 22:30 „Jetzt, wo Plan: Farm deine Top-Welle.“ Der Satzbug aus 024
  spricht wieder interne Etiketten.

Die vollständige Liste steht in den Kritiker-Urteilen von 027. Nimm sie als Arbeitsliste.

## 0. Vor allem anderen

1. **Die Sparsperre einbauen,** wie in Buch 16, Abschnitte 2 und 5 beschrieben:
   - `llm_api.aktiv()` nur mit `LOLCOACH_API=1`; `_anfrage` wirft ohne die Variable `APIFehler`.
   - `Coach starten.cmd` setzt `LOLCOACH_API=1`.
   - `generalprobe`, `nachspielen` und alle Werkzeuge entfernen die Variable aus der Umgebung ihrer Unterprozesse.
   - Test in `tests/alle.py`.
   - Neues Werkzeug `werkzeuge/guthaben.py`. Die erste Zeile des Berichts heißt „Guthaben: X $ (Abo-Aufrufe: N)“.
2. **Liegengebliebenes committen:**
   - `CLAUDE.md` (neue harte Grenze), `buecher/14_bauplan_gehirn.md`;
   - `buecher/15_lebendige_arbeitspakete.md`: war nie committet;
   - `buecher/16_sparprotokoll.md`, `buecher/02_lane_duell.md`;
   - `wissen/testpartien.toml` mit dem Werkzeug neu erzeugen, damit 091311 drinsteht.
   - `Reasoning/` bleibt, wie es ist.
3. **Messdefinitionen einfrieren:**
   - Die Endfassungen aus 027 (`messungen.md`) gelten unverändert.
   - Muss eine Definition geändert werden, stehen alter und neuer Wert nebeneinander im Bericht.
   - „Vorher“ sind die 027-Zahlen in `messungen.md`. Der alte Stand wird nicht noch einmal nachgemessen.
4. **Das Review kommt komplett raus** (Carlos, 30.09.2026 13:39): „nie einmal gelesen, er erzählt nur Quatsch.
   Sobald er besser wird, reden wir wieder darüber.“
   - **Entfernen, nicht abschalten:**
     - das Review nach der Partie („Partie vorbei. Ich schreibe jetzt das Review …“, `_review_ansage`);
     - `_reviews_nachholen` beim Start;
     - `review.py`, `review_server.py`, `web/review.html`, die Oberfläche :8791 und den Befehl `review`;
     - die Sprechtaste nach der Partie, die ans Review geht;
     - den Fokus aus dem letzten Review im Briefing;
     - jeden Satz im Spiel, der aufs Review verweist („Schau es dir im Review an“);
     - den automatischen Text-Bericht nach der Partie.
   - **Gleiches gilt für alles, was nur fürs Review da ist:**
     - `todesanalyse`, `verlauf`, die Todes-Bilder und `bericht` fallen weg, wenn nur das Review sie braucht.
     - Braucht der Live-Coach oder ein Messwerkzeug sie, bleibt genau dieser Teil, still und ohne Ansage.
   - **Bleiben:**
     - die Aufnahme mit Ansagen, Notizen und Bildern der Testpartien, also die Messgrundlage;
     - die Sprechtaste im Spiel, die Notizen.
   - **Nachziehen:**
     - Tests, `CLAUDE.md` (Einleitung, Modultabelle, Befehle), `ANLEITUNG.md`, `ANFORDERUNGEN.md`;
     - in `OFFEN.md` die Zeile „Review entfernt auf Carlos' Wunsch, wiederherstellbar aus Commit <hash>, wieder
       aufnehmen, wenn der Coach gut ist“.
   - **Nebenbei spart das Guthaben:** Die Sonnet-Aufrufe nach jeder Partie und beim Start fallen weg.

## 1. Eine Stimme, ein Plan (Hauptteil)

**Regel:** Zu jedem Zeitpunkt gibt es genau **einen aktiven Plan**: das Ziel und den nächsten Schritt. Alle Quellen
lesen ihn: Herzschlag, Kern, Pakete, Events, Stratege, Antworten. Keine Quelle plant an ihm vorbei.

1. **Planwechsel.** Ein Satz mit einem anderen Ziel als der aktive Plan ist ein Planwechsel. Erlaubt ist er nur in
   drei Fällen:
   - **Gefahr:** R1, neuer Gegner, Abbruch. Dann sofort.
   - **Echtes Event oder besseres Play** (Chancen-Scanner): hörbar als Wechsel mit dem Event als Grund, z. B.
     „Plan geändert: Sie haben den Drachen – drück ihren inneren Top-Turm, …“. Die Form entscheidest du, der Grund
     muss drin sein. Das gilt auch für Wendepunkte, sie sind nicht mehr ausgenommen.
   - **Carlos fragt oder widerspricht.**

   Sonst wird der Satz verworfen. Der Stratege bekommt den aktiven Plan als Fakt. Weicht er ohne Event ab, spricht
   stattdessen der Satz des Kerns.
2. **Antworten auf Fragen:**
   - Sie bestätigen den aktiven Plan oder ändern ihn ausdrücklich, mit Grund.
   - Eine Frage bekommt genau eine Antwort.
   - Keine Entschuldigungen („Mein Fehler“, „Tut mir leid“). Bei einer Korrektur: „Stimmt. Neu: …“.
3. **Keine Doppel:** Derselbe Inhalt kommt innerhalb von 10 s nur einmal, egal aus welcher Quelle.
4. **Satzbug:**
   - „Jetzt, wo Plan: …“ und „Jetzt, wo Wendepunkt: …“ reparieren.
   - Interne Etiketten nach „Jetzt, wo“ kommen in die verbotenen Begriffe von `pruefe`.
5. **Neues automatisches Maß „Widerspruch“:** ein Planwechsel ohne einen der drei Gründe, innerhalb von 20 s nach
   dem letzten Plan-Satz. **Soll ≤ 1 je Partie.** Die Kritiker zählen weiter mit.

## 2. Wiederholung und Füllsätze

Entschieden von Claude/Chat nach Carlos' Vorgaben: keine Füllsätze, immer der nächste Schritt mit Warum. Carlos
kann widersprechen.

- **Wiederkommen darf eine Anweisung nur mit etwas Neuem:**
  - mit dem nächsten Schritt: „Kanone in 18 Sekunden, dann Back: 1100 Gold für Eklipse“;
  - mit einem Countdown ≤ 10 s bis zur Handlung: „Welle crasht in 6 Sekunden – dann Back“;
  - mit einem neuen Grund aus der Lage.
- **Füllsätze und damit verboten:**
  - nackte Bestätigungen: „Bleib dabei.“, „Weiter so.“, „Bleib dabei, Kanone in 18 Sekunden.“ ohne Schritt danach;
  - Entschuldigungen.
- **Die zehn roten Alt-Szenarien** (0137, 1204, back-dauerton ×2, wohin-kurz, 1247, 1453, 0806, s23,
  a4-lagebild):
  - Lies je Szenario die ursprüngliche Beschwerde.
  - Ging es um wörtliche Wiederholung, bleibt die Regel: kein Satz ohne neue Info.
  - Ging es um „zu viel reden“, ist das durch Buch 15 abgelöst („nerv nicht“ hat geschadet). Schreib das Szenario
    um: Ein Satz ohne neue Info ist rot, ein Satz mit neuer Info ist grün.
  - Im Bericht je Szenario eine Zeile: was du entschieden hast und warum.
- **Soll:** Füllsätze ≤ 5 % (Tor).

## 3. Sicherheit: der Kill-Check für jede Quelle

Die Claude-Antwort „Xerath töten sofort“ kam durch, ohne Kill-Check.
- Finde heraus, welcher Weg `pruefe` oder den Kill-Check umgeht. `töte\w*` steht in den Mustern, also liegt es
  am Weg, nicht am Wort.
- Der Kill-Check gilt ab jetzt für jede Quelle: Stratege, Antworten, Herzschlag, Events.
- Dazu ein Szenario. **Soll: 0.**

## 4. Chancen zurück (53 → ≥ 68 %, Stub)

Die Chance geht vor allem als Nachsatz verloren.
- **Ein besseres Play ist kein Nachsatz.** Es ersetzt den Plan als Planwechsel mit Grund (Teil 1).
- **„Warum nicht“** bleibt nur für sichtbare, schlechtere Alternativen.
- **Im Kauf-Takt** kommt die Chance nach der Kauf-Kette: „Kauf …, dann …“.

## 5. Messen (Sparprotokoll)

1. **Während der Arbeit** läuft der Stub nur auf drei Partien (091311, 134020, 231200), dazu die betroffenen
   Szenarien.
   - **Einmal am Ende** kommen alle Testpartien und alle Szenarien dran.
   - Gemessen werden die Hör-Maße (Definitionen aus 027), Widerspruch (automatisch), Füllsätze, Chancen und
     Sicherheit.
2. **Einmal am Ende** kommt das Abo-Nachspiel von drei Partien: 091311, 134020 und 164809 (Holdout).
   - Mit Zwischenspeicher.
   - Danach die Kritiker: drei je Partie, Mehrheit, Soll-Liste.
3. **Die volle Tor-Runde** (alle Testpartien per Abo) läuft nur, wenn die drei Partien alle drei Bedingungen
   erfüllen:
   - Soll-Liste ≥ 75 %;
   - Widerspruch ≤ 1 je Partie;
   - Sicherheit 0.

   Sonst läuft sie nicht.
4. **Latenz und Kosten** werden hier nicht gemessen. Sie kommen nur aus Carlos' echten Spielen.

## 6. Aus der Ornn-Partie 134020 (Carlos, 30.09.2026 13:40, Blind Pick, Ornn gegen Tryndamere)

Carlos hat von sich aus einen Champion gespielt, den er nicht gut kennt, um zu prüfen, ob der Coach etwas kann.

**Sein Urteil:** Karte und Timer lesen kann der Coach schon gut („geht Drake – und der Drake ist wirklich ab“).
Aber es gibt Momente mit „schlechterem Rat als ein Eisen-Spieler“.

**Die Aufnahme zeigt:**
- 175 Ansagen;
- 42-mal „Kanone“;
- 13-mal „Bleib dabei“;
- Elixier 5-mal ungefragt empfohlen, auch nachdem Carlos widersprochen hatte;
- kein einziger eigener TP-Call.

Seine Notizen stehen in `aufnahmen/2026-09-30_134020_notizen.md`. 134020 wird Testpartie; jede Notiz wird ein
Szenario.

1. **Spiegel-Champions:** Beide Teams hatten Sejuani (Blind Pick).
   - Der Coach verwechselt sie: „Planwechsel: Sejuani kämpft mit Miss Fortune“, „Nicht zu Sejuani“, „Baron mit
     Sejuani“, „Sejuani Flussmitte“ (12:41, laut Carlos war es die eigene).
   - Die Spielakte nennt Sejuani zugleich als Gegner-Jungler und als eigene Frontlinie.
   - **Regel:** Champions werden überall über Team + Champion geführt, nie über den Namen allein: Minimap-Ring,
     Tracker, Kern, Spielakte, Stratege-Kontext.
   - Gibt es einen Namen doppelt, sagt der Satz „ihre Sejuani“ bzw. „eure Sejuani“.
2. **Kaufen, Teil 2.** Die Basis-Reaktion in 027 hat gemessen, *ob* eine Kauf-Anweisung kommt, nicht *ob sie
   stimmt*. Ab jetzt wird der Inhalt geprüft.
   - **Inventar zuerst:** Nie ein Item empfehlen, das Carlos schon hat. 1:14 kam „Back jetzt: Dorans Schild holen“,
     er hatte ihn seit Spielbeginn.
   - **Jeder Back-Ruf nennt die ganze Kette,** die das Gold kauft: „Back: Bamis Glutstein, Kettenweste und
     Rubinkristall“. Nicht „1000 Gold für Dornenpanzer“ (7:55, 12:56, 13:28, 14:01).
   - **Elixiere nur mit vollem Inventar** (sechs fertige Items), spät, vor einem entscheidenden Kampf. Sonst nie.
     Übriges Gold geht in Bauteile des Builds oder in ein Kontroll-Auge, nie in Verbrauchsgüter. Das ist die
     Nebenwirkung von „ganzes Gold ausgeben“ aus 027.
   - **Stiefel Stufe 2:**
     - Nach Gegnerteam und eigenem Champion, mit Grund: viel Auto-Angriffs-Schaden (Tryndamere, Miss Fortune) →
       Beschichtete Stahlkappen; viel CC oder Magie → Merkurs Schuhe.
     - Zum passenden Zeitpunkt im Build, spätestens nach dem ersten fertigen Item.
     - Die Riven-Stiefel aus `build_carlos.toml` gelten nur für Riven.
   - **Build-Quelle:** Hat Carlos für den Champion keinen eigenen Build, gilt der Build aus der Spielakte
     (Matchup). Die Spielakte nannte Stahlkappen an Platz 2, empfohlen hat der Coach nur „Kauf Stiefel“.
   - **Champion-Sonderregeln aus dem Lexikon wirken im Kern,** nicht nur als Text für Claude.
     - Ornn kauft ohne Rückruf („Lebende Schmiede“, `wissen/lexikon/champions/Ornn.md`). Für ihn gibt es also
       nie „Back, um zu kaufen“. Back nur für Leben und Mana; kaufen geht außerhalb des Kampfes in der Lane.
     - Die Stelle bitte allgemein bauen: Sonderregeln je Champion, die Kauf, Back oder TP ändern.
3. **Carlos' Korrektur gilt für die ganze Partie und für alle Stimmen.**
   - Nach 16:20, 19:42 und 20:03 („kein Elixier mitten im Spiel“) antwortete Claude „Du hast recht“. Der Kern
     empfahl das Elixier trotzdem noch 22:17, 25:05 und 32:31.
   - Ebenso 3:17–3:56: Carlos will freezen, der Coach sagt dreimal „crash“.
   - **Regel:** Ein Widerspruch von Carlos wird eine Sperre für alle Quellen. Er gilt für den Rest der Partie oder
     bis sich die Lage klar ändert, und steht im Stratege-Kontext.
4. **Antworten beantworten zuerst die Frage:** ja oder nein mit Grund, in einem Satz. Erst danach kommt der Plan.
   - 2:29 „Soll ich teleporten oder laufen?“ bekam eine Kauf-Kette.
   - 27:36 „Warum hatte ich keine Chance?“ bekam „Du lebst in …“.
   - Dazu der Satzbug „Jetzt, wo du gefragt hast: …“ (2:58, 14:07), zu Teil 1.4.
5. **Kanone:**
   - Genannt wird sie nur, wenn sie die nächste Handlung auslöst: „Kanone rein, dann Back“.
   - Höchstens einmal je Kanonenwelle.
   - Nie als Füller im Herzschlag.
   - **Soll:** höchstens 1 Nennung je 90 s Spielzeit, im Stub gemessen. Heute waren es 42 in 34 min.
6. **Spielende ohne Hin und Her:**
   - 29:26 „Jetzt beenden“, 29:44 „Back jetzt“, 30:01 „Jetzt beenden“ und „Raus jetzt“ in derselben Sekunde,
     30:04 „Geh auf ihren Nexus“, 30:07 „Zurück“, 30:17 „Zurück“.
   - „Jetzt beenden“ nur, wenn Carlos nicht unter R1 steht und sein Team wirklich dort ist.
   - Szenario 29:20–30:20.
7. **Nicht in diesem Auftrag:** TP-Plays und Sicht, also Wards zu festen Zeiten. Das wird Auftrag 029 mit eigenem
   Buch. Erst muss es eine Stimme geben, sonst widersprechen sich auch die TP-Calls.

## Sparsam arbeiten

- **Keine Agenten** außer den Kritikern am Ende.
- **Keine wiederholten Volläufe.**
- **Kein Nachmessen alter Stände.**
- **Die Arbeitsliste** für Teil 1 sind die Kritiker-Urteile aus 027. Nicht neu suchen.
- **Der Bericht ist knapp:** Tabelle, Entscheidungen, geänderte Zeilen. Keine Nacherzählung.

## Ende

1. **`028_bericht.md`:**
   - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“.
   - Dann „TOR ERREICHT“ oder „TOR NICHT ERREICHT“.
   - Eine Tabelle wie in 027, dazu Widerspruch (automatisch und Kritiker), Füllsätze und Chancen.
   - Für 091311 dieselben zehn Minuten 13:00–23:00: 027 neben 028, nur die geänderten Zeilen.
   - Für 134020 jede Notiz-Stelle: live gehört neben jetzt.
   - Die zehn Alt-Szenarien mit je einer Zeile.
2. Committen. Starte den Coach nicht.
