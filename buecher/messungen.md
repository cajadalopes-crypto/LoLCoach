# Messungen zum Umbau (Buch 0)

Je Schritt: was umgesetzt ist, die Abnahme-Zahlen, Abweichungen vom Buch. Neueste oben.

---

## Nachtrag zu Schritt 3 – Wellen-Wahrnehmung (27.09.2026)

Auftrag Carlos: kein Umbau am Kern; `welle.py` nur Icon und Ring ausblenden, Minimap-Ausschnitte der letzten drei
Partien behalten, `1315` auch OBJECTIVE erlauben, Eichung (Buch 1, 1.4) an der nächsten echten Partie wiederholen.

- **Icon und Ring statt Raute** (`welle.py`): Der Ring eines Champion-Icons liegt bei 30–33 px (Icon-Radius 32 px,
  764-px-Minimap; gemessen an 314 freien Icons der Partie 140253), ab 34 px ist nichts mehr davon. Jetzt werden je
  Champion Icon und Ring (1,1 Icon-Radien + 1 px) in den Farbmasken geschwärzt, danach wird gezählt. Vorher: eine
  Raute 0,05 um die Icon-Mitte, am Schwerpunkt geprüft – auf den Diagonalen enger als der Ring, auf den Achsen weiter.
  An allen 613 Ausschnitten von 140253: Punkte im Ring (≤ 36 px) **vorher 14, jetzt 0**; Vasallen direkt neben dem
  Ring (37–40 px) vorher 227, jetzt 394; insgesamt 8956 → 9089. Stichprobe von 12 der neuen Punkte am Ring: 11 echte
  Vasallen, 1 auf dem hellblauen Leuchtring eines Recalls/Teleports. Test `wellenleser_ring_und_nachbar` (fällt mit
  dem alten Stand durch: Ringstück gezählt, Vasall bei 38 px verloren).
  Was das nicht kann: Vasallen **unter** einem Icon sind im Bild verdeckt – die bekommt keine Maske zurück.
- **Ausschnitte behalten:** `lage.bilder_aufraeumen` schützt die Bilder der letzten drei *Partien* – gezählt nach
  aufgenommener Spielzeit (≥ 5 min), nicht nach der Spieluhr; Coach-Neustarts und Bruchstücke schoben echte Partien
  vorher hinaus (130355 verlor seine Bilder an 132154 und 133930). Während der Partie wird nicht mehr nach 20 min
  gelöscht (`BILDER_BEHALTEN` 90 min), sonst fehlte die Lane-Phase jeder längeren Partie. ~100–180 MB je Partie.
- **`1315-crash-dann-back`:** `modus = ["SEITE", "OBJECTIVE"]`, soll/darf_nicht unverändert – jetzt grün (der
  Kern-Plan-Teil bleibt übersprungen, bis der Kern OBJECTIVE/SEITE führt).
- **Werkzeug `werkzeuge/wellen_eichung.py`:** rechnet die Welle aus den behaltenen Ausschnitten einer Aufnahme neu
  (aktuelles `welle.py` + WellenPuffer des Kerns), legt eine Bildtafel und `buecher/wellen_eichung/<stamm>.json` an;
  `--auswerten` gibt die Quote.
- **Zwischenstand an 133930** (echte Partie, Riven Top gegen Gwen, rote Seite, 1073 Ausschnitte – die erste lag vor
  dem Umbau und war bisher nicht bekannt): 13 Zeitpunkte der Lane-Phase (die ersten ~4 min hatte die alte 20-min-Regel
  schon gelöscht). **9 eindeutig, 5 richtig (56 %); GECRASHT_BEI_IHM 0 / 2.** Richtig sind nur die leichten Fälle
  („deine Welle läuft los“, ZU_IHM); falsch alle aussagekräftigen: GECRASHT_BEI_DIR (4:00), GECRASHT_BEI_IHM (6:07,
  Riven im Recall – der Leuchtring schluckt die Vasallen daneben), ZU_IHM statt gehaltenem GECRASHT_BEI_IHM (6:28 –
  die Zustands-Hysterese im WellenPuffer hält den Crash zu lange), ZU_DIR (7:09 – die gegnerischen Vasallen halb unter
  Gwen, die Zählung kippt). Abnahme weiter **nicht erreicht**. Die Eichung an der **nächsten** echten Partie steht aus.
- Nebenbei: `tests/test_kern.py` und `szenarien.py --konstruiert` prüfen nur Lagen in Modi, die der Kern schon führt;
  die neuen Lagen aus `mitte.toml` (Buch 5, Schritt 4) stehen als „übersprungen“ und werden mit Schritt 4 geprüft.

---

## Schritt 3 – Der Kern übernimmt LANE, BASIS, TOT (27.09.2026)

### Umgesetzt

- `lolcoach/kern/`: `handlung.py` (Ziel, Handlung, vor/zurück/stumm/sicher), `gefahr.py` (p_da, p_verliere, p_tod
  nach 7.5), `wert.py` (EV, Todeskosten 7.3, Wellenwert, Zeitwert, sechs Fragen), `plan.py` (halten / Gefahr /
  Schritt / besser mit Hysterese / Erinnerung, 8.2), `sprechen.py` (Kategorien, Budget 9.2 im Kern selbst,
  wartender PLAN), `modi/lane.py`, `modi/basis.py`, `modi/tot.py`, `testlage.py` (konstruierte Lagen, Buch 1 6.2).
- `kern/merkmale.py`: `WellenStand` (Buch 1, 1.2–1.4: Median 6 s, Trend 20 s, Nebel, vorderster stehender Turm,
  Zustände mit Hysterese 3 s, GECRASHT_BEI_IHM sofort), Kanonen-Uhr, Jungler-Seite (`jungle.wahrscheinlich`), TP,
  Kaufplan, Lane-Gegner im Brunnen, Welle beim Verlassen der Lane.
- Buch 1 (Welle): FARMEN, WELLE_REIN_UND_BACK (mit Kanone), STAPELN, WELLE_HALTEN (angreifend/schützend),
  UNTER_TURM_FARMEN, PLATTEN; Buch 3 (Recall, Tempo, Kauf): die fünf Back-Gründe, „nie back“ (2.2), die Welle
  entscheidet den Zeitpunkt (2), Gefahr schlägt Timing (2.1), KAUFEN mit Namen und Kontroll-Auge (3), WOHIN mit
  Wellen-Uhr / Objective / TP zur Lane (4), BESTAETIGUNG (5): Back im Fenster, Rückzug gelohnt, Platte mit Fenster,
  unter dem Turm gefarmt, Stapel zur Kanone, Fokus Kontroll-Auge.
- `--kern neu` ist Default. In LANE, BASIS und TOT sind die alten Regeln stumm (Sperre), außer dem
  Todesrückblick (einmal je Tod ab 14 s) und `_afk`. Stellung `schatten` rechnet mit und schreibt „würde sagen“ in
  `_kern.jsonl`, `alt` ist der Stand von Schritt 2.
- Sprechplan-Weiche (9.6): `kern:`-Ansagen laufen an Themen-, Widerspruchs- und Rückzugssperre vorbei, das Budget
  prüft der Kern. Midgame-Plan des Strategen → INFO (9.1). `minimap_gesund` → TECHNIK durch den Sprechplan.
- Dashboard (9.5): Plan mit Grund, Top-3 mit EV, Gefahr-Markierung; Claude bekommt den Plan als zweite Kopfzeile.
- `_kern.jsonl`: je Takt dazu Plan, Schritt, Ziel, EV, Top-3, Gefahr, Wellenzustand und was gesagt wurde.
- Werkzeuge: `szenarien.py` prüft `soll`/`darf_nicht` gegen den Kern-Plan (überspringt Modi, die der Kern noch nicht
  führt), `--kern`, `--konstruiert`; `kennzahlen.py` misst alt und Kern nebeneinander (Lane-Phase je 30 s,
  GEFAHR/PLAN/ERINNERUNG/BESTAETIGUNG, p_da-Brier auf denselben Proben).
- Tests: `tests/test_kern.py` (alle konstruierten Lagen + Satzlängen 9.3), `bestaetigung_back_im_fenster`,
  `minimap_farben_relativ`.
- Die drei Szenarien aus Buch 3, 7.1 liegen in `tests/szenarien/2026-09-27_102112_buch3.toml`.

### Abnahme Schritt 3

| Abnahme | Soll | Ist |
|---|---|---|
| `0517-platte-ohne-flash`, `0850-kein-hin-und-her`, `0904-drei-kommen`, `3100-basis-braucht-ziel` (Kern) | grün | **alle grün** (5:18 „Back jetzt: 38 Prozent Leben, Sett ist tot.“; 9:02 ZURUECK) |
| `3004-basis-kauf-und-ziel` ohne `frage` | grün | **grün** (KAUFEN: Letzter Atemzug + Sonnenköcher) |
| Buch 3: `0545-back-bei-40-prozent`, `0600-basis-kauf` | grün | **grün** (`1315` gehört zu Schritt 4, s. u.) |
| konstruierte Lagen `lane.toml` + `recall.toml` | alle grün | **25 / 25** |
| Kehrtwenden | 0 | **0** in allen fünf Aufnahmen und in der echten Partie (alt 102112: 3) |
| Lane-Phase: ungefragte Ansagen je 30 s | ≤ 1 im Mittel | **0,83** (102112), 0,94 / 0,65 / 0,89 / 0,00 (andere); echte Partie 140253 **1,04** (alt 1,33) |
| `p_da` schlägt den schlimmsten Fall (Brier) | ja | **ja, überall**: 102112 0,059 gegen 0,317; echte Partie 0,044 gegen 0,273 |
| mindestens eine echte Partie ausgewertet | ja | **ja**: 140253 (Riven Mid gegen Yasuo, 10,8 min, vom alten System gespielt, mit dem Kern nachgespielt) |
| `tests/alle.py` | grün | **grün** (neu: `test_kern`) |
| Buch 1, 1.4: Wellen-Eichung ≥ 80 %, GECRASHT_BEI_IHM ≥ 90 % | ja | **nicht erreicht**, s. u. |
| Generalprobe | – | **nicht gelaufen**: Carlos spielte währenddessen (eigenes Fenster mit Spieltitel) |

Szenarien 102112 mit Kern: 11 grün / 13 geprüft. Rot bleiben `3632-ende-statt-back` (UNTERWEGS/GRUPPE,
Abnahme Schritt 4; das alte System sagt dort weiter „Geh jetzt back“) und `1315-crash-dann-back` (der Modus ist
um 13:15 OBJECTIVE, das Szenario sagt SEITE; Abnahme Schritt 4).

### Kennzahlen (Stand Schritt 3; alt = `--kern alt`, Kern = `--kern neu`)

| Aufnahme | ungefragt je 30 min alt → Kern | „… bei dir“ | Lane-Phase je 30 s | Kehrtwenden | 9.4-Verstöße 1–4, 7 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG | p_da-Brier schlimmster Fall → Kern |
|---|---|---|---|---|---|---|---|
| 2026-09-26_235433 | 74 → 58 | 3 → 0 | 1,21 → 0,94 | 0 → 0 | 4 → 0 | 6 / 10 / 2 / 0 | 0,198 → 0,069 |
| 2026-09-27_001155 | 29 → 39 | 2 → 2 | 0,49 → 0,65 | 0 → 0 | 2 → 0 | 0 / 4 / 0 / 0 | 0,213 → 0,198 |
| 2026-09-27_094832 | 71 → 53 | 3 → 0 | 1,18 → 0,89 | 0 → 0 | 2 → 0 | 4 / 5 / 2 / 0 | 0,229 → 0,047 |
| 2026-09-27_101832 | 27 → 0 | 0 → 0 | 0,45 → 0,00 | 0 → 0 | 0 → 0 | 0 / 0 / 0 / 0 | 0,308 → 0,144 |
| 2026-09-27_102112 | 61 → 57 | 11 → 3 | 1,18 → 0,83 | 3 → 0 | 2 → 1 | 5 / 23 / 1 / 1 | 0,317 → 0,059 |
| **2026-09-27_140253 (echt)** | 78 → 61 | 3 → 0 | 1,33 → 1,04 | 0 → 0 | 4 → 0 | 4 / 11 / 1 / 0 | 0,273 → 0,044 |

Die ungefragten Ansagen je 30 min liegen außer in 001155 unter dem alten System, aber noch über dem Ziel 45 aus
Kapitel 9.2 – der Rest kommt außerhalb der Kern-Modi (SEITE, OBJECTIVE, UNTERWEGS: Schritte 4/5). Der eine
9.4-Verstoß in 102112 ist `_afk` (1:30, „Euer Jungle ist leer“ ohne Lane), bis Schritt 8 eine alte Regel.

**Echte Partie 140253** (Carlos, Riven Mid auf der roten Seite, Coach um 10:45 von Carlos beendet: „ich bin jetzt
gerade zweimal gestorben wegen dir“): Das alte System sagte 9:25 „Schieb die Welle rein und geh dann zum
Drachen“, 10:05 starb Riven an Yasuo. Der Kern sagt an denselben Stellen „Bleib an deinem Mid-Tier-1-Turm:
Brand und Yasuo kommen“ (8:15) bzw. „Raus zu deinem Mid-Tier-1-Turm: Brand und Yasuo kommen“ (9:50) – in beiden
Todesfenstern die Warnung, nie ein „rein“. Dazu kamen die Wahrnehmungsfehler der roten Seite (unten, Punkt 10).

### Buch 1, 1.4: Wellen-Eichung – nicht erreicht

- **102112** hat keine Minimap-Ausschnitte mehr (am Partieende aufgeräumt), nur Spielbilder mit einer Minimap von
  237 px – Vasallen 1–3 px, nicht ehrlich zu beschriften.
- **Echte Partie 140253**: 20 Zeitpunkte der Lane-Phase aus den 764-px-Ausschnitten (während der Partie gesichert,
  nur lesend kopiert). Eindeutig beschriftbar waren 6 der 20 – am Kampfort liegen die Vasallen fast immer unter den
  Champion-Icons, und `welle.py` blendet Punkte am Icon bewusst aus (der Ring hat dieselben Farben). Davon 2 richtig
  (ZU_IHM 3:48, ZU_DIR 5:30), 4 falsch (4:00 ohne jede Lesung noch ZU_IHM statt UNBEKANNT/LEER; 4:12 und 5:42
  eigene Welle kommt, Kern ZU_DIR/MITTE; 4:49 die Wellen treffen sich an Rivens Turm, Kern ZU_IHM).
- Ursachen: (1) Die rote Seite war vertauscht (Punkt 10, behoben); (2) der Trend lief über Sprünge der Front
  (behoben: nur der letzte zusammenhängende Abschnitt, `[welle] front_sprung`); (3) die gegnerischen Vasallen am
  Kampfort fehlen (unter den Icons, im Nebel) – dann gilt `unsere − ihre ≥ 2`, und fast alles ist ZU_IHM. Das ist
  Wahrnehmung, kein Kern-Fehler.
- Folge für die Entscheidungen: WELLE_REIN_UND_BACK hängt an ZU_IHM/MITTE und damit praktisch nur am Back-Grund;
  BACK_JETZT, PLATTEN und STAPELN hängen an GECRASHT_BEI_IHM/LEER/MITTE und sind seltener als sie sein sollten.
  GECRASHT_BEI_IHM ließ sich nicht getrennt eichen (in der Stichprobe einmal, ohne Bild-Wahrheit).
- Offen (OFFEN.md): `welle.py` braucht eine Zählung, die unter den Icons nur den Ring ausblendet, nicht den ganzen
  Kreis, und eine echte Partie mit behaltenen Minimap-Ausschnitten (die Aufräumung am Partieende verschieben).

### Abweichungen vom Buch und Entscheidungen

1. **Gefahr-Gate (Buch 3, 2.1):** Schlägt die Gefahr beim Bleiben an (7.5), sind nur sichere Handlungen (ZURUECK,
   BACK_JETZT) und der schützende Freeze (Buch 1, 3.7) Kandidaten – sonst gewann „Welle rein, dann back“ mit
   Sett 900 entfernt (`k-nicht-back-gegner-nah`).
2. **`p_kampf` (nicht im Buch, `[gefahr] kampf_ohne_anlauf = 0.3`):** Mit p_da = 1 für jeden sichtbaren Gegner in
   1500 war jede ausgeglichene Lane „Gefahr“ (p_tod 0,3). Ein Sichtbarer, der nicht auf dich zuläuft, kämpft nur mit
   0,3; dein Lane-Gegner, der auf dich zuläuft, ebenso – außer er ist stärker (`kraefte()[0] ≤ −1`) oder du bist
   unter 50 % (echte Partie 140253, 0:38: „Raus zu deinem Turm“ zu Spielbeginn). Wer ungesehen ankommt oder als
   Jungler/Roamer auf dich zuläuft, kommt zum Kämpfen.
3. **„Menge der Ankommenden“ (7.5):** gerechnet gegen alle, die sichtbar in 1500 stehen oder im Fenster
   wahrscheinlich da sind (p_da ≥ 0,5) – nicht nur die Sichtbaren in 1500 (9:04: einzeln gerechnet war jeder der
   drei „schwächer“).
4. **ZURUECK:** zwei Fassungen (nur raus / raus, dann back), die bessere zählt; `[gefahr] rueckzug_faktor = 0.6` auf
   den Weg; mit Back zählt der Kanal danach am sicheren Ort mit (sonst war „erst raus“ fast immer besser als
   BACK_JETZT, gegen `k-back-40-prozent`). Der Grund ist, wer dich beim Bleiben tötet; stehst du schon dort:
   „Bleib an …“.
5. **WELLE_REIN_UND_BACK bei GECRASHT_BEI_IHM** (Buch 1, 3.2 zählt es dazu) ist BACK_JETZT (Buch 3, 2 und die Lage
   `k-back-bei-crash` mit `darf_nicht`): der erste Schritt ist schon erledigt.
6. **GEGNER_ZURUECK** (Buch 3, 1) gilt auch bei ZU_IHM/MITTE, nicht nur gecrasht – sonst hat „Sett ist gebackt:
   Welle rein, Platte, dann back“ (4.3, Lage `k-gegner-gebackt`) keinen Back-Grund.
7. **TP zur Lane (4.1):** Die Regel „kein Objective innerhalb der TP-Abklingzeit“ (300 s) widerspricht dem Beispiel
   im selben Kapitel („Drache erst in 4 Minuten“) und der Lage `k-tp-zur-lane` (250 s). Entschieden: das TP muss
   zum Kampf ums Objective zurück sein – Spawn + `tp_objective_nachlauf_s` (60) ≥ Abklingzeit.
8. **Kritisches Leben** (`[recall] leben_kritisch = 0.3`, Riven-Lexikon „außer Leben < 30 %“): kein
   WELLE_REIN_UND_BACK, BACK_JETZT unabhängig von der Welle (094832, 4:26: „Welle rein“ bei 11 %).
9. **Kaufplan nach dem Kern-Build:** Bei fertigem Kern kannte der Kaufplan kein Item mehr (3004: 3007 Gold, kein
   Kauf-Satz). Jetzt die Lexikon-Zeile „Item 4–6“, bei vollem Inventar mit „Verkauf <Start-Item>“ davor
   (`kaufplan.folge`).
10. **Minimap-Farben sind relativ** (Wahrnehmung, gefunden bei der Eichung): dein Team ist blau, der Gegner rot –
    der Code las blau als Team ORDER. Auf der roten Seite waren dadurch eigene und gegnerische Vasallen vertauscht
    (samt Richtung der Front), die Platten-Ziffern wurden in der falschen Farbe gesucht, und bei doppelten Champions
    kippte die Zuordnung. Behoben an den Einstiegen (`welle.zustaende(…, mein_team)`, `Plattenleser.lies_karte(…,
    mein_team)`, `lage.zuordnen`); dahinter heißt blau weiter ORDER. Test `minimap_farben_relativ`. Alte Aufnahmen
    der roten Seite: Wellen stimmen beim Nachspielen, aufgezeichnete Platten nicht.
11. **Wiederholen:** derselbe Plan (Art + Ziel) nicht vor 60 s erneut (`[sprechen] wiederholen_s`), dieselbe Warnung
    vor denselben Gegnern nicht vor 30 s (`gefahr_wiederholen_s`); in der Basis vor 1:00 schweigt der Kern
    (Spielbeginn, Briefing). Sonst lag die Lane-Phase über 1 je 30 s (6:47/6:59 zweimal „Stapel …“).
12. **Erinnerung (8.2 Punkt 5)** nur, wo „nicht ausgeführt“ messbar ist: BACK (nicht in der Basis und du läufst herum)
    und ZURUECK (Gefahr besteht, du bist nicht am sicheren Ort, der Weg wurde nicht kürzer).
13. **Bestätigungen:** „Pünktlich zurück“ fehlt (braucht die Ankunft der Welle am Turm); die Stärken stehen im Kern
    (`Kern.staerken`) und in `_kern.jsonl`, das Review nimmt sie ab Schritt 7.
14. **STAPELN** nur vor einem Objective auf deiner Seite; der zweite Auslöser („der Plan sieht einen Back oder Roam in
    60–90 s vor“) fehlt – es gibt noch keinen Plan, der so weit vorausschaut.
15. **Welle (1.2):** Trend nur über den letzten zusammenhängenden Abschnitt (`front_sprung = 0.12`), s. Eichung.
16. **`kern.toml`-Schlüssel, die nicht im Buch stehen** (alle so markiert): `[gefahr] kampf_ohne_anlauf`,
    `rueckzug_faktor`; `[sprechen] wiederholen_s`, `gefahr_wiederholen_s`; `[welle] lane_laenge_mid`,
    `vasallen_tempo`, `freeze_stabil_s`, `leer_ab_s`, `front_sprung`; `[recall] tempo_bonus`, `voll_ab`, `rueckweg_s`,
    `leben_kritisch`, `tp_objective_nachlauf_s`, `tp_abklingzeit_s`, `basis_warten_s`, `basis_wieder_s`,
    `basis_hoechstens`, `kauf_sprung`.
17. **Einfluss auf eine laufende Partie:** Carlos spielte 140253, während Schritt 3 entstand. Sein Coach lief seit
    13:39 im Stand von Schritt 2; spät geladene Module (`sperre`, `kaufplan`, `kern.toml`) kamen im neuen Stand,
    sind aber mit dem alten Ablauf verträglich (die Sperre ohne `kern_spricht`, der Kaufplan mit mehr Items). Der
    Kern selbst sprach nicht mit.

---

## Schritt 2 – Modus und Sofortmaßnahmen am alten System (27.09.2026)

### Umgesetzt

- `lolcoach/kern/`: `Kern` (ein Objekt je Partie), `merkmale.py` (Bereich, Lane-Phase, Verlauf 20 s, Leben-Trend,
  im Kampf, alle Objectives mit eigener Laufzeit, Mitspieler an/zur Grube, Fenster der Gegner, Bedrohung eigener
  Strukturen, frische Daten), `modus.py` (neun Modi, Priorität, Hysterese 1,5 s), `sperre.py` (Kapitel 14).
  `bewertung.verteidiger_ab` aus `ziele` herausgezogen und von Kern und `ziele` gemeinsam genutzt.
- `wissen/kern.toml`: [modus], [sprechen]; dazu vorgezogen [gefahr] (nur Kill-Beleg) und [objective_wert].
- Modus auf dem Dashboard (Kasten „Modus“ mit Grund und den INFO-Zeilen), in `aufnahmen/<stamm>_kern.jsonl` (live,
  je Takt: Zeit, Modus, Grund, Bereich, Lane-Phase, Kampf, frisch) und als erste Zeile jeder Claude-Frage
  („MODUS: BASIS - du stehst in eurer Basis“).
- Modus-Sperre der alten Regeln nach Kapitel 14 (`Regelwerk.pruefe` → `sperre.entscheide`: sprechen / info / stumm);
  Einwürfe des Strategen (außer Briefing) nicht in KAMPF und nicht 10 s nach einer Gefahr.
- Objective-Fehler (1.3 Punkt 5): Auswahl nach Erreichbarkeit und Wert (`Regelwerk._objective_waehlen`), die
  Laufzeit immer zum genannten Objective (`komponist.zahlen/jungler_tot(..., weg=)`).
- Team-Befehle nur, wenn du rechtzeitig dort bist; sonst „Dein Team kann … nehmen – du bist N s weg“ + dein Ziel,
  bzw. statt „Drückt jetzt den X-Turm“ dein eigenes Ziel.
- Kill-Ruf nur mit Beleg (`denker.kill_beleg`, 6.2): Combo reicht / Leben ≤ 1 s alt / `kraefte()[0]` ≥ 3,0; sagt die
  Rechnung „reicht (knapp) nicht“, kein Kill. Gesagt wird der eine Beleg.
- Budget im Sprechplan: `abstand_s` (12 s) für alles außer SOFORT und Briefing; INFO (Flash, Items, Level, CS)
  aufs Dashboard, gesprochen nur Lane-Gegner/Jungler in LANE/SEITE.
- Claude-Kontext: Modus zuerst; „Deine letzten Ansagen“ nur, wenn die Frage darauf zeigt, dann nur die letzte;
  Lane-Gegner, Lane-Welle und Kampf-Urteil nur in LANE/SEITE oder mit dem Lane-Gegner ≤ 3500.
- `--kern schatten` geht jetzt (in Schritt 2 gleich `alt`), `--kern neu` bricht mit Hinweis ab.
- Werkzeuge: `nachspielen` fährt den Kern mit (Modus je Takt) und zählt Kehrtwenden nach der neuen Regel
  (Carlos' Entscheidung, Kapitel 9.4 Punkt 5); `szenarien.py` prüft `modus` und `[[modus_soll]]`.
- Tests: `modus_sperre_budget` (Modus, Sperre, INFO, Budget, Frage-Bezug); `denkkette` und
  `von_deiner_position_aus` an die neuen Regeln angepasst (Kill ohne Beleg ist Trade; Team-Befehl nur rechtzeitig).

### Abnahme Schritt 2 (102112)

| Abnahme | Soll | Ist |
|---|---|---|
| Modus-Sollwerte (5.3) | ≥ 90 % | **16 / 16 (100 %)** |
| `darf_nicht_sagen` 2522, 2847, 3535, 3004 | grün | **alle grün** (3004 rot nur an `muss_item` der Frage – Pflicht ab Schritt 6) |
| 2601 (Frage „To-do“, Pflicht erst Schritt 6) | sollte grün werden | **grün** („Push den äußeren Mid-Turm, in 16 s bei dir …“) |
| ungefragte Ansagen je 30 min | ≤ 70 | **61** (Stand Schritt 1: 111) |
| Kehrtwenden | ≤ 4 | **3** (Stand Schritt 1, neu gezählt: 6) |
| Generalprobe | läuft | **läuft** (Coach spricht, `_kern.jsonl` wird geschrieben) |
| `tests/alle.py` | grün | **grün** |

Szenarien 102112, altes System mit Schritt 2: ohne Claude 9 grün / 10 geprüft (rot: 3632), mit Claude 9 / 12
(rot: 3004 `muss_item`, 3632, review-102112). 3632 („Ende statt back“) ist Abnahme von Schritt 4.

### Kennzahlen (altes System, Stand Schritt 2; Kehrtwenden nach der neuen Regel)

| Aufnahme | ungefragt (je 30 min) | „… bei dir“ | Flash | Kehrtwenden | 9.4: 1 / 2 / 3 / 4 / 7 |
|---|---|---|---|---|---|
| 2026-09-26_235433 | 28 (74) | 3 | 1 | 0 | 4 / 0 / 0 / 0 / 0 |
| 2026-09-27_001155 | 9 (29) | 2 | 0 | 0 | 1 / 1 / 0 / 0 / 0 |
| 2026-09-27_094832 | 16 (71) | 3 | 1 | 0 | 2 / 0 / 0 / 0 / 0 |
| 2026-09-27_101832 | 1 (27) | 0 | 1 | 0 | 0 / 0 / 0 / 0 / 0 |
| 2026-09-27_102112 | **62 (61)** | 11 | 1 | **3** | 2 / 0 / 0 / 0 / 0 |

Zum Vergleich 102112 im Stand von Schritt 1 (fd59e03), mit denselben Werkzeugen und der neuen Kehrtwenden-Regel
gemessen: 112 (111 je 30 min), „… bei dir“ 22, Flash 23, Kehrtwenden 6, 9.4: 6 / 0 / 0 / 0 / 1.

### Abweichungen vom Buch und Entscheidungen

1. **Modus-Tabelle mit den echten Regeln nachgerechnet (5.3)** – zwei Zeitpunkte lagen daneben, entschieden nach
   der Kernfrage:
   - **5:17 KAMPF statt LANE:** Riven kämpfte 5:06–5:16 gegen Sett (94 % → 27 %); Sett starb, KAMPF lief die 3 s
     Nachlauf. Entscheidung: KAMPF endet sofort, wenn kein lebender Gegner mehr in `kampf_radius` ist – dann ist
     die Kernfrage „rein, halten, raus?“ beantwortet. `kampf_ende_s` gilt nur, solange noch einer da ist.
   - **36:32 OBJECTIVE statt GRUPPE/UNTERWEGS:** Baron lebte seit 20:00; ≤ 25 s von einer Grube ist man von der
     Mid-Lane fast immer. Entscheidung: „du stehst an der Grube“ heißt in der Grube – oder ≤ `objective_nah_s`
     **und** genug von euch können in dieser Zeit dort sein (`mindestens`: Baron 3, sonst 2), sonst stellt sich die
     Kernfrage „nehmen, bestreiten, abgeben, tauschen?“ nicht. Aus der Basis heraus nie (der Heimweg-Schub macht
     die Laufzeit klein). Ein Mitspieler an der Grube genügt weiter.
2. **Modus ohne bekannten Ort = kein Modus** (4.3 „nicht raten“): die Generalprobe sah die Minimap kaum; ohne Ort
   fiel der Modus sonst auf UNTERWEGS und die Lane-Regeln wären stumm gewesen. Ohne Modus gilt keine Sperre.
3. **`kern.toml` enthält Schlüssel, die nicht im Buch stehen** (alle als „nicht im Buch“ markiert):
   `grube_radius`, `verteidigen_radius/_weg_s/_welle_front`, `kampf_leben_trend`, `kampf_balken_faellt`,
   `minimap_frisch_s`, `kill_leben_frisch_s`, `[objective_wert].mindestens` und `.dauer_s`. [gefahr] enthält nur den
   Kill-Beleg, [objective_wert] ist vorgezogen, weil die Objective-Auswahl nach Wert ihn braucht.
4. **Objective-Auswahl:** erreichbar = dein Weg + geschätzte Tötungszeit (`dauer_s`) passen vor den ersten Gegner
   an der Grube (`verteidiger_ab`; nicht das Todesfenster der Regel), und genug von euch sind bis dahin dort.
   In 102112 um 25:22 ist dadurch **kein** Objective wählbar (Baron klar nicht, der Drache 0,5 s über dem Fenster
   gegen Sett im schlimmsten Fall) – der Coach sagt „Drückt jetzt den äußeren Mid-Turm …“. Das `soll` des
   Szenarios (Drache nehmen) kommt mit Schritt 5 (Kampflage, Buch 6), nicht über einen angepassten Startwert.
5. **Budget und Frische:** Schritt 2 verlangt `abstand_s` = 12 s, die alte Frische-Grenze erlaubt WICHTIG nur
   10 s Warten – eine Ansage direkt nach einer anderen hätte nie kommen können. Nach 9.2 („gesagt, sobald wieder
   Platz ist und er dann noch gilt“) darf, wer nur am Budget wartet, `abstand_s` länger warten; ob er noch stimmt,
   prüft weiter seine Prüfung.
6. **INFO nach der Tabelle in Kapitel 14** (Flash des Lane-Gegners/Junglers auch in SEITE), nicht nur „in LANE“
   wie in der Kurzfassung von Schritt 2. `aufbruch` (Kauf beim Verlassen der Basis) gilt als KAUFEN, nicht als
   Lane-Info von `_items`.
7. **Sicherer Ort (7.5) vorgezogen:** Rückzug zum nächsten von Turm, Basis oder eigener Gruppe (≥ 2 Mitspieler
   beieinander) – nötig für die Abnahme von 3535 („Top-Tier-3-Turm, 31 s“, drei Mitspieler 8 s entfernt).
8. **Stratege „nicht in GEFAHR“** vor dem Kern (Schritt 3) genähert: 10 s nach einer Ansage mit Thema „gefahr“.
9. **`_kern.jsonl` nur live** (neben der Aufnahme); Nachspielen schreibt keine, damit es das Live-Protokoll nicht
   überschreibt.
10. **3004 `muss_item`:** Claude nannte „Lord Dominiks Ring“ – kein Name aus der Ladenliste. Frage-Teil, Pflicht in
    Schritt 6 (Kauf aus dem Kern).

---

## Schritt 1 – Messen, nichts am Verhalten ändern (27.09.2026)

### Umgesetzt

- `werkzeuge/nachspielen.py`: gemeinsame Grundlage – Aufnahme durch `Regelwerk` + `Sprechplan` (stumm) wie live,
  je Takt Leben, sichtbare Gegner, Kills, Objectives (für Kehrtwenden), Datenlücken, Proben für die Gefahr-Eichung.
- `werkzeuge/szenarien.py`: Szenarien gegen das alte System (nur Text: `darf_nicht_sagen`, `muss_nennen_eins`,
  `muss_ziel`, `kehrtwenden_max`, `ansagen_max`). Kern-Teile (`modus`, `soll`, `darf_nicht`, `[[modus_soll]]`)
  stehen als „übersprungen“. `--mit-claude` stellt die `frage` über den alten Antwortweg (sofort, sonst Claude
  mit Spielakte und Bildschirm des Moments) und prüft das gespeicherte Review. `--lage` zeigt die nachgespielte
  Lage je Szenario.
- `werkzeuge/kennzahlen.py`: je Aufnahme ungefragte Ansagen je 30 min, Ankunfts- und Flash-Ansagen, Kehrtwenden,
  Verstöße gegen 9.4 (1, 2, 3, 4, 7; 5 = Kehrtwenden; 6 erst mit Kern), Brier des schlimmsten Falls, Datenlücken,
  Szenario-Quote. `sinnpruefung.py` geht darin auf.
- `werkzeuge/szenario_aus_notizen.py`: 18 Stubs aus 4 Aufnahmen mit Notizen in `tests/szenarien/offen/`
  (212105: 1, 230520: 5, 235433: 2, 102112: 10).
- Wachhund nach Wanduhr (`lolcoach/wachhund.py`, Kapitel 4.3): nach 20 s ohne Schnappschuss bei offenem
  Spielfenster einmal „Ich sehe das Spiel gerade nicht – ich melde mich, sobald die Daten wieder da sind.“, bei
  Rückkehr „Ich sehe das Spiel wieder.“; jede Lücke in `aufnahmen/<stamm>_luecken.jsonl`. Ein Neustart des
  Coachs mitten in der Partie (Aufnahme fortgesetzt) wird dort ebenfalls als Lücke eingetragen.
  Test: `wachhund_meldet_datenluecke`.
- `--kern alt|schatten|neu` an `live` und `abspielen`; bis Schritt 2 nur `alt` (die anderen brechen mit Hinweis ab).
- `CLAUDE.md` (Verweis auf `buecher/`, Arbeitsweise Beschwerde → Szenario → Modelländerung, `--kern`, neue
  Werkzeuge), `OFFEN.md` („In Arbeit: Buch 0, Schritt 1“, ersetzte Punkte markiert).

### Datenlücke 15:55–24:24 in 102112: geklärt

Kein API-Fehler, kein Absturz: **der Coach wurde von Hand beendet.**

- Letzter Schnappschuss 10:37:06, nächster 10:45:34 (Wanduhr). Die Spielbilder (`schirm_*.jpg`) enden 10:37:09
  und beginnen 10:45:35 – der ganze Prozess war weg, nicht nur die API.
- `aufnahmen/absturz.log` (faulthandler): kein Absturz, neue Startzeile „Coach gestartet 10:45:33“.
- Letzter Tastendruck vorher 15:38 („Wo soll ich reingehen?“ vierfach erkannt). Carlos schrieb in dieser Zeit
  „ich musste den Coach ausmachen, der hat … mal hintereinander gesagt geh rein geh rein“ – die Schleife der
  Stimme (ein unterbrochener Satz kam nach jedem Tastendruck wieder).
- Behoben ist die Ursache schon: Commit 93f4fee (10:44, eine Minute vor dem Neustart), „Sprechtaste ist
  Stummtaste“ – unterbrochene Sätze werden nicht mehr wiederholt.
- Neu: der Wachhund (oben). Für diesen Fall (Coach aus) greift der Eintrag beim Neustart.

### Grundlinie (altes System, die 5 jüngsten Aufnahmen)

| Aufnahme | Minuten mit Daten | ungefragt (je 30 min) | „… bei dir“ | Flash | Kehrtwenden | 9.4: 1 / 2 / 3 / 4 / 7 | Brier schlimmster Fall (Proben, Grundrate) | Lücken > 5 s |
|---|---|---|---|---|---|---|---|---|
| 2026-09-26_235433 (Bots) | 11,3 | 40 (106) | 4 | 7 | 0 | 4 / 0 / 0 / 0 / 0 | 0,198 (1774, 0,157) | keine |
| 2026-09-27_001155 (Bots) | 9,2 | 18 (58) | 2 | 5 | 0 | 1 / 1 / 0 / 0 / 0 | 0,213 (456, 0,636) | keine |
| 2026-09-27_094832 (Bots) | 6,8 | 22 (97) | 4 | 3 | 0 | 1 / 0 / 0 / 0 / 0 | 0,229 (1351, 0,149) | keine |
| 2026-09-27_101832 | 1,1 | 2 (54) | 0 | 2 | 0 | 0 / 0 / 0 / 0 / 0 | 0,308 (52, 0,327) | keine |
| 2026-09-27_102112 (Bots) | 30,4 | **112 (111)** | **22** | **23** | 4 | 6 / 0 / 0 / 0 / 1 | 0,317 (6307, 0,105) | 0:04–0:11, 6:53–6:59, **15:55–24:23 (508 s)** |

Ziel laut Buch: ≤ 45 ungefragte Ansagen je 30 min. GEFAHR / PLAN / ERINNERUNG und `p_da` gibt es erst mit dem
Kern (Schritt 3); der Brier des schlimmsten Falls ist die Latte, die `p_da` dann unterbieten muss.
101832 ist ein Bruchstück von einer Minute (Coach vor der Partie neu gestartet).

### Szenarien 102112, altes System

| Szenario | ohne Claude | mit `--mit-claude` | Grund |
|---|---|---|---|
| 0517-platte-ohne-flash | rot | rot | 5:17 „… nimm die Platte mit“ |
| 0850-kein-hin-und-her | grün | grün | 1 Kehrtwende im Fenster (9:00 → 9:04, erlaubt: 1) |
| 0904-drei-kommen | rot | rot | 9:24 „Bleib an deiner Welle, … zusammen schwächer als du“ |
| 2522-kein-baron-drache-lebt | rot | rot | 25:22 „Nehmt jetzt Baron Nashor“ |
| 2601-frage-to-do | übersprungen | grün | „Push den äußeren Mid-Turm, in 21 s frei …“ (kein Sett) |
| 2847-baron-statt-drache | grün | grün | kein „Baron“ im Fenster (Team-Ruf-Grenze seit 1b5b60f) |
| 3004-basis-kauf-und-ziel | übersprungen | grün | nennt Kontroll-Auge und Top-Lane – inhaltlich dünn („rüste auf“) |
| 3100-basis-braucht-ziel | rot | rot | 30:56 „Geh zurück zu deiner Basis“ – in der Basis |
| 3500-drache-solo | übersprungen | grün | „Drache: ihr 2 in 15 Sekunden dort, sie 0 – nehmen.“ (Riven steht an der Grube: „15 s“ stimmt nicht) |
| 3535-rueckzug-31s | rot | rot | 35:35 „… zu deinem Top-Tier-3-Turm, das sind 31 Sekunden“ |
| 3632-ende-statt-back | rot | rot | 36:32 „Geh jetzt back, du hast 4400 Gold.“ |
| review-102112 | übersprungen | rot | Lücke nicht genannt; Lektion 1 „Kein Kontroll-Auge“; 17:19 „während du durchgehend oben standest“ |
| **Quote** | **2 / 8** (6 rot) | **5 / 12** (7 rot) | |

Modus-Sollwerte (16 Zeitpunkte): übersprungen, der Modus kommt in Schritt 2.

### Abnahme Schritt 1

- Läufer laufen: ja (`szenarien.py`, `kennzahlen.py`, `szenario_aus_notizen.py`).
- Grundlinie eingetragen: ja (oben).
- Das alte System fällt bei mindestens 6 der 102112-Szenarien durch: **ja, 6 von 8 ohne Claude** (7 von 12 mit).
- `tests/alle.py` grün: ja.

### Abweichungen vom Buch

1. **Kehrtwenden in 102112: 4 statt 8 (Kapitel 1.2).** Gezählt nach 9.4 Punkt 5 wörtlich: vor ↔ zurück in ≤ 30 s,
   Paare mit neuem Ereignis dazwischen fallen heraus. Ohne diesen Filter sind es 13 (9 davon mit Ereignis).
   Die Zählweise hinter der 8 steht nicht im Buch. Der Filter ist großzügig: „neuer Gegner sichtbar“ trifft in
   dichten Phasen fast immer zu (9:04 → 9:24 zählt deshalb nicht). Entscheidung: Zählung nach 9.4 wörtlich
   beibehalten. Vorschlag für Schritt 2: als neues Ereignis nur einen Gegner zählen, der in ≤ 3000 um dich
   auftaucht.
   **Entschieden (Carlos, vor Schritt 2):** der Vorschlag gilt – als neues Ereignis zählt nur ein Gegner, der in
   ≤ 3000 um dich neu sichtbar wird (in den 5 s davor nicht sichtbar). Eingetragen in Kapitel 9.4 Punkt 5, umgesetzt
   in `werkzeuge/nachspielen.neues_ereignis`.
2. **Szenario-Lagen nachgespielt, vier kleine Korrekturen** in `tests/szenarien/2026-09-27_102112.toml`:
   0517 Flash noch ~59 s (HUD) statt ~48 s; 2522 Ort „unten“ (Minimap), Galio stirbt genau in diesem Takt;
   3100 um 30:30 noch 3240 Gold, Kauf gegen 31:00; 3632 Brand „unten“ statt im eigenen Jungle. Alle anderen
   Lagen stimmen (Abstände ±150, Zeiten ±1 s).
3. **3500: `muss_nennen_eins` um „nehmen“ ergänzt.** Die Antwort „… sie 0 – nehmen.“ ist inhaltlich ein Ja; die
   Liste kannte nur „Ja/nimm/mach“. Der Fehler in derselben Antwort („ihr 2 in 15 Sekunden dort“, Riven steht an
   der Grube) wird damit nicht geprüft – er gehört in Schritt 5 (`fenster_gegner`, Objective-Dauer).
4. **Review mit `--mit-claude`:** geprüft wird das gespeicherte Review der Partie, kein neu erzeugtes (spart
   ~2 min Claude je Lauf). Für Schritt 7 muss der Läufer das Review neu erzeugen.
5. **9.4 Punkt 2 ohne Modus genähert:** „Lane-/Wellenbefehl außerhalb LANE/SEITE“ = du stehst weder auf deiner
   Lane noch (nach 14:00) auf einer Seitenlane; „an deiner Welle – geh hin“ zählt als Weg. Mit dem Modus aus
   Schritt 2 wird das exakt.
6. **`p_da`-Brier:** bis Schritt 3 nur der schlimmste Fall (p = 1, wenn früheste Ankunft ≤ 10 s). Wahrheit: der
   Gegner war in den nächsten 10 s **sichtbar** in 1500 um dich – wer ungesehen kam, zählt nicht (Grenze der
   Messung). Proben: je Sekunde jeder lebende Gegner mit bekannter frühester Ankunft; `p_da` muss in Schritt 3
   auf denselben Proben gemessen werden.
7. **Stub 26:20 in 102112** zeigt einen möglichen Wahrnehmungsfehler: das Nachspielen sieht Riven „in eurem
   unteren Jungle“, Carlos sagte „ich bin in der Midlane an meiner Base“. Beim Beschriften prüfen.
   **Geklärt (Carlos, vor Schritt 2): kein Wahrnehmungsfehler** – Riven lief um 26:15 von der Mid-Lane in den
   eigenen unteren Jungle; das Nachspielen sieht sie um 26:20 richtig dort.
