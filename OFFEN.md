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

**Auftrag 023 (stabile Messung, eine Stimme, Pflicht-Infos, Tempo) abgekuerzt** - Soll-Listen eingefroren
(`soll_023/`), drei Kritiker mit Mehrheit (`werkzeuge/kritik_mehrheit.py`). Runde 1: bekannt 59 %, neu 72,5 %;
Widersprueche 2-8 je Partie; Flash/Jungler/Lane 98-100 %. Das Tor misst 025 am Ende. Aufnahmen ausser den letzten
drei als `.jsonl.xz` (~12 MB je Partie statt ~46).

**Auftrag 022 (Speicher) umgesetzt** - 5,54 -> 4,35 GB; werkzeuge/aufraeumen.py laeuft nach jeder Partie.

**Auftrag 021 (Gehirn mit Plan, Buch 14 C) gebaut - TOR NICHT ERREICHT** - Soll-Liste bekannt 56 %, neu 70 %; Latenz
2,3-2,5 s; Widersprueche 1-7 je Partie; Lane-Gegner-weg 43-58 %. Carlos noch nicht live. Budget 5,46 $ von 6 $ verbraucht.

**Auftrag 020 (Kampfrechner, Buch 14 B) umgesetzt** - Riot-Eichung Tor erreicht (Schwelle 0,5), an Carlos'
Aufnahmen aber klar_vorn nur 13/24 - live nur klar_hinten sprechen. Eichung mit vollem Download wiederholen.

**Auftrag 018 (Graves-Partie 183125) umgesetzt** - Objective-Symbole (oben 99,5 %, unten 97,7 %), Plan in der Basis,
Turm mit Stufe, einzigartige Item-Gruppen und Elixiere, Kampf in der Naehe mit Kill-Check, Tod kurz. Offen: Elixier
ohne freien Platz widerspricht Carlos' Annahme im Auftrag (Spieldaten + 36:47 sagen: braucht Platz) - bei Gelegenheit
live pruefen; "Danach nach Top" ohne Grund (Kette gekuerzt) kommt noch vor.

**Auftrag 019 (Buch 14 A: Lagebild, API) umgesetzt** - Haiku ueber die API (1,6 s, ~0,25 $ je 30 min). Offen: Soll-Liste
~61 % (Ziel 80 % in Schritt C), I4 Lane-Gegner 6/12, Flash 183125 9/13; Riot-Schluessel in Schritt B (laeuft nach 24 h ab).

**Auftrag 017 (Inhalt statt Takt) gebaut, Messung offen** - siehe `buecher/auftraege/017_bericht.md`; die Messung
(Soll-Liste nachher, Fuellsaetze, Widersprueche, I1-I4, Latenz im Nachspiel) holt 019 nach. Latenz-Soll (<= 3 / <= 5 s)
verfehlt: Sonnet denkt adaptiv nach, per CLI nicht abschaltbar.

**Auftrag 016 (Pflichtenheft 133448: sagen, was er sieht, Ketten statt Schweigen) umgesetzt** - Zahlen in
`buecher/messungen.md` ("Auftrag 016"), Nachspiele in `buecher/protokolle/NACHSPIEL_*.md`. Offen aus der Kritik:
- Top-Wellen-Reflex ohne Blick auf die Karte (ADC und Support farmen dort; Welle schon am gegnerischen Nexus).
- Kauf: "Noch 225 Gold bis Axiombogen" direkt nach dem Kauf, "nichts zu kaufen" bei 4130 Gold (192113 28:24).
- Hin und her zwischen Kern-Satz und Antwort in < 10 s; gleiche Saetze mehrfach in kurzer Zeit.
- Carlos' Notizen bekommen nur "Notiert." - Forderungen wie "hilf Volibear", Freeze, 1 gegen 1 kommen selten.
- Latenz des ersten gueltigen Stratege-Satzes im Nachspiel 6-7 s (Median; die Kette wird bis zum Satzende gehalten) -
  an Wendepunkten spricht oft der Kern (4-s-Grenze).
- Sprechmenge 87-111 ungefragte Saetze je 30 min (vorher 54-80) - das alte Ziel ~75 ist kein Hauptmass mehr.

**Auftrag 015 (Stratege live, Pruefung erweitert) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 015").
Offen bis zur naechsten echten Partie:
- Ob der Stratege live besser ankommt als der Kern (Carlos entscheidet mit der Partie; Schalter `--ohne-stratege`).
- Die Objective-Pruefung ist streng ("Richtung Baron" ohne Spawn-Zeit wird verworfen) - kostet eine Wiederholung.
- Ein einzelner Satz ueber 30 Woerter bleibt ganz (gekuerzt wird auf ganze Saetze).

**Auftrag 014 (Stratege: Schutzschicht, Tor) - Tor knapp verfehlt, kein Live-Einbau** - Zahlen in
`buecher/messungen.md` ("Auftrag 014").
- Offen: "falsch" beim Strategen in der alten Menge 12,5 gegen 9,2 beim Kern (Tor: hoechstens +2). Reste pruefbar:
  Mitspieler-Orte, Sichtbarkeit, Gold (steht alles in der Lage, `stratege.pruefe` kennt es noch nicht).
- `stratege.VORWAERTS` nimmt "Nimm die Welle" faelschlich als Vorwaerts-Handlung.
- Laenge im Median 30 Woerter statt hoechstens 25.

**Auftrag 012 (Wellen-Endlosschleife, Fragen, Timer, Cassiopeia) umgesetzt** - Zahlen in `buecher/messungen.md`
("Auftrag 012").
- Braucht dich deine Welle nicht und gibt es kein anderes Ziel, heisst es "Geh nach Top: dort kommt ihre naechste
  Welle" (192113 19:48, 23:45 nach "mein Top ist reingepusht"). Ehrlich, aber Carlos will dann ein Makro-Ziel
  (Mid-Turm, Objective, Gruppe). Offen: soll der Kern in dieser Lage das Team oder das naechste Objective vorziehen,
  auch wenn beides ungeeicht oder klein im EV ist?
- 192113 (erste Botpartie in der Messung): 17,4 Warnungen je 30 min.
- Leerlauf ab 14:00 leicht hoeher (+0 bis +5 Punkte), weil das Druecken leerer Wellen wegfaellt (Szenario 101426 1400
  angepasst).
- Cassiopeia 22:24-22:29: vermutlich uebereinanderliegende Icons auf der Minimap, nicht weiter geprueft.

**Auftrag 011 (Warnungsrate, Szenario 2522) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 011").
- Warnungen je 30 min mit Vorsicht-Saetzen noch ueber 10 in 101426 (13,4: 11 GEFAHR + 5 "Du stehst tief") und in
  133930/140253/144655 (kurze Partien, 11-14); `a1-warnungen-je-30min` (nur GEFAHR) ist gruen.

**Auftrag 010 (Plan nach dem Wendepunkt) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 010"), Bericht in
`010_bericht.md`.

Offen aus Auftrag 010:
- **41 % nach schnellem Lebensverlust** (101426 29:36 "Weiter auf ihren Nexus-Turm", knapp ueber der R1-Grenze 40 %):
  die Grenze eventuell mit Sicherheitsabstand oder mit dem Lebenstrend statt dem Schnappschuss, sobald Buch 2/R1 noch
  einmal angefasst wird (nah an der bekannten Verzoegerung der Leben-Zahl, 008).
- **Zwei Leerlauf-Faelle ohne Ziel** (`tests/szenarien/offen/2026-09-28_101426_leerlauf.toml`): 17:03 (Turm stumm,
  Back gesperrt, keine Welle), 30:21 (46 % und 900 Gold sind kein Back-Grund).
- **WELLE_DRUECKEN kennt nur Wellen, die zu ihnen laufen** - eine Welle, die zu dir laeuft (ZU_DIR), ist weiter FARMEN
  (stumm).

**Auftrag 009 (letzte Sperren vor Testpartie 2) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 009"),
Bericht und Fragen in `009_bericht.md`.

Offen aus Auftrag 009:
- **Warnungen je 30 min wieder ueber 10** (101426 15,0, 164326 11,9, 173159 10,2): Folge von Entscheidung 2.1
  (Ungesehene <= 20 s als Koepfe) - 101426 20:01, 20:10, 21:35, 23:35 neu. Entscheidung im Bericht.
- **2522-kein-baron-drache-lebt (102112) rot:** ohne den Rang-Filter waehlt der EV den aeusseren Mid-Turm, weil
  Tryndamere den Drachen allein zu 86 % nimmt (Rivens Anteil 0,14); 0,5 s spaeter springt das Urteil (Anteil 1,0) und
  die Hysterese haelt den gesagten Turm. Entscheidung im Bericht.
- **Leerlauf ab 14:00:** in 6 von 10 Stichproben hat der Kern nach einem Wendepunkt nur HALTEN (kein Ziel mit EV > 0)
  in UNTERWEGS/GRUPPE - Tabelle in messungen.md.
- **"Zurueck unter deinen inneren Mid-Turm" auf der Bot-Lane** (101426 23:35, Kritiker: falsch): der sichere Ort nach
  Laufzeit ist dort der Mid-Turm, liest sich aber falsch.
- **DANACH-Antwort "Nach auf ihren Mid-Inhibitor-Turm: ..."** (213624 16:42): Grammatik von `fuehren.kurz` in
  "Nach {...}" - war schon vorher so.
- **Abgebrochene Saetze** (3 in 101426) stoeren den Carlos-Kritiker am meisten nach vagen Saetzen.

**Auftrag 008 (Testpartie 101426, Buch 4 Kartenlage und Makro) umgesetzt** - Zahlen in `buecher/messungen.md`
("Auftrag 008"), Kritik in `008_kritik.md`, Bericht und Fragen in `008_bericht.md`.

Offen aus Auftrag 008:
- **Warnungen in 101426 12,5 je 30 min** (Soll <= 10) und **falsch 2,5 je 30 min** (Soll <= 2) - nach der Kritik
  gebaut (Vorsicht nur in ihrem Jungle), nicht nachgezaehlt.
- **Leerlauf ab 14:00** 52-59 % in den echten Partien (Buch 11, Soll <= 10 %) - war schon vorher so; Buch 4 fuellt ihn
  nicht (Makro-Infos nur mit Wirkung).
- **Ungefragte Ansagen** 68-73 je 30 min (Ziel <= 45 bzw. <= 50 ohne Flash/Wendepunkt: 47-53) - Lagebild, Teamplan,
  Makro kamen dazu.
- **Abgebrochene Saetze** (4 in der Kritik): Transport im Sprechplan.
- **Wiederholte Frage, gleiche Antwort** (213624 10:19/10:26 "kein Platz"): die Antwort passt sich nicht an.
- ~~**20:16 in 101426**: A1 warnt nicht~~ erledigt (Auftrag 009, 2.1: warnt um 20:01/20:10).
- **Szenario 2411 (213624)** ist nach A1 ohne Pruefung (uebersprungen): die Episoden-Regel prueft kein Fall mehr.
- **Viego mit Standard-Skin**: der Gestalt-Fix liest rawSkinName - fehlt der beim Standard-Skin, heisst Viego in fremder
  Gestalt weiter wie der Getoetete.

**Auftrag 007 (Entscheidungen, Fehlerklassen, Live-Tauglichkeit) umgesetzt** - Zahlen in `buecher/messungen.md`
("Auftrag 007"), Kritik in `007_kritik_runde3.md`, Bericht und Fragen in `007_bericht.md`.

Offen aus Auftrag 007:
- ~~Generalprobe mit eingeschaltetem Bildschirm~~ erledigt 28.09.: Fenster 3840 x 2160 bei x = 1920 (Carlos' Aufbau),
  Takt Median 25/s, Minimap 3652/3654, HUD 146/146, keine Fehler.
- ~~HUD bei 32:9, Minimap am rechten Rand~~ falsch angenommen: League laeuft als 3840 x 2160-Fenster in der
  Schirmmitte, alle Ausschnitte rechnen vom Fenster aus (`buecher/messungen.md`, Auftrag 007, C1).
- **164326 2,8 falsch je 30 min** (Schwelle 2): Top-Inhibitor gegen den Drachen daneben (Buch 6, 8 Rangfolge) -
  Entscheidung; "Raus" waehrend des Recalls (Schranke) - Entscheidung.
- **Flash-Clips** werden live gesammelt; die Erkennung erst ab 20 echten Clips. `bilder_aufraeumen` raeumt sie nicht auf.

**Auftrag 006 (Wahrnehmung: Welle, Quest-Anzeige, Flash) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 006").
- Welle 173159 jetzt 10 von 12 eindeutigen (hysterese_zu_mitte_s); offen 7:33 (Icon am Zonenrand) und 9:25
  (uebereinanderliegende Vasallen, Wellenleser.punkte).
- Quest-Platz V wird passiv gelesen: Quest-TP ab dem Quest-Ende (9:51-12:12 statt 13:35). **Erledigt** ist damit der
  Punkt "Quest-Feld V im HUD lesen" aus Auftrag 003.
- Flash im Spielbild: mit den gesicherten Bildern nicht pruefbar; live 12/s vorhanden, sichtbare Flashs findet schon die
  Balkenspur. Entscheidung bei Claude (Chat).

**Auftrag 005 (Selbstpruefung mit Kritiker, zwei Runden) umgesetzt** - Zahlen in `buecher/messungen.md`
("Auftrag 005"), Klassen in `005_kritik_runde1.md` / `005_kritik_runde2.md`, Rueckfragen in `005_frage.md`.

Offen aus Auftrag 005 (Klassen mit falsch >= 2 nach Runde 2, nicht gebaut):
- **Antwort und Ansage zaehlen "euch" verschieden** (Klasse 6): an der Grube (2500) gegen in 45 s dort (213624 11:00/11:38).
- **Ueberlegene Turmziele wechseln sich ab** (Klasse 10): 164326 35:14, 42:33 - das Urteil haengt am Ziel.
- **FARMEN mit Vorschau statt Back** (Klasse 11): 164326 16:23, 25:56, 28:37 - seit 004 hoerbar.
- **Back in Gefahr oder in der Basis** (Klasse 9): 173159 6:39, 34:59; 213624 17:11.

**Auftrag 004 (Ueberlegenheit, echte Antworten, Kampf-Eichung) umgesetzt** - Zahlen in `buecher/messungen.md`
("Auftrag 004"), Bericht in `buecher/auftraege/004_bericht.md`, Rueckfrage in `004_frage.md`.

Offen aus Auftrag 004:
- **Kampf-Eichung besteht mit keinem Etikett** (gold, koepfe, ueberlebt) - Gold trennt verkehrt herum. Naechster
  Verdacht: Spielzeit (r = 0,56 mit gold_diff). Bis dahin sprechen Kampfrufe nur ueber die Ueberlegenheits-Regel.
- **Wendepunkt-Probe rot:** die spaeten Saetze stehen meist hinter einem stummen FARMEN ohne Vorschau (Teil A 1) -
  gewollt still, von der Probe als rot gezaehlt. Entweder die Probe nimmt sie aus, oder FARMEN bekommt am Wendepunkt
  einen Satz - Entscheidung.
- **Widersprueche:** 213624 13:18 (Korrektur "ich bin beim Drachen" gegen den Basis-Beobachter), 164326 35:00 (zwei
  ueberlegene Turmziele in 15 s).
- **Test `kamera_gibt_nur_einmal_frei`** scheitert am Bildschirm 7680 x 2160 (dxcam gibt die volle Flaeche zurueck) -
  auch auf dem Stand vor 004; pruefen, ob der Coach dort je Takt den ganzen Bildschirm kopiert.

**Auftrag 003 (Buch 11 Fuehren, Schritt 6 Fragen) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 003 /
Schritt 6"), Bericht in `buecher/auftraege/003_bericht.md`. Carlos hat Stimme und Tempo gewaehlt: Killian, +25 %.

Offen aus Auftrag 003:
- **Quest-Feld V im HUD lesen** (Auftrag 003, Teil A 5): das Quest-TP gilt erst ab 13:35 als bereit, fertig war die
  Quest 1,5 bis 4 Minuten frueher. Tuerkiser Ring = laeuft, violett = bereit, dunkel mit Zahl = Abklingzeit
  (Befund in messungen.md, Auftrag 002, S4). Gehoert nach `hud.py`.
- **Wendepunkt-Probe nicht ganz gruen** (Buch 11, 7): nach Turmfall, Objective und Basis-Verlassen kommt der Satz
  nicht immer in 3 s - Ursachen und Zahlen in messungen.md.
- **Mid-Game-Plaene haengen am ungeeichten Kampfmodell** (Entscheidung 2): Turm- und Objective-Handlungen mit Kampf
  sind stumm, oft bleibt nur "Farm deine Welle". Gefragt nennt der Coach sie mit "unsicher". Erst die Kampf-Eichung
  macht Buch 11 im Mid-Game voll wirksam.

**Auftrag 002 (Sofort-Fixes aus 213624) umgesetzt** - Zahlen in `buecher/messungen.md` ("Auftrag 002"), Bericht in
`buecher/auftraege/002_bericht.md`. Carlos' Wuensche aus der Partie 213624 (Notizen und Sprechtaste), je mit dem, was
sie abdeckt:
- **Vorausplanung, naechste Schritte frueher** (17:08, 20:32: "zwei, drei Minuten in die Zukunft gucken", "Leerlauf,
  man wartet auf Anweisungen"): **Buch 11** (Claude schreibt es). Nicht in Auftrag 002.
- **Fragen werden nicht beantwortet** (11:49, 13:23: "zehnmal dieselbe Frage, du antwortest einfach nicht"):
  **Buch 11** (Schritt 6, Fragen per Sprechtaste). Nicht in Auftrag 002.
- **Aussprache** der Champion- und Item-Namen (5:59: "englische Woerter auch wirklich auf Englisch"): Auftrag 002, S2 -
  Stimmproben in `aufnahmen/stimmproben/`, **Carlos waehlt** (`[stimme] name` in `wissen/kern.toml`).
- **Tempo** (16:02: "viel zu lange und viel zu langsam ... immer zu spaet"): Auftrag 002, S2 - +50 %, PLAN <= 14,
  GEFAHR <= 8 Woerter. Offen: Killian hat ~0,95 s Stille je Satz (Florian 0,57 s), die +50 % nicht kuerzt.
- **Flash** (19:41: "du sagst nicht, wenn jemand geflasht hat"; 23:22 "keine Daten"; 23:45 "extrem gut, wenn die kein
  Flash haben"): Auftrag 002, S3 - INFO_FLASH, Flash-Stand aller Gegner, Regel "ohne Flash = Grund fuer Angriff".
- **Quest-TP** (14:20: "du planst nie meinen Teleport ein"): Auftrag 002, S4.
- **Zahlen** (7:00 Schraegstrich, 11:12 "3-0-0-0"): Auftrag 002, S1.
- Offen aus Auftrag 002 (Entscheidung): 16:21 zwei klar unterlegene Gegner (Caitlyn 32 %, Sona) loesten GEFAHR aus -
  gilt die Regel "klar unterlegen" auch fuer zwei? RAUS bei < 30 % Leben, wenn der Balken des Gegners unbekannt ist
  (213624 19:00) - Beleg oder nicht?

**Qualitaetsrunde 3 (Pruefung 27.09. c, R1-R10, Auftrag 001) umgesetzt** - Zahlen in `buecher/messungen.md`
("Qualitaetsrunde 3"), Protokolle neu in `buecher/protokolle/`, Bericht in `buecher/auftraege/001_bericht.md`.
Schranken-Verstoesse 0 in allen sechs Partien, 86 / 86 Szenarien gruen.

Offen aus der Qualitaetsrunde 3:
- **Ungefragte Ansagen in 173159: 52 je 30 min** (Ziel <= 50; 164326: 46). Der Rest ist zur Haelfte GEFAHR, fast
  jede vor einer anderen Gegnermenge. Eine Sperre fuer die zweite Warnung in 15 s wurde gemessen und zurueckgenommen
  (69 statt 68, die Warnung vor dem Tod 22:13 fehlte). Naechster Hebel: die Gefahr-Schwelle (Eichung) - Entscheidung.
- **Fassungswechsel-Kennzahl** zaehlt in 102112 zwei begruendete Wechsel (je nach Kills). Entscheidung: Soll sie
  Kills, Objectives und Lebensverlust als Ereignis zaehlen wie die Kehrtwenden?

**Schritt 5 umgesetzt (Buch 7 Kampf, Buch 6 Objectives, a2e418d)** - der Kern spricht in allen neun Modi. Zahlen und
Abweichungen in `buecher/messungen.md` ("Schritt 5"), Protokolle neu in `buecher/protokolle/`. Naechster Schritt laut
Pruefung b: Carlos prueft alle Protokolle; erst danach wieder live.

Offen aus Schritt 5:
- **Kampfmodell nicht geeicht** (Entscheidung 2): ANNEHMEN, REIN, DREHEN sind stumm (`[kampf].geeicht = false`),
  bis `kampf_eichung.py` an echten Partien mit >= 30 entschiedenen Proben einen Brier-Wert besser als die Grundrate
  zeigt. Heute 41 Proben, Brier 0,320 gegen 0,249; das Gold trennt sogar verkehrt (AUC 0,30), nur das Leben schwach
  richtig (0,58) - Carlos baut das Modell danach gezielt um (Tabelle in messungen.md).
- **Objective-Eichung:** 15 Versuche (< 30), Brier 0,276 gegen 0,160 - Startwerte. Die Toetungszeit-Messung erkennt
  Vorbeilaufen als Beginn (3 s bis 123 s) - strengeren Beginn und mehr Partien.
- **Welle 173159: 7 von 12** (Soll 8 von 10; 164326: 13 von 15). Ursachen je Zeitpunkt in messungen.md; nach
  Entscheidung 3 nichts umgebaut, die strenge Prio-Regel aus Buch 6, Kapitel 6 bleibt.
- Nicht umgesetzt aus Buch 6: Lane-Form von ABGEBEN_TAUSCHEN ("Gangplank ist zu den Larven: Platten jetzt"),
  Herold-Ritt (Kapitel 7, `wert_ritt` mit Turm-Leben aus dem Wiki), Folgewert Larven 3:0, Bestaetigungen aus
  Kapitel 9 ("Sauber: Drache ohne Kampf").
- Die Kampf-Proben mit dem groessten Fehler liegen als Stubs in `tests/szenarien/offen/<stamm>_kampf.toml`
  (Buch 7, 10) - Soll setzt Carlos.
- (Stand Qualitaetsrunde 3: 46-63, s. oben) **Ungefragte Ansagen <= 45 je 30 min nicht erreicht** (59-80). Die alten Regeln sind bis auf Rueckblick und AFK
  still; es ist der Kern selbst, 40-50 % GEFAHR (Rueckzug "Raus zu deinem ...-Turm: X und Y kommen"). Naechster Hebel:
  die Gefahr seltener und zusammengefasst.
- (Qualitaetsrunde 3, R10: jetzt 2/0/0, die zwei begruendet - s. oben) **Fassungswechsel 2/1/3** (102112, 133930, 164326; Soll 0): "Back jetzt" -> "Jetzt back" mit neuem Gold nach
  einem Rueckzug (seit der Rueckzug ohne Gefahr endet), Turm-Ziel wechselt ohne Ereignis in 12-14 s, KAUFEN mit
  anderer Liste. Einzelstellen in messungen.md, Schritt 5.

**Qualitaetsrunde 1 (Pruefung 27.09., A-F) umgesetzt** - Zahlen in `buecher/messungen.md`, Protokolle neu in
`buecher/protokolle/`. Naechster Schritt laut Pruefung: Schritt 5 (OBJECTIVE, KAMPF), dann Schritt 6, dann die
naechste Pruefung an allen Protokollen - erst danach wieder live.

Offen aus der Qualitaetsrunde 1:
- **F1 an 133930 nicht belegbar:** die Minimap-Bilder wurden 17:26 aufgeraeumt; mit den Live-Punkten 4 von 7.
  Braucht eine neue echte Partie mit Bildern (Ordner mit Datei `BEHALTEN` schuetzen). 144655: 9 von 11.
- **F2 Flash, entschieden (Pruefung 27.09.b):** Weg 1 (keine Timer aus Spruengen von Dash-Champions,
  `wissen/dashes.toml`) und Weg 3 (Carlos pingt in der Anzeigetafel, der Coach schweigt, das Dashboard zeigt den
  Timer) sind umgesetzt. **Weg 2 nach Schritt 6:** den Flash-Effekt im Spielbild erkennen (gelber Blitz an Absprung
  und Landung) - unterscheidet Flash von Dash.
- Nach dem Ende der laufenden Partie (Start 17:31) raeumt Carlos' Coach 140253 auf (alter Code ohne BEHALTEN) -
  Bilder liegen gesichert im Scratchpad der Sitzung; zuruecklegen, falls weg. Den Coach vor dem naechsten Test
  neu starten (er lief seit 16:43 mit altem Code).
- Lane-Phase je 30 s ueber 1 in 133930 (1,25) und 144655 (1,06): Schutzplan der verlorenen Lane nach jedem
  Tod/Basis neu (gewollt) und einmal mit neuem Item (144655 3:34).
- Anzeige "Spawn um 8 00" (`komponist.uhr_gesprochen`, seit Schritt 3): gesprochen richtig ("acht Minuten"),
  im Protokoll/Dashboard haesslich.

**Buch 0, Schritt 4 umgesetzt** (Buch 5, Mid-Game Top): der Kern entscheidet und spricht jetzt auch in SEITE,
GRUPPE, UNTERWEGS, VERTEIDIGEN - Karten-Rechnung (Turm, Seitenwelle, Gruppe/TP, Welle rein und rotieren), Umwandeln
nach gewonnenem Kampf bis zum Nexus, Schweigen wenn du schon hinlaeufst, Bestaetigungen aus Kapitel 9. Zahlen und
Abweichungen in `buecher/messungen.md`. Jetzt: Carlos spielt echte Partien (Coach neu starten) und haelt Momente
nach 14:00 per "Notiz ..." fest (Buch 5, 11.3); danach Schritt 5 (OBJECTIVE, KAMPF). Schritte 1-3 sind erledigt.

Offen aus Schritt 4:
- **Ungefragte Ansagen <= 50 je 30 min nicht erreicht** (102112 56, 133930 88, 140253 61): der Kern allein liegt
  darunter, der Rest ist das alte System im Modus OBJECTIVE (19 bzw. 26 Ansagen) - geht mit Schritt 5 an den Kern.
- 9.4 Punkt 1 in den Aufnahmen vom 26.09. (10 Stellen): alte Regeln, wenn die Minimap Riven > 10 s nicht findet
  (kein Modus = keine Sperre). "Schieb die Welle in seinen Turm" (`_lane_tot`, `_gold`, `jetzt:drache`) ohne Lane -
  mit Schritt 8 weg oder vorher die Lane in den Satz.
- Lane-Phase 133930: 1,21 Ansagen je 30 s (Abnahme Schritt 3: <= 1) - ansehen.
- **Carlos testet live erst wieder, wenn es offline nachgewiesen gut ist** (27.09., nach Partie 144655). Beweise:
  `werkzeuge/nachspielen.py` (Stimme in Spielzeit, Abbrueche), `werkzeuge/protokoll.py` (`buecher/protokolle/`),
  Szenarien. Der Coach wird nie gestartet, waehrend Code geaendert wird (CLAUDE.md).
- (gemessen in der Qualitaetsrunde 1, F2 - s. oben) **Flash-Erkennung findet zu wenig** (144655: 1 Flash in 9,5 min; 3 echte Partien: 27 Spruenge auf dem Bildschirm,
  keiner wurde ein Timer): Spruenge von Champions mit Dash/Blink werden bewusst verworfen, Namen ueber den
  Lebensbalken sind selten lesbar, auf der Minimap fehlen Spruenge im Kampfgewuehl. Der Weg zum Dashboard stimmt
  (Headless-Chrome mit dem Code der Partie: Gangplanks Flash 1:56-6:56 stand im Gegner-Kasten). Naechster Schritt
  waere eine Wahrnehmungsaufgabe (Flash-Effekt im Spielbild erkennen) - Carlos' Entscheidung.
- Alter Zielsatz "fruehestens in 0 Sekunden kann einer von ihnen dort sein" (komponist.ziel_satz, BASIS-Ziel ohne
  Karten-Ziel) - bei 0 den Grund weglassen.

Offen aus Schritt 3:
- (Qualitaetsrunde 1, F1: Front statt Summe umgesetzt, 144655 jetzt 9 von 11 - s. oben) **Wellen-Eichung (Buch 1, 1.4) nicht erreicht** (Nachtrag in messungen.md): Icon+Ring-Maske und behaltene
  Ausschnitte sind erledigt; 133930: 5 von 9 (56 %), **144655: 4 von 10 (40 %)**. Hauptursache (144655): die
  Zustandsregel zaehlt alle Vasallen der Lane - steht die gegnerische Welle an deinem Turm und laeuft deine naechste
  dahinter los, wird GECRASHT_BEI_DIR zu ZU_IHM. **Carlos' Entscheidung:** nur die Vasallen um die Front zaehlen
  (Umbau am Kern). Dazu: Hysterese haelt GECRASHT zu lange, Vasallen direkt am eigenen Icon fallen unter die
  Ring-Maske, Recall-Leuchten, `wellen_eichung.py` waehlt auch Zeitpunkte, an denen du tot bist.
- Generalprobe mit `--kern neu` (lief nicht, Carlos spielte).
- Bestaetigung "Puenktlich zurueck" (Ankunft der Welle am Turm) und der zweite STAPELN-Ausloeser (Back/Roam im Plan).
- Stub-Notizen aus der echten Partie 140253 (9:09-10:25) nach `tests/szenarien/offen/` (werkzeuge/
  szenario_aus_notizen.py) und beschriften.

Carlos' Ziel 26.09. (/goal): Challenger-Coach, individuelle Ansagen aus vielen Faktoren, keine
Standardsaetze; Grundlage `Reasoning/LoL Reasoning.txt` (Entscheidungskette Zustand -> Welle ->
Prio -> Tempo -> Information -> Gegner-Vorhersage -> Aktionen -> Gegenantwort -> Wert).
**Die Entscheidungsseite dieses Ziels ist ersetzt durch Buch 0** (Kern: Modus, Handlung, Wert, Plan,
Sprechen - Schritte 2-8). Die Wahrnehmungspunkte darunter bleiben offen.

- Gegner-Leben vom Bildschirm: laeuft seit 3b71e7d (Balken per gelesenem Namen, in Kill-Rechnung und Fenster-
  Saetzen); nachgeprueft 27.09. gegen die Gegner-Tode (`werkzeuge/gegner_leben_probe.py`): kein falsch
  zugeordneter Balken. Offen: nur 21 von 133 Toden hatten eine Lesung - Gegner ausserhalb des Bildes.
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

- Minimap, gemessen 26.09. abends (eigene Flashes aus dem HUD als Wahrheit): von 12 eigenen Flashes
  erkannte die Minimap 1, Fehlalarme 0 - im Kampf liegt das Icon unter anderen (physikalische Grenze).
  Verbuendete galten nur in 57-94 % der Takte als sichtbar; mit "verdeckt/Brunnen/Tod/Recall" jetzt 88-100 %.
  Erledigt 26.09. nachts: Icons in der Brunnen-Ecke (`minimap.ecke`, sichtbarer Teil) - 19:45 war Riven 2,5 min
  im Brunnen ungesehen (das Lagebild hielt sie dort schon per "zuletzt in der Basis"; neu ist der Spielbeginn ohne
  erste Sichtung und eine echte statt einer gehaltenen Position - Korrektur zu 0fdab75); eigenes Icon gegen den Kamerarahmen geprueft (`werkzeuge/kamera_rahmen.py`: 99,3-99,7 %
  im Rahmen, Ausreisser = Kameraschwenks). Offen: Verwechslung im Klumpen (13:07: Riven unten "gesehen", stand
  oben unter Heimerdinger) - nur an 60-Bilder/s-Live-Daten nachstellbar; im Klumpen koennte der Kamerarahmen
  die eigene Position liefern (bei gesperrter Kamera: Rahmenmitte +0,018 nach unten).

- Camp-/Buff-Timer des gegnerischen Junglers (Camp-Icons der Minimap) fuer die Jungler-Prognose.
- Fragen per Maustaste: Claude braucht ueber die Kommandozeile ~2,5 s bis zum ersten Satz. Ein
  Anthropic-API-Schluessel wuerde das auf ~1 s druecken (kostet je Frage) - Carlos' Entscheidung.

## Braucht eine Partie

- NEU 27.09. ~00:50 (Coach NEU STARTEN): Stimme gebaut auf Tempo - spielt ab dem ersten MP3-Stueck (e4b360d), der
  naechste wartende Satz wird vorab synthetisiert, Ausgabe ueber WASAPI statt MME (e35083c, 60 statt 182 ms Puffer).
  Stumm gemessen (Coach-Weg, stimmprobe): erster Ton Median 0,10 s mit vorgewaermten Satzanfaengen (1b7fbf1; live
  vorher 0,63 s); neuer Text ~0,45 s beim Dienst. Eigene Position aus dem Kamerarahmen, wenn das Icon verdeckt ist
  (5004a96), Verbuendete unter Icons 6 s (1bfb9cd). Satzanfaenge mit der Handlung vorn und vorgewaermt: 75-88 %
  der Ansagen beginnen aus dem Speicher (407c931). Haengt der Dienst beim ersten Teil > 2 s, spricht die
  Windows-Stimme (ddb7bb2) - hoert Carlos sie oft, ist der Dienst live langsam: melden. Danach gerechnet statt
  Vorlage: Jungler Level 6 (5b4c355), Vorwarnung tot/im Brunnen (40f8d97), Tod mit dem Rat davor (127c88a, c8f723b).
  Aus Carlos' Live-Fragen: Objective laeuft und du bist zu weit -> Recall/Druck statt "geh hin" (178e2e7), zwei
  Wards nur mit Kontroll-Auge, Kauf-Fragen sofort aus dem Kaufplan (d4babb0). Turmschuss mit Ruestung (36c099e),
  Wecker fuer Flash/Gegner nah (47ca6b8).
  LIVE PRUEFEN: klingt die
  Stimme auf beiden Ohren, ohne Knacken/Aussetzer, und nicht abgeschnitten am Satzende? Sonst `_Neural._wasapi = False`
  setzen (MME) und melden. Danach `python werkzeuge/verzoegerung_live.py`.
  [Ab hier bis "klingen die Saetze jetzt knapper": ersetzt durch Buch 0, Kapitel 8-9 (Plan halten, Sprechen,
  Budget) - nicht mehr live pruefen, sondern ueber Szenarien.]
  Satzlogik aus dem Nachlauf aller drei Partien (83e8923): kein zweites "geh zurueck" 12 s nach dem ersten (ausser
  Gefahr), eine Gefahr bricht die andere erst nach 4 s ab, stirbt ein genannter Gegner, faellt der Satz ("Ach nee"),
  "Geh jetzt zurueck, Ekko und Vex koennen da sein" bricht ab, wenn keiner mehr vor dir am Turm sein kann; ohne
  frische eigene Position trotzdem ein benannter Turm (letzte Sichtung / aeusserster der Lane).
  Danach (bis ~02:00): Handlung zuerst - "Geh rein, das ist ein Kill: dein Combo macht ..." (6f193bd), "Geh jetzt
  zurueck zu deinem Top-Tier-1-Turm, das sind 16 Sekunden: Vi ..." (ae13a7f); Beiwerk kuerzer (b18e9b5); Konter-Kauf
  ohne eigene Items (1151bf2); "kein Flash" beim Jungler gerechnet statt "nutz das Fenster" (ad20ab4); kein
  Plan-Hin-und-Her (5e2930f). LIVE PRUEFEN: klingen die Saetze jetzt knapper und kommt das Entscheidende zuerst?

- LIVE 26.09. 23:05 (Practice Tool, Graves top gegen Sion): erste Live-Verzoegerung gemessen - 'Stimme' (Abgabe
  bis erster Ton) Median 1,5 s, bis 2,5 s; Ursache: jede zehnte edge-tts-Anfrage haengt 1,4-1,8 s -> zweite Anfrage
  nach 0,35 s (891f246, 90 % jetzt 0,45 s). Zwei Absturz-/Zustandsfehler behoben: Neustart mitten in der Partie
  brach an einer gesperrten Aufnahme ab (18d970b); Practice-Tool-Neustart galt als Reconnect - Briefing und Rolle
  ("Voll-Clear", Smite) aus der ersten Partie blieben (3da384b). Aufnahme 2026-09-26_230520 enthaelt deshalb zwei
  Partien (74 Schnappschuesse Nasus/Rumble-Partie, dann Sion/Ekko) - fuer Auswertungen die ersten 74 abschneiden.
  Nach der naechsten Partie: `python werkzeuge/verzoegerung_live.py` - kommt die Stimme jetzt unter 0,5 s?
  Danach, gleiche Partie (Carlos: "du bist sowas von in der Vergangenheit", "die Top-Aktualitaet ist das
  Wichtigste ueberhaupt", "was ist denn mein Tower?"): Antippen der Sprechtaste hielt die Stimme minutenlang an
  (9e6b0b8); jeder Satz prueft sich vor und waehrend des Sprechens, bricht ab und das Neue beginnt mit "Ach nee"
  (f2f8f10); Tuerme heissen "Top-Tier-1-Turm" (9331d68); Gegner am Drachen bei weitem Weg: "zu weit fuer dich"
  (8fa9652); Bruchstuecke ohne Frage bekommen keine Antwort (b5e7874). Live pruefen: kommt "Ach nee" an der
  richtigen Stelle, bricht nichts ab, was noch stimmt (Fehlabbrueche = Satz fehlt ganz)?
  Nacht 27.09., ohne Partie gemessen: Minimap-Erkennung - Sichtprobe 30 Icons, 0 Verwechslungen; Ringfarbe aller
  Sichtungen 0,17-0,43 % falsch (Einzel-Champions, neue Partien; `werkzeuge/minimap_ringprobe.py`); verloren unter
  einem Icon nur 2-3x je Partie. Eigene Flashes (HUD als Wahrheit): Minimap 2 von 7, 0 Fehlalarme - die 5
  verpassten lagen im Kampf komplett unter dem Gegner-Icon (Grenze der Minimap; der Bildschirm deckt den Kampf vor
  dir ab). Bildschirm-Sprung jetzt mit Kamerarahmen: die Minimap nennt den Springer oder verwirft (fc9eaa7).
  Sofort-Antworten "Soll ich backen?" / "Sollen wir Drache machen?" (bc78656); feste Rat-Anhaenge gerechnet
  (6cec013); 'seit X nicht zu sehen' nach Neustart ab Zuschau-Beginn (d6fcf0e). Generalprobe (stumm, 2 min): laeuft.

- NEU 26.09. nachts: (1) jede Ansage protokolliert live ihren ersten Ton und ob sie abgebrochen wurde - nach der
  Partie `python werkzeuge/verzoegerung_live.py` (Warten im Plan vs. Stimme, je Vorrang; das Mass fuer "geisteskrank
  zu spaet"). (2) "Kann ich ihn killen?" / "Soll ich reingehen?" per Sprechtaste antwortet sofort aus dem
  Kampf-Urteil statt ~3 s ueber Claude - pruefen, ob die Antwort passt. [(2) ersetzt durch Buch 0, Kapitel 10:
  SOLL_ICH beantwortet der Kern.] (3) Lebensbalken geeicht (78 px, blasses
  Ende). (4) Kampf-Urteile ueber 4 Partien: kill 24 -> 10 Kills, 0 Tode (Schadensrechnung hat Vorrang).

- LIVE GEPRUEFT 26.09. 21:21 (Riven gegen Gragas, 11/1/2, Stand bis 0148c93): Denkkette spricht zusammenhaengend,
  Kill-Urteile trafen (4:12 -> Kill 4:20, 15:11 -> Kill 15:17), Verbuendete 92-100 % sichtbar, Minimap 32 Bilder/s
  (vorher 33,6-34,4 - die Balkenspur kostet ~5 %), Verzoegerung Median 0 s. Behoben (dieser Commit): Flash-
  Meldungen warteten 9-17 s hinter langen Saetzen (jetzt unterbrechbar), Lane-Anweisung waehrend Carlos tot war,
  "du bist frueh staerker" gegen die Siegquote (45,9 %), Schnellantwort auf Aussagen, "geh rein" ohne Ort,
  Bildschirm-Flash bei Dash-Champions (9:18 Gragas + Tryndamere zugleich = Engage), Lissandra-E als "Flash".
  Offen: Bildschirm-Flash bei Champions ohne Dash hat noch keinen echten Treffer - naechste Partie pruefen.

- NEU 26.09. spaet: Flash auf dem Spielbild (`lebensbalken.Balkenspur`, ~10 Bilder/s im eigenen Thread): ein
  Gegner-Balken springt in einem Bild 250-600 px mit demselben Leben, ein zweiter Balken bleibt ruhig, Namen an
  Absprung und Landung stimmen -> Flash-Timer "das sehe ich auf dem Bildschirm". Generalprobe: laeuft, Minimap
  unverlangsamt. Nach der Partie: `balkenspur`/`schirm_sprung` im Protokoll gegen Carlos' Pings und die eigenen
  HUD-Flashes pruefen (Treffer, Fehlalarme); bei Fehlalarmen stummschalten.

- [Ersetzt durch Buch 0, Kapitel 6.2 (Kill-Beleg), 7 (Wert) und 12 (Szenarien statt Live-Pruefen).]
  NEU 26.09. abends: Denkkette und ganze Saetze (91968eb .. df9205e). Live pruefen: stimmen die
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

- Stimme "stottert" (Partie 144655, 27.09.): nicht die Stimme, der Coach widerrief seine Saetze mitten im Sprechen -
  11 von 18 brachen ab, die Kern-Gefahr "Bleib an deinem Top-Tier-1-Turm" nach 0,3 s, weil ihr Plan-Schritt im
  naechsten Takt erledigt war (dann "Ach nee: ..."). Jetzt bricht nur eine Gefahr einen Satz ab; ein Satz, der beim
  Sprechen falsch wird, wird zu Ende gesagt (bei einer Gefahr folgt die Korrektur mit "Ach nee"). Nachgespielt:
  alter Stand 10 von 19 abgebrochen, neuer keiner ausser durch eine Gefahr. Dashboard zeigt jetzt auch Ult-Timer.
  Gegner gelten nie mehr als AFK (Stufe und Items zeigt die API nur, wie er zuletzt gesehen wurde - Kha'Zix bis 3:34
  "Stufe 1"); SEITENWELLE erst nach der Lane-Phase (0:58: "Welle gerettet - kein Turm verloren").
- Minimap-Groesse aus der game.cfg: Partie 27.09. 13:03 lief mit MinimapScale 2,91 statt 1,5 - der Coach
  schnitt die alte 570er-Karte aus, sah in 1629 von 1717 Bildern niemanden und sagte deshalb staendig
  "ich erkenne niemanden, rechne ohne Karte". Jetzt liest er MinimapScale (nur lesen, alle 2 s per stat),
  Karte, Icons, Suchradien und Mitspieler-Leiste wachsen mit (Test minimap_groesse_aus_der_einstellung).
  Andere Werte als 1,5 und 2,91 sind linear angenommen, nicht vermessen.

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
