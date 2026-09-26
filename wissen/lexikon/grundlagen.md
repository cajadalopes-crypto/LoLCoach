# Grundlagen-Lexikon (Nachschlagewerk fuer das Coach-Modell)

Stand: Patch 26.19 (Saison 2026), nachgeschlagen 26.09.2026. Jeder `## `-Abschnitt steht fuer sich
und darf einzeln ausgeschnitten werden. Form: Regel -> Bedingung -> Grund. Zahlen mit Quelle, wo sie
mit Patches wandern; `[ungeprueft]` = aus Erfahrungswissen vor 2026, nicht gegen 2026 geprueft;
`[Schaetzung]` = abgeleitet. Was 2026 neu ist: `saison2026.md`.
Quellen (alle 26.09.2026): Patchnotes 26.1 / 26.9 / 26.15 / 26.19 (leagueoflegends.com), Wiki-Seiten
Minion, Turret, Role_Quests, Teleport, Unleashed_Teleport, Summoner_spell, Crystalline_Overgrowth,
Champion_gold_bounties, Dragon (wiki.leagueoflegends.com), Data Dragon 16.19.1 (Itempreise).

## Zeitleiste

Spielzeit -> Ereignis (Quelle: Patch 26.1, Wiki Minion, objektive.toml):
- 0:30 erste Welle (frueher 1:05). Treffen in der Lane: Mid ~0:50, Top/Bot ~0:55-1:00 [Schaetzung].
- 0:30 passives Gold beginnt.
- 0:55 Buffs, Woelfe, Raptoren; 1:07 Krugs, Gromp. Wiederkehr: Camps 2:15, Buffs 5:00 [ungeprueft].
- 1:30 erste Kanonenwelle (Welle 3). Bis 14:00 jede 3. Welle = alle 1:30 (1:30, 3:00, 4:30, 6:00,
  7:30, 9:00, 10:30, 12:00, 13:30).
- 1:40 Kristall-Aufwuchs (Crystalline Overgrowth) auf Tuermen aktiv.
- ~2:00-2:15 fruehester Level-3-Gank; 2:55 Scuttle (beide Seiten).
- 5:00 erster Drache, danach 5:00 nach jedem Kill.
- 8:00 Leerenlarven (3 Stueck, einmalig), weg um 14:45.
- 10:00 Teleport wird fuer alle zu Unleashed Teleport.
- 11:00 Plattengold sinkt 10 g/min (120 -> 80 ab 15:00); Aussenturm verliert 15 Ruestung/MR pro min
  (ab 15:00 bei 0 Bonus).
- spaetestens 13:35 Top-Rollenquest fertig (passiv); Mid/Bot spaetestens 15:08.
- 14:00 Wellen alle 25 s statt 30 s; Kanone jede 2. Welle; Kanonenwellen 1 Nahkaempfer weniger.
  Heimweg-Tempo (Homeguard) steigt von 80 % auf 150 %.
- 15:00 Herold, weg 19:45. 20:00 Baron (Respawn 6:00 [ungeprueft]).
- 25:00 Kanone in jeder Welle. 30:00 Wellen alle 20 s, 1 Fernkaempfer weniger.
- Aeltester: 5:00 nach dem Seelen-Drachen, Respawn 6:00. Nexustuerme: Respawn mit 40 % HP (Patch 26.1).
  Inhibitor-Respawn: objektive.toml 5:00, Wiki-Auszug nannte 3:00 [Widerspruch, ungeprueft].

## Wellenmanagement

**Welle lesen.** Zaehle beide Seiten (Kanone ~ 2 Nahkaempfer an Wert und Haltbarkeit). Die Welle
laeuft zur Seite mit WENIGER Vasallen. Unterschied 1-2 = langsames Wandern, 4+ = schneller Push,
6+ auf einer Seite = "grosse Welle" (stapelt, crasht). Fernkaempfer sterben zuerst, Nahkaempfer
tanken. Richtung ueber Zeit: wo trafen sich die letzten zwei Wellen? Verschiebt sich der Treffpunkt
zu dir, pusht der Gegner.

**Wert einer Welle:** 3 Nahkaempfer (je ~20 g) + 3 Fernkaempfer (je ~14 g) + ggf. Kanone (50-69 g),
115-148 g pro Welle (Wiki Minion). Eine verpasste Welle = ~1/3 Level XP in der fruehen Lane.

**Freeze (einfrieren).** Ziel: Welle steht knapp VOR deiner Turmreichweite, Gegner muss weit nach vorn
(gankbar, ohne Schutz) zum Farmen. Voraussetzung: gegnerische Welle hat 3-4 Vasallen mehr als deine
(sonst wandert sie weiter). Halten: nur Last Hits, nichts antippen; wenn deine Verstaerkung ankommt
und die Zahl kippt, gegnerische Vasallen NICHT toeten, sondern deren Aggro ziehen (einen Gegner-Vasall
anhauen und zurueckgehen), damit die Welle zurueckwandert. Nie IN Turmreichweite freezen - der Turm
toetet Vasallen und bricht den Freeze. Wann: du bist vorn und willst den Gegner verhungern lassen;
Gegner hat kein Flash/keinen Jungler in der Naehe; du bist hinten und willst sicher farmen (Freeze
vor eigenem Turm). Wann nicht: Drache/Herold in <60 s (Freeze bindet dich an die Lane), Gegner-Jungler
auf deiner Seite gesehen und du stehst im Freeze-Punkt ohne Ward. Freeze bricht, wenn der Gegner mit
Jungler kommt oder mit starkem Waveclear die eigene Welle abraeumt -> dann auf slow push umschalten.

**Slow push (stapeln).** Ziel: 2-3 Wellen zu einer grossen Welle bauen, die dann crasht. Technik:
gegnerische Fernkaempfer toeten (die hinterste Reihe), Nahkaempfer nur last-hitten -> deine Welle hat
2-3 Vasallen Ueberschuss und waechst jede Welle. Beginn: direkt NACH einer Kanonenwelle; Crash auf der
naechsten Kanonenwelle (3 Wellen = 1:30 bis 14:00, danach 2 Wellen = 50 s). Nutzen: Zeit fuer Recall,
Roam, Objective, Platten; der Gegner verliert CS oder Platten, wenn er nicht bleibt. Wann: vor Drache/
Herold, vor Recall mit Vorlauf, wenn der Gegner-Jungler weit weg ist.

**Fast push / Crash.** Alles so schnell wie moeglich toeten, Welle in den gegnerischen Turm. Wann:
sofort Recall/Roam/TP noetig, Gegner-Welle klein, oder um die naechste Welle zurueckprallen zu lassen.
Nachteil: du stehst vorn und bist gankbar; nur mit Sicht oder bekanntem Jungler-Standort.

**Bounce.** Nach einem Crash toetet der Gegnerturm deine Vasallen; die naechste gegnerische Welle
trifft dann auf DEINE kleinere Welle und wandert zu dir zurueck (1-2 Wellen spaeter). Nutzen: crashen,
recallen - die Welle kommt dir entgegen, du verlierst nichts. Kanonenwelle crashen verlaengert den
Abbau unter dem Turm und damit dein Zeitfenster.

**Cheater Recall.** Grosse Welle in den Gegnerturm druecken; der Gegner MUSS unter dem Turm farmen,
du recallst sofort und verlierst hoechstens eine halbe Welle. Alternative: recallen, wenn beide Wellen
gerade leer sind. Nie recallen, wenn eine grosse Gegnerwelle auf deinen Turm zulaeuft (der Turm frisst
dein Gold, der Gegner kann Platten schlagen).

**Welle vor Recall / Objective / Roam.** Recall: crash oder Cheater Recall; wenn du hinten bist,
recall wenn die Gegnerwelle klein ist. Objective: 45-60 s vorher slow push starten, 20-30 s vorher
crashen -> der Gegner-Laner muss waehlen: CS/Platten verlieren oder spaet zum Objective. Roam: erst
crashen, sonst verlierst du Welle + Platten fuer einen Roam, der auch scheitern kann.

**Welle unter dem eigenen Turm (Last Hits).** Faustregel [ungeprueft 2026; Wiki-Werte vor 2026:
Aussenturm 45 % Max-HP an Nahkaempfer, 70 % an Fernkaempfer, 14 % an Kanone]: Nahkaempfer = 2
Turmschuesse + 1 Auto. Fernkaempfer = 1 Auto, dann Turmschuss, dann Last Hit (bei hohem AD: Turmschuss
+ Auto). Kanone ~7 Turmschuesse, am Ende mit Faehigkeit sichern. Wenn der Turm schon auf einen
Vasallen schiesst, den naechsten vorbereiten.

**Welle unter dem Gegnerturm.** Plattenzeit: eigene Vasallen tanken den Turm -> Platten schlagen,
solange 3+ eigene Vasallen stehen. Der Kristall-Aufwuchs (siehe saison2026.md) gibt dem ERSTEN
Champion-Treffer nach langer Ruhe Bonus-Echtschaden - einen lange nicht angefassten Turm immer selbst
zuerst anhauen. Bei Turmfokus sofort raus (Aufwaermen: +50 % Schaden je Treffer, bis +150 %; Wiki).

**Nach 14:00.** Wellen alle 25 s -> Stapel wachsen schneller, Seitenlanes muessen oefter abgeholt
werden. Eine Seitenwelle, die 2-3 Wellen ungestoert laeuft, nimmt Platten/Turm allein an.

## Recall und Gold

**Recall-Fenster (erster Back).** Bester Zeitpunkt: nach einem Crash (Welle prallt zurueck), mit
Gold fuer eine volle Komponente, oder bei wenig Leben/Mana, bevor der Gegner dich dazu zwingt.
Typisch Top: erster Back 3:30-5:30 [Schaetzung] mit 900-1300 g. Recall-Kanal 8 s [ungeprueft],
Heimweg-Tempo (Homeguard) vor 14:00 +80 % abfallend auf +40 % ueber 4 s; ab 14:00 +150 % -> +65 %;
endet bei Kampf, Jungle-Betreten, Objective-Naehe (Patch 26.1).

**Gold-Schwellen (Data Dragon 16.19.1, Preis gesamt).**
- Basis: Langschwert 350, Ampl.-Folio 400, Rubinkristall 400, Stoffpanzer 300, Null-Magie-Mantel 400,
  Leuchtender Staub (Glowing Mote) 250, Dolch 250, Stiefel 300, Kontrollward 75, Heiltrank 50.
- AD-Komponenten: Spitzhacke (Pickaxe) 875, Caulfields Kriegshammer 1050 (20 AD, 10 Tempo), Gezackter
  Dolch (Serrated Dirk) 1000 (20 AD, 10 Letalitaet), Brutalizer 1337, Tiamat 1200, Phage 1100 (15 AD,
  200 HP), Tunneler 1150 (15 AD, 250 HP), Steel Sigil 1100 (15 AD, 30 Rue), Hearthbound Axe 1200,
  Sheen 900, Kindlegem 800, B.F.-Schwert 1300, Letztes Fluestern 1450.
- Verteidigung: Kettenweste 800, Negatronmantel 850, Riesengurt 900, Wardens Mail 1000, Bramble 800,
  Spectre's Cowl 1250, Hexdrinker 1300.
- Stiefel Stufe 2: Ionische Stiefel 900, Berserker 1100, Stahlkappen 1200, Merkurs 1250.
- Fertige Kampfgegenstaende Top: Profane Hydra 2850, Hubris 2800, Eclipse 2900, Black Cleaver 3000,
  Sundered Sky 3100, Steraks 3200, Deaths Dance 3300, Serylda 3000 (Build selbst: Champion-Wissensbasis).
Regel: Recall mit Gold fuer die naechste Komponente, die den Trade veraendert (z. B. Tiamat fuer
Waveclear, Kettenweste gegen AD-Laner). Unter ~500 g nur recallen, wenn Leben/Mana es erzwingt.
Ueber ~1500 g ungenutzt in der Lane = Verlust; ueber 2500 g = sofort nach Crash zurueck.

**Rueckweg und Tempo.** Nach dem Back: der Rueckweg dauert ~1 Welle [Schaetzung]; plane so, dass du
ankommst, wenn die zurueckprallende Welle deinen Turm erreicht. Wer zuerst zurueck ist, hat Prio -
er kann pushen und die naechste Aktion waehlen (Roam, Scuttle, Drache). Gleichzeitiger Back beider
Laner = neutral; hat der Gegner eine grosse Welle auf dich zulaufen, verliert er nichts.

**Tempo-Regeln.**
- Recall 60-90 s vor einem Objective (Drache, Herold, Baron), nicht 20 s davor.
- Nach einem Kill/Solo-Kill: Welle crashen, Platten, dann recallen - nicht mit Gold in der Lane
  stehen bleiben.
- Nach einem Tod: kein panischer Rueckweg in eine grosse Gegnerwelle unter Turm; erst farmen, was der
  Turm uebrig laesst.
- Kontrollward bei jedem Back mitnehmen, wenn ein Slot frei ist (Support nach Quest: 40 g).

## Lane-Phase und Trading

**Level-Spikes.** Solo-Lane: Level 2 = Welle 1 + 1 Nahkaempfer von Welle 2; Level 3 = Wellen 1+2 +
2 Nahkaempfer von Welle 3 (XP-Rechnung mit Vor-2026-Werten, Solo-XP 2026 +5 % -> eher frueher)
[Schaetzung]. Wer zuerst Level 2 hat, gewinnt den ersten Trade: in Welle 1 Fernkaempfer anhauen, um
schneller zu werden; den Gegner-Level-2 im Blick behalten (Levelanzeige, erster Punkt in einer
Faehigkeit). Level 3, 6, 9 (2. Ult-Rang ab 11) und fertige Komponenten = Fenster fuer Kills.

**Trading-Fenster.**
- Gegner hat gerade eine Schluessel-Faehigkeit benutzt (Dash, Schild, CC): Fenster = deren Cooldown.
  Handeln, bevor sie zurueck ist, und rausgehen, wenn sie zurueckkommt.
- Gegner macht einen Last Hit (Animation) -> kurzer Trade.
- Gegner-Welle kleiner als deine -> Vasallen-Aggro trifft ihn, nicht dich.
- Eigene Welle kleiner -> nicht traden, 3+ gegnerische Vasallen machen frueh ~20-40 Schaden pro Sekunde
  zusaetzlich [Schaetzung].
- Kurzer Trade (Faehigkeit + 1-2 Autos, raus) gegen Gegner mit starkem All-in-Level; All-in nur, wenn
  Schaden inkl. Zuenden reicht und Flash-Stand bekannt ist.

**Vasallen-Aggro.** Wer einem Gegner-Champion mit Auto oder Faehigkeit Schaden macht, zieht die Aggro
naher gegnerischer Vasallen (~500 Einheiten Erfassung; bei angegriffenem Verbuendeten 1000; Wiki
Minion). Aggro loesen: raus aus Reichweite oder ins Bueschel. Trades daher am Rand der Welle oder wenn
die Gegnerwelle fast leer ist.

**Turmschaden.** Aussenturm 182-350 pro Schuss je nach Minute, +50 % je Folgetreffer bis +150 %,
Reset nach 5 s ohne Champion-Treffer (Wiki Turret). Dive-Regel: nur wenn Kill sicher UND ein Tank/
der Vasallenstand die Turmschuesse traegt; der Taucher nimmt 2-3 Schuesse = frueh halbes Leben.

**Zuenden / Flash-Fenster.** Gegner ohne Flash: 300 s Fenster (mit Summoner-Haste kuerzer, siehe
Beschwoererzauber). Zuenden 180 s. Nach gegnerischem Flash: sofort ansagen, All-in-Chance fuer
Laner und Jungler. Eigenes Zuenden fuer Kill-Schwelle aufheben, nicht in Trades verschwenden.

**Jungler-Tracking.** Startseite: wo war er bei 0:55-1:10 (Leash, Sicht Level 1)? Faustregel 2026
[Schaetzung aus Patch 26.1-Spawns und Guides 2026, dodge.gg/boostroom]: 3 Camps fertig ~1:55-2:10,
6 Camps / Full Clear ~2:55-3:15, Scuttle 2:55.
- Start auf der Seite GEGENUEBER deiner Lane (z. B. Bot-Buff fuer eine Top-Gefahr): 3 Camps enden
  bei dir -> Level-3-Gank 2:00-2:30.
- Start auf DEINER Seite: Full Clear endet auf der anderen Seite ~3:00, Scuttle dort; du bist
  sicher bis ~3:30, dann Rueckweg oder Back.
- Gesehen am anderen Ende der Karte = 30-40 s Sicherheit fuer dich [Schaetzung].
- Nach Recall kommt er meist von der Seite, auf der er zuerst farmt; Camp-Wiederkehr 2:15 nach Kill.
- Vasallenwelle stark auf deiner Seite + Jungler fehlt = Freeze-Gank-Gefahr: nicht nach vorne.

**Sicht in der Lane.** Top: erstes Ward ~2:30-2:45 (vor Level-3-Gank) in Flussbueschel oder
Tri-Bush, je nachdem, von wo der Jungler kommt; zweites Ward ~5:00 (Drache/Scuttle-Wechsel).
Bueschel an der Lane: wer im Lane-Bueschel steht, verliert keine Aggro-Pruefung, aber nimmt dem
Gegner die Sicht fuer Skillshots. Ward im gegnerischen Lane-Bueschel nur bei Bedarf (Freeze gegen dich).

## Top-Lane im Detail

**Rollenquest Top (Wiki Role_Quests, Patch 26.9/26.12/26.19).** 1200 Punkte: Vasall 2 (in Lane),
Platte 40, Turm 50, Takedown 15, Epic 30; passiv 7,5 Pkt/5 s in der Lane. Spaetestens 13:35 fertig,
mit gutem Farm und Platten frueher (typisch 10-12 min [Schaetzung]). 12 s nach Recall keine
Passivpunkte; 120 s in der Lane geben 60 s Roam-Schonfrist; ausserhalb der Lane weniger Punkte.
Belohnung: +600 XP sofort, +11 % XP, +80 XP je Takedown, Level-Cap 20. Mit Teleport: TP wird
verstaerkt (Cooldown 300-210 s, Stand 26.19; Schild 35 % Max-HP fuer 10 s nach vollendetem Kanal).
Ohne Teleport (z. B. Flash+Zuenden): zusaetzliches Unleashed Teleport im Quest-Slot, Cooldown 390 s.
Konsequenz: JEDER Top hat ab Quest-Ende TP. Coach-Regel: Quest-Ende ansagen, weil sich ab da die
Karte oeffnet ("ab jetzt hast du TP fuer Drache").

**Teleport-Nutzung.**
- Kanal 3 s + Flug 0,5-4 s (Unleashed) -> der Kampf muss 5-7 s spaeter noch laufen. Nicht in einen
  Kampf teleportieren, der schon gekippt oder vorbei ist.
- Vor TP zum Drachen: eigene Welle crashen, sonst verlierst du Welle und Platten. Kein Crash moeglich
  -> TP nur, wenn der Kampf ein Objective oder 2+ Kills entscheidet.
- Ziel: Ward/Vasall HINTER dem Gegner (Flanke) > Turm (sicher, aber langsam). Flanke nur, wenn die
  Gegner nicht auf das Ward zurueckfallen koennen.
- TP-Vorteil: hast du TP und der Gegner-Top nicht (oder seiner ist auf Cooldown), sind Bot-Kaempfe 5v4
  -> ansagen, Team zum Drachen draengen.
- TP zurueck in die Lane nur fuer eine grosse Welle oder Platten, nicht fuer eine normale Welle, wenn
  das TP 60 s spaeter fuer den Drachen gebraucht wird.

**Herold/Larven-Prio.** Larven 8:00 (3 Stueck, einmalig bis 14:45; Gold nur an den Killer). Top-Prio
(Welle gepusht) 30-45 s vor 8:00 -> du hilfst dem Jungler, der Gegner-Top verliert CS. Herold ab
15:00: Auge fuer Ramme gegen Tuerme (3000 Schaden am Turm, Patch 26.1). Sinnvoll auf die Lane, wo
der Turm mit Platten noch steht oder zur Mitte fuer Tempo. Top verliert Prio gegen Drachen-Wechsel:
Drache bot genommen -> Top mit Jungler Larven/Herold (Cross-Map).

**Splitpush vs. Gruppe.** Siehe Abschnitt Splitpush. Kurz: Top splittet, wenn er jeden Gegner 1v1
schlaegt, TP hat und das Team 4v5 halten oder abgeben kann; sonst gruppieren und Seitenwellen nur
zwischen Objectives abholen.

**Seitenwelle.** Mitte-/Spaetspiel: die Top-Welle nie laenger als 2 Wellen unbeachtet lassen, wenn
kein Objective ansteht. Vor Objective: Top-Welle 60 s vorher crashen, dann ueber den Fluss zum Team.

**Melee-Top (z. B. Riven).** Gegen Fernkampf-Top: Freeze vor dem eigenen Turm, Trades nur ueber
Faehigkeiten-Engage, wenn der Gegner Last Hit macht oder Hauptfaehigkeit weg ist; Level 3 und 6 sind
Kill-Fenster. Gegen Tanks: Platten statt Kills, Welle ausnutzen, Zuenden gegen Heilung.

## Rollen-Aufgaben

**Top.** Frueh: Lane gewinnen oder sicher farmen, Quest bis ~12 min, Jungler bei Larven (8:00)
decken. Mitte: TP fuer Drachenkaempfe, Herold (15:00), Seitenwelle top halten, Platten (Gold bleibt
bis Turmfall, 80 g ab 15:00). Spaet: Splitpush oder Frontlinie/Flanke im Teamfight; Baron-Seite
kontrollieren.

**Jungle.** Frueh: Clear + Level-3-Gank oder Full Clear -> Scuttle 2:55, Drache 5:00, Larven 8:00;
Gegner-Jungler auf der Gegenseite tauschen. Quest: 35 Treats (Primal Smite, +10 g/+10 XP je Camp, +4 %
Tempo im Jungle/Fluss, +8 % ausser Kampf). Mitte: Objective-Timer fuehren, Sicht um die naechste
Grube. Spaet: Smite-Duell bei Baron/Aeltester; nie ohne Smite zu Objectives.

**Mid.** Frueh: Prio fuer Scuttle und Drachen, Roams nach Crash. Quest 1350 Pkt (spaetestens 15:08):
Stiefel Stufe 3 kostenlos, +8 % Bonus-AD/AP (Patch 26.11). Frueh 25 % weniger Vasallen-Gold/XP bis
Level 3 (Quest-Malus). Mitte: Welle schieben, Fluss kontrollieren, mit Jungler zu jedem Objective.
Spaet: Mitte halten, Sicht-Setup vor Baron/Aeltester.

**ADC (Bot).** Frueh: farmen, Level 2 mit Support erzwingen/abwehren, Platten. Quest 1350 Pkt:
+300 g, +2 g je Vasall, +40 g je Takedown, Stiefel wandern in den Quest-Slot (7. Gegenstand).
Mitte: Drachen-Seite, sicher farmen auf der Seite mit Sicht, nicht allein auf Seitenlanes ohne Info.
Spaet: Position im Kampf hinter der Frontlinie, erst den naechsten sicheren Gegner schlagen.

**Support.** Frueh: Level-2-Spike bot, Sicht Fluss/Tri-Bush bot, Roam mid nach Crash. Quest 800 Pkt
ueber World Atlas/Runic Compass -> Stufe-2-Item, Kontrollwards 40 g im Quest-Slot. Mitte: Sicht vor
jedem Objective, Sweeper, Tiefe Sicht bei Vorsprung. Spaet: Engage oder Peel, Sicht um Baron.

**Phasenwechsel (Coach-Satz "was ist ab jetzt mein Job").** Lane-Phase endet praktisch mit dem ersten
Aussenturm oder um 14:00 (Wellentakt 25 s, Homeguard 150 %). Danach: Top/Mid schieben die Seite,
auf der das naechste Objective NICHT liegt, und kommen 45-60 s vorher zusammen.

## Objectives

**Setup (Pflichtreihenfolge).** 60 s vorher: Seitenwellen slow push. 45-30 s: Wellen crashen, Recall
falls noetig, Kontrollwards in und um die Grube. 30-15 s: Gegner-Wards raeumen (Sweeper), Positionen
am Flusseingang. 15-0 s: Zahlen pruefen (wer lebt, wer hat Flash/Ult/Smite). Ohne Welle-Prio auf
Mid UND der naechsten Seitenlane ist ein Objective-Start ein Muenzwurf.

**Zahlen.** Objective beginnen, wenn: Zahlenvorteil (Gegner tot oder weit weg gesehen) ODER gleiche
Zahl mit Prio, Sicht und staerkerem Teamfight. Abgeben, wenn: 1+ Mann weniger, keine Prio, Gegner-
Jungler lebt und steht naeher, oder die eigenen Leute haben wenig Leben (Coach: vor "Baron jetzt"
Leben pruefen).

**Tausch (Cross-Map).** Kann das Team ein Objective nicht bestreiten, auf der anderen Seite gleich-
wertig nehmen: Drache <-> Larven/Herold/Top-Turm; Baron <-> Drache + Bot-Turm; Seelen-Drache nie
tauschen. Wert grob (Patch 26.1): Drache 75 g Killer + Buff; Larven 90 g Killer; Herold 100 g +
Ramme; Baron 850 g + Buff; Aeltester 850 g + Exekution; erster Turm +300 g.

**Drache.** Buffs stapeln, Rache-Buff (Dragon Vengeance) 15/30/45 % Schadensreduktion fuer das
zurueckliegende Team. Nach dem 2. Drachen verwandelt sich die Karte (Elemental Rift). Seele beim 4.
Drachen des eigenen Teams. Steht der Gegner auf Seelen-Punkt (3 Drachen): alles, auch Baron, fuer
diesen Drachen; steht ihr darauf: Kampf erzwingen, Sicht 90 s vorher.

**Aeltester.** 5:00 nach dem Seelen-Drachen. Buff: Exekution unter einer Leben-Schwelle + Schaden
[Werte ungeprueft 2026]. Aeltester schlaegt Baron: bei gleichem Timing zuerst den Aeltesten.
Wer ihn nimmt, sucht sofort den Kampf; wer ihn verliert, verteidigt 2:30 unter Tuermen [Dauer
ungeprueft].

**Baron (ab 20:00).** Starten nach: gewonnenem Kampf mit 2+ Kills, Gegner-Jungler tot oder Smite
bekannt weg, oder Sicht-Kontrolle mit 5 Gegnern gesehen auf der anderen Seite. Nicht starten, wenn
2+ Gegner unsichtbar sind und die eigenen Leute unter 50 % Leben. Baron-Buff = Belagerung: danach
zwei Lanes gleichzeitig mit verstaerkten Vasallen, nicht alle fuenf in eine Lane.

**Herold / Larven.** Larven bei 8:00 fuer Tempo auf der Top-Seite; einmalig. Herold 15:00-19:45,
Auge 6 s Cooldown, Ramme 3000 Schaden an Turm. Mit Plattengold, das bis Turmfall bleibt, lohnt der
Herold auf jede Lane mit hohem Turm.

**Seele.** Schlaegt jede Einzelentscheidung ausser Nexus-Gefahr. Seelen-Punkt des Gegners = das
wichtigste Objective der Karte.

## Sicht

**Werkzeuge (Patch 26.1).** Stealth Ward (Trinket) Cooldown 170-90 s je Level, 2 Ladungen
[Ladungen ungeprueft]. Oracle Lens (Sweeper) 8 s Wirkung. Kontrollward 75 g (Support nach Quest 40 g),
eine pro Spieler auf der Karte [ungeprueft]. Farsight ab Level 9 [ungeprueft]. Faelights: ein Ward
auf einem Faelight-Punkt bekommt +25 % Sichtradius und deckt 45 s eine Bonus-Region auf.
Scryer's Bloom Respawn 200-260 s (90-120 s nach Elemental Rift).

**Faelight-Punkte (Patch 26.1).** 4 an den Basis-Zugaengen des Jungles (Jungle-Sicht), 2 in den
Insel-Bueschen top/bot (Fluss-Sicht), 2 an den Flusswaenden Mitte (Fluss-Sicht), nach Elemental Rift
4 weitere an den Seitenlanes (Jungle-Pfade). Genaue Lage [ungeprueft]. Regel: das erste Ward einer
Phase auf ein Faelight setzen, wenn es den gewuenschten Pfad abdeckt.

**Frueh (0-8 min), Top.**
- Tri-Bush top (Dreier-Bueschel am Top-Aussenturm der roten Seite): deckt den Gank-Weg des roten
  Junglers; fuer Blau-Top = Gegnerseite, fuer Rot-Top = eigene Seite.
- Flussbueschel top (am Baron-Eingang): Weg des Junglers ueber den Fluss.
- Pixel-Bueschel top (kleines Bueschel zwischen Flussbueschel und Lane) [Lagebeschreibung ungeprueft]:
  guenstiger Spot, sieht den Flusszugang zur Lane.
- Erstes Ward vor dem Level-3-Gank (~2:00); zweites nach dem ersten Back.
Bot: Tri-Bush bot (blaue Seite), Flussbueschel bot (am Drachen), Pixel-Bueschel bot.
Mid: beide Flussbueschel neben der Mid-Lane, Raptoren-Eingang.

**Mitte (8-20 min).** Um die naechste Grube: Drache 60 s vorher Kontrollward in Grube/Flussbueschel,
Stealth Wards an den gegnerischen Zugaengen (Tri-Bush bot, Raptoren/Krugs-Eingang der roten bzw.
blauen Seite). Top-Splitpusher: Ward am Gegner-Raptoren- oder Gromp-Eingang seiner Seite, damit
Anlauf 5-8 s frueher sichtbar ist.

**Tiefe Sicht bei Vorsprung.** Wards IN den gegnerischen Jungle: Buff-Camps, Gromp, Krugs, Jungle-
Eingaenge nahe der Gegnerbasis -> du siehst Rotationen, bevor sie den Fluss erreichen. Nur mit Prio
(Wellen gepusht), sonst stirbt der Warder.
**Bei Rueckstand.** Wards im eigenen Jungle an den Engstellen (eigene Raptoren, Blau-Buff-Eingang,
Tri-Bush eigener Seite); nicht in den Fluss ohne Prio.

**Kontrollward-Regeln.** Immer eins auf der Karte. Beste Orte: Flussbueschel vor Objective,
Tri-Bush, Grube (Baron/Drache) 60-90 s vorher. Ein Kontrollward, das niemand raeumt, liefert auch
Info (Gegner hat keine Sicht dort).

**Sweeper.** Vor Objectives und beim Betreten eines Bueschels im Gegnergebiet. Support/Jungler ab
Mitte des Spiels meist mit Sweeper [ungeprueft].

## Teamfight und Kartenzustand

**Zahlen zuerst.** Vor jedem Kampf: lebende Gegner, sichtbare Gegner, wer fehlt seit wann. Fehlt ein
Gegner >10 s und kann er in <10 s da sein, rechne ihn mit. 4v5 ist nur mit Objective-Deckung (Turm)
oder 2+ fehlenden Ults/Flash beim Gegner spielbar.

**Timer, die Kaempfe entscheiden.** Gegner-Flash (300 s), Gegner-Ult (Cooldown je Rang; Champion-
Wissensbasis), Smite, TP, Zhonya/Guardian Angel/Steraks-Stand. Faustregel: fehlt dem Gegner-Engager
Flash ODER Ult, erzwingt dein Team den Kampf; fehlt es deinem Engager, weiche aus. Flash-down-Fenster
bleibt gueltig, auch wenn der Gegner zurueck in der Basis war (Recall setzt keine Cooldowns zurueck).

**Engage / Disengage.** Engagen, wenn: Gegner eng stehen, getrennt (einer seitlich/vorne), CC-Kette
bereit, Zahlen gleich/besser. Abbrechen, wenn: Engage-Tool verfehlt, Kernziel fliehen kann, Gegner
bekommt Verstaerkung (TP-Kanal sichtbar!). Disengage-Team: zurueck ueber die eigene Sicht, Welle als
Puffer.

**Front / Back.** Frontlinie: vorne stehen, Faehigkeiten auf die NAECHSTE Bedrohung, nicht durchlaufen.
Backline: auf den naechsten sicheren Gegner schlagen, Abstand halten. Bruiser/Assassine (Riven):
Flanke, Ziel = gegnerische Backline, wenn deren Flash/Peel weg ist; sonst die gegnerische Frontlinie
stueckweise angehen und auf den Rueckzug der Backline warten.

**Kartenzustand lesen.** Welle-Lage aller drei Lanes: wo gepusht ist, hat dein Team Tempo. Zwei
Wellen auf dich zu + Objective in 60 s = das Team verliert Zeit -> vorher Wellen abholen. Kampf nie
ohne Wellen-Prio suchen, wenn der Gegner Seitenwellen auf dich laufen hat.

**Vision-Control vor Baron.** 90 s vorher: Kontrollwards an Grube und oberem Flussbueschel, Sweeper,
Seitenwellen bot und mid pushen, Team top-seitig. Sieht der Gegner die Grube nicht, kann Baron
schnell gehen; sieht er sie, erst Kampf oder Zonen-Kontrolle.

**Nach dem Kampf.** Gewonnen: sofort in Objective (Baron/Drache/Turm) umsetzen, nicht jagen.
Verloren: Wellen abwehren, Zeit bis Respawn verteidigen; Top nimmt Seitenwelle, wenn er ueberlebt.

## Splitpush

**Wann splitten (alle drei):** 1) du schlaegst jeden einzelnen Gegner, der kommt, oder entkommst
sicher; 2) dein Team kann 4v5 halten (Waveclear, Disengage) oder hat nichts zu verteidigen; 3) kein
eigenes Objective in <60 s. Dazu: TP bereit oder Unleashed-TP-Cooldown bekannt.

**Wann gehen:** 2+ Gegner fehlen und koennen dich in <10 s erreichen; du hast keine Sicht am
Gegnerjungle-Eingang deiner Seite; Objective spawnt in <45 s auf der anderen Seite; deine Welle ist
ueber den Fluss hinaus und der Gegner-Jungler ist unbekannt.

**Wann TP zum Team:** Kampf beginnt am Objective und dein Team hat Zahlen-Gleichstand; du ziehst
die Aufmerksamkeit ohnehin nicht mehr (nur 1 Gegner bei dir). Nicht TP, wenn 2 Gegner zu dir laufen:
dann ist dein Team 4v3 - sag es an ("zwei bei dir, Team soll Objective nehmen").

**Druck-Regel.** Splitpush zwingt Reaktion. Kommt 1 Gegner: 1v1 oder weiter pushen unter Sicht.
Kommen 2+: zurueck, die Seite haelt sie besetzt, Team sucht das Objective.
**Kristall-Aufwuchs.** Ein seit Minuten unberuehrter Seitenturm hat maximale Kristalle (bis 18,9 %
Max-HP Echtschaden beim ersten Treffer auf Level 18) - Splitpush lohnt besonders auf Tuermen, die
niemand angefasst hat.

**1-3-1 / 1-4.** 1-3-1: zwei Seiten-Splitter, drei Mitte - nur mit zwei sicheren Duellanten. 1-4:
Top splittet auf der Seite gegenueber dem naechsten Objective, Team spielt 4 um das Objective.

## Beschwoererzauber

Cooldowns (Wiki Summoner_spell / Teleport / Unleashed_Teleport, Patchnotes 26.19):
- Flash (dt. Blitz) 300 s.
- Zuenden (Ignite) 180 s. Barriere 180 s. Heilen 240 s. Erschoepfung 240 s. Geist 240 s. Reinigen 240 s.
- Zerschmettern (Smite) 90 s pro Ladung laut Wiki-Tabelle [Ladungs-/Cooldownsystem ungeprueft];
  Schaden 600/1000/1400 (Patch 26.1).
- Teleport 300 s bis 10:00; ab 10:00 Unleashed Teleport 330-240 s je Level (Flug 4500 Einh./s,
  0,5-4 s, +50 % Tempo 3 s nach Ankunft). Kanal 3 s.
- Top-Quest: verstaerktes TP 300-210 s (Stand 26.19) mit Schild 35 % Max-HP/10 s; Quest-TP ohne
  eigenes TP 390 s. Die Wiki-Tabelle nennt 420 s fuer "Teleport" - Stand vor 26.19 fuer das Quest-TP;
  Ueberlagerung der Werte [ungeprueft].

**Zauber-Tempo (Summoner Spell Haste).** Cooldown = Basis x 100 / (100 + Haste).
- Kosmische Einsicht (Cosmic Insight, Rune): 18.
- Ionische Stiefel: 10. Crimson Lucidity (Stufe-3-Stiefel, Mid-Quest): 20.
Flash-Timer: 300 s ohne; 254 s mit 18; 273 s mit 10; 234 s mit 28; 217 s mit 38.
Zuenden: 180 / 153 / 164 / 141 / 130 s.
Die Live-API liefert Runen und Items aller Spieler -> Haste des Gegners ist berechenbar.

**Coach-Regeln.**
- Flash-Timer ab Sichtung/Ping starten; ansagen bei 60 s und bei Ablauf ("Flash von X wieder da").
- Kein Flash beim Gegner-Laner: All-in-Fenster fuer Laner + Jungler (Gank ansagen).
- Kein Flash beim eigenen Spieler: Stand weiter hinten, nicht an Wellen-Rand, kein Tri-Bush-Check
  ohne Sicht.
- Beide Summoner des Gegner-Carrys weg = Kampf-Fenster fuer das ganze Team.

## Glossar

Form: Begriff (deutsch / englisch / Spieler-Slang) = Bedeutung. Fuer Spracherkennung und Zuordnung.
- Welle / wave / minion wave = Vasallengruppe. Kanone / cannon / siege minion = Belagerungsvasall.
  Super minion = Supervasall (nach Inhibitor-Fall).
- Einfrieren / freeze / halten = Welle vor dem eigenen Turm halten.
- Langsam pushen / slow push / stacken = Welle aufbauen. Crashen / crash / reindruecken / shoven /
  fast push = Welle in den Turm druecken. Bounce / zurueckprallen = Welle kommt nach Crash zurueck.
- Cheater Recall = Back nach Crash ohne Verlust. Back / recall / zurueck / basen = in die Basis.
- Prio / priority = deine Welle pusht, du darfst zuerst handeln. Tempo = Zeitvorteil fuer Aktionen.
- Reset = Back mit Gold/Leben auffuellen; auch Cooldown-Ruecksetzung durch Kill.
- Gank = Jungler-Angriff auf eine Lane. Dive / tauchen = unter dem Gegnerturm angreifen.
  Roam / roamen = Lane verlassen, um woanders zu helfen. Countergank = Gegenangriff.
- Trade / traden = Schaden austauschen. Short trade / kurzer Trade. All-in = bis zum Tod.
  Poke = Schaden aus Distanz. Zoning / zonen = Gegner von der Welle fernhalten. Sustain = Heilung.
- Spike / Power spike = Stufe/Item, ab der ein Champion deutlich staerker ist.
- Splitpush / splitten = allein auf einer Seitenlane pushen. Seitenwelle / side lane.
  1-3-1, 1-4 = Aufteilung der Spieler. Gruppieren / group / grouping.
- Engage / reingehen = Kampf beginnen. Disengage / rausgehen = Kampf verhindern. Peel = Carry
  schuetzen. Flanke / flank. Frontlinie / frontline, Backline. Kite / kiten = Schlagen im Rueckwaerts-
  gehen.
- Objective / Objekt: Drache / dragon / drake, Aeltester / Elder, Seele / soul, Seelenpunkt / soul
  point, Baron Nashor / Baron / Nash, Herold / Rift Herald / Herald, Leerenlarven / Void Grubs /
  Grubs / Larven, Scuttle / Flusskrebs / Krabbe [dt. Clientname ungeprueft], Aeltester-Buff.
- Jungle-Camps: Blau / blue buff, Rot / red buff, Kroten / Krugs, Raptoren / raptors / Huehner,
  Woelfe / wolves, Gromp.
- Buesche: Tri-Bush / Dreier-Bueschel, Flussbueschel / river bush, Pixel-Bueschel / pixel bush,
  Lane-Bueschel. Faelight = Sichtpunkt 2026.
- Ward / Auge / Sichtstein, Kontrollward / control ward / pink, Sweeper / Oracle Lens / Linse,
  Farsight / blaues Trinket.
- Summoner / Beschwoererzauber: Flash = Blitz, Ignite = Entzuenden, Teleport / TP, Smite =
  Zerschmettern, Exhaust = Erschoepfung, Ghost = Geist, Heal = Heilen, Barrier = Barriere,
  Cleanse = Reinigen [dt. Clientnamen teils ungeprueft; "Blitz" im Chat bestaetigt].
- Platten / plates / Turmplatten, Turm / tower / turret, Inhib / Inhibitor, Nexus.
- CS / Farm / Vasallen-Kills. Last Hit / letzter Schlag. Deny.
- Cooldown / CD / Abklingzeit. Haste / Tempo (Faehigkeits-/Zauber-Tempo). Ult / R.
- Shutdown = Kopfgeld auf einem Spieler im Vorsprung (bis +700 g). Bounty / Kopfgeld.
- Level-Cap 20 (Top-Quest). Rollenquest / role quest.
- Homeguard / Heimwaechter-Tempo = Laufbonus nach Recall.
