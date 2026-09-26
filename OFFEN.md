# OFFEN - alle Aufgaben, nichts bleibt liegen

> **GRUNDSATZ AGENTEN (Carlos, 26.09.2026, verbindlich):**
> Agenten nur, wenn sie WIRKLICH effizient sind. Kein Kaltstart-Mist, keine
> vergeudeten Tokens, kein verschwendetes Nutzungsguthaben. Ein Agent lohnt sich
> nur fuer abgeschlossene Arbeit mit klarer Grenze (eigene Dateien, eigenes Thema),
> die er ohne langes Einlesen schafft - hier gut moeglich: frisches Projekt, flache
> Struktur, CLAUDE.md + OFFEN.md reichen als Einstieg. Alles, was Kontext aus
> dem laufenden Gespraech braucht oder Dateien anderer beruehrt: selbst machen.
> Ein laufender Agent wird fortgesetzt (SendMessage), nicht neu gestartet.

Lebendes Dokument (Carlos: "flexibel, im Flow"): jeder Wunsch aus Carlos'
Rueckmeldungen (Chat, Sprachnotizen im Spiel, `aufnahmen/*_notizen.md`) landet
sofort hier. Kein Zeitdruck - sauber und funktionsfaehig vor schnell.
Abgearbeitet wird von oben nach unten, allein oder mit Agenten nach obigem
Grundsatz. Erledigtes wandert mit Commit nach unten.

## In Arbeit

Carlos' Ziel 26.09. (/goal): Challenger-Coach, individuelle Ansagen aus vielen Faktoren, keine
Standardsaetze; Grundlage `Reasoning/LoL Reasoning.txt` (Entscheidungskette Zustand -> Welle ->
Prio -> Tempo -> Information -> Gegner-Vorhersage -> Aktionen -> Gegenantwort -> Wert).

- Gegner-Leben vom Bildschirm (Lebensbalken ueber den Koepfen) -> Kill-Rechnung mit echten
  Zahlen. Wartet auf Spielbilder MIT Gegnern: die naechste Partie legt alle 5 s `schirm_*.jpg`
  ab - damit eichen, erst dann in Ansagen (lieber stumm als falsch).
- Eigene Wards auf der Minimap lesen (Sicht als Faktor: "Fluss gewardet - Gank kommt nur ueber ...").
- Gegner-Ults ohne Ping: globale Ults (TF, Shen, Pantheon, Galio, Ryze, Taliyah, Nocturne, Sion) und Teleport
  erkennt die Minimap jetzt als Fernsprung (197c7b1); alle anderen Ults nur ueber Chat-Pings.
  Live pruefen: kommen TP-Meldungen, und keine falschen?
- "Welle crasht in X s" (Reasoning #6 wave_crash_in): aus der Wellenfront nicht verlaesslich - die Front
  springt, wenn eine Welle stirbt (dann ist die naechste an der eigenen Basis die "Front"); Klumpen nach
  Flaeche zu zaehlen aenderte nichts (Camille-Partie: 62 -> 65 Spruenge > 0,15). Experiment mit der
  fuehrenden Welle als verfolgtem Objekt: kommt sie an, liegt die Vorhersage im Median 2,2 s daneben -
  aber nur 6-9 % der Vorhersagen kommen an (gegnerische Vasallen im Nebel sind unsichtbar, ob der Weg
  frei ist, weiss man nicht). Bleibt draussen; Kanonen-Uhr statt Crash-Zeit.

Erledigt fuer dieses Ziel (26.09., je mit Commit): Lagebewertung + Komponist (jede Ansage gerechnet),
Entscheider (Plaene inkl. Jungle, spaete Phase, Mitspieler-Hilfe, Todesserie-Reset), Jungler-
Startseite, Kampf-Vorhersage am Objective, Platten von der Minimap, Lane-Prio, Kaufplan aus dem
Lexikon-Build, Todespreis, Trade-Hinweis aus der Akte, Sofort-Antworten (Plan, Jungler-Ort,
Platten, Prio), Themen-Sperre + Widerspruchs-Waechter, Dashboard "Jetzt", 4 Takte/s live,
verdeckte Icons unter bekannten Icons, doppelte Champions per Ringfarbe, 170 Champion-Eintraege,
Mechanik-Lexikon, Pruefwerkzeug `werkzeuge/ansagen_pruefen.py` (0 Widersprueche in 4 Partien),
Wiedereinstieg (Kauf + Ziel kurz vor dem Respawn), Kontroll-Auge situativ, Review vergleicht Live-Ansagen
mit dem Ausgang, Teleport/globale Ults von der Minimap.

Live-Partie 26.09. abends (Heimerdinger, "Vollkatastrophe"): erledigt am selben Abend - Denkkette
(`denker.py`: alle Kampf-Faktoren addiert, Erwartungswert, Matchup-Kurve fuer 173 Champions, Zone,
Gegner-Gold), ganze zusammenhaengende Saetze in allen Ansagen, keine Claude-Wartezeit mehr im Spiel
(Vorwarnung/Spike kamen 5-21 s zu spaet), Stimme Satz fuer Satz (erster Ton ~0,4 s statt 1,5 s),
Aussprache ("Vi" war "sechs"), Ult-Fehllesung "Heimerd / r", kein Dive-Rat. Stand je Faktor: `FAKTOREN.md`.

## Als Naechstes

- Camp-/Buff-Timer des gegnerischen Junglers (Camp-Icons der Minimap) fuer die Jungler-Prognose.
- Fragen per Maustaste: Claude braucht ueber die Kommandozeile ~2,5 s bis zum ersten Satz. Ein
  Anthropic-API-Schluessel wuerde das auf ~1 s druecken (kostet je Frage) - Carlos' Entscheidung.

## Braucht eine Partie

- NEU 26.09. abends: Denkkette und ganze Saetze (91968eb .. df9205e). Live pruefen: stimmen die
  Kill-/Trade-Urteile (Level, Items, Leben, Flash, Jungler, Matchup, Zone)? Sind die Saetze zu lang
  waehrend eines Kampfs (bis ~25 s Sprechzeit; SOFORT unterbricht)? Kommt die Ansage jetzt ohne
  Verzoegerung? "Wai" statt "sechs"? Nach der Partie: `python werkzeuge/ansagen_pruefen.py`.

- NEU 26.09. Lagebewertung + Komponist + Entscheider (e434179, 189a636, 74d01b0): jede Ansage
  gerechnet (Laufzeiten, Leben, Flash, Tiefe, Kraefte, Welle, Objective), Plaene zwischen den
  Ereignissen, Jungler-Startseite, Trade-Hinweis aus der Akte, Sofort-Antwort "was soll ich
  jetzt machen". Nachgespielt an der Camille-Partie: 79 Ansagen, keine Widersprueche mehr.
  Live pruefen: Haeufigkeit, ob die Zahlen stimmen (Ankunftszeiten!), ob etwas fehlt.
- NEU 26.09. (spaeter): 4 Takte/s live; Sprechplan fragt die Stimme "beschaeftigt" (keine veralteten
  Saetze mehr?); Platten live alle 2 s aus dem Beobachter; Teleport/globale Ults als Fernsprung;
  "2 gegen 1 hier - rein!"; Wiedereinstieg (Kauf + Ziel); Kanonenwelle vor dem Objective; Shutdown im
  Todespreis; Jungle-Plaene (bei Graves). Nach der Partie: `python werkzeuge/ansagen_pruefen.py
  aufnahmen/<neu>.jsonl.gz` und das Review (vergleicht jetzt Ansagen mit dem Ausgang).

Alles hier ist vorbereitet und mit Aufnahmen/Generalprobe getestet - die echte
Partie ist der letzte Schritt. Nach Carlos' naechster Partie: Log, Aufnahme,
Notizen und Review durchsehen und nachschaerfen.

- Recall-Fenster und Wellen: in Partie 4 einmal (2:49, Welle lief in seinen Turm) - passend.
  Offen: Haeufigkeit ueber eine ganze Partie.
- Briefing, situative Vorwarnungen live: Briefing kam 22 s nach Spielstart (0:36), war aber
  45 s lang -> auf 75 Woerter begrenzt (f18828d). Offen: kommt es jetzt kuerzer an; welche
  weiteren Anlaesse situativ werden.
- Stimme, Unterbrechen, Notizen: Frage per Sprache in Partie 4 beantwortet (1:52). Offen:
  Unterbrechen/Wiederholen, Notizen.
- Review einer Partie mit vollem Protokoll (Partie 4 endete nach 6 min ohne Review - der Coach
  wurde geschlossen): stimmen die Momente, sind die Lektionen belegt und hilfreich?
- Todesanalyse live: kommt der Satz vor dem Wiedereinstieg, trifft er den Grund? An
  Partie 3 nachgespielt: 5 von 6 Toden mit konkretem Grund in ~6 s.
- Fokus im Briefing: kam in Partie 4 als letzter Satz an. Offen: passt er, wirkt er?
- "Du stehst tief": Partie 4 einmal in 6 min (4:32 - Amumu flashte 5:16 oben auf ihn),
  Partie 3 nachgespielt 15 in 35 min. Offen: stoert die Haeufigkeit in einer ganzen Partie?
- Dashboard-Minimap mit 25/s aus 60 Bildern/s, Icons auf einem Fleck gefaechert: fluessig?
- Bildschirm fuer Claude (320f58f): Sprachfrage, Todesanalyse, situative Saetze mit Bild -
  liest Claude Lebensbalken und Kampflage richtig, bleibt es unter der Frist?
- Lane-Guide + Zettel (442e2fb): kommt er an, hilft er in den ersten Minuten?
- Objective-Start (16d4010): "Dein Team faengt Drache an" / "Gegner an der Drachengrube" -
  an Testpartie 2 nachgespielt zweimal "Lee Sin faengt Drache an", Drache fiel erst Minuten
  spaeter (Bot?). Im Spiel mit echten Mitspielern pruefen.
- Kamera-Schwenk (bf72298): "Schwenk kurz die Kamera: ..." und die Antwort mit dem neuen Bild.
- Eigene Zauber/Faehigkeiten aus dem HUD (fbfa43b): stimmt "Flash weg, noch ~X s" im Spiel?
  Bildschirm-Aufnahme und HUD-Lesen liefen noch nie live (Beobachter meldet Fehler am Ende).
- (geklaert, Partie 7: Pings sind Carlos' eigene, nicht Maus 5) Pings von Carlos' Konto ("Rumble hat Blitz benutzt" 2:13, 7:17):
  <Partie>_sprechtaste.log gegen die Chatzeilen legen - liegt Maus 5 im Spiel auf Pingen?
- Bildschirm-Momente (99c97da): werden live alle 5 s und vor jedem Tod Bilder gesichert? Nutzt
  das Review sie sinnvoll ("Bild 19:40: ...")? Echt geprueft bisher nur mit einem Bild (Partie 6, 2:37).
- Sprechtaste nach der Partie -> Review (c920f0a): im echten Ablauf pruefen.
- Verdeckte Icons (700b52c): Pruefstand 80-87 % statt 71-72 % - im Spiel mit Stapeln pruefen.

## Erledigt

- Review mit Bildschirm-Momenten: Spielbild alle 5 s + 12 s vor jedem Tod auf der Platte; Review
  bekommt die Bilder der wichtigsten Momente, das Gespraech das Bild zur gefragten Zeit, die
  Review-Seite zeigt es neben der Minimap; Aufraeumen der Minimap-Bilder lief seit Partie 4 nicht
  (int("chat_...")) - 99c97da

- Partie 7 ausgewertet: Strich-Pings zaehlen wieder (4916472); Objective-Warnungen kamen
  nicht (einmal je Spawn, Naehe schaltete Gegner-Warnung ab, zu kurz gueltig) und HUD-Flackern
  (5c7e9e8); Neustart setzt dieselbe Aufnahme fort (671d29e), Zusammenfuehr-Werkzeug (ce6f953);
  nur ein Coach zur Zeit (203ea99); Laden mit Preisen (6cc8571); Sprechtaste nach der Partie
  fragt das Review (c920f0a)

- Partie 6 ausgewertet: falsche Rumble-Flash-Timer kamen aus dem Chat (alte Zeilen nach jedem
  Kill neu gelesen; "Rumble — Blitz" als Verbrauch gewertet) - a56c544; Objective-Start
  ansagen - 16d4010; Kamera-Schwenk - bf72298; eigene Zauber/Faehigkeiten aus dem HUD
  (gelber Tasten-Buchstabe = bereit) - fbfa43b

- Bildschirm verstehen: Spielbild je Sekunde (12 s im Speicher) geht mit Sprachfragen,
  Todesanalyse (6 und 3 s davor) und situativen Saetzen an Claude - 320f58f
- Lane-Guide zu Spielbeginn (Spielweise, Level 1-3, Wellen, erster Back, Gefahr, danach)
  gesprochen und als Zettel auf dem Dashboard; Fenster zu = nichts verloren (Protokoll
  alle 2 s, Ansagen alle 20 s, fehlende Reviews beim Start) - 442e2fb
- Minimap 60 Bilder/s, halb/ganz verdeckte Icons, Flash nach Zeit bestaetigt - 700b52c;
  Chat-Pings bis 58 s zu spaet (neueste Zeile unter dem Ausschnitt) - ee82672

- Echte Partie 4 ausgewertet: Chat-Fenster an 46 Bildern geeicht (0.70-0.93), Chat-Ping
  "Tryndamere hat Blitz benutzt" kam trotz OCR-Rauschen an, Timer jetzt ab dem Zeitstempel
  der Zeile (23a94be); Flash an echten Bahnen: Rakan und Amumu echt, Galio war eine
  Fehlzuordnung -> Bestaetigung erst nach zwei ruhigen Bildern (50b37d2)
- 87 neue Matchups (Riven 42, Camille 45, Graves 30), Suche auf ganze Woerter - 5843df4

- Dashboard-Kasten "Dein Fokus heute" - e10873b; Kontroll-Auge nach dem Einkauf - e38bb00;
  nach der Partie gesprochen: "Review fertig, wichtigster Punkt, Fokus" + alles Gesprochene
  sprechbar ("30 bis 40 Sekunden" statt "30-40 s") - fca9ecb
- Live: "Du stehst tief, und Warwick und Swain sind seit 30 s weg" - die Hauptlektion aus
  dem Review von Partie 3 als Regel (tief = an/hinter seinem Aussenturm oder weit in
  seinem Jungle; nur Gegner, die dich seit der letzten Sichtung erreichen koennen; einmal
  je Vorstoss, bei langem Splitpush alle 90 s)
- Review: Recall-Analyse - ff615b9; Kaempfe nach Zeit UND Ort - d8d3afb; eigene
  Powerspikes live - 7528c6a; Todes-Fakten fuer Fragen - f4848da
- Todesanalyse live (`todesanalyse.py`): Rueckblick der letzten 45 s (Leben, Gold, Ort,
  Welle, wer zu sehen war); beim Tod mit >= 14 s Todeszeit sagt Claude statt des
  Standardsatzes den Grund und was naechstes Mal zu tun ist; ohne Minimap-Daten keine
  Aussage ueber Sicht
- Review: Farm-Loecher (lebendig, kaum gefarmt) - 41b864d; Fortschritt ueber alle
  Partien als Startansicht der Review-Seite - 844ba7a
- Gedaechtnis ueber Partien (`profil.py`): Kennzahlen je Partie (CS bei 10:00, Tode vor
  14:00, Gold gehortet, ...), der Fokus aus dem letzten Review geht als eigener Satz ins
  Briefing und in die Spielakte, das Review benennt Wiederholungen und ob der Fokus
  umgesetzt wurde; die eigenen Beschwoererzauber stehen jetzt in der Akte (vorher riet das
  Briefing bei Zuenden-Riven zu Teleport)
- Live: Partie endet erst nach Spielende (10 s Stille) oder 2 min Stille ohne Spielende -
  ein Reconnect beendet sie nicht mehr mittendrin
- Review per Sprache (Push-to-Talk im Review, Antwort gesprochen) - 54f7e40
- Offene Fakten: Inhibitor 5:00, Teleport-Abklingzeit nach Zeit/Level/Quest - bca57f3
- Tests fuer die Bausteine + tests/alle.py - 0eb3a7f; Doku + ANLEITUNG.md - 37cc39c

- Wellen-Zustand aus Vasallen-Punkten, Recall-Fenster, Wellen im Review - 87ccd7d
- Ward-Vorschlaege (Stelle + Anlass) - bd96a61
- Anlauf-Warnungen ("X kommt ... auf dich zu"), Port-Schutz der Server - 0341eb3
- Ult-Timer aus Chat-Pings, Level-6-Warnung mit dem Inhalt der Ult - 278f2e0
- Generalprobe ohne Spiel (`werkzeuge/generalprobe.py`) - fand Absturz, Flash-
  Fehlalarme bei stehenden Bildern, zu lange Ansagen, Meta-Gerede; alles behoben;
  Spielakte + Briefing in 22,7 s statt 46 s; Item-Namen abgesichert - cf618e1
- Champion-Lexikon: alle 173 Champions (29 ausfuehrlich, 144 kompakt) -
  34b8891 ... 5217081

- Review nach dem Spiel: `verlauf.py` (Zeitleiste + Momente aus Daten),
  `review.py` (Claude-Lektionen mit Beleg, Gespraech), Oberflaeche
  `python -m lolcoach review` / :8791 mit Zeitleiste, Minimap-Wiedergabe,
  Lektionen, Gespraech; automatisch nach jeder Partie - 87ebcda, 1327693
- Mitspieler-Leiste (Leben + Ult) aus dem HUD, Objective-Calls nur mit genug
  Leben, Ereignisprotokoll, Nachspielen aus dem Protokoll - 83c43d6

- Gehirn (`gehirn.py`) + Stratege (`stratege.py`): Spielakte, Briefing,
  Midgame-Plan, situative Vorwarnungen (Claude aus der Lage, sonst Standardsatz
  nach 12 s), Fragen mit Spielakte + Lexikon; Platten bis zum Turmfall - 5d59197
- Grundlagen-Lexikon `wissen/lexikon/grundlagen.md` + `saison2026.md` - 32934eb
- Minimap 15 Bilder/s, Flash an Spruengen, Chat lesen (Windows-OCR),
  Zauber-Timer mit Ansagen/Antworten/Dashboard, Bilder nur 20 min - 7bee474
- Wissensbasis Stufe 1: `lolcoach/champions.py` (173 Champions) - bf43408
- Stimme Killian (Carlos' Wahl) - 202f354; neuronale Stimmen - 9afaec7
- Unterbrechen ohne Verlust, Notizen, Teleport-Quest, Team-Zustand, Basis,
  volles Inventar, wenig Leben, Mid-Lane/Fluss - 32954ac
- Alte Minimap-Bilder aufraeumen (letzte 3 Partien), 4 Bilder/s - dcc4cee
