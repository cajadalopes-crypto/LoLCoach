# Mechaniken-Lexikon (Nachschlagewerk fuer Coach-Modell und Engine)

Stand: Patch 26.19 (Data Dragon 16.19.1), nachgeschlagen 26.09.2026. Jeder `## `-Abschnitt steht fuer
sich. Form: Regel -> Zahl -> Entscheidung. Q = Quelle, [ungeprueft] = nicht nachgeschlagen/bestaetigt.
Maschinenlesbar: `wissen/mechanik.toml`. Saison-Neuerungen im Detail: `saison2026.md`.
Quellen: wiki.leagueoflegends.com (Experience_(champion), Death, Gold, Champion_gold_bounties, Minion,
Melee/Caster/Siege_minion, Turret, Blue_Sentinel, Red_Brambleback, Crest_of_Insight, Crest_of_Cinders,
Gromp, Murk_Wolf, Crimson_Raptor, Krug_camp, Rift_Scuttler, Smite, Dragon, Dragon_pit, Dragon_Soul,
Aspect_of_the_Dragon, Elder_Dragon, Baron_Nashor, Hand_of_Baron, Rift_Herald, Voidgrub, Armor,
Lethality, Grievous_Wounds, Crowd_control, Cleanse, Quicksilver_Sash, Mercury's_Treads, Boots,
Movement_speed, Summoner_spell, Summoner_spell_haste, Flash, Ignite, Heal, Barrier, Exhaust, Ghost,
Teleport, Ward, Stealth_Ward, Control_Ward, Oracle_Lens); Patchnotes 26.1 (leagueoflegends.com).

## Schaden und Kill-Rechnung

- Ruestung/MR: Schaden x 100/(100+R). 100 R = halber Schaden. Effektives Leben = HP x (1+R/100):
  jeder Punkt R = +1 % EHP. Q: Wiki Armor.
- Negative R: Faktor 2 - 100/(100-R) (bei -20 R: x1,17). Nur Reduktion (flach/%) drueckt unter 0;
  Durchdringung/Letalitaet wirken nicht, wenn R <= 0. Q: Wiki Armor, Lethality.
- Reihenfolge: flache Reduktion -> %-Reduktion -> %-Durchdringung -> flache Durchdringung
  (Letalitaet). Letalitaet = 1:1 flache Rue.-Durchdringung auf jedem Level (seit 14.1).
  Rechnung: R_eff = max(0, R x (1-%Pen) - Letalitaet). Q: Wiki Lethality.
- Echtschaden ignoriert R; Schilde fangen ihn trotzdem ab. [ungeprueft: %-Schadensreduktion wirkt auch]
- Krit: Basis 200 % (seit 26.1). Q: Patch 26.1 (s. saison2026.md).
- Heilungsreduktion (Grievous Wounds): 40 %, alle Quellen gleich, wirkt auf Heilung und
  Regeneration, NICHT auf Schilde. Q: Wiki Grievous_Wounds.
- Zuenden: 70 Echtschaden auf Level 1, +20 je Level bis Level 5 (150), dann +25 je Level ->
  Level 6: 175, 9: 250, 11: 300, 13: 350, 16: 425, 18: 475. Ueber 5 s, 600 Reichweite, 40 % GW,
  von Schadensverstaerkern unbeeinflusst (25.15). Q: Wiki Ignite.
  -> Zuenden bringt nur die volle Zahl, wenn der Gegner 5 s nicht geheilt/zurueckgeholt wird.
- Hinrichtung: Aeltester-Buff richtet unter 20 % Max-HP hin (0,5 s Verzoegerung). Q: Wiki
  Aspect_of_the_Dragon. Champion-/Item-Schwellen [ungeprueft] -> Champion-Lexikon.
- Schilde: werden vor dem Leben abgezogen. Barrier 100-460 fuer 2,5 s (Endwert laut Wiki-Box
  502, uneins), Heal 80-346 (zweiter Heal binnen 35 s nur 50 %). Q: Wiki Barrier, Heal.
- Faustregeln "reicht mein Combo":
  1. Combo nach Mitigation (R_eff) + Zuenden (Level-Wert, nur wenn 5 s Zeit) >= aktuelles Leben
     + moegliches Schild (Barrier-Wert bei gegnerischem Barrier) + Heal x 0,6 bei GW.
  2. Aeltester aktiv: Ziel ist tot bei 20 % Max-HP, nicht bei 0.
  3. Gegner-Flash offen = +400 Weg; ohne Ghost/Flash eigener Seite reicht Nahkampf-Combo selten
     ueber 400 Einheiten hinaus.
  4. Unter dem Gegner-Turm: 182-427 pro Schuss, +50 % je weiterem Schuss -> 2-3 Schuesse sind
     frueh oft schon toedlich (s. Tuerme).

## Erfahrung und Level

- Gesamt-XP je Level (1->18): 0, 280, 660, 1140, 1720, 2400, 3180, 4060, 5040, 6120, 7300, 8580,
  9960, 11440, 13020, 14700, 16480, 18360 (jedes Level +100 mehr als das vorige). Q: Wiki.
- Vasallen-XP (solo / je Kopf zu zweit): Nah 62 / 40,3, Fern 31 / 20,15, Kanone und Super
  75 / 48,75. Q: Patch 26.1, Wiki Minion-Seiten.
- Geteilt (seit 26.1): 100 % allein; Gesamtpool 130 % -> 2: 65 %, 3: 43,3 %, 4: 32,5 %, 5: 26 %
  je Kopf. Reichweite 1500 Einheiten; wer weiter weg ist, bekommt nichts. Q: Wiki V26.01.
  -> Jungler in der Lane zieht dem Laner 35 % der Welle ab. Aussenstehen auf 1500 = Welle verpasst.
- Kill-XP (Level des Opfers 1->18): 42, 114, 144, 174, 204, 234, 308, 392, 486, 590, dann +50 je
  Level (990 auf 18). Geteilt: Pool 66,6 % bis Level 6, 82 % auf 7-8, 90 % ab 9, gleich verteilt.
  Reichweite 1600. Je volles Level Unterschied ueber dem ersten +-20 %, Abzug hoechstens -60 %.
  Q: Wiki Experience_(champion).
  -> Ein Kill auf Level 6+ ist fast eine halbe Welle Vorsprung; ein hoeheres Opfer zahlt mehr.
- Level 2/3 (reine Rechnung aus den Zahlen oben, erste Kanone in Welle 3):
  Top solo: L2 = Welle 1 + 1 Nahkaempfer der 2. (279 XP je Welle, 1 XP zu wenig!), L3 = 2 Wellen
  + 2 Nahkaempfer der 3. Mid (Quest-Malus -25 % bis L3): L2 = Welle 1 + 2 Nah, L3 ~ 3 volle Wellen.
  Bot zu zweit: L2 = Welle 1 + 3 Nah der 2., L3 = 3 Wellen + 2 Nah der 4. Support hat bis L5 -33 %
  (Quest-Malus) -> hinkt hinterher. Uhrzeiten: Top ~1:35-1:45, Bot ~1:55-2:05 [ungeprueft,
  Schaetzung aus Welle 0:30 + 30-s-Takt].
  -> Der Laner, der zuerst L2 hat, hat ein Trade-Fenster; mit dem letzten Nahkaempfer angreifen.
- Solo-XP 2026: Top-Quest +11 % XP und Level-Cap 20 (s. saison2026.md/Rollenquests).

## Gold

- Start 500 g. Passiv 20,4 g je 10 s (122 g/min) ab 1:05. Q: Wiki Gold, Patch 26.1 ("Ambient Gold
  Start Time: 65 seconds"). ACHTUNG: saison2026.md nennt 0:30 - Widerspruch, nicht aufgeloest.
- Vasallen: Nah 20, Fern 14, Kanone 50 +1 je 90-s-Stufe (bis 69), Super [ungeprueft]. Welle
  ohne Kanone 102 g, Schnitt 115-148 g. Q: Patch 26.1, Wiki Minion.
  -> Eine verpasste Kanone = 2,5 Nahkaempfer; eine ganze Welle ~ ein Drittel Kill.
- Kill-Gold nach Level des Opfers: 300 bis L6, dann +10 je Level bis 420 (L18). Minimum 50.
  First Blood +100. Assist: die Haelfte des ausgezahlten Kopfgelds, hoechstens 50 % der Basis,
  frueh auf 50-100 % gekuerzt (nach Spielzeit). Q: Wiki Champion_gold_bounties.
- Kopfgeld: Aufbau 1 je 3 g aus Kills/Assists, 1 je 20 g aus Farm (im Plus), 1 je 7 g (im Minus,
  26.3). Shutdown ab Basis +100, hoechstens Basis +700. Tod durch Turm/Vasall/Monster zahlt nichts
  aus. Abwertung beim Tod 1 je 3,5 g verteilt (26.3). Q: Wiki Champion_gold_bounties.
  -> Shutdown-Traeger nicht in unklare Fights schicken; ein Exekutionstod (Turm) verschenkt
  kein Kopfgeld.
- Objective-Kopfgeld: unterdrueckt Shutdown-Gold des verlierenden Teams; Schwellen und Hoehe
  [ungeprueft].
- Tuerme: Platte 120 g lokal (ab 11:00 -10 g/min, ab 15:00 80 g; Q: Patch 26.1 via saison2026.md),
  5 Platten je Turm = das lokale Turmgold. Global: Aussen 50, Innen 25, Inhibitor 25, Nexus 50.
  Erster Turm +300 g fuer die Beteiligten. Q: Wiki Turret, Patch 26.1.
- Objectives: Drache 75 g; Larve 30 g lokal (90 fuer alle drei); Herold 100 g an den Killer;
  Baron und Aeltester je 850 g gesamt (150 je Spieler + 100 Killer), 3250 XP (650 je Spieler).
  Q: Patch 26.1, Wiki.

## Tod und Wiedereinstieg

- Todeszeit = BRW x (1 + TIF). BRW (Level 1->18): 10, 10, 12, 12, 14, 16, 20, 25, 28, 32,5, 35,
  37,5, 40, 42,5, 45, 47,5, 50, 52,5 s. Q: Wiki Death (keine Aenderung in 25/26 vermerkt).
- TIF nach Spielminute m: bis 15:00 0 %; 15-30: ceil(2(m-15)) x 0,425 %; 30-45: 12,75 % +
  ceil(2(m-30)) x 0,30 %; 45-55: 21,75 % + ceil(2(m-45)) x 1,45 %; Deckel 50 % (ab ~54:30).
  Level 18 nach 55 Minuten: 78,75 s. Q: Wiki Death.
- Beispiele (gerechnet): L6 @10:00 16 s, L9 @20:00 29,2 s (28 x 1,0425), L13 @25:00 43,4 s,
  L16 @30:00 53,6 s, L18 @40:00 62,3 s.
  -> Vor 15:00 kostet ein Tod wenig Zeit, aber Welle+Platten. Ab ~30 min = 50-60 s: ein Pick
  vor Baron/Aeltester ist der Objective. Timer des Gegners + Laufzeit (s. Bewegung) = Fenster.

## Vasallen und Wellen

- Erste Welle 0:30. Takt: bis 14:00 alle 30 s, 14:00-30:00 alle 25 s, ab 30:00 alle 20 s. Q: Wiki
  Minion, Patch 26.1. Welle: 3 Nah + 3 Fern; Kanone in Welle 3, dann bis 14:00 jede 3., bis 25:00
  jede 2., danach jede Welle. Ab 14:00 1 Nah weniger in Kanonenwellen, ab 30:00 1 Fern weniger.
- Super-Vasall: 1 je Lane bei gefallenem Inhibitor dieser Lane, 2 wenn alle drei fallen.
- Tempo: 350 (26.1, vorher 325), steigt nach Minuten auf 375/400/425/450 [Schwellen ungeprueft].
  Seitenlanes (Welle 2 bis 14:00): Starttempo-Bonus +111, faellt ab. Q: Wiki Minion.
- Ankunft/Treffpunkt: Mitte ~0:55-1:00, Seiten ~1:10-1:20 [ungeprueft, Schaetzung].
- Werte (Start -> Maximum): Nah 465 -> 1550 HP, 11 -> 80 AD, Rue. 0 -> 20, 110 Reichweite; Fern
  284 -> 600 HP, 21 -> 125 AD, 550; Kanone 835 -> 5850 HP (laut Wiki), 37,5 -> 126 AD, 300.
  Aufwertung alle 90 s ab 0:30. Vasallen machen 60 % Schaden an Champions/Gebaeuden. Q: Wiki.
- Turmschaden an Vasallen (% Max-HP je Schuss): Nah 45 % (3 Schuesse), Fern 70 % (2), Kanone
  14/11/8 % (Aussen/Innen/Inhib+; 8/10/13 Schuesse), Super 5 %. Q: Wiki Turret/Siege_minion.
  -> Unterm Turm: Nahkaempfer nach 2 Turmschuessen mit einem Treffer farmen (10 % Rest), Fernkaempfer
  vor dem Turmschuss antippen (nach 1 Schuss 30 % Rest).

## Tuerme

- Leben: Aussen 9000, Innen 5000, Inhibitor 4750, Nexus 3500 (26.1 stark erhoeht). Rue./MR 60.
  Q: Patch 26.1, Wiki Turret.
- Schaden an Champions: Aussen 182, +12/min bis 350; Innen/Inhib 187, ab 3:00 +16/min bis 427
  (17:00); Nexus 165 -> 405. Aufwaermen: +50 % je weiterem Treffer auf Champions, bis +150 %,
  Reset 5 s nach dem letzten Treffer, nicht beim Zielwechsel. Reichweite 750. Q: Wiki Turret.
  -> Unter dem Turm tauchen: der Tank nimmt die ersten 2-3 Schuesse, dann Zielwechsel ueber
  Reichweite 750 hinaus, sonst stapelt der Schaden weiter.
- Befestigung: bis 5:00 50 % Schadensreduktion. Nahkampf-Champions +20 % Schaden an Tuermen (26.1).
- Platten 2026: 5 je Turm (auch Innen/Inhib/Nexus) als Leben-Schwellen 10/25/45/70/100 % fehlend,
  120 g, fallen NICHT mehr um 14:00. Q: Patch 26.1.
- Kristall-Aufwuchs: an unberuehrten Lane-Tuermen nach 90 s (Wiki; saison2026.md: 1:40) 60 s
  Mindestwert, dann 240 s linear bis Maximum. Echtschaden 2-3,3 % (L1) bis 8,8-18,9 % (L18) der
  Turm-Max-HP beim naechsten Champion-Treffer. Q: Wiki Turret.
- Respawn: Inhibitor 5:00 (Q: Wiki Inhibitor, objektive.toml). Nexustuerme 3:00 mit 40 % HP.

## Dschungel

| Camp | Erst | Respawn | Gold | XP (Lvl-abh.) | Q |
|---|---|---|---|---|---|
| Blau (Waechter) | 0:55 | 5:00 | 90 | 95-142,5 | Wiki |
| Rot (Brambleback) | 0:55 | 5:00 | 90 | 95-142,5 | Wiki |
| Gromp | 1:07 | 2:15 | 80 | 120-180 | Wiki |
| Woelfe (1+2) | 0:55 | 2:15 | 85 | 80-120 | Wiki |
| Raptoren (1+5) | 0:55 | 2:15 | 75 | 70-105 | Wiki |
| Krugs (8 Einheiten) | 1:07 | 2:15 | 109 | 121-181,5 | Wiki (Summe gerechnet) |
| Scuttle | 2:55 | 2:30 | 55-121 | 100-150 | Wiki |

- Blau (Crest of Insight): 120 s, 10/15/20 Faehigkeitstempo, 5 % Max-Mana +25 je 5 s.
  Rot (Crest of Cinders): 120 s; Angriffe brennen 15-60 Echtschaden ueber 2 s, verlangsamen
  Nahkampf 10/15/25 %, Fernkampf 5/7,5/12,5 % fuer 3 s; ausser Kampf 0,5-3 % Max-HP je 5 s.
  Buff geht an den Toeter ueber. Q: Wiki Crest_of_Insight/Cinders.
- Scuttle: hinterlaesst Tempo-Schrein 90 s, Sicht 525, +30 % Tempo. Q: Wiki Rift_Scuttler.
- Smite: 600 Echtschaden an Monstern; nach 15 Treats Unleashed 1000, nach 35 Primal 1400.
  2 Ladungen, 1 zu Beginn, weitere alle 90 s ab 0:48, 15 s zwischen Einsaetzen. Unleashed/Primal
  auf Champions 80-160 Echtschaden + 20 % Verlangsamung 2 s. Nur Jungle-Rolle in Ranked (25.9).
  Jungle-Quest-Belohnung s. saison2026.md. Q: Wiki Smite, Patch 26.1.
  -> Objective-Smite-Kampf: Primal 1400 gegen Unleashed 1000 = der Primal-Jungler gewinnt
  frueher; Drache/Baron-HP unter Smite-Wert = sofort smiten.
- Clear-Zeiten [ungeprueft, Schaetzung aus Spawnzeiten]: 3 Camps fertig ~2:00-2:15, Full Clear
  ~2:45-3:00 (passt zu Scuttle 2:55). Erstes Gank-Fenster: ~2:15 nach 3 Camps oder ~3:15 nach
  Full Clear + Scuttle.

## Epische Monster

- Drache: 5:00, Respawn 5:00. Arten: Infernal, Berg, Ozean, Wolke, Hextech, Chemtech. 75 g,
  160-400 XP lokal. Elemental Rift (Karte wandelt sich) nach dem 2. Drachen. Q: Wiki Dragon_pit.
- Stapel je Drache (1/2/3/4): Infernal 3/6/9/12 % AD+AP; Berg 5-20 % Rue.+MR; Ozean 2-8 %
  fehlendes Leben je 5 s; Wolke 5-20 % Verlangsamungsresistenz + Tempo ausser Kampf; Hextech
  5-20 Faehigkeitstempo + 5-20 % Angriffstempo; Chemtech 6-24 % Zaehigkeit + Heil-/Schildstaerke.
  Q: Wiki Dragon_Soul.
- Seelen (4. Drache): Infernal Explosion 100 + Skalierung; Berg Schild 220 +; Ozean Heilung 150 +
  100 Mana; Wolke +15 % Tempo, 60 % nach Ulti; Hextech 25-53 Echtschaden + Verlangsamung; Chemtech
  13 % mehr Schaden/weniger Schaden unter 50 % HP. Details der Skalierung [ungeprueft]. Q: Wiki.
- Rache (Dragon Vengeance): der Drache nimmt 15 % weniger Schaden je Drachen-Stapel des
  angreifenden Teams (bis 45-60 %, Quellen uneins). Q: Patch 26.1, Wiki.
  -> Das Team mit mehr Drachen braucht laenger fuer den naechsten: Contest-Fenster fuer den Gegner.
- Aeltester: nach der Seele 5:00, dann 6:00. Buff 150 s: Brand 75-225 Echtschaden ueber 2,25 s,
  Hinrichtung unter 20 % Max-HP. 850 g/3250 XP gesamt. Q: Wiki Aspect_of_the_Dragon, Patch 26.1.
- Baron: 20:00 (26.1, vorher 25:00), Respawn 6:00. Hand of Baron 180 s: 12-48 Bonus-AD und
  20-80 AP (nach Minute), Recall halb so lang, Vasallen-Aura: Nah/Fern 50-70 % weniger Schaden
  von Champions, Kanone +750 Reichweite gegen Gebaeude, Super +25 % Angriffstempo. 850 g/3250 XP.
  Q: Wiki Hand_of_Baron, Baron_Nashor.
- Herold: 15:00, verschwindet 19:45. 100 g Killer, 240 XP. Auge: Rammstoss 3000 Echtschaden am
  Turm, jeder weitere schwaecher. Q: Wiki Rift_Herald.
- Leerenlarven: 8:00, 3 Stueck, einmal, verschwinden 14:45. 30 g lokal, 65 XP je Larve. Je Larve
  ein Stapel: gegen Gebaeude 4-24 (Nah) / 3-18 (Fern) Echtschaden je 0,5 s ueber 4 s; ab 3 Stapeln
  Leerenmilben beim Turmangriff (15 s Abklingzeit). Q: Wiki Voidgrub.
- Entfernt seit 26.1: Atakhan, Blood Roses, Feats of Strength, Leeren-Verwandlung von Blau/Rot bei
  Baron-Spawn. Q: Patch 26.1, Wiki.

## Bewegung

- Grundtempo Champions 325 (Anivia) bis 355 (Master Yi). Q: Wiki Movement_speed.
- Weiche Obergrenze: 415-490 -> x0,8 + 83; ueber 490 -> x0,5 + 230. Unter 220 -> 110 + x0,5.
- Verlangsamung: nur die staerkste zaehlt, weitere werden ignoriert. Verlangsamungsresistenz
  multipliziert (50 % Resistenz: 40 % -> 20 %). Q: Wiki Movement_speed.
- Stiefel: Stufe 1 +25 (300 g); Stufe 2 +45 (Swiftness +55, 25 % Verlangsamungsresistenz);
  Stufe 3 +45, Swiftmarch +65 - nur ueber die Mid-Quest. Mercury's 30 % Zaehigkeit, Ionian 10
  Beschwoerertempo. Q: Wiki Boots/Mercury's_Treads, Patch 26.1.
- Homeguard ohne feste Dauer: vor 14:00 +80 % -> +40 %, danach +150 % -> +65 % (ueber 4 s).
  Endet bei Kampf/Jungle/Objectives. Q: Patch 26.1.
- Flash: 400 Einheiten, 300 s. Ghost: 24-50,8 % fuer 10 s, ohne Kollision. Q: Wiki.
- Laufzeiten Basis -> Lane (mit Homeguard, Stiefel 1) [ungeprueft, Richtwerte]: Mitte-Turm ~18 s,
  Aussenturm Top/Bot ~25-30 s, Flussmitte ~25 s. -> Recall 8 s + Laufweg = Abwesenheit ~35 s.

## Kontrolle und Gegenmittel

- Hart (unbeweglich): Hochgeschleudert, Bezaubern/Spotten/Furcht/Berserk, Festhalten, Schlaf,
  Stasis, Betaeubung, Unterdrueckung. Weich: Blind, Verkrueppeln, Entwaffnen, Erden, Kurzsicht,
  Polymorph, Verlangsamung, Schlaefrig. Q: Wiki Crowd_control.
- Zaehigkeit kuerzt NICHT: Hochgeschleudert, Stasis, Unterdrueckung, Erden, Schlaefrig, Kurzsicht,
  Kinematik. -> Gegen Knock-ups hilft nur Stellung, nicht Mercury's.
- Reinigen (Cleanse): 240 s, entfernt fast alles plus Zuenden/Erschoepfung, nicht:
  Hochgeschleudert, Kurzsicht, Unterdrueckung (und unter Unterdrueckung/Stasis nicht nutzbar);
  danach 75 % Zaehigkeit fuer 3 s. Q: Wiki Cleanse.
- Quecksilberschaerpe (QSS): 1300 g, 30 MR, 90 s, entfernt alles ausser Hochgeschleudert (auch
  Unterdrueckung, Kurzsicht). Q: Wiki Quicksilver_Sash.
  -> Gegen Unterdrueckung (Malzahar/Skarner/Warwick-Typ) QSS, nicht Cleanse.
- Mercury's Treads: 30 % Zaehigkeit, 20 MR, 45 Tempo, 1250 g. Q: Wiki.
- Unanvisierbar: nicht als Ziel waehlbar (Flaechen treffen je nach Effekt [ungeprueft]).
  Unverwundbar: nimmt keinen Schaden. Zauberschild: blockt eine Faehigkeit komplett inkl. CC.
  -> Zauberschild zuerst mit einer billigen Faehigkeit brechen, dann die Kontrolle.

## Beschwoererzauber 2026

| Zauber | Abklingzeit | Wirkung | Q |
|---|---|---|---|
| Flash | 300 s | Sprung 400 | Wiki |
| Zuenden | 180 s | 70-475 Echtschaden/5 s, 40 % GW, 600 Reichweite | Wiki |
| Heilen | 240 s | 80-346 fuer sich + 1 Verbuendeten, +30 % Tempo 1 s | Wiki |
| Barriere | 180 s | Schild 100-460 fuer 2,5 s | Wiki |
| Erschoepfung | 240 s | 40 % langsamer, -35 % Schaden, 3 s, 650 Reichweite | Wiki |
| Reinigen | 240 s | CC weg + 75 % Zaehigkeit 3 s | Wiki |
| Geist | 240 s | +24-50,8 % Tempo 10 s, ohne Kollision | Wiki |
| Teleport | 300 s | 3 s Kanal, Ziel Turm/Vasall/Ward; ab 10:00 Unleashed (+50 % Tempo 3 s) | Wiki |
| Smite | 90 s je Ladung | s. Dschungel | Wiki |

- Unleashed-TP-Abklingzeit 330-240 s [ungeprueft, Wiki-Zeile von 13.10]. Top-Quest-TP s.
  saison2026.md.
- Beschwoerertempo: CD x 100/(100+Tempo). Ionian Boots 10, Crimson Lucidity 20, Cosmic Insight 18.
  Flash mit 28 Tempo: 234 s. Q: Wiki Summoner_spell_haste.
  -> Flash-Timer notieren: 5 Minuten (300 s) ohne Tempo; mit Ionian + Cosmic knapp 4 Minuten.

## Sicht

- Stealth Ward (Trinket): lebt 90-120 s (Durchschnittslevel), 2 Ladungen, Aufladung 210-90 s
  (26.03 wieder erhoeht; 26.1 hatte 170-90), hoechstens 3 gelegt, 3 Treffer, Sicht 900, 10 g beim
  Zerstoeren. Q: Wiki Stealth_Ward.
- Kontrollward: 75 g, 2 im Inventar, 1 gelegt, 4 Treffer (heilt nach 6 s ohne Schaden), Sicht 900,
  deckt auf und schaltet feindliche Wards ab. Support startet damit im Quest-Slot (26.3). Q: Wiki.
- Farsight: Sicht 500, 1 Treffer, unbegrenzt. Q: Wiki Ward.
- Oracle Lens (Sweeper): 8 s (26.1, vorher 6), 2 Ladungen, 160-100 s Aufladung, Radius 600-750.
  Q: Wiki Oracle_Lens.
- Faelights 2026 (Ward darauf = +25 % Sicht, 45 s Bonus-Region): s. saison2026.md, wards.toml.
- Buesche: wer drin steht, ist unsichtbar fuer Gegner ohne Sicht im Busch [ungeprueft,
  Grundregel]. -> Vor einem Facecheck Sweeper/Ward, nicht den Carry schicken.
