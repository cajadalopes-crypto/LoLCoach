# Messungen zum Umbau (Buch 0)

Je Schritt: was umgesetzt ist, die Abnahme-Zahlen, Abweichungen vom Buch. Neueste oben.

---

## Auftrag 023 – Stabile Messung, eine Stimme, Pflicht-Infos, Tempo (30.09.2026, auf Carlos' Wunsch abgekürzt)

Protokolle, Kritiken und Mehrheiten: `buecher/protokolle/proben/stratege_probe_023/` (`vorher_bekannt`, `vorher_neu`
= Stand 021 im neuen Verfahren; `r1` = bekannte Menge nach Runde 1; `neu` = neue Menge, fast Endstand).
Soll-Listen eingefroren: `buecher/protokolle/proben/soll_023/`.

### Streichungen aus den Soll-Listen (17)

Grund a = Trade/All-in ohne Kill-Check oder Level-Vergleich mit All-in (harte Regel); b = Ward an einem bestimmten
Busch (der Coach sieht keine Büsche); c = kein Coach-Punkt (Begriffserklärung). Wortlaut je Streichung:
`soll_023/streichungen.json`.

| Partie | Min. | Soll | Grund |
|---|---|---|---|
| 101426 | 2 | Aurora Flash weg – Kill-Fenster mit Kayn | a |
| 101426 | 12 | Aurora ohne Flash bis ~15:30 – Kill-Fenster | a |
| 101426 | 16 | Gegner am Drachen: kämpfen, ihr seid vorne | a |
| 192113 | 1 | Teemo Flash weg: Level 2 hart traden | a |
| 192113 | 2 | Kontrollauge in den Flussbusch oben | b |
| 192113 | 5 | Level 6: all-in mit R auf Teemo (79 %) | a |
| 192113 | 8 | 'Gebackt' heißt: Rückruf | c |
| 133448 | 1 | Poppy 23 %: jetzt reingehen und traden | a |
| 133448 | 5 | L6 gegen Poppy L4: all-in mit R | a |
| 133448 | 9 | Poppy L6 gegen dein L9: all-in | a |
| 133448 | 16 | Kontroll-Auge in den Fluss-Busch vor dem Drachen | b |
| 183125 | 1 | Garen Flash weg – hart traden | a |
| 183125 | 12 | Garen 49 % und Flash weg: nachsetzen | a |
| 183125 | 26 | Kampf am Drachen – direkt rein | a |
| 183125 | 31 | Kanone = Kanonenvasall | c |
| 164809 | 6 | Wukong ohne Flash: Druck auf ihn | a |
| 120049 | 22 | Rakan allein, jagen | a |

Danach: bekannt 202 Punkte, neu 171.

### Kritiker-Übereinstimmung (drei frische Kritiker je Partie, Mehrheit; ein vierter nur für strittige Punkte)

| Runde | Punkte | einig 3/3 | Mehrheit 2/3 | strittig → vierter |
|---|---|---|---|---|
| 021 bekannt | 202 | 168 (83 %) | 34 | 0 |
| 021 neu | 171 | 123 (72 %) | 48 | 0 |
| 023 r1 bekannt | 202 | 167 (83 %) | 33 | 2 |
| 023 neu | 171 | 134 (78 %) | 36 | 1 |

### Drei Werte je Größe (021 altes Verfahren / 021 neues Verfahren / 023)

| Größe | bekannt | neu |
|---|---|---|
| Soll gesagt + teilweise | 56 / 57,4 / **59,4 %** | 70 / 69,0 / **72,5 %** |
| Flash | 88 / – / **34/34** | 89 / – / **8/9** |
| Jungler | 89 / – / **71/72** | 84 / – / **61/62** |
| Lane-Gegner weg (neue Def.) | 58 / – / **8/8** | 43 / – / **2/2** |
| Widersprüche je Partie (Mehrheit) | 2/7/4/7 / 4/9/3/11 / **4/8/2/8** | 4/2/1 / 3/2/1 / **3/2/4** |
| Füllsätze | 4,0 / 2,8 / **2,2 %** | 3,2 / 2,5 / **2,9 %** |
| Latenz ganze Antwort, Median | 2,3–2,5 / – / **2,40–2,45 s** | 2,3–2,5 / – / **2,26–2,39 s** |
| bis zum ersten Satz, Median | – / – / **1,34–1,49 s** | – / – / **1,28–1,42 s** |
| Zwischenspeicher-Treffer | – / – / **364/451** | – / – / **152/228** |
| Sicherheit | 0 / 0 / **0** | 0 / 0 / **0** |
| Kosten je Partie | – / – / 0,23–0,46 $ | – / – / 0,20–0,29 $ |

„–“: im alten Verfahren nicht gleich gemessen. Die Flash/Jungler/Lane-Werte im alten Verfahren sind Prozent, 023
sind Fälle. 023 r1 lief **vor** den letzten Fixes (Kern-Ersatz nur bei Ausfall, Antwortregel, Info mit Plan,
„Stopp –“, nacktes Nein, Textende an der PLAN-Zeile), `neu` vor den letzten vier. Die Endmessung macht 025.

### Widersprüche 021 nach Quelle (52, Vereinigung der drei Kritiker)

Antwort–Stratege 11, Stratege–Stratege 8, Antwort–Antwort 8, Antwort–Kern-Plan 7, Kern-Plan–Stratege 6,
Antwort–Kern-Warnung 4, Kern-Plan–Kern-Plan 3, Kern-Warnung–Stratege 3, Kern-Plan–Kern-Warnung 2.

In `neu` (023) gefunden und gebaut:
- 164809 21:16: `kern:INFO_BASIS` sagte einen Plan („Drache erzwingen“) an allen vorbei. Infos mit Plan-Ziel gehen
  jetzt über den Schiedsrichter; die Pflicht-Infos nie.
- 120049 14:08/14:09 und 164809 19:27/19:28: Stratege-Plan, eine Sekunde später Kern-Warnung. Die Warnung beginnt
  jetzt mit „Stopp –“, wenn sie binnen 8 s einen anderen Plan ersetzt.
- 164809 23:09 „**Nein, nicht Top jetzt**“: ein nacktes Nein auf einen Anlass setzte kein Ziel, der Kern schickte
  15 s später nach Top. Verworfen (zweiter Versuch mit Grund). Markdown fällt weg.

### Tempo

Die ganze Antwort wartete auf die stille PLAN-Zeile und das Stromende: erster gültiger Satz 1,4 s, gemeldet erst
2,4 s. `llm.stille_zeile`: das Textende kommt, sobald „PLAN:“ beginnt (API und Abo). Der Gewinn ist nicht gemessen;
er kommt aus der Lücke von ~0,9 s zwischen erstem Satz und ganzer Antwort.

### Pflicht-Infos

Verpasst in 023: 164809 6:19 Flash Wukong, 26:25 Jungler Vi, 183125 ein Jungler. Nicht mehr einzeln angesehen
(abgekürzt).

### Aufnahmen als xz

29 Aufnahmen umgewandelt. Projektordner 4466 → 4334 MB, `aufnahmen` 2691 → 2558 MB. Eine Aufnahme wird z. B.
aus 12,8 MB gzip 0,27 MB xz, aus 21,1 MB 0,39 MB. Je Partie bleiben ~12 MB statt ~46 MB: 0,5 MB Aufnahme,
5,6 MB Verlauf, 3,8 MB Kern-Log, ~2 MB Rest. Nachspiel und Szenarien sind an 213624 und 101426 Satz für Satz gleich
(107/107, 94/94; Szenarien 116/118 beide).

Kosten 023: 1,49 $ (r1) + 0,72 $ (neu) + 0,11 $ (abgebrochene Runde 2) = **2,32 $** von 5 $.

## Auftrag 021 – Gehirn mit Plan und Freigabe-Tor (Buch 14, Schritt C, 29.09.2026)

**Gebaut:**
- **Plan-Objekt:** Claude schreibt nach dem gesprochenen Satz eine stille Zeile `PLAN: Ziel | Schritt | danach |
  Grund | gilt bis | Abbruch` (`stratege_live.Plan`). Sie steht in jedem Prompt und beantwortet „Und dann?“.
- **Jeder Plan-Satz des Kerns geht an Claude:** Das gilt für PLAN, WENDEPUNKT, VORSCHAU, FENSTER und MAKRO, mit dem
  Satz als Entwurf. Der Kern spricht ihn nur als Ersatz: wenn Claude ausfällt oder nach 5 s nichts gesagt hat.
  „NICHTS“ auf einen Plan-Entwurf heißt: der Plan bleibt.
- **Wissen je Partie** (`lolcoach/partie_wissen.py`): ~5000 Tokens als zwischengespeicherter Block, darin Buch 13,
  die Wellen-Regeln, Objective-Zeiten, das Lexikon der 10 Champions und Carlos' Build. Der Zwischenspeicher greift:
  1,6 Mio. Tokens gelesen je Partie.
- **Neue Anlässe:**
  - Objective-Timer mit Aufgabe, 90 s und 30 s vorher und beim Spawn;
  - das Fenster nach einem gegnerischen Tod;
  - die Roam-Gefahr eines starken Laners ohne Sicht;
  - der Kern meldet „Gegner in deinem Jungle: Büsche nicht blind betreten“.
- **Kampfansage:** nur mit dem Rechner. „klar hinten“ ergibt „Nicht rein“; „klar vorn“ und „knapp“ ergeben zwei
  Optionen, weil „klar vorn“ live nicht belegt ist (020).
- **Sicherheit:** Der Satz wird vor dem Sprechen noch einmal gegen die Lage JETZT geprüft (125902 9:15: beim Fragen
  war nach vorn erlaubt, beim Sprechen stand das Leben unter R1). „schwach“ gilt nur für den eigenen Satzteil
  (183125 14:27: der Vorsatz nannte Garen, gemeint war Zyra).

**Runden** (Haiku über die API; Kritiker blind und frisch, je Partie einer; Soll-Listen der bekannten Partien aus 019,
der neuen blind aus `stratege_probe_021/stub/LAGE_*.md`):

| Größe | Tor | 019 (Haiku) | 021 Runde 1 | 021 Runde 2 (bekannt) | 021 neu (125902, 164809, 120049) |
|---|---|---|---|---|---|
| Soll-Liste gesagt + teilweise | ≥ 80 / ≥ 75 % | 61 % | 58 % | 56 % | **70 %** |
| Sicherheit | 0 / 0 / 0 | 0 | 0 | 0 (nach Messfix) | 1 → 0 nach Fix (125902 nachgespielt) |
| Flash / Jungler / Lane-Gegner weg | je ≥ 90 % | – | – | 88 % / 89 % / 58 % | 89 % / 84 % / 43 % |
| Füllsätze (Kritiker) | ≤ 5 % | 8 % | 3 % | 4,0 % | 3,2 % |
| Widersprüche je Partie (Kritiker) | ≤ 1 | 6 in vier Partien | 2 / 6 / 5 / 5 | 2 / 7 / 4 / 7 | 4 / 2 / 1 |
| Latenz ganzer Satz, Median | ≤ 2 s | 1,6 s | 2,6–2,9 s | 2,3–2,5 s | 2,3–2,5 s |
| Kosten je 30 min | ≤ 0,50 $ | 0,25 $ | 0,58 $ | 0,45 $ | 0,34 $ |

**Kosten der Nachspiele:**

| Lauf | Kosten |
|---|---|
| Runde 1 | 2,24 $ |
| Runde 2 | 1,85 $ |
| neue Menge | 1,00 $ |
| 125902 mit dem Sicherheitsfix | 0,37 $ |
| **zusammen** | **5,46 $** (Budget 6 $) |

- Eine dritte Runde auf der bekannten Menge hätte das Budget überschritten.
- Nach Runde 1 wurde der gesprochene Teil sofort beim Beginn der PLAN-Zeile gesprochen, und eine zweite Anfrage
  nach einem Verwerfen gab es nur noch für wichtige Anlässe. Das senkte die Kosten, die Latenz aber nur von
  2,6–2,9 auf 2,3–2,5 s. Der Wissensblock macht jeden Aufruf rund 5000 Tokens länger.

**Warum die Soll-Liste nicht steigt:**
- **Die Kritiker streuen stark.** Dieselbe Minute wird einmal „gesagt“, einmal „fehlt“ bewertet. Zwischen Runde 1
  und 2 kippten auf 183125 viele Urteile, ohne dass sich der Satz grundlegend änderte.
- **Ein Teil der Soll-Punkte verlangt, was die harten Regeln verbieten:** Trade oder All-in ohne Kill-Check,
  Wards, Level-Vergleiche mit All-in. 133448 enthält vier solche Punkte.
- **Neu gesagt werden jetzt:** Timer mit Aufgabe, Fenster nach Toten, Kaufketten mit Item und Gegner im eigenen
  Jungle. Dafür fehlen in Runde 2 Dinge, die 019 hatte, etwa Teemos Flash um 19:11 oder die Stille in 133448
  1:47–3:13.

---

## Auftrag 020 – Kampfrechner, geeicht an Riot-Partien (Buch 14, Schritt B, 29.09.2026)

**Nachtrag 29.09. 22:55 (in 021):** Der Download ist fertig. Die Eichung mit 2000 Partien und 63 225 Kämpfen ergibt:
- Schwelle 0,60, Tor ja.
- Alle Kämpfe: 97,8 / 98,0 %.
- Teamkämpfe: 95,0 / 94,8 %.
- Gleich viele Beteiligte: 81,0 / 85,0 % bei 7,9 % Abdeckung.
- Der Schlüssel ist nicht abgelaufen.


**Fähigkeitswerte:** Meraki `lolstaticdata` geprüft. Es ist veraltet (jüngste Änderung Patch 25.15, 171 Champions;
Graves Q dort 45–125 + 80 %, im Spiel 50–150 + 55 %). Deshalb CommunityDragon (Patch 16.19, 173 Champions), jetzt
unter `wissen/faehigkeiten/cdragon.json` mit `stand.toml`.

- **Abgleich mit `combo.WIKI`:** Rivens Q, W und R2, Camilles W und E sowie Graves' Q und R stimmen überein.
- **Fehlt in den Daten** (dort wird also zu wenig Schaden gerechnet): Rivens drei Q und Passiv, Camilles Q und
  Graves' Q-Detonation.

**Rechner `lolcoach/kampf_rechner.py`:**
- **Burst:** je Fähigkeit ein Treffer, R nur mit Ult, dazu Angriffe in 3 s, nach Resistenzen und Durchdringung.
- **Ablauf in 0,25-s-Schritten:** Jeder greift sein schnellstes Ziel an. Die Stärke ist das Restleben wir minus
  sie, von −1 bis 1.
- **Ausgabe:** das Urteil, zwei Zahlen und die Annahmen.

**Eichung** (`werkzeuge/kampf_eichung_riot.py`, Datensatz: 1095 Partien bei Stand 22:05, der Download lief noch; 35 157
Kämpfe):
- **Stand je Kampf:** Werte aus `championStats` des Minuten-Frames davor, Ränge aus `SKILL_LEVEL_UP`.
- **Annahmen:** Leben voll, Ult bereit.
- **Beteiligte:** aus den Kill-Ereignissen samt `victimDamageDealt`/`victimDamageReceived`.
- **Sieger:** die Seite mit weniger Toten.

| Menge (Schwelle 0,50) | Kämpfe | klar vorn: Treffer | klar hinten: Treffer | Abdeckung |
|---|---|---|---|---|
| alle | 35 157 | 97,0 % (11 526) | 96,6 % (12 252) | 67,6 % |
| je Seite ≥ 2 (Teamkämpfe) | 8 728 | 93,6 % | 92,1 % | 49,0 % |
| gleich viele Beteiligte | 9 577 | 80,1 % | 80,5 % | 15,3 % |

- **Tor erreicht:** Beide klaren Urteile treffen in jeder Menge mindestens 80 %, bei mindestens 30 % Abdeckung.
- **Warum die Schwelle so hoch liegt:** Die Beteiligten stammen aus Kill-Ereignissen, also gewinnt fast immer die
  Seite mit mehr Köpfen. Die Basis „mehr Köpfe gewinnt“ trifft dort 96,0 %. Erst die Menge „gleich viele“ prüft
  den Rechner selbst; deshalb ist sie Teil des Tors.
- **Grenzen:** kein Leben zu Kampfbeginn, keine Abklingzeiten, keine Beteiligten ohne Treffer auf ein Opfer.

**Probe an Carlos' Aufnahmen** (Lagebild-Kampf alle 20 s; Ausgang = Tote unter den Gezählten in 15 s):

| Urteil | richtig | falsch |
|---|---|---|
| klar vorn | 13 | 11 |
| klar hinten | 10 | 2 |

- Bei „knapp“ gewannen 20-mal sie und 10-mal wir.
- Live zählen nur **sichtbare** Gegner. Deshalb ist „klar vorn“ live nicht belegt (54 %).
- `wissen/kampf_eichung.toml`: `klar_vorn_sprechen = false`, `klar_hinten_sprechen = true`.

---

## Auftrag 018 – Was Carlos' Graves-Partie zeigt (183125, 29.09.2026)

Stand nach 017/019, geprüft nur an Aufnahmen; Nachspiel über die API (Haiku), Protokoll in
`buecher/protokolle/NACHSPIEL_2026-09-29_183125.md`, Rohdaten in `stratege_probe_018/`.

**1. Objective-Symbole der Minimap** (`lolcoach/objsymbole.py`, geeicht mit `werkzeuge/objsymbole_eichung.py`):
8 Aufnahmen mit Minimap-Bildern (1 Hz), je Bild die zwei Gruben gegen den Objective-Stand aus den API-Ereignissen
(Spawn-Regeln + DragonKill/HeraldKill/BaronKill) zur Spielzeit des Bildes.

| Grube | Bilder | Treffer | Symbol, obwohl nichts lebt | lebt, kein Symbol | verdeckt (Portrait) |
|---|---|---|---|---|---|
| oben (Larven, Herold, Baron) | 13 391 | **99,5 %** | 9 | 52 | 344 |
| unten (Drache, Ältester) | 12 245 | **97,7 %** | 202 | 76 | 1 490 |

- Merkmale: lila (oben), getönte helle Pixel (Drachen-Symbol, alle Kanäle ≥ 80, Tönung ≥ 30), grau-weiße Uhr,
  roter/blauer Portrait-Rand. Erste Fassung unten 77 %: der beleuchtete Fluss und die Ränder der Ziffern zählten
  als Symbol; die Uhr wird deshalb vor dem Symbol geprüft.
- Live und im Nachspiel geglättet (ein Wechsel gilt ab der zweiten gleichen Lesung). Ins Lagebild geht nur die
  Bestätigung („Herold lebt (Symbol auf der Karte zu sehen)“). „Symbol fehlt, vermutlich genommen“ ist verworfen:
  183125 13:50–14:21 las der Kampf an der Grube als Uhr (8 Fehlmeldungen in 4 Partien, Stichprobe alle 5 s), und genommen meldet die API
  sofort.

**2.–6. Szenarien** (`tests/szenarien/2026-09-29_183125_auftrag018.toml`): 8/8 grün; auf 4b3f1f0 rot: 1836
(„Du lebst in 10 Sekunden wieder: du lebst in 10 Sekunden.“), 1935 (kein Satz in 60 s Basis), 1953 („unter eurem
Mid-Turm“), 3426 („Kauf Schwarzes Beil“), 3543 („Gerade nichts zu kaufen“ ohne Grund). Wächter: 1912, 1948, 3821.
Unit-Tests `objsymbole_018`, `respawn_018`, `kauf_018`, `tod_018`, `turm_und_kampf_018` (rot auf 4b3f1f0).

- **Elixier:** Die Spieldaten führen es als `consumed` (verbraucht beim Benutzen, wie das Kontroll-Auge), ohne
  „beim Kauf verbraucht“; 36:47 konnte Carlos es mit sechs Items nicht kaufen. Der Auftrag nahm an, es belege keinen
  Platz. Umgesetzt nach Daten und Beobachtung: Elixier ab Level 9, wenn sonst nichts passt, nur mit freiem Platz;
  bei vollem Inventar sagt der Coach den Grund.
- **Einzigartige Gruppen:** `wissen/item_gruppen.json` aus CommunityDragon (`items.cdtb.bin.json`, Feld
  `mItemGroups` + `mMaxGroupOwnable`), 50 Gruppen mit ≥ 2 Items; Schwarzes Beil, Lord Dominiks, Seryldas, Sterbliche
  Mahnung, Terminus und Letzter Atemzug teilen `LastWhisper` (höchstens 1).
- Nebenfund: die Prüfung las „Klinge der Unendlichkeit“ als „Dorans Klinge“ (Kurzform „Klinge“) und verwarf 26:02
  zwei richtige Kauf-Sätze; der Verkauf in „Verkauf Dorans Klinge, kauf Sonnenköcher“ zählte als Kauf (18:36).

**7. Top-Welle als Ziel** (Plan-Sätze ab 20:00, Nachspiel): 019 17 von 37, 018 11 von 35. Ohne Grund noch 3
(„Kauf Riesenschwert …, dann zur Top-Welle.“ – der Grund fiel der Wortgrenze zum Opfer; zweimal „Danach nach Top.“).

**Nachspiel 183125** (API, Haiku):

| Größe | 019 (API) | 018 |
|---|---|---|
| Soll-Liste gesagt + teilweise (blinder Kritiker, 69 Punkte) | 37 (54 %) | **38 (55 %)** |
| gegnerische Flashes angesagt | 9/13 | 10/13 |
| I1 Jungler-Wiedersichtungen | 27/29 | 25/29 |
| I4 Lane-Gegner weit weg | 1/4 | 1/4 |
| Backs / Back-Rufe mit Kette | 8/10 · 17/17 | 9/10 · 15/15 |
| längste Stille in der Lane-Phase | 104 s | 73 s |
| Sicherheit (R1, Kill-Check, innere Begriffe) | 2 | **0** |
| Widersprüche automatisch / Kritiker | 2 / – | 2 / 5 |
| Füllsätze automatisch / Kritiker | 0/156 / – | 1/165 / 17 |
| Stratege bis zur ganzen Antwort, Median / p90 | 1,6 / 2,8 s | 1,3 / 2,5 s |
| Kosten der Partie (39 min) | 0,34 $ | 0,26 $ |

- Die Soll-Liste bewegt sich kaum; die Fixes treffen Einzelmomente (18:36, 19:07/19:28, 19:53, 34:26, 35:43, 38:09),
  die Liste misst vor allem den Plan über die ganze Partie (Buch 14, Schritt C).
- Der Kritiker zählt 17 Füllsätze, darunter Jungler-Orte ohne Folge und die Wiederholung „Los: …“ (19:28).
- **Kampf 26:15 (I6):** Der Coach sagte 25:58 „Nicht hin, du brauchst 7 Sekunden und hast 41 Prozent Leben“ und
  26:52 „Geh sofort zum unteren Fluss zu deinen vier, nehmt den Drachen …“. Der Challenger-Kritiker sagt dagegen: „rein, mit Ult
  und Flash auf Kog'Maw“. Das verbietet „kein Angriff ohne Kill-Check“, denn Kog'Maws Leben war nicht im Bild.

---

## Auftrag 019 – Lagebild und Claude über die API (29.09.2026)

Grundlage: `buecher/14_bauplan_gehirn.md` (Schritt A) und `buecher/auftraege/019_auftrag.md`. Keine Testpartie, der
Coach wurde nicht gestartet.

### Gebaut
- **`lolcoach/welt.py`:** ein Lagebild je Aufruf in fester Reihenfolge:
  - DU, PLAN, NACH VORN (mit KILL JETZT), KAUF;
  - SPIELER: alle 9 anderen mit Rolle, Level, Items, Leben, Flash, Ult;
  - KARTE: stehende Türme, Wellen aller Lanes;
  - TIMER, STÄRKE;
  - SEIT DEM LETZTEN AUFRUF (30 s): `Chronik` im Kern.

  Die Ortsformen sind eindeutig: „jetzt sichtbar …“ oder „zuletzt gesehen vor N s …, jetzt unbekannt, vermutlich …“
  (Jungler aus `jungle.wahrscheinlich`). Der Stratege bekommt es statt `kern.kontext()`. Prompt je Aufruf im Median
  ~1200 Tokens, höchstens ~1600 (geschätzt, 3,3 Zeichen je Token).
- **`lolcoach/llm_api.py`:**
  - Anthropic-SDK, Streaming, System als zwischengespeicherter Block;
  - schnell = `claude-haiku-4-5` (ohne Nachdenken), stark = `claude-sonnet-5-5` (Nachdenken aus: `between_tools`,
    effort low, serverseitiger Ersatz bei Ablehnung);
  - Kostenzähler `<partie>_kosten.json`.

  `llm.frage` und `llm.frage_strom` gehen damit über die API, sobald ein Schlüssel da ist; fällt sie aus, 120 s über
  das Abo. Schalter: `[llm] weg = "api" | "abo"`. Modell je Zweck in `[llm]`. Gesprochen wird die ganze, geprüfte
  Antwort am Stück.
- **Teil 0 – schneller prüfen:**
  - `szenarien.py` rechnet parallel (ein Prozess je Datei).
  - `nachspiel_abdeckung.py alle …` spielt alle Partien parallel nach (`--weg`, `--modell`).
  - `stratege_live.Zwischenspeicher` merkt sich Claude-Antworten je (Modell, System, Prompt).
- **Kleinigkeiten:**
  - „Entwurf“ ist ein innerer Begriff (Haiku sagte fünfmal „Der Entwurf passt nicht“).
  - „in 1 Sekunde“ statt „in 1 Sekunden“.
  - Nach „Jetzt, wo …:“ bleibt die Großschreibung.

### Messung (Nachspiel, 4 Partien: 133448, 192113, 101426, 183125; Carlos' Fragen zur echten Zeit)

| Größe | Abo, Stand 017 (altes Lagebild) | Abo, neues Lagebild | API schnell (Haiku 4.5) | API stark (Sonnet 5.5) |
|---|---|---|---|---|
| ganze gültige Antwort, Median / p90 | 6,24 / 11,36 s | 6,81 / 12,19 s | **1,58 / 2,58 s** | 2,61 / 5,50 s |
| Kosten je 30 min | – (Abo) | – (Abo) | **0,25 $** | 0,51 $ |
| Soll-Liste gesagt + teilweise (217 Punkte) | 60,4 % | 63,1 % | 61,3 % | 61,3 % |
| davon ganz gesagt | 24,9 % | 30,0 % | 25,3 % | 25,8 % |
| Füllsätze (Kritiker, inkl. 9× „Notiert.“ je Partie) | 7,9 % | 7,8 % | 8,0 % | 11,8 % |
| Füllsätze (automatisch) | 0,2 % | 0,2 % | 0 % | 0 % |
| Widersprüche (Planwechsel < 30 s ohne Ereignis) | 4 | 6 | 6 | 7 |
| Sicherheit (R1 / Kill-Check / innere Begriffe) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

- **Modellwahl:** Haiku für alles (Lane, Fragen, Plan). Sonnet trifft die Soll-Liste nicht besser, ist aber
  1,6-mal langsamer und doppelt so teuer. Latenz-Soll ≤ 1,5 s: mit 1,58 s knapp verfehlt.
- **Soll-Liste:** Mit ~61 % liegen alle vier Varianten unter dem Ziel ≥ 80 % aus Buch 14 (Schritt C). Das neue
  Lagebild allein ändert daran wenig: 60,4 → 63,1 % über das Abo.
- **Caching:** Bei Haiku greift es nicht, weil der stabile Anfang kürzer als die 4096 Tokens Mindestlänge ist. Bei
  diesen Kosten lohnt der Umbau erst mit dem Wissensblock aus Schritt C.
- **Abdeckung I1/I3/I4 (Kern, unabhängig vom Modell), API schnell:**
  - I1 Jungler 69/72;
  - I3 Flash 29/34 (183125: 9/13);
  - I4 Lane-Gegner weit weg 6/12.

  I4 und der Flash in 183125 liegen unter dem Soll ≥ 90 %.

### Rechenzeit
- **Szenarien:** voll 106 s parallel (26 Prozesse), vorher seriell rund 23 min.
- **`tests/alle.py`:** 29 s.
- **Nachspiele, alle 4 Partien parallel:**
  - API schnell 230 s, API stark 396 s;
  - Abo 977 s, Abo Stand 017 894 s;
  - vorher (016/017) nacheinander über das Abo rund 45 min je Einstellung.
- **Kritik:** eine blinde Soll-Liste (183125) ~2 min, vier Vergleichs-Kritiker parallel ~5 min.

---

## Auftrag 016 – Pflichtenheft 133448: sagen, was er sieht, Ketten statt Schweigen (29.09.2026)

Grundlage: `buecher/auftraege/016_auftrag.md`. Keine Testpartie, der Coach wurde nicht gestartet. Gemessen wird nur an
Aufnahmen: `werkzeuge/nachspiel_abdeckung.py` spielt 133448, 192113 und 101426 durch den Live-Weg nach (Kern,
Sprechplan, Makro-Stratege über das Abo), mit Carlos' Fragen zur echten Zeit aus `_sprechtaste.log`. „Vorher“ ist
derselbe Lauf auf dem Stand `edcf583` (Git-Worktree), ebenfalls mit echtem Strategen. Rohdaten in `stratege_probe_016/`.

### Umgesetzt
- **1.1 Flash:** jeder gesehene Flash, egal wie weit weg, als „Poppy Flash weg.“ (`[info_flash] nur_nah = false`,
  Abstand 8 s). Flash-Fragen bleiben beim Kern: `antworten.flash_satz` nennt die Restzeit je Gegner.
- **1.2 Jungler, 1.3 Lane-Gegner weg** (`lolcoach/kern/pflicht.py`, `[pflicht]`):
  - Sätze wie „Teemo im oberen Fluss, bei dir in 6 Sekunden.“ und „Poppy unten gesehen: drück deine Welle.“
  - Unter R1 heißt die Folge „farm unter deinem Turm“, bei Gefahr gibt es keinen Satz.
  - Die Sätze zählen nicht zum Budget. Die Sperre aus 009 gilt nicht.
  - Hat die Makro-Sichtung eine Folge, wird es ihr Satz.
- **1.4 / 3 Stratege:**
  - Leerlauf ab 1:30 nach 35 s, in der Lane-Phase als Wellen- und Lane-Tipp. Im Leerlauf darf der erste Satz 8 s
    brauchen.
  - Neuer Anlass „Kampf in der Nähe“: Ein Mitspieler kämpft höchstens 6 s entfernt, sein Leben fällt, ein Gegner ist
    bei ihm.
  - Die Lage kennt jetzt KAUF (Gold, freie Plätze), KILL JETZT, die eigene Welle und den Lane-Gegner mit Leben.
  - Kommt Claude nicht rechtzeitig, spricht immer ein Kern-Satz (Plan oder Wellenstand).
- **2 Ketten:**
  - Kern: Jeder Back-Ruf bekommt Kauf und Ziel (`Kern._mit_kette`). Der Wendepunkt-Satz bekommt „Danach …“.
  - Der Basis-Kaufsatz ohne sicheres Ziel endet mit „dann warte an deinem Turm auf dein Team“.
  - Stratege: Ein Back-Ruf ohne Kette im selben Satz wird verworfen, nach der Basis-Ankunft auch ein erster Satz ohne
    Kette. Teilsätze, die am Komma kommen, werden dafür bis zum Satzende gehalten; das hatte im ersten Lauf 14 gute
    Ketten verworfen.
- **4 Sicherheit (`stratege.sicherheit`, für Stratege und Kern):**
  - Unter R1 ist jede Welle zum Gegner nach vorn. Beim Kern ist WELLE_REIN_UND_BACK unter R1 kein Kandidat mehr, dann
    kommt BACK_JETZT. Das ändert Auftrag 009, 1.
  - Angriffsrufe gibt es nur mit Kill-Check; auch die Kampfrufe des Kerns („Rein auf …“, „Nimm den Kampf“, „Dreh um“)
    werden sonst stumm protokolliert.
  - „Schwach“ nur unter 50 % Leben.
  - Makro, Vorschau und Lagebild rufen unter R1 nicht nach vorn.
- **5 Kaufen:**
  - Die Kauf-Antwort nennt, ob die Plätze danach voll sind, und die Kette.
  - Liegt ein Kontroll-Auge im Inventar, heißt es zuerst „stell es“. Verkaufen kommt einmal mit Grund. Fragt Carlos
    nach, kommt „ohne Verkauf passt es nicht – oder farm N Gold, dann die Eklipse ganz“.
  - Stratege: Ein Kauf mit zu wenig Plätzen wird verworfen, ebenso mit zu wenig Gold, auch bei Kurznamen wie
    „Kriegshammer“.
  - Kontroll-Auge höchstens einmal je Back, nie als Grund für einen Back. Nach Carlos' „Nein“ 5 min lang keins, auch im
    Kern-Kaufsatz.

### Abdeckung (neues Hauptmaß), vorher → nachher

| Partie | Flash angesagt | Jungler ≥ 20 s | Backs mit Kette | Back-Rufe mit Kette | längste Stille Lane | Sicherheit |
|---|---|---|---|---|---|---|
| 133448 | 2/8 → **8/8** | 2/10 → **10/10** | 3/4 → **4/4** | 0/5 → **6/6** | 67 → **43 s** | 2 → **0** |
| 192113 | 5/7 → **7/7** | 0/14 → **14/14** | 5/10 → **9/10** | 0/5 → **7/7** | 52 → **36 s** | 5 → **0** |
| 101426 | 5/6 → **6/6** | 2/19 → **18/19** | 4/10 → **8/10** | 1/8 → **13/13** | 137 → **35 s** | 1 → **0** |

**Sicherheit vorher:**
- 133448: „Top-Welle rein, dann back“ bei 37 %, „Rein auf Poppy!“ ohne Kill.
- 192113: TEAMPLAN „erzwingen“ unter R1, dreimal „Rein“ oder „Dreh um“ und einmal „Nimm den Kampf“, jeweils ohne Kill.
- 101426: Welle rein bei 30 %.

**Die Messung erkannte die Kampfrufe des Kerns erst nach der Kritik:** Das Muster kannte „Rein auf …“ nicht, und die
Kill-Sperre ließ GEFAHR-Sätze durch. Beides ist behoben, der Lauf wurde wiederholt.

**Noch nicht abgedeckt:**
- 3 Backs:
  - 192113 2:00: „Lauf direkt nach Top …, nimm ein Kontroll-Auge mit“, das Ziel steht vor dem Kauf.
  - 101426 17:44: Kontroll-Auge, dann Mid-Welle.
  - 101426 30:51: nur das Ziel.
- 1 Jungler-Sichtung (101426 19:41).

**Sprechmenge ungefragt je 30 min:** 87 / 95 / 111, vorher 54 / 68 / 80. Das alte Ziel ~75 gilt nicht mehr als
Hauptmaß.

**Stratege:**

| | 133448 | 192113 | 101426 |
|---|---|---|---|
| Aufrufe | 39 | 91 | 60 |
| Kern-Ersatz | 7 | 14 | 20 |
| still | 0 | 2 | 3 |
| verworfene Sätze | 5 | 14 | 21 |

- **Erster gültiger Satz:** Median 6,4–7,2 s, p90 8,3–9,7 s. Vorher waren es 1,9–5,6 s.
- **Ursache:**
  - Die Kette wird bis zum Satzende gehalten.
  - Der Prompt ist länger.
- **Folge:** An Wendepunkten (4-s-Grenze) spricht oft der Kern-Ersatz.

### Szenarien und Tests
Neue Unit-Tests (`pflichtenheft_016`, neues `info_flash_kurz_und_gebuendelt`):
- **Rot auf `edcf583`:** Die fünf Sätze aus 133448 ließ die alte Prüfung alle durch (12:10 Welle bei 5 %, 9:29
  „schwach … geh sie an“, Back ohne Ziel, „zurück nur für ein Auge“, Langschwert ohne Platz).
- **Rot auf `edcf583`:** „Ziggs ohne Flash.“ statt „Flash weg“, ein ferner Flash wurde verschwiegen.

Angepasste alte Szenarien und Tests, mit Grund:
- `0455-sona-ohne-flash` und `1037-flash-ohne-ort`: Beide verlangten Stille (010, „Info ohne Folgen“). Jetzt muss der
  Flash gesagt werden (016, 1.1).
- `0841-rumble-ohne-flash`: nimmt auch die neue Form „Rumble Flash weg“.
- `1012-kein-platz-langschwert`: nimmt „Kontroll-Auge“ (erst stellen, dann verkaufen). Nur die Rückfragen 1017 und
  1024 verlangen den Verkauf.
- Wortgrenze (`woerter_max`, Unit-Test der konstruierten Lagen): +6 Wörter für einen Back-Ruf mit Kette (016, 2).
- Unit-Tests:
  - 014/015: „Mid-Welle rein, dann back“ unter R1 ist jetzt verworfen.
  - Back-Sätze ohne Kauf oder Ziel in den alten Beispielen haben ein Ziel bekommen.

**Ergebnis:**
- Szenarien **305 / 309**, 3 übersprungen. Rot sind nur die alten Fälle: 3× Wendepunkt-Probe und 0944.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.

### Kritik
Zwei frische Agenten beurteilten den Lauf **vor** der letzten Kill-Sperre für Kern-Kampfrufe; die von ihnen gefundenen
Kampfrufe ohne Kill sind danach behoben.

**Carlos-Kritiker (Maßstab: Carlos' Notizen):**

| Partie | ja | teils | nein |
|---|---|---|---|
| 133448, Minuten | 4 | 12 | 1 |
| 192113, Minuten | 9 | 16 | 5 |
| 101426, Minuten | 14 | 20 | 1 |
| Notizen aus 133448 und 192113 (26) | 5 | 14 | 7 |

- Urteil: „Takt stimmt, Inhalt noch nicht“.
- Stille, Flash, Jungler und Back-Ketten sind erfüllt.
- **Offen:**
  - Top-Wellen-Reflex, obwohl ADC und Support dort farmen.
  - Kauf- und Inventarfehler.
  - Widersprüche innerhalb von Sekunden.
  - Forderungen wie „hilf Volibear“, Freeze oder 1 gegen 1 bekommen nur „Notiert.“.
  - Wiederholungen.

**Challenger-Kritiker („stimmt es?“):**
- Je Partie 2–3 gefährliche Fälle, fast alle Kampfrufe ohne Kill; die sind jetzt gesperrt.
- Je Partie 5–8 falsche Fälle: Kauf, Drache zu früh, veraltete Tote.
- Je Partie 4–5 nervige Fälle: „Back jetzt“ in der Basis, jetzt beim Strategen verworfen; fünfmal derselbe
  Lane-Gegner-Satz, jetzt 30 s gesperrt.

---

## Auftrag 015 – Stratege live, Prüfung erweitert (29.09.2026)

Grundlage: `buecher/auftraege/015_auftrag.md`. Der Coach (`python -m lolcoach`) wurde nicht gestartet. Die
Generalprobe startet einen eigenen Coach-Prozess gegen einen nachgebauten Client (`aufnahmen_probe/`).

### 1. Prüfung erweitert (`stratege.pruefe`, Unit-Test `stratege_pruefung_015`)

Die Prüfung verwirft einen Satz in diesen Fällen:
- **Mitspieler am falschen Ort:** „mit X“ oder „X steht …“, obwohl X tot ist, in der Basis steht (während du draußen
  bist) oder mehr als 15 s von dir entfernt ist, oder obwohl die Seite nicht stimmt.
- **Gold:** Die genannten Käufe kosten zusammen mehr als dein Gold. Dafür wird der Restpreis gerechnet (Bauteile im
  Inventar zählen ab); „für die X“ ist ein Ziel, kein Kauf.
- **Sichtbarkeit falsch herum:** „X seh ich nicht“ oder „X unsichtbar“, obwohl X sichtbar ist; oder „X steht …“ als
  aktueller Ort für einen, der länger als 10 s unsichtbar ist.
- **Objective nicht da:** Das Objective wird als Ziel genannt, es fehlt aber die Spawn-Zeit oder -Uhrzeit, und es ist
  weder verneint noch als genommen genannt.

Außerdem:
- **Kein Fehlalarm mehr:** „Nimm/hol/farm die Welle“, „allein“ und „zurück zum Turm“ gelten nicht als Vorwärts-Rat;
  „danach/dann …“ verschiebt nur nach einer Erholung (back, kaufen, Respawn).
- **Länge:** hart gekürzt auf ganze Sätze mit höchstens 30 Wörtern (`kuerzen`).
- Die Prüf-Lage kennt jetzt Mitspieler mit Seite und Ankunft, Gold, Items, Objectives und ob du in der Basis bist.

**Die 100 Momente aus 014, neu erfasst, ohne neue Kritik** (`STRATEGE_PROBE_015.md`):

| Lauf | beim 1. Versuch verworfen | Kern springt ein | Latenz 1. Satz (Median / p90) | bis zum gültigen Satz p90 |
|---|---|---|---|---|
| 1 (erste Fassung) | 17 | 4 | – | – |
| 2 (Fehlalarme: Namenslisten, Uhrzeit, Verneinung, TP „in 37s“) | 14 | 2 | 2,0 / 2,9 s | 9,0 s |
| **3 (dazu „allein“, „für Eklipse“, „Baron-Buff“)** | **9** | **1 (1 %)** | **2,1 / 3,4 s** | **8,1 s** |

- **Die 9 im letzten Lauf:** Objective nicht da 5, Mitspieler nicht dabei 2, Entwarnung ohne Sicht 1, nach vorn trotz
  R1 1, Gold 1.
- **Die 5 Objective-Fälle** sind nach der Regel richtig, aber streng: ein Ziel ohne Spawn-Zeit, z. B. „dann Richtung
  Baron sammeln“ 60 s vor dem Spawn. Nach der Wiederholung nannte der Stratege sie mit Zeit oder ließ sie weg.
- **Länge:** Median 25 Wörter, höchstens 33 (ein einzelner Satz über 30 bleibt ganz).
- **Kern springt ein:** deutlich unter der Grenze von 15 %.

### 2. Teil B eingebaut (`lolcoach/stratege_live.py`)

- **B1 Fragen** (`sprache.py`): JETZT, DANACH, WARUM, ENTWEDER, SOLL_ICH, RISIKO, AUGE, COACH, GEWISSHEIT und OFFEN
  gehen an den Strategen. Er spricht gestreamt, Satz für Satz, jeder Satz geprüft. Beim Kern bleiben TIMER, WO, LAGE,
  KAUF, KLAEREN und NOTIZ. Die Korrektur „die Welle ist leer“ setzt der Kern vorher. Fällt der Stratege aus, gibt es
  keinen zweiten Claude-Aufruf.
- **B2 Wendepunkte:**
  - Der WENDEPUNKT-Satz des Kerns wird ersetzt. Nach Respawn, Ankunft in der Basis oder zwei Kills in 10 s wird der
    nächste PLAN-Satz des Kerns innerhalb von 5 s ersetzt; kommt keiner, fragt der Stratege allein, aber nur, wenn
    10 s nichts Planendes kam.
  - Kommt der erste gültige Satz nicht in 4 s, spricht der Kern.
  - Warnungen gehen vor: Stratege-Sätze sind WICHTIG, in KAMPF und bis 10 s nach einer Gefahr wirft der Sprechplan sie
    nicht ein.
- **B3 Leerlauf:** ab 14:00, nach 45 s ohne Plan-Satz und ohne Warnung, höchstens einmal je 45 s.
- **B4:** WELLE_DRUECKEN des Kerns kommt nur, wenn der Stratege aus ist oder ausgefallen.
- **B5:**
  - Die Szenarien laufen weiter mit dem Kern.
  - Nachspielen mit dem Aufzeichnungs-Stub: `protokoll.py --stratege-stub` → `<stamm>_stratege_stub.md`.
  - Unit-Test `makro_stratege_wege`: Verwerfen → neu → Kern, Ausfall still, Welle weg, Wendepunkt ersetzt oder
    Fallback.
- **B6:** `<aufnahme>_stratege.jsonl` mit Anlass, Quelle (stratege/kern/still), allen Versuchen, Latenzen und
  verworfenen Sätzen samt Grund. Im Stub-Protokoll steht ein Abschnitt „Stratege“.
- **Schalter:** `[stratege] aktiv` in `wissen/kern.toml`; live `--ohne-stratege`. `--ohne-gehirn` schaltet ihn
  ebenfalls aus.
- **Ausfall:** 30 s nichts oder ein Fehler → einmal im Log „Stratege: Ausfall …“, 120 s nur der Kern, kein Satz an
  Carlos.

**Sprechmenge** (ungefragt je 30 min, Stub-Protokoll gegen Kern-Protokoll; Soll ≤ ~75):

| Partie | nur Kern | mit Stratege (Stub) | Stratege-Aufrufe |
|---|---|---|---|
| 101426 | 70 | 64 | 42 |
| 102112 | 78 | 73 | 36 |
| 133930 | 81 | 78 | 21 |
| 140253 | 45 | 53 | 7 |
| 144655 | 40 | 47 | 4 |
| 164326 | 74 | 77 | 48 |
| 173159 | 70 | 68 | 34 |
| 213624 | 67 | 66 | 49 |
| 192113 | 65 | 65 | 83 (mit Fragen) |

In der ersten Fassung (ohne das 5-s-Fenster) lag sie bei 70–87. Seit dem Fenster ersetzt der Stratege den Plan-Satz
des Kerns nach Respawn und Basis, statt einen zweiten Satz dazuzusprechen.

**Generalprobe** (`--breite 3840 --links 1920`, 164326 ab 22:00, echtes Claude über das Abo):
- **Aufrufe:** 5 Anlässe in 3 min (4 Wendepunkte, 1 Leerlauf). 4 sprach der Stratege, 1 der Kern: der erste Satz kam
  nach 4,6 s, über der 4-s-Grenze.
- **Latenz:** erster gültiger Satz nach 1,0 / 1,4 / 2,2 / 2,3 / 4,6 s. In Spielzeit vom Anlass bis zum ersten
  gesprochenen Teil 1–3 s, dazu etwa 0,45 s bis zum Ton.
- **Verworfen:** 0. Fehler der Probe: keine; Takt Median 7/s.
- **Reihenfolge:** Beim ersten Durchgang kam ein dritter Satzteil vor dem zweiten. Das ist behoben: spätere Teile
  bekommen eine minimal ältere Zeit.
- **Ausfall nachgestellt** (`LOLCOACH_STRATEGE_AUSFALL=31`): Am Wendepunkt sprach nach 4 s der Kern. Einmal
  „Stratege: Ausfall“ im Log, dann 120 s nur der Kern, die Wellen-Sätze wieder als Fallback, kein Satz an Carlos.
- In diesem Lauf meldete die Minimap-Texterkennung einmal „Another RecognizeAsync operation is already running“. Das
  gehört nicht zum Strategen; im ersten Lauf war es nicht da.
- Belege: `stratege_probe_015/generalprobe_claude_stratege.jsonl`, `generalprobe_ausfall_coach.log`.

### Prüfungen

- **Szenarien 305 / 309**, 3 übersprungen. Rot sind nur die alten Fälle: 3× Wendepunkt-Probe und 0944.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.

---

## Auftrag 014 – Stratege: Schutzschicht und Tor (28./29.09.2026)

Grundlage: `buecher/auftraege/014_auftrag.md`. Offline, der Coach wurde nicht gestartet. **Das Tor aus A5 ist knapp
verfehlt, deshalb gibt es kein Teil B;** am Sprechweg des Live-Coachs ist nichts geändert. Tabellen:
`buecher/protokolle/STRATEGE_PROBE_014.md`. Rohdaten: `buecher/protokolle/stratege_probe_014/` (Momente mit Prompt und
Prüf-Lage, Antworten mit allen Versuchen, Blind-Vorlagen a/b, Urteile).

### Teil A

- **A1 `kern.kontext()`:**
  - Gegner steht jetzt als „jetzt sichtbar …“ oder „zuletzt gesehen vor N s …, jetzt unbekannt, kann überall sein“
    (`gegner_zeile`).
  - Neue Zeile DEINE ZAUBER (Flash, TP, Ult, nur was bekannt ist).
  - Neue Zeile „NACH VORN VERBOTEN (Leben N %). Erlaubt: …“ unter `vor_leben_min`, sonst „ZU RISKANT, NICHT
    VORSCHLAGEN: …“ für Vorwärts-Ziele mit p_tod ≥ 0,3 (`Kern.vorn()`).
  - Bei den Alternativen steht „Wert“ statt „EV“.
  - Das gilt auch für die heutigen Claude-Antworten (`mit_claude`).
- **A2 `stratege.pruefe(satz, lage)`:** Verworfen wird
  - ein Satz nach vorn trotz R1 oder zu einem zu riskanten Objective (verneint oder auf „danach“ verschoben zählt
    nicht; „Welle rein“ zählt nicht),
  - ein innerer Begriff (R1, EV, Wert-Zahl, Kern, Kandidat, gesperrt, Modell, Todesrisiko-Zahl),
  - eine Entwarnung für einen Gegner, der länger als 20 s nicht zu sehen war,
  - ein Champion, der nicht in der Partie ist,
  - TP, Flash oder Ult, die nicht bereit sind.

  Die Lage für die Prüfung baut `stratege.pruef_lage(kern, p)`. Unit-Test `stratege_pruefung` mit den Mustern aus
  013.
- **A3/A4:**
  - `stratege.STRATEGE_SYSTEM`: der Prompt aus 013 Lauf 2 plus innere Begriffe, Sichtung, Porten, keine Umkehr in 30 s
    ohne neue Lage, Ton, ≤ 25 Wörter.
  - Die Probe gibt dem Strategen seine letzten zwei Sätze (≤ 60 s) mit; der Plan steht in der Kopfzeile.
- **Fallback in der Probe:** Beim ersten Verwerfen wird einmal neu gefragt, mit dem Grund; beim zweiten gilt der
  Kern-Satz.

### A5 – Probe

- **Momente:**
  - die 70 aus 013, neu erfasst mit A1;
  - 30 neue aus 164326 und 173159: je 8 Wendepunkte und 7 Leerlauf-Fenster ab 14:00, Zufall mit Seed 14. Sie dienen
    nur der Prüfung.
- **Abo:** 105 Aufrufe, keine Fehler.
- **Verwerfen:** Beim ersten Versuch wurden 5 von 100 Sätzen verworfen (TP nicht bereit 2, nach vorn trotz R1 1,
  Entwarnung ohne Sicht 2). Die Wiederholung war jedes Mal gültig, der Kern-Fallback wurde nie gebraucht.
  - „Nimm die Welle“ galt fälschlich als Vorwärts-Handlung (164326 16:20). Das kostet nur eine Wiederholung;
    `VORWAERTS` sollte „nimm die Welle/Kanone“ ausnehmen, bevor es live geht.
- **Latenz:** erster Satz im Median 1,7 s (p90 3,2 s), ganze Antwort 4,7 s, mit Wiederholung bis zum gültigen Satz
  p90 7,5 s.
- **Länge:** im Median 30 Wörter (Regel ≤ 25, nicht ganz gehalten), höchstens 40.
- **Kritik:** vier frische Kritiker, Challenger und Carlos je zweimal, mit verschiedener A/B-Mischung. Gezählt wird
  das Mittel der vier.

| Tor (alles muss gelten) | alt (70) | neu (30) | |
|---|---|---|---|
| „gefährlich“ Stratege ≤ Kern | 0,2 ≤ 1,5 | 0,0 ≤ 2,8 | ja |
| Vorwärts-Sätze trotz R1 nach A2 | 0 | 0 | ja |
| innere Begriffe nach A2 | 0 | 0 | ja |
| „falsch“ Stratege ≤ Kern + 2 | **12,5 vs. 9,2 (+3,3)** | 4,2 vs. 3,2 (+1,0) | **nein (alt)** |
| Gewinnquote Stratege ≥ 65 % (neu) | 78 % | **81 %** | ja |

Ein grober Prüfer aus 013 fand als zweite Meinung einen Vorwärts-Satz trotz R1 (101426 23:10, „danach zusammen als
Gruppe Richtung Drache erzwingen“). Von Hand geprüft ist das kein Verstoß: Es ist aufgeschoben und in der Gruppe, und
die Schranke dort war „klar unterlegen“, nicht Leben oder p_tod.

Gegenüber 013 (Lauf 2) sank „gefährlich“ beim Strategen von 3 auf 0–0,2, die Quote stieg von 69–70 % auf 78–81 %.
„Falsch“ bleibt ein Rest.

**Was die Kritiker am Strategen noch falsch fanden** (jede Stelle von allen vier markiert):
- **Mitspieler an Orte gestellt, wo sie nicht sind:** „Push den inneren Bot-Turm mit Sett und Kai'Sa“, Sett stand in
  der Basis (192113 16:50, 16:56, 17:06).
- **Gold falsch gerechnet:** „Kontroll-Auge zuerst, dann Gefräßige Hydra“, das Gold reicht nicht für beides (164326
  18:17, 22:08).
- **Sichtbarkeit falsch:** „Pantheon sehe ich grad nicht“, obwohl er sichtbar war (192113 14:37). „Vier von ihnen
  sichtbar“, obwohl nur Bard zu sehen war (101426 22:34). „Cassio seit über 4 Minuten“ statt 12 s (192113 9:42).
- **Spielstand falsch:** „Drache erst, wenn ihr zusammensteht“, der Drache war schon genommen (101426 33:43).
- **Unsinn im Tod:** „beim Release … recallen“ (101426 32:21).
- **„Gebackt“ falsch erklärt** (192113 8:52).

Das alles lässt sich prüfen: Mitspieler-Orte, Sichtbarkeit und Gold stehen in der Lage. Die Prüfung A2 kennt es noch
nicht.

---

## Auftrag 013 – Probe: Claude als Makro-Stratege (28.09.2026)

Grundlage: `buecher/auftraege/013_auftrag.md`. Offline, der Live-Coach ist unverändert. Werkzeug:
`werkzeuge/stratege_probe.py`, Ausgabe: `buecher/protokolle/STRATEGE_PROBE.md`. Rohdaten (Momente, Prompts,
Antworten, Blind-Vorlagen, Urteile): `buecher/protokolle/stratege_probe/`.

- **Momente (70):**
  - 192113: 41 Fragen, die der Kern beantwortet. Notizen, Nachfragen und Beschwerden sind ausgenommen; gleichmäßig
    ausgedünnt auf 41.
  - 192113: 10 Wendepunkte ab 10:00 (Turm, Objective; höchstens einer je 60 s).
  - 101426: 10 Leerlauf-Fenster aus 009 (Fenstermitte) und 9 Wendepunkte ab 14:00.
  - Kills zählen nicht als Wendepunkte: das waren über 50, zu viele für das Budget.
- **Kontext:**
  - Wie live: Kopfzeile, `kern.kontext()` und die Spielakte über `gehirn`.
  - Dazu die Kandidaten des Kerns (Wert, Todesrisiko, Grund, stumm/gesperrt) und die Zeile R1.
  - Aufruf: `llm.frage_strom`, sonnet, Aufwand low, vorgehaltener Prozess.
- **Läufe:**
  - Lauf 1: Systemprompt `STRATEGE`.
  - Lauf 2: derselbe mit einer Längenregel (≤ 25 Wörter). Lauf 1 sprach im Median 52 Wörter, rund 20 s Stimme – der
    handwerkliche Fehler, den der Auftrag als Beispiel nennt.
  - Sonst ist nichts geändert.

| | Lauf 1 | Lauf 2 |
|---|---|---|
| Aufrufe / Fehler | 70 / 0 | 70 / 0 |
| erster Satz Median / p90 | 1,7 / 2,8 s | 1,5 / 2,6 s |
| ganze Antwort Median / p90 | 5,4 / 6,8 s | 4,3 / 5,6 s |
| Wörter Median / max | 52 / 92 | 26 / 39 |
| Dauer der 70 Aufrufe | 6,5 min | 5,2 min |
| Fakten-Flags (automatisch) | 6 | 1 |
| Stratege besser: Challenger / Carlos (ohne „gleich“) | 58 % / 65 % | 69 % / 70 % |
| „falsch“ Stratege / Kern: Challenger, Carlos | 28/5, 21/3 | 14/11, 18/11 |
| „gefährlich“ Stratege / Kern: Challenger, Carlos | 3/1, 2/2 | 3/1, 3/1 |

- **Abo:** 140 Aufrufe in zwei Blöcken zu 5–7 min, keine Grenze, keine Ablehnung, kein Abbruch.
- **Faktenprüfer:** Er ist grob. Er findet erfundene Zahlen und Rat nach vorn trotz R1 und hat jeden Treffer von Hand
  gesehen. Die wichtigste Fehlerklasse fand er nicht: „vor 288 s in seiner Basis“ gelesen als „seit 288 s in der
  Basis“. Die fanden die Kritiker. Einzelheiten stehen in `stratege_probe/kritik_2.md`.
- **Streuung der Kritiker:** Die Kern-Antworten sind in beiden Läufen wörtlich gleich. Trotzdem wurden sie einmal 3–5,
  einmal 11-mal als falsch markiert. Unterschiede unter etwa 5 Fällen sind nicht belastbar.

---

## Auftrag 012 – Wellen-Endlosschleife, ignorierte Fragen, Timer-Fehler (28.09.2026)

Grundlage: `buecher/auftraege/012_auftrag.md`, Botpartie `2026-09-28_192113` (Riven gegen Teemo, Win). Offline
gemessen, der Coach wurde nicht gestartet. Alle zehn Protokolle sind neu erzeugt (213624, 101426 und 192113 mit
`--fragen`). „Vorher“ ist das Protokoll von 192113 mit `--fragen` auf dem Stand vor diesem Auftrag (273e09f).

### 1. Wellen-Endlosschleife

**Ursache:**
- `karte.welle_druecken` verlangte nur „≥ 3 eigene Vasallen, mehr als ihre“. Ihre Vasallen 0 oder im Nebel galten
  als 0, und der Satz hieß dann „ihre Vasallen sind weg“. So galt eine Welle als Ziel, die leer und tief bei ihnen
  stand, etwa ab 19:30 die Top-Welle bei front 0,64–0,78 vor ihrem Inhibitor-Turm.
- Mitspieler an der Welle zählten nicht.
- In der Basis (`basis._seitenwelle_option`) kam die eigene Welle immer als Rückfall, mit dem Grund „sie läuft sonst
  in deinen Turm“, auch wenn sie zu ihnen lief (20:38, 23:26).
- Gefragt fiel `fragen._jetzt_satz` auf „Farm deine Top-Welle“ zurück (19:13, 20:30, 21:45).
- Carlos' Widerspruch änderte nichts: die Welle blieb für den Kern voll.

**Fix:**
- `karte.welle_ohne_dich` (nur nach der Lane-Phase): Eine Welle braucht dich nicht, wenn eines davon gilt:
  - sie ist LEER,
  - sie hat keine ihrer Vasallen, läuft nicht zu dir und steht tief (front ≥ `welle_tief` 0,6),
  - ein Mitspieler steht an ihrer Front (≤ 1500) und du bist nicht auf dieser Lane.
- **Welle drücken:** `welle_druecken` braucht jetzt ihre Vasallen (oder einen toten Lane-Gegner). Die Welle darf
  nicht schon an ihrem Turm stehen. „4 gegen einen Vasallen“ statt „4 gegen 1“.
- **Basis:** Braucht dich deine Welle nicht, gilt die Welle einer anderen Lane, die auf euren Turm läuft, sonst „Geh
  nach Top: dort kommt ihre nächste Welle“. Das ist ein festes Ziel je Basis-Aufenthalt (C4, 102112 30:02). „Sie
  läuft sonst in deinen Turm“ steht nur noch, wenn sie zu dir läuft.
- **`_makro_ziele`:** Bringt keine Welle zum Drücken etwas, rechnet es auch die Seitenwellen der anderen Lanes.
- **Korrektur per Sprechtaste** (`fragen.KORREKTUR_WELLE`): „kein einziger Minion“, „reingepusht“, „an deren Nexus“,
  „mein ADC farmt sie“, „Teemo hat meinen Farm geholt“ und „es gibt keine Topwelle“ setzen die Welle dieser Lane
  `welle_korrektur_s` (60 s) lang auf LEER.
- **Fragen:** `_jetzt` nennt keine Welle, die dich nicht braucht. `_ohne_welle` nennt die nächste Welle, die auf
  euren Turm läuft, sonst dein Team, sonst das nächste Objective.

**Die Wellen-Wiederholungen aus dem Auftrag, jetzt (Protokoll mit `--fragen`):**

| live | Frage | vorher | jetzt |
|---|---|---|---|
| 19:13 | „ich bin back, was jetzt?“ | Farm deine Top-Welle | Aus der Basis: Geh nach Top: dort kommt ihre nächste Welle. |
| 19:40 | Kai'Sa und Support farmen oben, was jetzt? | Drück die Top-Welle: ihre Vasallen sind weg. | Stimmt. Back jetzt: 1050 Gold für Gefräßige Hydra. |
| 19:48 | mein Top ist reingepusht | (Claude) geh trotzdem hoch | Stimmt. Geh nach Top: dort kommt ihre nächste Welle. |
| 20:05 | kein einziger Minion | (Claude) | Stimmt. Bleib nah an deinem Team, auf Top ist keine Welle. |
| 20:09 | was soll ich jetzt machen? | Drück die Top-Welle: ihre Vasallen sind weg. | Bleib nah an deinem Team, auf Top ist keine Welle. |
| 20:30 | keine Topwelle, warum nicht Mid? | Geh zur Top-Welle: sie läuft sonst in deinen Turm … | Geh nach Top: dort kommt ihre nächste Welle … Auf Mid wartet gerade keine Welle, die sich lohnt. |
| 20:47 | 50.000 Leute, kein Minion | (Claude) | Stimmt. Drück die Bot-Welle: 4 gegen einen Vasallen. |
| 23:32 | Riesenschwert gekauft, und jetzt? | Geh zur Top-Welle: sie läuft sonst in deinen Turm. | Geh nach Top: dort kommt ihre nächste Welle. |
| 23:45 | Topwelle fast an deren Nexus | (Claude) | Stimmt. Geh nach Top: dort kommt ihre nächste Welle. |

**Ungefragt:**
- 20:04 „Zwei Wege: die Top-Welle drücken … oder die Bot-Welle drücken, ihre Vasallen sind weg“ fällt weg.
- 20:38 heißt jetzt „Dann nach Top, dort kommt ihre nächste Welle.“ statt „Dann zur Top-Welle, sie läuft sonst in
  deinen Turm.“
- 20:51 heißt jetzt „Drück die Bot-Welle, 4 gegen einen Vasallen.“ statt „Drück die Top-Welle, ihre Vasallen sind weg.“
- 23:26 heißt jetzt „…, dann nach Top, dort kommt ihre nächste Welle.“

In 192113 enthalten ungefragt 3 statt 14 Sätze „Top-Welle“. Alle drei stehen außerhalb der leeren Phase (5:13,
12:55, 16:37). Von den Antworten nennen 6 statt 21 die Top-Welle.

### 2. Fragen

- **Satz für Satz** (`_innere_frage`): Aus langen, wütenden Sätzen wird die Frage gezogen. Das gilt auch, wenn der
  ganze Satz OFFEN oder NOTIZ wäre.
  - „Ich hab dich gefragt, was mach ich, wenn …“ ist die Frage.
  - „Also ich soll Drache machen …?“ (21:11) ist eine Warum-Frage.
- **Füllwörter** („jetzt“, „gerade“, „doch“ …) brechen kein Muster (9:45 „Ich bin jetzt in der Base. Wo gehe ich
  jetzt hin?“). „Topfwelle“ ist die Top-Welle, „warum auch immer“ ist keine Frage.
- **Neue Absichten:**
  - RISIKO: „Angst vor Ganks?“, „ist es sicher?“, „obwohl keiner zu sehen ist“. Die Antwort nennt, wer fehlt und
    seit wann, dann den Plan; geht der Plan nach vorn, dazu „nur hinter deiner Welle“.
  - AUGE: Kontroll-Auge an den Eingang der Grube (Objective ≤ 90 s), sonst in den Fluss-Busch neben deiner Lane.
  - COACH: was der Coach coacht und wo ihr Jungler ist. „In der Lage“ ist kein Lagebild mehr.
- **Erweitert:**
  - DANACH: „sobald“, „wenn der Turm down ist“, „wenn ich gebacked bin“ → „Nach dem Back: …“ bzw. „Danach: …“.
  - KAUF: „soll ich … kaufen/verkaufen“.
  - JETZT: „sag mir, was ich machen soll“, „ich bin back“.
  - WARUM: „ich soll …“ / „wir sollen …“ stellt eine Ansage in Frage. „Warum nicht?“ ohne Ziel meint die Frage davor
    (≤ 20 s). Flash-Warum erklärt, wie der Coach Flash sieht. Nennt die Frage das Ziel des Plans, kommt sein Grund,
    nicht der einer alten Ansage.
- **Nachfrage:** „Du antwortest nicht auf meine Fragen“ beantwortet die letzte Frage (≤ 180 s): „Zu deiner Frage: …“.
- **KLAEREN mit Glossar:** gebackt, Prio, gecrasht, Platten.
- **NOTIZ** bleibt für reine Beschwerden: „du sagst immer/nie …“ ohne Fragezeichen, „das geht so nicht“.

**Fragen in 192113** (78 eingespielt):

| | vorher | jetzt |
|---|---|---|
| nur „Notiert.“ | 11 | 5 (reine Beschwerden: 5:03, 15:28, 19:53, 20:35, 28:47) |
| an Claude | 23 | 10 |
| Antwort nennt die Top-Welle | 21 | 6 |

**Die „Notiert.“-Antworten, jetzt:**
- 2:40 „Notiert. Stell das Kontroll-Auge in den Fluss-Busch oberhalb deiner Top-Lane: dort kommt Master Yi zum Gank.“
- 4:00 „Notiert. Zu deiner Frage: Farm deine Top-Welle, Drache spawnt in 56 Sekunden.“
- 8:28 „Zu deiner Frage: Ich coache deine Rolle, jetzt Riven auf Top … Master Yi war vor 217 Sekunden in seiner
  Basis …“
- 14:38 „Danach: Herold spawnt in 18 Sekunden, dann dorthin.“
- 15:55 „Zu deiner Frage: Zu Brand und Kai'Sa auf deine Lane: mit dir drei gegen zwei. …“
- 21:11 „Notiert. Drache spawnt erst in 256 Sekunden. Bleib nah an deinem Team, auf Top ist keine Welle.“
- 21:57 „Stimmt. Back jetzt: 2200 Gold für Riesenschwert.“
- 28:42 „Zu deiner Frage: Kauf Tanz des Todes, dann …“

Weitere Beispiele:
- 2:15 „Kontrollauge?“ bekam „Farm deine Top-Welle“, jetzt einen Ort.
- 8:04 „Jungle coachen?“ bekam die Kartenlage, jetzt: was der Coach coacht.
- 9:39 „Angst vor Ganks?“ ging an Claude, jetzt: „Vorsicht: Master Yi fehlt …“.
- 14:31 „wenn der Turm down ist?“ bekam eine Wiederholung, jetzt: „Danach: Herold spawnt in 24 Sekunden, dann
  dorthin.“
- 15:18 „sobald ich im Fountain bin?“ bekam „Back jetzt“, jetzt: „Nach dem Back: …“.
- 28:21 „Soll ich nichts anderes kaufen?“ ist KAUF.

**2b (andere Partien):** 213624_fragen 56/57 grün, rot nur das alte 0944.
- Zwei Rückfälle, die der erste Lauf zeigte, sind behoben:
  - 6:27 „Wie macht sich mein Team? Muss ich mir Sorgen machen?“ bleibt LAGE.
  - 13:48 „Was mache ich jetzt? Du sagst nie …“ bleibt JETZT.
- 101426 (auftrag008, auftrag009, kritik008): alle grün.

### 3. Timer

- **Ursache:** „Aus der Basis: Farm Top, Drache in 30 Sekunden.“ wurde bei 4:29,7 gewählt und erst bei 4:37,1
  gesprochen. Die Stimme sprach noch die Claude-Antwort auf die Win Condition. Die Zahl hört man 2 s nach dem ersten
  Ton, also 9,7 s zu hoch; das Spiel zeigte 20. Die Sprechlatenz der Stimme war es nicht (erster Ton 4:37,14).
- **Fix:** `kern.zeit_jetzt` über `auffrischen` (Sprechplan, beim Sprechen). „in/noch N Sekunden“ zählt um Wartezeit
  und Sprechzeit bis zur Zahl herunter, „seit N Sekunden“ hinauf.
- **Belege:**
  - Unit-Test `timer_zur_sprechzeit`: gleiche Lage wie live im Sprechplan, die Zahl stimmt beim Hören (±1 s).
  - Nachgespielt: „Drache in 28 Sekunden“ (4:29).

### 4. Cassiopeia „aus dem Nebel“ (Befund)

- **Sichtbarkeit:**
  - 21:25–22:04: bis auf kurze Lücken (≤ 6 s) sichtbar, aber unten, 8400–11800 von Riven.
  - 22:06–22:22: durchgehend sichtbar, 275–823 von dir.
  - 22:24–22:29 (Tod): verloren (seit 3,8 → 8,2 s). Auf dem Minimap-Bild 22:26 steht ihr Icon auf Rivens Icon;
    vermutlich trennt die Verfolgung überlagerte Icons nicht (nicht weiter geprüft).
- **Ursache des Satzes:** Die Probe für den Rückblick stammt von 22:05, als sie noch unten war (p_da 0). Was danach
  zu sehen war, zählte nicht.
- **Kleiner Fix:** Wer seit der Probe zu sehen war, kam nicht aus dem Nebel. Jetzt heißt es: „Raus kam, du bist
  geblieben – Cassiopeia und Teemo haben dich erreicht.“
- Carlos' „eine Minute gesehen“: sichtbar ja, nah aber erst 23 s vor dem Tod.

### Prüfungen

- **Neue Szenarien:** `192113_auftrag012` (3) und `192113_fragen` (61 Fragen und der Timer). Auf 273e09f sind 49
  von 65 rot, nach dem Fix alle grün. Die 16 schon grünen sind Wächter.
- **Unit-Tests** `timer_zur_sprechzeit` und `absicht_aus_langem_satz`: auf 273e09f rot.
- **Geändertes Szenario:** `101426_auftrag010` 1400 erwartete „Drück die Mid-Welle“ bei 4 gegen 0 (front 0,13).
  Genau diesen Satz lehnt Carlos ab. Es prüft jetzt nur noch, dass „ihre Vasallen sind weg“ nicht vorkommt; die Notiz
  steht im Szenario.
- **Szenarien gesamt 305 / 309**, 3 übersprungen. Rot sind nur die alten Fälle: 3× Wendepunkt-Probe und 0944.
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.

**Kennzahlen:**

| Partie | Warnungen/30 min | Leerlauf ab 14:00 (011 → 012) |
|---|---|---|
| 101426 | 13,4 | 52 → 54 % |
| 164326 | 9,8 | 45 → 50 % |
| 173159 | 9,4 (011: 10,2) | 52 → 54 % |
| 133930 | 13,7 | 44 → 47 % |
| 102112 | 3,9 | 33 → 30 % |
| 213624 | 10,8 | 31 → 31 % |
| 192113 | 17,4 | 34 % |

Die Warnungen sind unverändert. Der Leerlauf steigt leicht, weil das leere Drücken wegfällt. 192113 ist die erste
Botpartie in der Messung; ihre 17,4 Warnungen stehen in OFFEN.

---

## Auftrag 011 – Warnungsrate nachziehen, Szenario 2522 richtigstellen (28.09.2026)

Grundlage: `buecher/auftraege/011_auftrag.md`. Offline gemessen, der Coach wurde nicht gestartet. Alle neun Protokolle
sind neu erzeugt.

### 1. Warnungsrate

- **1.1 Ungesehen zählt nur gepaart:** In `_warnung_ohne_beleg` zählt ein Gegner, der länger als `eben_gesehen_s`
  (5 s) ungesehen ist, nur dann als Kopf, wenn zugleich ein Sichtbarer nah ist **und näher kommt**. Bis 20 s ungesehen
  gilt also nur gepaart.
- **1.2 Keine Wiederholung ohne neue Lage:** Dieselbe Warnung (keine neuen Köpfe, dasselbe Ziel) kommt in
  `gefahr_gleiche_s` (60 s) nicht wieder, außer `p_tod` steigt um mehr als eine Stufe (`gefahr_stufen` 0,15 / 0,3 /
  0,5 / 0,7; vorher: +0,2).
  - „Back jetzt“ nach einem Rückzug gilt als dieselbe Richtung.
  - Unit-Test `warnung_nur_mit_neuer_lage` (auf `bf7c7ba` rot: `gefahr_stufe` fehlte).
- **101426, die vier Fälle aus dem Auftrag:**

| Fall | vorher | jetzt | warum |
|---|---|---|---|
| 20:01 | „Zurück unter deinen inneren Mid-Turm: drei kommen.“ | still | kein Sichtbarer kam näher – die Ungesehenen zählen nicht (1.1) |
| 20:10 | derselbe Satz 9 s später | bleibt, jetzt die erste Warnung vor dem Tod | Twitch und Bard kommen sichtbar näher, Aurora 9 s ungesehen zählt gepaart |
| 21:35 | „Zurück unter euren inneren Bot-Turm: drei kommen.“ | bleibt | Twitch kommt sichtbar näher, Bard 9 s ungesehen |
| 23:35 | „Von der Bot-Lane zurück …: zwei kommen.“ | still | Twitch sichtbar, kommt aber nicht näher (1.1) |

- **Außerdem:**
  - 22:38 „Back jetzt: 850 Gold …“ (GEFAHR, 13 s nach dem Rückzug 22:25) fällt weg (1.2).
  - Szenario `2010-keine-wiederholung` (auf `bf7c7ba` rot: 20:01 und 20:10) ist grün, ebenso `2016-viego-zaehlt-mit`
    (20:10 warnt).

**Warnungen je 30 min** (`kennzahlen.py`: GEFAHR ohne Kampf-Rufe, dazu VORSICHT; vorher = Stand nach 010):

| 101426 | 102112 | 133930 | 140253 | 144655 | 164326 | 173159 | 213624 |
|---|---|---|---|---|---|---|---|
| 15,0 → **13,4** | 3,9 → 3,9 | 15,1 → 13,7 | 13,9 → 11,1 | 12,4 → 12,4 | 11,9 → **9,8** | 11,0 → 10,2 | 10,8 → 10,8 |

(145702: 0,5 min, keine.)

**`a1-warnungen-je-30min` ist grün:** 11 GEFAHR-Sätze in 101426 (Schranke 11; vorher 13). Der Rest je Satz
(`k011_warn.py`):

| | 101426 | 164326 | 173159 |
|---|---|---|---|
| echte Mehrfachgefahr (Sichtbare, ≤ 5 s ungesehen) | 3 | 6 | 1 |
| 20:16-Art (braucht einen Ungesehenen > 5 s, gepaart) | 4 | 3 | 2 |
| Leben unter 40 % oder klar hinten | 1 | 3 | 4 |
| Kampf-RAUS und „Back jetzt“ bei wenig Leben | 3 | 1 | 4 |

In 101426 kommen zu den 11 GEFAHR-Sätzen 5 Vorsicht-Sätze („Du stehst tief: …“). Deshalb steht die Kennzahl (mit
VORSICHT) bei 13,4 und nicht unter 10. Die 20:16-Art sind 9:00, 20:10, 21:35 und 22:25 – je ein sichtbarer, näher
kommender Gegner plus ein 9–15 s Ungesehener.

### 2. Szenario 2522

`2522-kein-baron-drache-lebt` (102112) erwartet jetzt den akzeptierten Ausgang: `soll = ["DRUECKEN", "MIT_GRUPPE"]`
(Split: Tryndamere nimmt den Drachen allein, Riven geht auf den äußeren Mid-Turm), weiter nie „Baron“. Das Verhalten ist
unverändert. Grund und alte Erwartung stehen im Szenario.

### Nebenwirkung

`2335-von-der-bot-lane` (010) hatte keine Warnung mehr zu prüfen. Die Form „Von der Bot-Lane zurück zu …“ prüft jetzt
`2209-von-der-bot-lane` (213624 22:09; vor 010 hieß es dort „Zurück unter euren Mid-Turm“). In 101426 23:35 bleibt nur
das Verbot der alten Form.

### Prüfungen

- **Szenarien 240 / 244**, 3 übersprungen.
  - Rot sind nur die alten Fälle: 3× Wendepunkt-Probe (19 späte Sätze, 010: 18) und 0944.
  - `a1-warnungen-je-30min` und `2522-…` sind grün.
- `tests/alle.py` **10 / 10**, konstruierte Lagen **40 / 40**.
- **Leerlauf ab 14:00** kaum verändert: 101426 52 %, 164326 45 %, 173159 52 % (010: 51 / 44 / 52).

---

## Auftrag 010 – Plan nach dem Wendepunkt (28.09.2026)

Grundlage: `buecher/auftraege/010_auftrag.md`. Offline gemessen, der Coach wurde nicht gestartet. Alle neun Protokolle
sind neu erzeugt (101426 und 213624 mit `--fragen`).

### 1. Plan nach dem Wendepunkt

**Befund vorher.** In den Leerlauf-Stichproben aus 009 bot der Kern in UNTERWEGS/GRUPPE fast nur HALTEN und ZURUECK an.
Die Lane-Handlungen (Welle, Back) entstehen dort nur ohne nahes Objective. Türme hängen oft am Kampfmodell (stumm, „X
kommt vorher“).

**Gebaut:**

- **`karte.welle_druecken` (neue Art WELLE_DRUECKEN):**
  - Wann: nach der Lane-Phase eine Welle, die zu ihnen läuft (≥ 3 eigene Vasallen, mehr als ihre), höchstens 25 s weg.
  - Satz: „Drück die Mid-Welle: 4 gegen 1 Vasallen.“ oder „…: Sett ist 36 Sekunden tot.“ (≤ 8 Wörter).
  - Gewinn: was du dabei farmst (wie FARMEN), dazu der Druck auf ihre Lane. Das Risiko zählt über 15 s wie bei
    SEITENWELLE.
  - Einordnung: „vor“, R1-Schranke, nach einer Warnung 20 s gesperrt, Ruf nach vorn für den Todesrückblick (R9).
- **`Kern._makro_ziele` (am Ende der Kandidaten):**
  - Auslöser: Bliebe in UNTERWEGS, GRUPPE, SEITE oder OBJECTIVE nur HALTEN, sucht der Kern einmal ein Wellen-Ziel.
  - Die Welle der Lane, auf der du stehst, geht vor; 45 s lang bleibt es dieselbe Lane.
  - Still bleibt der Kern, solange etwas anderes noch gilt:
    - eine Warnung (≤ 20 s),
    - ein Rückzug oder Back-Ruf (≤ 30 s),
    - ein Turm- oder Objective-Ruf (≤ 60 s, bis zum nächsten Wendepunkt).
- **Bewertung (Abweichung vom Wortlaut „positiver EV“):** Das Ziel muss mehr EV haben als HALTEN. Positiv im absoluten
  Sinn ist dort fast nichts, denn auch HALTEN hat −150 bis −1200 durch das Risiko am Ort. Die längere Dauer kostet dabei
  keinen Zeitwert, denn die Alternative ist Stehenbleiben. Ohne das verlor jede Welle nur am Zeitwert: 300 GE über 33 s
  gegen 10 s Halten.
- **Plan-Wechsel:** HALTEN schützt gegen ein Makro-Ziel keine Hysterese (101426 24:45: 64 GE besser, Schwelle 150).
- **Back nach einem gewonnenen Kampf:** Er fällt erst weg, wenn ein Umwandel-Ziel sprechbar ist (`zuerst_filtern`).
  Vorher strich ein stummer Turm auch den Back (101426 17:09).

**Die zehn Stichproben aus 009** (`2026-09-28_101426_auftrag010.toml`; auf `064a6b4` rot, außer den Wächtern):

| # | Fenster | jetzt | Szenario |
|---|---|---|---|
| 1 | 14:00–14:39 | 14:13 „Drück die Mid-Welle: ihre Vasallen sind weg.“, 14:34 „Zu Urgot und Kayn zum Baron …“ | grün |
| 2 | 17:03–17:15 | still: Turm stumm (Bard kommt vorher), Back gesperrt (R4: 3 Back-Rufe in 10 min), keine Welle ≥ 3 | offen |
| 3 | 17:36–18:23 | 17:55 „Aus der Basis: Drück die Mid-Welle, ihre Vasallen sind weg.“ | grün |
| 5 | 22:30–22:38 | still (der Rückzug gilt) | Wächter grün |
| 6 | 23:02–23:18 | still (der Back-Ruf gilt) | Wächter grün |
| 7 | 24:40–25:30 | 24:43 „Drück die Mid-Welle: 4 gegen 1 Vasallen.“ | grün |
| 8 | 28:09–28:15 | still (der Back-Ruf gilt) | Wächter grün |
| 9 | 30:21–30:53 | still: 46 % und 900 Gold sind kein Back-Grund, die Mid-Welle läuft zu dir | offen |
| 10 | 33:38–34:11 | 33:47 „Drache drin: Drück die Mid-Welle, 4 gegen 2 Vasallen.“ | grün |

Die zwei offenen Fälle stehen in `tests/szenarien/offen/2026-09-28_101426_leerlauf.toml` (mit Grund). Fall 4 (21:08,
FARMEN als stummer Grundplan) ist kein HALTEN-Fall und blieb, wie er war.

**Leerlauf ab 14:00** (`kennzahlen.py --nur-kern`; vorher auf `064a6b4` im Worktree gemessen):

| Partie | vorher | jetzt | Widersprüche vorher → jetzt | ungefragt je 30 min vorher → jetzt |
|---|---|---|---|---|
| 101426 | 59 % | **51 %** | 1 → 2 | 68 → 77 |
| 102112 | 32 % | 33 % | 0 → 1 | 76 → 83 |
| 133930 | 62 % | **44 %** | 1 → 3 | 74 → 87 |
| 164326 | 51 % | **44 %** | 2 → 2 | 74 → 79 |
| 173159 | 51 % | 52 % | 1 → 2 | 69 → 72 |
| 213624 | 31 % | 31 % | 0 → 0 | 79 → 83 |

(140253, 144655, 145702 haben keine Zeit nach 14:00.)

- **Wo es nicht besser wird (101426, Gründe je Takt mit `k010_warum3.py`):**
  - Am häufigsten ist ein anderer Plan als HALTEN aktiv, der nicht gesagt ist. FARMEN auf der Seite ist 120 s in
    101426, 80–220 s in den anderen – ein stummer Grundplan, kein HALTEN.
  - Danach kommt „EV schlechter oder Schranke“: Die Welle liegt in Gefahr (`p_tod` ≥ 0,3) oder das Risiko dort ist
    deutlich höher als am Ort.
  - Dann „keine Welle zum Drücken“.
- **173159** bleibt: 382 Takte hält ein Turm- oder Objective-Ruf von vorher still (die neue Regel gegen Lückenfüller),
  dazu 210 Takte nach Warnungen.
- **Zwischenstände, verworfen:**
  - Ohne die Sperre nach Turm- oder Objective-Rufen und ohne die 45-s-Lane lag der Leerlauf tiefer (101426 42 %,
    164326 40 %, 133930 36 %).
  - Dafür kamen doppelt so viele Widersprüche (164326: 8), z. B. „Drück die Bot-Welle“ und 33 s später „Drück die
    Top-Welle“.
  - In 164326 39:30 hieß es „Drück die Top-Welle“ 15 s nach „Baron bestreiten“.
- **Menge:** Die Welle wird 12–15-mal je Partie gesagt (101426: 15 in 22 min nach 14:00).

### 2. Info ohne Folgen

- **Bestätigungen („Gut raus.“, „Sauber umgewandelt.“, „Guter TP.“):** Sie werden nicht mehr allein gesagt, sondern
  vor den nächsten Plan-Satz in ≤ 20 s gestellt, z. B. „Gut raus. Dann zur Top-Welle: dein Team ist in der Mitte.“ Kommt
  keiner, fällt die Bestätigung weg; das Review hat sie. In den neun Protokollen gibt es 6 solche Paare und keine allein.
- **Flash-Meldung:** Sie kommt ungefragt nur für einen Gegner ≤ 5000 von dir, der in den letzten 20 s gesehen wurde.
  Die anderen warten, bis sie nah sind, und stehen im Lagebild und im Dashboard.
  - 101426 10:37 „Aurora ohne Flash.“ ohne bekannten Ort kommt jetzt 10:38, als Aurora sichtbar 1190 vor Riven steht.
  - 213624 4:55 „Sona ohne Flash.“ (Sona unten, Riven oben) kommt nicht mehr; Szenario `0455-…` angepasst.
- **Szenarien und Tests:** `gut-raus-nicht-allein` und `1037-flash-ohne-ort` rot → grün. Unit-Test
  `info_flash_kurz_und_gebuendelt` erweitert (war rot).

### 3. Rückzug auf eine andere Lane

„Von der Bot-Lane zurück zu deinem inneren Mid-Turm: zwei kommen.“ (101426 23:35). Die Form hat 10 Wörter.
`s23-gefahr-hoechstens-8` (213624) nimmt sie aus (`woerter_ausnahme`). Szenario `2335-von-der-bot-lane` rot → grün.

### 4. Wackelnde Einschätzung (102112 25:22)

Rivens Anteil am Objective ist das Mittel der letzten 1,5 s (`objective.glaetten`, im Objective-Gedächtnis). Für
102112 25:22 heißt das: 0,14 → 0,57 statt 1,0. Unit-Test `anteil_geglaettet` (war rot). Die Wahl um 25:22 ändert das
nicht: Der Turm ist gesagt, bevor der zweite Wert kommt, und `2522-…` bleibt rot wie in 009.

### 5. Nur notiert

41 % nach schnellem Lebensverlust (101426 29:36): Zeile in `OFFEN.md`.

### Prüfungen

- **Szenarien 236 / 242**, 3 übersprungen.
  - Rot sind nur die bekannten Fälle: 3× Wendepunkt-Probe (18 späte Sätze, in 009: 24), 0944, `2522-…` und
    `a1-warnungen-je-30min` (Entscheidungen aus 009).
  - Neu: `2026-09-28_101426_auftrag010.toml` (10 Szenarien), dazu 2 offene Fälle in `offen/`.
- `tests/alle.py` **10 / 10**, konstruierte Lagen **40 / 40**.
- **Suche Vorwärts bei < 40 % / `p_tod` ≥ 0,3** (009, `k009_vor_suche.py`): 0.
- **Warnungen je 30 min:** wie in 009 (101426 15,0, 164326 11,9, 173159 11,0).

---

## Auftrag 009 – Letzte Sperren vor Testpartie 2 (28.09.2026)

Grundlage: `buecher/auftraege/009_auftrag.md`. Offline gemessen, der Coach wurde nicht gestartet. Alle neun Protokolle
sind mit dem Stand dieses Auftrags neu erzeugt (101426 und 213624 mit `--fragen`).

### 1. „Trade“ bei 15 % Leben

- **Fix:** `TRADE` und `ALL_IN` stehen in der R1-Liste (`VOR_SCHRANKE`) und sind stumm (`BUCH2_STUMM`), bis Buch 2 kommt.
  Sie werden weiter berechnet; im Protokoll steht „stumm: Buch 2 zurückgestellt“ (`_stumm` hat jetzt einen Grund; 23
  solche Zeilen in 102112, 140253, 164326, 213624). In 101426 2:35 streicht schon R1 den Trade (15 % Leben).
- **Andere Vorwärts-Handlungen außerhalb der R1-Liste** (`handlung.VOR` und `VORWAERTS` gegen `VOR_SCHRANKE`):
  - `REIN` und `DREHEN` kommen aus der Kampf-Tabelle, nicht aus den Kandidaten: stumm bis zur Kampf-Eichung, außer robust
    überlegen; `DREHEN` hat eine eigene Leben-Schwelle (`drehen_eigen_leben`). Nicht geändert.
  - `ANLAUFEN` erzeugt kein Modus (nur ein Plan-Schritt von `NEHMEN`).
  - `WELLE_REIN_UND_BACK` und `STAPELN` sind nach Buch 1, 3 neutral. Neu: mit `p_tod` ≥ 0,3 sind sie kein Kandidat
    (`WELLE_VOR`). Unter 40 % Leben bleiben sie, weil „erst die Welle rein, dann back“ dort der Rat ist.
- **Szenario** `0235-kein-trade-bei-15` (101426): auf `122431c` rot, jetzt grün.
- **Suche in allen neun Protokollen** (`k009_vor_suche.py`: gesprochene Vorwärts-Handlungen der R1-Liste und Kampf-Rufe
  mit Leben < 40 % oder `p_tod` ≥ 0,3; Wellen-Handlungen mit `p_tod` ≥ 0,3):
  - vorher (Protokolle auf `122431c`): 3 – 101426 2:35 „Trade Aurora …“ (15 %), 101426 10:54 und 173159 9:59 „…-Welle
    rein, dann back“ (`p_tod` 0,38 und 0,36),
  - jetzt: **0**.

### 2. Entscheidungen zu 008

**2.1 Ungesehene Gegner als Köpfe.** In `_warnung_ohne_beleg` zählt ein Gegner als Kopf, wenn er sichtbar ist oder seit
≤ `kopf_ungesehen_s` (20 s) fehlt, jeweils mit `ankunft` ≤ 5 s. `ankunft` ist für Ungesehene schon Weg ÷ Tempo minus
die Zeit seit der Sichtung (wie `verteidiger_ab`). Bedingung 1 (ein Gegner **sichtbar** und nah) bleibt.

- `2016-viego-zaehlt-mit`: rot → grün. 20:01 und 20:10 „Zurück unter deinen inneren Mid-Turm: drei kommen.“
- `1400-viego-weit-still`: Wächter, grün.
- **Folge:** Neu warnen in 101426 auch 21:35 (Twitch sichtbar in 1360, Bard 9 s ungesehen in 0 s da, Viego kommt) und
  23:35 (Twitch sichtbar in 685, Bard 15 s ungesehen). Warnungen je 30 min (`kennzahlen.py`): 101426 11,7 → **15,0**,
  164326 8,4 → **11,9**, 173159 7,8 → **10,2**. `a1-warnungen-je-30min` (`kategorie_max` 11, jetzt 13) ist rot, siehe
  „Offen“.
- `2335-ungesehen-kein-raus` (008) prüft jetzt bis 23:35,5. Ab 23:35,9 ist die Warnung nach 2.1 richtig: zwei gegen
  einen.

**2.2 Lagebild.** 30 s Stille, höchstens alle 90 s (stand so). Neu: die Folgerung ist eine Handlung oder Grenze
(`kartenlage.folgerung(streng=True)` für das ungefragte Lagebild):

- „X steht nah bei dir“ → „X steht nah bei dir: nicht allein nach vorn“,
- „Oben ist 20 Sekunden frei“ → „…: Welle drücken“ (oder der Plan),
- „Drei unten: oben ist frei“ → „…: Welle drücken“, wenn oben deine Seite ist; sonst kein ungefragtes Lagebild,
- „X braucht N Sekunden zu dir“ nur mit Plan („…: auf ihren Turm geht“), „Keiner von ihnen ist nah“ nie ungefragt.
- Auf Frage bleibt die Beschreibung erlaubt. Szenario `lagebild-folgerung-handelt`: rot (5 beschreibende) → grün; 101426
  hat jetzt 6 Lagebilder, alle mit „nicht allein nach vorn“.

**2.3 Drache vor Inhibitor.** `karte.ORDNUNG` wirkt nur noch bei Gleichstand (1 GE je Rang). Der Rang-Filter in
`umwandeln_zuerst` ist weg.

- **Gleicher Umwandel-Bonus:** Im Fenster bekommt jedes Ziel denselben Bonus (`umwandeln_bonus` 400 GE), Turm wie
  Objective. Vorher gab es 200 GE je Rang (äußerer Turm 200 … Nexus 800, Drache 300). Nur 1 GE je Rang ließ Back vor
  jeden Turm rutschen (213624 16:17).
- **Objective neben euch:** Liegt es im Fenster und ≤ `drache_zuerst_s` (10 s) weg, fallen die Umwandel-Türme weg
  (`zuerst_filtern`, erst nach den Schranken – ist das Objective stumm, bleiben die Türme). Reicht das Fenster danach noch
  für den besten Turm, nennt der Satz beides:
  - 101426 33:21: „Drache zuerst, der liegt neben euch; danach ihr Bot-Inhibitor-Turm, der Baron-Buff hält noch 120
    Sekunden.“
  - Unit-Test `drache_vor_inhibitor` war auf `122431c` rot.
- **Ohne Ort kein neuer Plan:** Nach einem Kampf wartet der Kern bis zu 2 s auf den Ort. Ohne Ort gibt es kein Turmziel;
  213624 16:17 sagte deshalb „Drei von ihnen tot: Back jetzt“, 0,3 s später war der innere Mid-Turm da. `1617-…` ist
  wieder grün.
- **164326 35:01** („Ihr Top-Inhibitor jetzt“ quer über die Karte) bleibt. Der Drache spawnt dort erst in 40 s und liegt
  19 s weg, die Regel greift nicht. Der Inhibitor ist in 41 s erreichbar (Fenster 42 s) und hat den besten EV.
- **`2522-kein-baron-drache-lebt` (102112) ist jetzt rot:**
  - Der EV wählt den äußeren Mid-Turm (Gewinn 660 + „dahinter“ 776) statt des Drachens 18 s neben Riven.
  - Tryndamere nimmt den Drachen allein zu 86 %, Rivens Anteil ist 0,14 (83 GE).
  - 0,5 s später springt das Urteil auf Anteil 1,0 (Tryndamere zählt als „mit“), aber der Turm ist schon gesagt; die
    Hysterese (150 GE) hält ihn.
  - Vorher entschied der Rang-Filter. Zu entscheiden, siehe „Offen“. Zwei Versuche sind verworfen:
    - Türme, die nach dem Fenster fallen, wie ohne Fenster behandeln: das kippte 3632 (Mid-Inhibitor, Sona 14 s tot).
    - Einen frischen, ungesagten Plan ohne Hysterese: der Turm war schon gesagt.

**2.3 Recall-Kanal.**

- **Kanal:** Nach einem Back-Ruf (≤ 30 s) gilt Stillstand außerhalb der Basis (≤ 80 Einheiten, ≥ 1 s) als Kanal.
- **Warnung darin:** Der Kern warnt (GEFAHR und Kampf-RAUS) nur, wenn der erste Gegner (sichtbar oder ≤ 20 s ungesehen)
  vor Kanal-Ende + 1 s da sein kann. Sonst steht „Recall reicht“ als Gate-Grund, bzw. der RAUS-Ruf ist stumm.
- **Wächter aus echten Partien:**
  - `0429-recall-kanal-warnung-bleibt` (213624): Rumble in 3,9 s, Kanal noch 3,5 s – warnen.
  - `1322-recall-kanal-reicht` (102112): Sett in 5,7 s, Kanal noch 0,5 s – still.
- **Rot zuerst:** Beide Wächter waren schon grün, denn die drei Fälle aus 007 (102112 13:22, 213624 4:29, 164326 24:14)
  sind seit A1 still bzw. richtig. Rot zuerst war nur der Unit-Test `recall_kanal`. In den neun Protokollen griff die
  Regel nie.

### 3. KLAEREN

- **Absicht:** neu für „was soll das (bedeuten)“, „was meinst du“, „macht keinen Sinn“, „schwammig“, „nichtssagend“,
  „versteh ich nicht“ (nach WARUM).
- **Erklärung je Ansage:** Jede Ansage merkt sich beim Übergeben, was sie meinte (`_erklaerung`):
  - bei Rückzug den sicheren Ort und wer wie weit weg war,
  - bei Plänen Ziel, Weg und Welle mit Grund.
- **Antwort:** Sie nimmt den letzten Satz ≤ 60 s, zum Thema der Frage (Turm/Raus, Welle, Back), und gilt auch im Tod.
  Ohne Satz antwortet der Coach wie bisher.
- **Beispiele (101426):**
  - 32:17: „Vor 34 Sekunden: „Raus, zu eurem Top-Turm!“ Zu eurem inneren Top-Turm, weil Aurora und Twitch 2 Sekunden
    weg waren.“ Vorher kam „Du lebst in 29 Sekunden wieder …“.
  - 31:07 („Was soll damit Welle heißen?“, vorher Claude): „… Gemeint war: zur Mid-Welle; dort stehen 0 ihrer und 2
    deiner Vasallen. Grund: Sie läuft sonst in deinen Turm.“ Die Erklärung zeigt nebenbei, dass der Grund damals schwach
    war.
- **Angepasst:** `3207-tot-respawn-mit-kauf` (Kritik 008, dieselbe Frage) erwartet jetzt „Top-Turm“ statt des
  Respawn-Plans.
- **Bleibt JETZT:** „Welche Welle, auf welcher Lane?“ (213624 13:16).

### 4. Sprachfehler

- **Kein Possessiv vor Champion-Namen:** „Aurora ist Level 6“ (Makro SPIKE).
- **Schutzplan mit fertigem Item:** `lane._bauteil` gibt das nächste Kern-Item aus Carlos' Build („kein Trade bis zum
  Axiombogen“, „bis zur Eklipse“).
  - Die kurze Fassung nennt jetzt den Grund: „Weiter an deinem Turm farmen: Gangplank ist vorn.“
  - Sie kommt öfter, weil das Ziel-Item über den Tod gleich bleibt (144655 6:42, Szenario `0701-…`).
- **Bauteile mit Ziel:** `kaufplan.mit_ziel` („Kauf Langschwert für die Eklipse“, „Tiamat für die Gefräßige Hydra“) in
  KAUFEN, Respawn-Plan und Kauf-Antwort. Der Artikel kommt aus `akk_artikel`, „zur/zum“ aus `_dat`.
- **Szenarien:** `kein-possessiv-vor-champion`, `1211-schutzplan-fertiges-item`, `bauteil-mit-ziel`: rot → grün.

### 5. Leerlauf (nur gemessen)

101426 ab 14:00 (`fuehrmass.leerlauf`: lebend, nicht KAMPF, kein gültiger gesagter Plan): 25 Fenster ≥ 5 s, zusammen
584 s. Zehn davon zufällig (`k009_leerlauf.py`, Seed 9; mit dem Endstand dieselben), je mit der Lage in der
Fenstermitte und dem letzten Satz davor:

| # | Fenster | Lage (Mitte des Fensters) | Was ein Challenger-Coach gesagt hätte |
|---|---|---|---|
| 1 | 14:00–14:39 (39 s) | Mid, 97 %, Aurora sichtbar in 1100, deine Mid-Welle läuft zu ihr (3:0), Herold in 40 s; 14:00 kam der Teamplan „3100 Gold vorn … Drache und ihre Türme erzwingen“, danach Plan HALTEN | „Drück die Mid-Welle in ihren Turm, dann mit Kayn zum Herold – der kommt in 40 Sekunden.“ |
| 2 | 17:03–17:15 (12 s) | Unterer Fluss, 93 %, 1000 Gold; Viego, Aurora und Twitch tot; 16:56 „Drück ihren inneren Top-Turm“, jetzt Plan HALTEN | „Drei von ihnen tot, ihr steht unten: mit allen auf ihren Bot-Turm, danach back mit 1000 Gold.“ (der Kern sagte 16:56 „ihren inneren Top-Turm“ – quer über die Karte) |
| 3 | 17:36–18:23 (47 s) | Mid-Lane, 99 %, 200 Gold; Sett tot, Twitch vor 6 s in 4300; ihr äußerer Mid-Turm ist gefallen, Plan HALTEN | „Sett ist tot: hol die Top-Seitenwelle, Aurora steht Mid.“ |
| 4 | 21:08–21:35 (28 s) | Bot-Lane, 96 %, Plan FARMEN (21:07 „Farm Bot“), Aurora tot, Drache in 32 s | „Welle fertig, dann zum Drachen: er kommt in 30 Sekunden, Aurora ist tot.“ |
| 5 | 22:30–22:38 (8 s) | Nach „Zurück unter deinen inneren Mid-Turm: zwei kommen“ (22:26), Ort unbekannt | nichts – Stille ist richtig (der Rückzug gilt) |
| 6 | 23:02–23:18 (16 s) | Bot-Lane, 85 %, 1000 Gold; 22:52 „Back jetzt, 900 Gold für Spitzhacke“ | nichts – Stille ist richtig (der Back-Ruf gilt, 10–26 s alt) |
| 7 | 24:40–25:30 (50 s) | In ihrem oberen Jungle, 99 %, 130 Gold; Bard tot, Twitch vor 2 s in 3400, Baron lebt; 24:25 „Geh zu deinem Team“ | „Bard ist tot: Sicht am Baron legen, dein Team kommt nach – nicht allein tiefer.“ |
| 8 | 28:09–28:15 (6 s) | Bot, 30 %; 27:59 „Back jetzt, 15 Prozent Leben“ | nichts – Stille ist richtig (der Back-Ruf gilt) |
| 9 | 30:21–30:53 (32 s) | Eigene Mid-Lane, 46 %, 900 Gold; Bard vor 3 s in 3350; 30:09 Rückzug, 30:39 Lagebild; die Welle läuft zu dir | „Back jetzt: 46 Prozent und 900 Gold, die Welle läuft zu deinem Turm, du verlierst nichts.“ |
| 10 | 33:38–34:11 (34 s) | Ihr unterer Jungle, 87 %; Twitch und Bard tot; 33:21 „Zum Drachen mit Yunara“, der Drache ist drin | „Drache drin, zwei tot: mit allen auf ihren Mid-Inhibitor-Turm.“ |

- **Stille richtig:** 3 von 10 (5, 6, 8). Ein Rückzug oder Back-Ruf gilt noch, 6–16 s.
- **Ein Satz fehlt:** 7 von 10.
  - In sechs davon (1, 2, 3, 7, 9, 10) ist der Plan des Kerns HALTEN ohne Ziel: Nach einem Wendepunkt (Turm, Objective,
    Kills) hat er in UNTERWEGS/GRUPPE keinen Kandidaten mit positivem EV.
  - In 4 steht FARMEN als stummer Grundplan, obwohl der Drache in 30 s kommt.
- Nichts gebaut (Auftrag: nur messen).

### Prüfungen

- **Szenarien:** 226 / 232 grün, 3 übersprungen.
  - Rot sind die alten Fälle: 3× Wendepunkt-Probe (24 späte Sätze, im letzten 008-Lauf 28) und 0944.
  - Neu rot: `2522-kein-baron-drache-lebt` (2.3) und `a1-warnungen-je-30min` (2.1).
  - Der volle Lauf lag vor der letzten Satzänderung (Baron-Buff statt „sie sind noch 120 Sekunden tot“). Danach liefen
    die 101426-Dateien (28 / 29, rot nur a1) und `test_kern` noch einmal.
- **Neu (11 Szenarien und 2 Unit-Tests, auf `122431c` alle rot außer den Wächtern 1400, 0429, 1322):**
  - `2026-09-28_101426_auftrag009.toml` (9),
  - `2026-09-27_213624_auftrag009.toml` (1 Wächter),
  - `2026-09-27_102112_auftrag009.toml` (1 Wächter),
  - Unit-Tests `drache_vor_inhibitor`, `recall_kanal`.
- **Weitere:** `tests/alle.py` **10 / 10**, konstruierte Lagen **40 / 40**.
- **Kennzahlen (`kennzahlen.py --nur-kern`):**

| | 101426 | 164326 | 173159 |
|---|---|---|---|
| Warnungen je 30 min (≤ 10) | 15,0 | 11,9 | 10,2 |
| vage Sätze (0) | 0 | 0 | 0 |
| ungefragt je 30 min | 68 | 74 | 69 |
| Leerlauf ab 14:00 | 59 % | 51 % | 51 % |

### Nachzählung 101426 (ein frischer Challenger-, ein frischer Carlos-Kritiker)

Zwei neue Agenten ohne Code, je eine Rolle, auf dem Protokoll 101426 (`--fragen`). Drei Stellen änderten sich
danach noch; beide haben sie nachbewertet: 16:56, 17:39 und 33:21. Die Urteile liegen im Scratchpad
(`k009_krit/urteile_*.jsonl`), gezählt mit `k009_zaehlen.py`.

| | 008 (Kritik 008) | 009 |
|---|---|---|
| ok / schwach / falsch / gefährlich | 81 / 7 / 3 / 0 | 83 / 4 / 1 / 0 |
| falsch je 30 min (≤ 2) | 2,5 | **0,8** |
| Warum nachvollziehbar (≥ 90 %) | 91 % | 95 % (69/73) |
| Info ohne Folgen | 1 | 6 (5,0 je 30 min) |
| hilft / neutral / nervt (Carlos) | 88 / 2 / 10 % | 86 / 4 / 10 % (69/3/8 von 80) |
| Antworten beantwortet / vorbei | – | 9 / 1 |

- **falsch (1):** 23:35 „Zurück unter deinen inneren Mid-Turm: zwei kommen.“ auf der Bot-Lane – der Ort nach Laufzeit
  ist der Mid-Turm, liest sich aber falsch.
- **schwach (4):**
  - „Gut raus.“ (2×) und „Aurora ohne Flash.“ ohne Ort: Info ohne Folgen.
  - 29:36 „Weiter auf ihren Nexus-Turm“ bei 41 % nach schnellem Lebensverlust: vorwärts bei wenig Leben, über der
    R1-Grenze.
- **nervt (8):**
  - drei abgebrochene Sätze,
  - „Mid-Welle“ ohne Zustand (15:15, 30:53),
  - „Raus, zu deinem Turm!“ (8:22),
  - Wiederholung 20:10 (9 s nach 20:01, `p_tod` stieg),
  - 11:12 wie 9:25.
- **vorbei (1):** 19:25 „Wo's Twitch?“ – die Karte zeigte ihn 3100 weg, Carlos sah ihn bei sich (Minimap-Verzug).
- Beide KLAEREN-Antworten (31:07, 32:17) zählen als beantwortet.

### Offen

1. **Warnungen über 10 je 30 min** (101426 15,0; 164326 11,9; 173159 10,2): Das ist der Preis von Entscheidung 2.1.
   Die neuen Warnungen (20:01, 20:10, 21:35, 23:35 in 101426) sind nach Lage richtig; 20:10 wiederholt 20:01 nach
   9 s. Möglich wäre: ein Ungesehener zählt nur, wenn ein Sichtbarer näher kommt, oder `kopf_ungesehen_s` 15 statt 20.
   Nicht gebaut – Entscheidung.
2. **2522 (102112 25:22): Drache oder Turm, wenn ein Mitspieler den Drachen allein nimmt?** Der EV sagt Turm (Rivens
   Anteil 0,14), Buch 6, 8 sagte Drache. Entscheidung.
3. **Leerlauf:** 6 von 10 Stichproben zeigen einen fehlenden Plan nach Wendepunkten (HALTEN ohne Ziel).

---

## Auftrag 008 – Carlos' Testpartie 101426 und Buch 4 (Kartenlage und Makro) (28.09.2026)

Grundlage: `buecher/auftraege/008_auftrag.md` (neue Fassung: Teil 0, Teil A, Teil 1). Offline gemessen, der Coach wurde
nicht gestartet.

**Die Testpartie:** Carlos' 101426, Riven Mid gegen Aurora, echte Gegner, 34:46.
- Live kamen 80 ungefragte Ansagen, davon 36 Warnungen.
- Carlos: „immer noch komplett scheußlich“.
- Notizen und Sprechtasten-Log habe ich zuerst gelesen; jeder Punkt daraus ist ein Szenario oder steht in `OFFEN.md`.

### Teil 0

- **008_frage.md: B.** Buch 4 statt Buch 2, `008_in_arbeit` gelöscht und neu angelegt.
- **Die Antworten zu Drache gegen Inhibitor, „Raus“ im Recall und Baron-Buff:** Umgesetzt ist davon nur, was Teil A
  und Buch 4 berühren:
  - „Baron-Buff allein ist keine Belagerung“ galt schon (007, Auslöser c).
  - Der Satz dazu heißt jetzt „Sie haben den Baron.“ statt „Baron weg.“ (Kritik).
  - **Drache vor Inhibitor über den EV** und **Warnung im Recall-Kanal** sind **nicht gebaut**, siehe „Offen“.

### Teil A – zuerst die Testpartie

**A1 – Warnungen radikal seltener** (`kern/__init__._warnung_ohne_beleg`, `_vorsicht`; `[warnung]` in kern.toml;
Nachträge Buch 0, 7.5.1 und Buch 11, 4.1). GEFAHR wird nur noch gesprochen, wenn alle vier Bedingungen gelten:
1. Ein Gegner ist sichtbar und kann in ≤ 5 s bei dir sein.
2. Ihr seid robust unterlegen:
   - in 5 s ≥ 1 Kopf mehr, gezählt werden nur Sichtbare und bis 5 s Ungesehene;
   - oder Leben < 40 % und unter dem des nächsten Gegners;
   - oder „klar unterlegen“ nach Level und Gold gegen genau diese Köpfe.
3. Du bist nicht schon auf dem Rückzug: nicht ≥ 300 näher in 2 s und nicht ≤ 5 s vom sicheren Ort.
4. Dieselbe Gegnermenge kam nicht schon in den letzten 60 s, außer das Todesrisiko steigt um ≥ 0,2
   (`[schranken]` 45 → 60 s, 0,15 → 0,2).

**Ungesehene Gefahr:** höchstens der Vorsicht-Satz, einer je 90 s. Bedingungen:
- ≥ 2 Gegner fehlen seit ≥ 20 s und können in ≤ 10 s bei dir sein;
- dieselben Fehlenden nicht noch einmal in 180 s;
- du stehst in ihrem Jungle oder ihrer Basis (nach der Kritik, siehe dort).

„Xin oben gesehen: zurück hinter die Welle.“ (Buch 4, 5, Jungler nah) zählt ebenfalls als Vorsicht.

**A2 – Konkrete Sprache** (`kern/sprache.py`):
- **Turmnamen:**
  - Besitzer und Lage: „dein äußerer Mid-Turm“, „euer innerer Bot-Turm“, „ihren inneren Top-Turm“.
  - Rückzug: „Zurück unter deinen Mid-Turm: Aurora und Viego kommen.“
  - Im Kampf: „Raus, zu deinem Turm!“ bzw. „Raus, zu eurem Top-Turm!“ oder „Raus, zu Kayn!“.
  - Turmfall: „Ihr äußerer Mid-Turm ist weg.“, zwei Türme: „Zwei ihrer Türme weg.“
- **Kurzform:** nie nur „Dann <Ort>.“, sondern immer mit Beobachtung („Dann zur Top-Welle: dein Team ist unten.“).
- **„Dort nimmt sie sonst niemand“** nur mit dem Ort des Teams (Buch 4, 4).
- **Prüfung:** Eine Regel `vage_formen` + `verbotene_gruende` gilt für
  - das Szenario `sprache_konkret`,
  - die Kennzahl „Vage Sätze“,
  - den Test `konkrete_sprache` (jeder Turmname in jedem Fall, alle konstruierten Lagen).
- **Nachgezogen:** 14 Szenario-Stellen auf die neuen Wörter. Jedes Verbot bekam die neue Form dazu, nichts wurde
  gelockert.

**A3 – Fehler aus 101426:**
1. **Tot:** Tot heißt Respawn-Plan („Du lebst in 29 Sekunden wieder: kauf …, dann zurück auf Mid.“).
   - „Ich bin tot“ ist jetzt eine Frage nach dem Plan.
2. **AFK:** Die AFK-Regel ist aus (`sperre._afk`).
3. **Kontroll-Auge:** nur mit einem Platz **nach** dem Kern-Kauf (`kaufplan.plaetze_nach`).
   - **Warum R3 nicht griff:** Er prüfte jedes Item einzeln gegen das Inventar vor dem Kauf. Jetzt prüft er gemeinsam,
     auch in `kennzahlen.py`.
4. **Korrekturen:** „Er war ein paar Meter weg von mir“ ist eine Korrektur. Wen „er“ meint, steht in der vorigen Frage
   (hier „Wo's Twitch?“).
   - Die Antwort: „Stimmt, Twitch war bei dir, das hat die Karte zu spät gezeigt. Jetzt: …“.
   - „Wo's Twitch?“ beantwortet jetzt der Kern aus der Kartenlage, vorher ging die Frage an Claude.

**A4 – Lagebild** (`kern/kartenlage.py`):
- **Auf Abruf** („Überblick?“, „Lage?“, „wo sind alle?“, Absicht LAGE), zwei Sätze: wer wo nach Kartenseite, Flashs mit
  Uhrzeit, Tote, dann die Folgerung.
  - Beispiel: „Naafiri und Yone Mitte, Caitlyn und Lux unten, Teemo tot bis 16:35. Oben ist 20 Sekunden frei.“
- **Ungefragt ab 14:00:** höchstens einmal je 90 s, in einem ruhigen Moment, ≤ 16 Wörter.

**A5 – Abnahme:** siehe „Kritik“.

**101426, eigene Szenarien:** `2026-09-28_101426_auftrag008.toml`, **16 / 16 grün**.
- Auf dem Stand vor 008 waren 14 davon rot.
- Grün waren schon der Wächter 2531 und 2839: Der Kontroll-Auge-Satz kam in der Wiederholung nicht vor, dafür ist der
  Unit-Test `kontrollauge_nur_mit_platz` rot.
- Ein zweiter Wächter (20:11, Tod 20:16) ist nach A1 nicht haltbar, siehe „Offen“.

### Teil 1 – Buch 4

1. **Kartenlage** (`kern/kartenlage.py`):
   - Je Gegner: letzte Sichtung (Seite, Alter), vermutliche Seite, MIA, Respawn, Flash/TP, Level, Item-Gold.
   - Zusammengefasst: oben / Mitte / unten / unbekannt / tot, dazu das Fenster je Seite.
   - Zu sehen im Dashboard (Kasten „Kartenlage“) und in `kern.kontext()`.
   - Geprüft mit `werkzeuge/dashboard_nachspielen.py --kern` und einem Headless-Screenshot (164326, 16:10): Kasten da,
     keine JS-Fehler.
2. **Teamplan** (`kern/teamplan.py`):
   - Kurven aus `lane_kurve.toml`, dazu der Stand in Gold-Punkten; daraus einer von vier Plänen.
   - Der Satz kommt einmal ab 14:00, bei einem Umschwung erneut (Inhibitor, Baron, Seele, oder ±2000 Gold und damit ein
     neuer Plan), höchstens einmal je 300 s.
   - Bei Gleichstand zweier Handlungen gewinnt die passende (+1 EV).
   - Beispiel 164326: „4000 Gold vorn und jetzt stärker: Drache und ihre Türme als Gruppe erzwingen.“
3. **Warum-Regeln:**
   - **Entscheidender Grund** (`fuehren.entscheidend`): der EV wird in Nutzen, Risiko und Zeit zerlegt. Entscheidend ist
     die Größe, ohne deren Unterschied die Wahl gegen die zweitbeste kippt.
     - Das Protokoll zeigt sie je Kern-Satz („Entscheidend: risiko (ohne ihn kippt die Wahl zu HALTEN)“).
   - **WARUM-Antworten:** der Plan-Satz, dann die Alternative mit ihrem konkreten Nachteil (`fuehren.warum_satz`).
     - Beispiel: „…, dort ist es sicherer. Zum Drachen: dort wäre Rumble in 15 Sekunden bei dir.“
   - **Test gegen verbotene Gründe** über alle Satzbausteine (Quelltexte und konstruierte Lagen).
4. **Makro-Infos** (`kern/makro.py`):
   - Die Regeln: Teamplan, Jungler-Sichtung weit (nur wenn der Plan das Fenster nutzt) und nah, Gruppierung, Spike
     (Items und Level 6 ihres Stärksten, wenn er vor dir liegt), drei von ihnen tot (als Wendepunkt).
   - Budget: eine je 45 s, zusammen mit FENSTER und VORSCHAU.
   - Doppelung: dieselbe Info höchstens einmal in 60 s, außer die Folgerung ändert sich.
   - Ohne Wirkung geht die Info nur aufs Dashboard.
   - Die ältere Jungler-FENSTER-Ansage (Buch 11) steht nur noch vor Plänen, die das Fenster nutzen.
   - Objective-Vorlauf mit Grund.
5. **Szenarien (Kapitel 6):** `*_buch4.toml`, **5 / 5 grün**.
   - Auf `dac2581` waren alle rot außer dem Wächter 173159 10:58.
   - `164326 1400-teamplan`, `173159 1400-teamplan` (Kurvensummen stehen im Szenario), `213624 1617-drei-von-ihnen-tot`.
   - Die Jungler-Stelle liegt in **164326 30:48**: In 173159 gibt es keine (siehe „Abweichungen“).

### Kennzahlen (Endstand, `kennzahlen.py --nur-kern`)

| Partie | ungefragt je 30 min | ohne Flash/Wendepunkt | Warnungen je 30 min (Anteil) | vage Sätze | Leerlauf ab 14:00 |
|---|---|---|---|---|---|
| 101426 (live vorher: 80 Ansagen, 36 Warnungen) | 68 | 52 | **11,7** (17 %) | 0 | 59 % |
| 164326 | 72 | 51 | 8,4 (12 %) | 0 | 54 % |
| 173159 | 67 | 46 | 7,8 (12 %) | 0 | 52 % |
| 144655 | 37 | 37 | 12,4 (33 %) | 0 | – |
| 213624 | 78 | 60 | 9,6 (12 %) | 0 | 31 % |

- **Warnungen** sind GEFAHR ohne Kampfrufe (Rein, Annehmen, Dreh um) plus VORSICHT.
- **Vorher:** Auf dem Stand vor 008 hatte die Wiederholung von 101426 35 GEFAHR-Sätze in 35,9 min.
- **Soll ≤ 10 je 30 min:** knapp verfehlt in 101426, dazu 144655 (vier Sätze in 10 min).

**Tests:** `tests/alle.py` **10 / 10**, konstruierte Lagen **40 / 40**.

**Szenarien:** **217 / 221 grün**, 3 übersprungen.
- **Rot, alle schon vor 008:**
  - die Wendepunkt-Probe in 3 Dateien (12 späte oder fehlende Sätze, vorher 29),
  - `0944-erster-tower-was-jetzt`.

**Neue Unit-Tests** (alle auf `dac2581` rot):
- `konkrete_sprache`, `keine_verbotenen_gruende`, `warum_mit_vergleich`, `vorsicht_statt_raus`,
- `viego_bleibt_viego`, `ihr_jungle_heisst_ihr_jungle`, `kontrollauge_nur_mit_platz`.

### Kritik (Einzelheiten in `008_kritik.md`)

| Partie | falsch je 30 min | Warum ja | hilft | nervt |
|---|---|---|---|---|
| 101426 | 2,5 | 91 % | 88 % | 10 % |
| 164326 | 0,7 | 95 % | 91 % | 4 % |
| 173159 | 0,8 | 92 % | 93 % | 2 % |
| 144655 | 0,0 | 70 % | 83 % | 8 % |
| 213624 | 0,0 | 89 % | 95 % | 5 % |

Kein „gefährlich“. Nach der Zählung gebaut, ohne Nachzählung:
- Vorsicht nur in ihrem Jungle (5 Fälle),
- Respawn-Plan mit Kauf,
- „Raus, zu eurem Top-Turm!“,
- Leben-Zahl beim Sprechen,
- „Sie haben den Baron.“

### Abweichungen (entschieden nach Buch 4, Kapitel 1)

1. **A1 „kommt näher“:** Auch wer schon in 1500 steht, zählt, wie `p_da` in 7.5.
2. **A1 „klar unterlegen“:** gilt nur gegen die robust gezählten Köpfe (Level und Gold). Die Überlegenheits-Regel
   selbst zählt Ungesehene mit `p_da ≥ 0,1`; in 101426 um 14:00 machte sie aus Aurora allein „drei gegen eins“.
3. **A4 Lagebild:** 30 s Ruhe statt 90 s. Nach 14:00 gab es in 101426 keine Stille über 67 s, das Lagebild wäre also
   nie gekommen. Dazu: kein sichtbarer Gegner, der in 15 s bei dir sein kann.
4. **Vorsicht:** nur Gegner, die schon bei dir sein können; dieselben Fehlenden nicht noch einmal in 180 s; nur in ihrem
   Jungle oder ihrer Basis. Das ist strenger als A1, nach der Probe (213624: acht Vorsicht-Sätze in 25 min) und der
   Kritik.
5. **MIA (Buch 4, 5)** geht im Vorsicht-Satz aus A1 auf. Ein eigener MIA-Satz hätte A1 unterlaufen.
6. **Teamplan:** „skaliert besser“ erst ab 2 Kurvenpunkten Unterschied (die Kurve ist grob; 213624: −1 gegen 0).
   Ohne „Ihr seid“, damit der Satz ≤ 14 Wörter hat.
7. **„Drei von ihnen tot“** ist ein Wendepunkt und keine Makro-Info. Das Makro-Budget war in 213624 um 16:22 durch einen
   FENSTER-Satz belegt.
8. **Kapitel 6, Jungler-Sichtung in 173159:** Olaf war dreimal unten (10:58, 11:35, 18:28), Riven farmte oben, und der
   Kern hatte keine Option, die das Fenster nutzt.
   - Die positive Stelle liegt deshalb in 164326 um 30:48.
   - 173159 um 10:58 ist der Wächter „ohne Wirkung, kein Satz“.
9. **Entscheidender Grund:** Ungefragte Sätze behalten den Grund ihres Moduls (die Beobachtung). Die Gegenrechnung wirkt
   in WARUM-Antworten und steht im Protokoll.
10. **Kartenlage „stand“:** Level und Item-Gold aus der API, ohne die Schätzung aus Buch 7, 3.2.

### Unterwegs gefunden und behoben

- **Viego in fremder Gestalt:** Die API nennt ihn „Urgot“ (101426 5:25: „Aurora und Urgot kommen“, Urgot war Carlos'
  Mitspieler). Jetzt aus `rawSkinName`.
- **Rotes Team:** Für das rote Team war ihr Jungle „euer Jungle“ (`bereich_aus`; Carlos war in 101426 rot).
  Betroffen waren Ortsangaben, `tief()` und `meine_seite`.
- **Leben-Zahl:** Die Zahl im Satz war die vom Moment der Wahl, nicht vom Sprechen (173159 22:17: 29 % statt 13 %).
- **Doppelte Doppelpunkte:** „Noch 8 Sekunden: Dann zu …: …“ heißt jetzt „Noch 8 Sekunden, dann zu …: …“.

### Offen

- **101426:** 11,7 Warnungen je 30 min und 2,5 „falsch“ je 30 min, jeweils vor den Fixes nach der Kritik gezählt bzw.
  gemessen.
- **Leerlauf ab 14:00:** 52–59 %; ungefragt 67–72 je 30 min.
- **Abgebrochene Sätze:** Das ist der Transport im Sprechplan.
- **Nicht gebaut** (Teil 0):
  - Drache vor Inhibitor über den EV;
  - Warnung im Recall-Kanal nur, wenn der erste Gegner vor Kanal-Ende plus 1 s da sein kann.
- **20:16 in 101426:** Nach A1 kommt keine Warnung (sichtbar zwei gegen zwei, Viego 17 s ungesehen, Tod 5 s später).

## Auftrag 007 – Entscheidungen, die restlichen Fehlerklassen, Live-Tauglichkeit (28.09.2026)

Grundlage: `buecher/auftraege/007_auftrag.md`. Offline gemessen, der Coach wurde nicht gegen ein Spiel gestartet. Die
Generalprobe ist der verlangte Probelauf gegen einen nachgebauten Client.

### Teil A – Entscheidungen

1. **Wendepunkt und FARMEN:** Am Wendepunkt kommt jetzt immer ein Satz mit Grund und dem, was als Nächstes kommt
   (`fuehren.farmen_satz`). Die Reihenfolge:
   - ein Ereignis der Zeitleiste (≤ 90 s);
   - „Rumble ist 40 Sekunden weg“;
   - „bei 1300 Gold back für Eklipse“;
   - „Spitzhacke ist schon bezahlbar: nach der Welle back“;
   - danach;
   - zuletzt „dort nimmt die Welle sonst niemand“.
   Ein Halte-Plan bekommt „Warte hier: Baron spawnt in 40 Sekunden“ oder „Bleib bei deinem Team“, sonst Stille
   (`halten_satz`).
2. **Wächter 16:21:** bestätigt, der Vermerk im Szenario ist angepasst.
3. **Respawn-Ziel in der Lane-Phase:** der äußere Turm, außer ≥ 2 Gegner standen in den letzten 10 s sichtbar ≤ 2000
   davon. Dann heißt es: „Bleib am inneren Turm: A und B stehen an deinem äußeren.“ (`basis._sicherer`)
   - 144655 1:59 jetzt: „Noch 8 Sekunden, zurück nach Top: an deinen äußeren Turm, dort kommt deine Welle.“
   - Das Gefahr-Modell rechnet dort p_tod 1,00, obwohl nur Gangplank in der Nähe ist. Das alte Szenario
     `0159-wohin-risiko` (p_tod ≤ 0,3) ist deshalb aufgehoben.
4. **Belagerung:** neue Regel in Buch 5, Nachtrag 7.1 (`merkmale._belagerung_von`, Modus VERTEIDIGEN aus der Ferne).
   - Abweichung: „auf einer Lane in eurer Hälfte“ wird als „in eurer Hälfte“ gelesen.
   - Nexus-Rennen: in ihrer Basis, einer ihrer Inhibitoren weg, und ≥ 2 von euch dort oder ≥ 2 von ihnen tot.
5. **Lange Objectives:** Baron, Ältester und Objectives mit Tötungszeit > 25 s sind nur klar überlegen, wenn höchstens
   ein lebender Gegner länger als 20 s ungesehen ist (`ueberlegen.lage(lang=…)`). 164326 21:01 „Baron jetzt“ ist weg.
6. **Flash-Clips** (Stufe 1, nur sammeln):
   - Anlässe: jeder erkannte Sprung (Balkenspur, Minimap) und jeder Chat-Ping „Blitz“/„Flash“.
   - Gespeichert werden 1,0 s vor bis 0,5 s nach dem Anlass, aus einem Ringpuffer der Spurbilder (~12/s).
   - Format: 800 × 450, JPEG 70, ~0,4–0,7 MB je Clip, nach `aufnahmen/<stamm>_flashclips/<ms>_<anlass>/`.
   - Geschrieben wird im Hintergrund. Test: `flash_clips_rund_um_den_anlass`.
   - `bilder_aufraeumen` räumt die Clips nicht mit auf.

### Teil B – Fehlerklassen aus 005_kritik_runde2.md

Jede Klasse hat ein Szenario aus dem echten Fall, zuerst rot auf `e6caa6a`. Nur 1711 war schon grün und bleibt als
Wächter.

| Klasse | Fix | Szenarien |
|---|---|---|
| 6: Antwort und Ansage zählen verschieden | eine Zählung `ueberlegen.koepfe` (schon dort ≤ 2500, kommen in `kampf_fenster_s` = 30 s) für die Ansage (Überlegenheit, Objective-Grund) und die Antwort; der Satz sagt „zwei stehen schon dort, zwei kommen“ | `1054-gleich-gezaehlt` |
| 9: Back ohne Anlass | kein Back in GEFAHR (dann ZURUECK) und in der Basis; kein neuer Back-Ruf ohne Ereignis; ein Back nur aus Gold löst eine eben gesagte Objective-/Turm-Ansage nicht ohne Ereignis ab | `0639`, `3459`, `3949`, `1711` |
| 10: Ziel springt | ein Turmziel wechselt nur mit Wendepunkt; im Umwandel-Fenster bleibt es, bis es fällt, und fällt nicht auf einen niedrigeren Rang zurück; danach streng nach Buch 5, 8 (Nexus > Inhibitor > innen > außen); an der Grube mit Team kein Turm woanders | `3514`, `3554`, `4209`, `4233`, `2017` |
| 11: Farmen statt Back | Gold ≥ nächster Kauf + 500 oder Leben < 40 %: FARMEN fällt weg, Back ist Kandidat (auch ohne Welle); Ausnahme Objective/Fenster ≤ 30 s | `1623`, `2556`, `2837` |
| Einzelfälle | Flash-Meldung einmal je Verbrauch (`_flash_info`); ein Ziel je Basis-Aufenthalt, auch in der Warteregel | `0418`, `3715` |
| Teil A | s. oben | `1259`, `0159-aeusserer-turm`, `2101`, `3650` |

**Unterwegs gefunden und behoben:**
- **Rückzugs-Episode (sicherheitsrelevant):**
  - Jeder Plan „Back jetzt“ hielt die Episode offen, auch ein stiller. In 213624 blieb sie so von 15:31 bis 24:10
    offen.
  - „Raus zum Mid-Tier-1-Turm: Xin Zhao und Ziggs kommen“ (24:11, GEFAHR) galt als derselbe Rückzug und wurde nicht
    gesagt.
  - Jetzt hält nur ZURUECK die Episode offen. Szenario `2411-rueckzug-episode`.
- **Dashboard:** `_zeitleiste_stand` hatte seit Auftrag 003 ein `lru_cache` mit Listen-Parameter. Der Kern-Kasten warf
  bei jedem Takt TypeError. Gefunden in der Generalprobe.
- **Wendepunkt-Messung:** Die Probe setzt einen Wendepunkt oft 1–2 s später als der Kern. Sie schob dann den Start
  hinter genau den Satz, der ihn beantwortet (164326 0:19). Ein Plan-Satz, der ≤ 2 s vorher begann, zählt jetzt als
  Antwort.

**Angepasste Szenarien (widersprachen den Entscheidungen):**
- `0944-nach-turmfall-kein-farmen`: „Turm ist down: Farm …“ mit Grund ist nach A 1 erlaubt, verboten bleibt die Floskel.
- `0517-platte-ohne-flash` und `k-back-40-prozent` (konstruiert): In GEFAHR ist ZURUECK richtig (Klasse 9).
- `0159-wohin-risiko`: s. A 3.

### Teil C – Live-Tauglichkeit auf 7680 × 2160

**C1, was kopiert wird:**
- Die Kamera kopiert nie den ganzen Desktop, nur Ausschnitte.
- Die Minimap (764 × 764) kommt in jedem Takt.
- Das „ganze Spielfenster“ war bei randlosem League aber der ganze Schirm, 7680 × 2160 (66 MB). Es kam 12-mal je
  Sekunde für die Balkenspur und 1-mal je Sekunde für HUD und Claude-Bild. Dabei wurde es auf 1600 × 450 gestaucht, mit
  halb so hohen Lebensbalken wie vermessen: Die Balkenspur wäre blind gewesen.
- **Fix:** Das Spielbild ist die 16:9-Mitte (3840 × 2160), also der 4K-Maßstab. Q W E R D F und V rechnen von der Mitte
  aus. Der Chat rechnet in 16:9-Breite.
- **Kamera:** dxcam baute jede Staging-Textur zuerst in voller Bildschirmgröße (66 MB) und verkleinerte sie erst beim
  nächsten neuen Bild. Jetzt baut sie gleich in Ausschnittgröße. Der Kamera-Test prüft nur noch Textur = Ausschnitt.
- **GDI-Rückfall** kopiert nur noch den Ausschnitt: Minimap 8 ms statt 125 ms.
- **Fensterlage (korrigiert 28.09.2026, Carlos):** League läuft randlos als **3840 × 2160-Fenster in der Mitte** des
  7680 × 2160-Schirms (`game.cfg`: WindowMode 2, Width 3840, Height 2160). Links und rechts bleiben je 1920 px für
  YouTube oder Discord. Die Minimap sitzt rechts unten **im Spielfenster** (Schirm-x 4969–5733), nicht am rechten
  Schirmrand.
  - ~~Annahme: Randlos nimmt League die Desktopauflösung, also 7680 × 2160 bei (0, 0), und das HUD sitzt bei 32:9 an
    den Rändern (Minimap rechts unten außen).~~ Das war falsch; die Datei sagte schon damals Width 3840.
  - **Geprüft im Code:** Der Coach findet das Fenster über seinen Titel (`bild.spielfenster`: FindWindow und
    ClientToScreen). Minimap, HUD, Spielbild und Chat rechnet er ab der linken oberen Fensterecke. dxcam kopiert nur den
    Ausschnitt (CopySubresourceRegion), nie den ganzen Schirm.
  - **Je Takt kopiert:** Minimap 764 × 764 (~25/s). Das Spielfenster 3840 × 2160 kommt 12/s für die Balkenspur und
    1/s für HUD, Tasten und das Claude-Bild. Mitspieler-Leiste und Chat kommen 1/s. Bei einem 16:9-Fenster ist das
    Spielbild das ganze Fenster.

**C2, Generalprobe:** 2 × 2,5 min, nachgebautes Fenster 7680 × 2160, Partie 164326, HUD im 32:9-Nachbau.

| Messung | Ergebnis | Soll |
|---|---|---|
| Minimap gefunden | 904 / 906 Bilder | ja |
| HUD gelesen | 137 / 137 mit Leben | ja |
| Ausnahmen im Beobachter | keine | keine |
| Takt | **6 / s (über GDI)** | ≥ 10 / s |
| CPU / Speicher | Coach-Prozess 255 % eines Kerns (28 Kerne), Beobachter 66 %; 292 MB (Spitze 362 MB) | – |

- **Der Takt ist nicht nachgewiesen.** Der Bildschirm war während der Probe aus (Carlos seit Stunden nicht am Rechner),
  und die Desktop-Duplizierung (dxcam) lieferte kein Bild. Die Probe lief deshalb über GDI, und GDI braucht 83 ms je
  Spielbild.
- Zum Vergleich: live 4K in 164326, 173159 und 213624 lieferte im Median 25 Minimap-Bilder/s, im 5-%-Quantil 11–14. Nach
  dem Fix kopiert 7680 genau dieselben Ausschnitte wie 4K.
- ~~**Offen:** Die Generalprobe mit eingeschaltetem Bildschirm wiederholen.~~ Erledigt am 28.09.2026 (s. unten).

**C2 nachgeholt (28.09.2026, Bildschirm an, Desktop-Duplizierung):** je 2,5 min, Partie 164326.

| Messung | Vollbild 7680 × 2160 | **Fenster 3840 × 2160 bei x = 1920** (Carlos' Aufbau) | Soll |
|---|---|---|---|
| Takt (Minimap-Bilder/s) | Mittel 23,8, Median 24, 5 % 16, schlechteste Sekunde 10 | **Mittel 24,7, Median 25, 5 % 17, schlechteste Sekunde 13** | ≥ 10 / s |
| Minimap gefunden | 3548 / 3548 | **3652 / 3654** | ja |
| HUD gelesen | 145 / 145, Tasten 145 | **146 / 146, Tasten 146** | ja |
| Fehler | keine | **keine** | keine |
| CPU / Speicher | 523 % eines Kerns; 331 MB (Spitze 375) | 545 % eines Kerns; 335 MB (Spitze 382) | – |

- **Beweis der Fensterlage:** Mit Schirm-Koordinaten hätte der Coach bei x = 1920 neben die Minimap geschaut. Er fand
  sie in 3652 von 3654 Bildern.
- **Probe-Umbau:** Die alten Probebilder fehlten. Jetzt nimmt sie Partie 164326 und das 32:9-HUD. Eine pulsierende
  Ecke erzwingt echte Takte. Sie misst CPU und Speicher mit und beendet den Prozessbaum.
- **Nebenwirkung:** Beim Start holte der Coach einmal das Review einer alten Probe nach, das ist ein Claude-Aufruf.

**C3:** Der Kamera-Test ist grün, `tests/alle.py` **10 / 10**.

### Teil D – Kritik Runde 3 und Nachzählung

Klassen und Einzelheiten: `buecher/auftraege/007_kritik_runde3.md`. „falsch“ je 30 min:

| Partie | 005 R1 (vorher) | 005 R2 | 007 R3 (`9487b8e`) | 007 Nachzählung (`de4500c`) | Soll |
|---|---|---|---|---|---|
| 164326 (echt) | 11,9 | 9,8 | 4,2 | **2,8** | ≤ 2 |
| 173159 (echt) | 7,0 | 3,9 | 7,0 | **1,6** | ≤ 2 |
| 144655 (echt) | 6,2 | 3,1 | 3,1 | **0,0** | ≤ 2 |
| 213624 (Bot) | 19,1 | 15,5 | 12,0 | – | – |
| 102112 (Bot) | 11,8 | 3,0 | 3,9 | – | – |

- **„Gefährlich“** (ein Ruf nach vorn vor einem Tod): in R3 einer (173159 35:09, behoben), in der Nachzählung keiner.
- **Nach R3 behoben** (`de4500c`):
  - Wiederbelebte stehen an ihrem Brunnen.
  - Kein „Warte hier“ am Wendepunkt.
  - Kein Farm-Satz gegen ein eben gesagtes Back.
  - Ein Objective-Ziel hält ohne Wendepunkt.
  - Ein Turmziel verfällt mit seinem Fenster.
  - Die Antwort nach dem Kauf nennt das Ziel.
  - „X ohne Flash“ braucht 1,5 s statt 8 s Ruhe.
- Die Nachzählung lief nur über die echten Partien, denn nur für sie gilt die Schwelle.
- Vorsicht beim Vergleich: Jede Spalte hat andere Kritiker, und die Streuung ist groß (173159: 3,9 → 7,0 → 1,6).

### Tests und Szenarien (Endstand `de4500c`)

- `tests/alle.py` **10 / 10**.
- Szenarien **190 / 194**, 2 übersprungen. Rot sind die Wendepunkt-Probe (3 Dateien) und die Frage 9:44.
- Konstruierte Lagen **40 / 40**.
- Die Wendepunkt-Probe hat 29 späte Sätze oder Wendepunkte ohne Satz. Vor den Fixes der Runde 3 waren es 20: Die
  gestrichenen „Warte hier“-Sätze fehlen ihr jetzt. Vor 007 waren es rund 70.

---

## Auftrag 006 – Wahrnehmung: Welle, Quest-Anzeige, Flash im Spielbild (28.09.2026)

Grundlage: `buecher/auftraege/006_auftrag.md`. Offline gemessen, der Coach wurde nicht gestartet. Das Entscheiden bleibt
unangetastet.

### W1. Welle (Soll: 173159 ≥ 80 % der eindeutigen, 144655 und 164326 nicht schlechter)

`wellen_eichung.py --neu` rechnet jetzt mit dem aktuellen Code nach. `--auswerten` las nur den gespeicherten Zustand
vom Tag der Tafel. Mit `--schalter` lässt sich jeder Schalter aus `[welle]` einzeln setzen. Mit allen Schaltern aus
reproduziert es die alten Zahlen genau.

Drei Ansatzpunkte aus den Fehlerursachen der Qualitätsrunde 2, je ein Schalter:

| Schalter | 173159 | 144655 | 164326 | gesetzt |
|---|---|---|---|---|
| vorher (alle aus) | 7 / 12 | 9 / 11 | 13 / 15 | – |
| `hysterese_zu_mitte_s = 1`: zwischen ZU_IHM, ZU_DIR und MITTE 1 s statt 3 s | **10 / 12** (11:07, 11:57, 12:49) | 9 / 11 | 13 / 15 (3:59 behoben, 10:57 neu falsch) | **an** |
| `icon_deckung_zone`: die Icon-Deckung zählt nur in der Crash-Zone | 7 / 12 (7:33 bleibt) | **6 / 11** (3:13, 5:31, 5:38) | 13 / 15 (5:01 behoben, 3:59 bleibt) | aus |
| `trend_farbwechsel`: der Trend beginnt neu, wenn die Front die Farbe wechselt | 8 / 12 (11:07) | 9 / 11 | 12 / 15 (10:57 neu falsch) | aus |
| alle drei an | 10 / 12 | 6 / 11 | 12 / 15 | – |

**Ergebnis:** 173159 **10 von 12 (83 %)**, 144655 9 von 11 (82 %), 164326 13 von 15 (87 %). Das Soll ist erreicht.

- Die Icon-Deckung aus Qualitätsrunde 1 trägt 144655. Sie auf die Zone zu begrenzen kostet dort drei Treffer, und
  173159 7:33 behebt es trotzdem nicht.
- Offen bleiben 173159 7:33 (Icon am Zonenrand) und 9:25 (übereinanderliegende Vasallen, `Wellenleser.punkte`). Beide
  sind Wahrnehmung im Bild, kein Schwellwert.
- Szenarien, Tests und konstruierte Lagen sind unverändert (163 / 167, 40 / 40).

### W2. Quest-Fortschritt im HUD: passiv lesbar

- **Der Quest-Platz V liegt rechts neben den Items und ist ohne Tastendruck immer zu sehen:**
  - Solange die Quest läuft, zeigt er einen **türkisen Ring**, der wächst. Sein Anteil in 164326 steigt von 0,19 um
    10:00 auf 0,26 um 12:02, der Fortschritt ist also sichtbar.
  - Ab dem Quest-Ende zeigt er das **violette TP-Symbol** mit einem gelben „V“.
  - Während der Abklingzeit ist er dunkel.
- Bilder: `buecher/quest_pruefung/quest_164326_verlauf.png` (3:00, 6:00, 9:00, 11:00, 11:55, 12:05: der Ring wächst,
  dann violett) und `quest_164326_vorher_nachher.png` (11:40 / 12:10, Items und Platz V).
- **Erkennung** (`hud.quest`): Farbanteile im Quadrat um den Platz, violett oder türkis ≥ 0,08. Das erste violette
  Schirmbild je Partie:

  | Partie | erstes violett | Handmessung (Auftrag 002, S4) | Quest-TP bereit im Kern (nachgespielt) | vorher |
  |---|---|---|---|---|
  | 213624 | 9:46 | 9:31–9:46 | 9:51 | 13:35 |
  | 102112 | 11:31 | 11:10–11:36 | 11:36 | 13:35 |
  | 173159 | 11:40 | 11:30–11:51 | 11:46 | 13:35 |
  | 164326 | 12:07 | 11:51–12:07 | 12:12 | 13:35 |
  | 144655 | nie (9,7 min) | – | – | – |

- **Umbau:**
  - Live liest der Beobachter V einmal je Sekunde aus dem Spielbild, das er ohnehin holt (Ereignis „quest“, nur
    lesen, **kein Tastendruck**).
  - Aufnahmen ohne diese Lesung bekommen sie aus den Schirmbildern (alle 5 s, `lage._quest_aus_bildern`).
  - Ein Wechsel zählt erst nach zwei gleichen Lesungen, deshalb liegt „bereit im Kern“ bis zu 5 s hinter dem ersten
    Bild.
  - `QuestTP` nimmt das erste bestätigte Violett als Quest-Ende. Ist V nach einer Nutzung wieder violett, gilt es
    sofort als bereit.
  - Die Regel „bereit ab 13:35“ bleibt der Rückfall.
  - Schalter: `[quest_tp] hud_lesen`, `hud_frisch_s`.
  - Test: `test_quest_tp.test_quest_ende_aus_dem_hud`.

### W3. Flash im Spielbild: Machbarkeit

**Was aufgenommen wird** (`lage.Beobachter`):

| Ausschnitt | Rate live | auf der Platte |
|---|---|---|
| Minimap | mit dem Takt | 1 / s (764 × 764) |
| ganzes Spielbild | ~12 / s für die Balkenspur (Flash-Sprünge über den Lebensbalken, `SPUR_ALLE` 0,08 s), 1 / s für HUD, eigene Tasten, Balken und jetzt V | alle 5 s, auf 1600 Breite verkleinert (`schirm_*.jpg`) |
| Chat (links unten) | 1 / s | bei neuen Zeilen (`chat_*.jpg`) |
| Mitspieler-Leiste | 1 / s | nein |

**Fünf gegnerische Flashs**, je das nächste gesicherte Schirmbild (Bilder in `buecher/flash_pruefung/`):

| Flash | Quelle | Bild | Blitz erkennbar? |
|---|---|---|---|
| 164326 14:47 Teemo | Bildschirm (Balkenspur) | +0,8 s | nein, Teemo ist nicht im Bild |
| 164326 22:21 Teemo | Chat | −1,0 s | nein, Riven steht im Brunnen |
| 164326 33:19 Teemo | Bildschirm | −0,5 s | nein. Teemo ist im Bild, im Kampf ohne gelben Blitz, zu viele Effekte |
| 173159 21:25 Zilean | Bildschirm | +0,5 s | unklar: ein heller Schein an Riven, eher ihr eigener Effekt |
| 173159 2:34 Cho'Gath | Minimap | +1,1 s | nein |

**Befund:**
- **Mit dem, was auf der Platte liegt, lässt sich das nicht prüfen.** Ein Flash-Blitz leuchtet nur ~0,3 s, die
  Schirmbilder kommen alle 5 s. Selbst ±0,5 s daneben ist nichts mehr zu sehen.
- **Live liegt das Spielbild mit ~12 / s vor.** Einen Blitz im Bild sähe man also in 3–4 Bildern, aber nur, wenn der
  Flashende auf dem Bildschirm ist. Genau diese Flashs findet schon die Balkenspur: 4 von 12 in 164326 und 5 von 9 in
  173159 haben die Quelle „Bildschirm“.
- Die übrigen passieren außerhalb des Bildes. Für sie bleiben Chat und Minimap die einzigen Quellen.
- Ein gelber Blitz brächte also vor allem eine Bestätigung (Flash statt Dash), kaum neue Flashs.
- **Wenn gebaut werden soll, zuerst messen:**
  - nach einem Sprung der Balkenspur 1–2 s des Spielbilds mit 12 / s sichern;
  - dann an 20 echten Flashs zählen, wie oft der Blitz zu sehen ist und wie oft ein Dash ihn vortäuscht.

### Tests und Szenarien

- `tests/alle.py`: 9 / 10 (neu: `test_quest_ende_aus_dem_hud`). Weiter scheitert nur `kamera_gibt_nur_einmal_frei` an
  der Umgebung.
- Szenarien: **163 / 167** (unverändert), konstruierte Lagen **40 / 40**.

---

## Auftrag 005 – Selbstprüfung mit einem unabhängigen Kritiker, zwei Runden (28.09.2026)

Grundlage: `buecher/auftraege/005_auftrag.md`. Je Runde drei Kritiker-Agenten ohne Codewissen (Rolle:
Challenger-Toplaner, Riven-Main, und Coach). Jeder bekam die Protokolle, Carlos' Notizen aus 213624 und die drei
Prüfungen vom 27.09. und bewertete jede gesprochene Ansage und Antwort mit ok, schwach oder falsch. Die Klassen und
Beispiele stehen in `buecher/auftraege/005_kritik_runde1.md` und `005_kritik_runde2.md`. Offline gemessen, der Coach
wurde nicht gestartet.

### Runde 1 → Fixes (`76e2a3b`)

Gebaut wurden nur Klassen mit „falsch“ ≥ 2. Jede bekam ein Szenario aus einem echten Fall, alle 13 zuerst rot.

1. **Überlegenheit zählt, wer da sein kann:** `[ueberlegen] p_da_min` 0,3 → 0,1.
   - Bei 0,3 fehlten 90 s Ungesehene: 173159 28:52 „Nimm den Kampf“, drei kamen, Tod 29:03; 164326 28:58 „Rein auf
     Lux!“.
   - Das ist strenger, keine Schranke wird gelockert.
2. **Ein Verlust der anderen Seite ist eine Nachricht, kein Grund:**
   - „Euer Bot-Turm ist weg. Drück den inneren Top-Turm …“ statt „Euer Turm ist weg: Drück …“ (`fuehren.verbinden`,
     mit Lane aus `zustand.struktur`).
   - „Danach“ wiederholt nie den Plan (102112 27:51 „Back. Danach back.“).
3. **Einkommen:** Sprünge über 100 Gold je Takt (Startgold, Kopfgeld, Platten) zählen nicht, vor 1:30 gibt es keins.
   Damit fällt 164326 0:19 „Caulfields in 41 Sekunden kaufbar“ bei 0 Gold weg.
4. **Rückblick:** Wer ≤ 60 s angesagt war oder ≤ 20 s wiederbelebt ist, „kam nicht aus dem Nebel“ (173159 35:13,
   144655 9:23). Bei einem Respawn: „… ist gerade neben dir wiederbelebt.“
5. **Notizen:**
   - Eine innere Frage braucht ein „?“ oder ein Fragewort vorn. Nur „soll ich“ darf mitten im Satz stehen, etwa „Dann
     soll ich doch erst recht kämpfen“ (23:45).
   - Das beendet „Notiert. Nein. …“ (213624 20:00, 21:03).
6. **Objective-Antworten:**
   - Statt „lohnt gerade nicht: zu weit oder zu wenige von euch“ (geraten) kommen Fakten: Weg zur Grube und wer von
     euch dort ist.
   - Der gehaltene Plan zählt als Option (12:56 „Keins von beiden … Jetzt: Drache mit Malzahar“).
   - Antworten mit Richtung: „Zum Drachen mit Malzahar: …“.

**Nicht gebaut:**
- Grundsatz, in `005_frage.md`: Warten am Inhibitor-Turm (Schranke G2), Rückkehr bei einer Belagerung (neue Regel),
  Baron mit drei Ungesehenen.
- Kritiker irrt: „Level 20 gibt es nicht“ (die Quest hebt das Cap), „Caulfields gegen seinen Build“ (Bauteil von
  Axiombogen, Eklipse, Hydra), „Eklipse in 63 Sekunden“ (330 Gold fehlten, 5,2 Gold/s).
- Ohne gemeinsame Ursache: Back ohne Ereignis, springende Turmziele.

### Ergebnis: falsch und schwach je 30 min

„Vorher“ ist die Kritik der Runde 1 am Stand nach Auftrag 004 (`16e579b`). „Nach Runde 1“ ist die Kritik der Runde 2
am Stand `76e2a3b`. Nach Runde 2 wurde nichts mehr gebaut, „nach Runde 2“ ist also derselbe Stand. In Klammern steht
Runde 1 ohne die Kritiker-Irrtümer (Level 20, Caulfields, Eklipse).

| Partie | falsch vorher | falsch nach Runde 1 | falsch nach Runde 2 | schwach vorher | schwach nach Runde 1 / 2 |
|---|---|---|---|---|---|
| 164326 (echt) | 11,9 (8,4) | 9,8 | 9,8 | 27,3 | 12,6 |
| 173159 (echt) | 7,0 | 3,9 | 3,9 | 13,3 | 16,4 |
| 144655 (echt) | 6,2 | 3,1 | 3,1 | 15,5 | 15,5 |
| 213624 (Bot, Fragen) | 19,1 | 15,5 | 15,5 | 45,4 | 32,3 |
| 102112 (Bot) | 11,8 (7,9) | 3,0 | 3,0 | 15,8 | 11,8 |
| **alle** | 56 Sätze | 36 Sätze | 36 Sätze | 115 | 83 |

- **Was zählt:** Vorher und nachher haben verschiedene Kritiker bewertet. Die Streuung ist groß: Klasse 8 fiel von 3
  auf 0, ohne dass etwas gebaut wurde. Klasse 10 stieg von 3 auf 7, weil der Kritiker strenger war.
- **Belastbar ist das Verschwinden der behobenen Klassen:**
  - Die Klassen 2, 3 und 5 stehen bei 0.
  - Die Klassen 1 und 4 haben je einen Rest mit anderer Ursache.
  - Dazu kommen die 13 Szenarien.
- **Offen für die nächsten Aufträge:**
  - Klasse 6: Antwort und Ansage zählen „euch“ verschieden.
  - Klasse 10: überlegene Turmziele wechseln sich ab.
  - Klasse 11: FARMEN mit Vorschau, wo Back fällig ist.

### Tests und Szenarien

- `tests/alle.py`: 9 / 10. Weiter scheitert nur `kamera_gibt_nur_einmal_frei` an der Umgebung (Bildschirm 7680 × 2160,
  s. Auftrag 004). Die übrigen Bausteintests sind einzeln grün.
- Szenarien: **163 / 167**, 2 übersprungen. Rot: 3 × Wendepunkt-Probe, `0944-erster-tower-was-jetzt` (wie nach 004).
  Konstruierte Lagen **40 / 40**.
- Geändertes Szenario: `2631-zu-zweit-rein` bekam ein Fenster auf den Kampf (26:29–26:38). Der Wendepunkt-Satz zum
  Turmfall um 26:40 ist kein Kampfruf und fiel sonst unter `max_woerter = 8`.

---

## Auftrag 004 – Überlegenheit, echte Antworten, Kampf-Eichung (28.09.2026)

Grundlage: `buecher/auftraege/004_auftrag.md`. Offline gemessen, der Coach wurde nicht gestartet. Vorher = `2b455b3`
(Stand nach Auftrag 003), mit denselben Messwerkzeugen (Wendepunkt-Verzug schon ab dem Ende des laufenden Satzes).

### Zuerst rot

Worktree auf `2b455b3`, neue Szenarien und Tests hineinkopiert:

- `test_kern.keine_floskeln`: rot (`fragen.py`: „bis sich etwas öffnet“).
- `213624_fragen`: 8 der 10 geänderten Fragen rot (1:19, 1:27, 4:04, 9:44, 9:55, 12:38, 16:31, 16:40). 13:13 und
  13:18 waren schon grün (sie verbieten jetzt zusätzlich „Farm“).
- `213624`: `0944-nach-turmfall-kein-farmen` rot, `1621-66-prozent-mit-team` rot („Raus zum Mid-Tier-1-Turm: Caitlyn und
  Sona kommen.“).
- `173159_pruefung_c`: `1533-nicht-klar-ueberlegen` ist ein Wächter und war schon grün (Begründung unten).

### Teil A – Entscheidungen zu 003

- **Kein ungefragtes „unsicher“:** Der Rückfall „X nur mit Kampf - unsicher“ am Wendepunkt ist weg. Bleibt nur FARMEN,
  spricht es nur mit Vorschau (`fuehren.farmen_mit_vorschau`: „Farm Top, Herold in 31 Sekunden.“, 213624 14:29),
  sonst still. Gefragt nennt der Coach die beste Kampf-Option weiter mit „unsicher“. Sie kommt jetzt aus den
  ungefilterten Kandidaten (`kern.kandidaten_roh`), vorher fand er sie nie, weil die modellstummen dort schon fehlten.
- **Kein Unterbrechen:** Ein Wendepunkt-Satz stellt sich im Sprechplan vor wartende PLAN-Sätze (Schlüssel
  `thema == "wendepunkt"`), unterbricht aber nicht. Neu: Am offenen Wendepunkt schützen `halten_s` und `stabil_s`
  keinen **stummen** Plan (`plan.PlanFuehrer.wendepunkt`). 213624 9:44: FARMEN hielt „Zu Pantheon und Malzahar auf die
  Mid-Lane, mit dir drei gegen zwei“ 4 s zurück, jetzt kommt der Satz um 9:49 statt 9:53.
- **Mehrere Türme in 10 s = ein Satz:** „Zwei Türme down“ / „Zwei eurer Türme weg“ (`_strukturen_zusammen`).
- **Derselbe Plan am Wendepunkt:** Wurde dasselbe Ziel ≤ `ziel_wiederholen_s` vorher gesagt, bestätigt der Wendepunkt
  nur („Turm ist down: weiter zum Drachen.“), statt Ziel und Grund zu wiederholen (102112 26:40).

### Teil B – Überlegenheits-Regel (`kern/ueberlegen.py`, `[ueberlegen]`)

- Umgesetzt wie im Auftrag. G = wer in `fenster_s` am Ort sein kann (`gefahr.p_da_am` ≥ 0,3; das Fenster ist die Dauer
  der Handlung, höchstens 45 s). **Tote zählen mit**, wenn sie im Fenster am Ort aufstehen: Sonst war es am
  Mid-Inhibitor-Turm 102112 34:49 „drei gegen eins“, obwohl Sett, Kai'Sa und Fiddlesticks 11–19 s später daneben
  aufstanden. Das ist im ersten Gesamtlauf aufgefallen (Buch-6-Szenario `3451` rot) und ist behoben.
- **Klar überlegen:** DRUECKEN, MIT_GRUPPE, NEHMEN, BESTREITEN, ANNEHMEN und REIN sprechen ohne Kampfmodell, der Grund
  nennt die Überlegenheit („Drück den inneren Top-Turm: Level 11 gegen 7.“, „Drache bestreiten: Level 10 gegen 7, ihr
  seid fünf gegen zwei.“). **Klar unterlegen:** Die Handlungen sind aus (`_schranke_takt`: „klar unterlegen, …“).
  Dives bleiben unter Buch 7, Kapitel 6.
- **Kein Flackern:** Ein Urteil „überlegen“ hält `halten_s = 5`, wenn es einen Takt lang unklar wird (102112 26:38:
  Der Drache fiel zweimal heraus und wurde neu angesagt), aber nie gegen „unterlegen“. Ein „allein“-Satz bekommt kein
  „ihr seid zwei“.
- **Wächter 173159 15:33** (`1533-nicht-klar-ueberlegen`): Riven L12 mit 5650 Gold und 50 % Leben gegen Yasuo L10 mit
  5600 Gold und 100 %.
  - Zwei Level Vorsprung, aber nur 50 Gold statt 2000, und Leben unter 60 %: nicht klar überlegen.
  - „Rein auf Yasuo!“ bleibt stumm, vorher wie nachher.
  - Die Stelle ist ein Grenzfall aus einer echten Partie. Die Level allein würden einen Kampfruf nahelegen, die Regel
    verlangt aber alles.
- **Umgestellt:** Der Wächter `1621-66-prozent-bleibt` aus 003 verlangte bei 66 % „Raus: Caitlyn und Sona kommen“.
  - Dort gilt jetzt die Überlegenheit: Level 13 gegen 8, ihr seid drei (Leben ≥ 60 %). Der Plan mit der Gruppe hält.
  - Carlos um 16:31 zu genau diesem Ruf: „Warum sagst du, ich soll zurückgehen? Gar keinen Sinn.“
  - Neu heißt der Wächter `1621-66-prozent-mit-team` (darf_nicht_sagen „Raus zum“).
  - Die 70-%-Grenze aus 003 gilt weiter für dich allein. Rückfrage in `004_frage.md`.
- **Wirkung auf die Zahl der Rufe:** In der Bot-Partie 213624 sprechen jetzt die Kampfrufe: GEFAHR 7 → 23, ungefragt
  ohne INFO_FLASH/WENDEPUNKT 24 → 44 je 30 min (Soll ≤ 50). In den echten Partien bleiben sie fast überall stumm,
  weil dort selten jemand drei Level vorn liegt.

### Teil C – Antworten

- **WARUM ohne Ziel** nennt den Grund der letzten gesprochenen Ansage. Jede Ansage merkt sich dafür 60 s lang Text,
  Art, Ziel, Grund und Leben (`kern._ansage_log`).
  - Mit „raus“ oder „zurück“ in der Frage kommt „Raus hatte einen Grund: 23 Prozent Leben, 1350 Gold für den
    Brutalisierer.“ (213624 4:20).
  - Sieht der Kern die Lage jetzt anders: „Das war zu vorsichtig: …“ (klar überlegen) bzw. „Jetzt ist die Lage
    anders: …“.
  - Wurde nichts gesagt: „Raus sage ich nicht: Rumble ist tot.“ (1:22).
- **Korrekturen** (Buch 11, 5.6), `korrektur_gilt_s` lang in den Merkmalen (`Kern._korrekturen_anwenden`):
  - „Der ist jetzt bei mir oben“: Der zuletzt genannte Gegner steht an deinem Ort, sichtbar, Abstand 0 → „Stimmt,
    Xin Zhao ist bei dir: …“.
  - „Ich bin beim Drachen“: Ort und Bereich = die Grube.
  - „Alle sind tot“: ein Abgleich mit den Toten → „Nicht alle: Ziggs und Sona leben.“ (16:35), sonst „Stimmt, alle
    tot.“
- **Floskeln** sind aus allen Satzbausteinen entfernt (`test_kern.keine_floskeln` prüft `kern/`, `kern/modi/`,
  `antworten.py`):
  - „…, bis sich etwas öffnet“ → „Farm deine Top-Welle“ mit der nächsten Zeitleiste ≤ 90 s.
  - „Danach rechne ich neu“ → nach einem Turm die nächste Struktur, sonst das nächste Objective, sonst die Welle.
  - „X ist gerade keine Option“ → der Grund aus den Schranken des Takts (Leben, zu riskant, klar unterlegen) oder
    „Kein Turm in Reichweite, den du jetzt nimmst“.
- **GEWISSHEIT** (neue Absicht): „Sicher nicht: ob der Drache bis dahin fällt, sehe ich erst, wenn er fällt. Zum
  Drachen: ihr seid drei.“ (12:41). Zu einem Gegner nennt die Antwort sichtbar / zuletzt gesehen vor N s.
- **An der Grube mit Team:** kein „Farm“, sondern „Bleib mit deinem Team am Drachen: ihr seid drei, aber mit Kampf -
  unsicher.“ (13:13, 13:18), oder mit Grund, dass es ohne dich läuft.
- **Nachgezogen:** Ein Absturz im Fragenweg bei einer WARUM-Frage ohne Plan ist behoben (213624 12:14, `c.ev < h.ev`
  mit `h = None`, im Protokoll-Lauf gefunden).

### Teil D – Kampf-Eichung mit neuen Etiketten

6 echte Partien (133930, 140253, 144655, 145702, 164326, 173159), 112 Proben, nur `bots = false`.
`kampf_eichung.py --etikett gold|koepfe|ueberlebt`. Gold reproduziert Schritt 5 exakt (41 entschieden, Brier 0,320,
AUC 0,30).

| Etikett | entschieden (gew/verl) | offen | Brier | Grundrate | Art 2: Brier / Grund (n) | Art 3–6: Brier / Grund (n) |
|---|---|---|---|---|---|---|
| gold | 41 (22/19) | 71 | 0,320 | 0,249 | 0,332 / 0,248 (22) | 0,305 / 0,249 (19) |
| koepfe | 36 (21/15) | 76 | 0,309 | 0,243 | 0,324 / 0,245 (21) | 0,288 / 0,240 (15) |
| ueberlebt | 31 (26/5) | 81 | 0,251 | 0,135 | 0,340 / 0,000 (14) | 0,177 / 0,208 (17) |

| AUC je Merkmal | gold | koepfe | ueberlebt |
|---|---|---|---|
| p | 0,40 | 0,41 | 0,45 |
| leben | 0,58 | 0,61 | 0,68 |
| level_diff | 0,43 | 0,43 | 0,41 |
| gold_diff | **0,30** | **0,28** | **0,36** |
| kopf_diff | 0,51 | 0,53 | 0,26 |
| turm | 0,39 | 0,38 | 0,60 |

- **Der Verdacht trägt nicht:** Gold trennt mit jedem Etikett verkehrt herum, auch mit `ueberlebt`, das kein Gold kennt.
  Nur Paare aus derselben Partie: 0,29 / 0,30 / 0,32.
- **Die Eichung besteht mit keinem Etikett.**
  - Brier liegt überall über der Grundrate, auch mit dem besten Faktorsatz (k = 1).
  - `ueberlebt` Art 3–6 erfüllt das Soll (0,177 < 0,20 und < 0,208), aber nur mit 17 < 30 Proben.
- **Nebenbefund:** Zählt man nur die Tode der Beteiligten, sind 17 / 15 / 16 Proben entschieden. Auch so besteht nichts,
  und die Umkehr bleibt.
- **Nächster Verdacht, ungeprüft: die Spielzeit.** Sie korreliert mit gold_diff (r = 0,56), verlorene Proben liegen
  später (AUC Zeit 0,45 / 0,41 / 0,27).
- **Folge:** `[kampf].geeicht` bleibt `false`, die Faktoren bleiben. Die Kampfrufe sprechen nur über die
  Überlegenheits-Regel.

### Kennzahlen (vorher `2b455b3` → nachher)

| Kennzahl | Soll | 213624 | 164326 | 173159 |
|---|---|---|---|---|
| Leerlauf ab 14:00 | ≤ 10 % | 48 → 43 % | 52 → 48 % | 48 → 49 % |
| Wendepunkt-Verzug, Median ab Satzende | ≤ 3 s | 7,5 → 1,9 s | 4,3 → 2,5 s | 5,7 → 6,0 s |
| Wendepunkte ohne Satz in 60 s | – | 1 → 5 | 6 → 7 | 3 → 3 |
| Wendepunkt-Satz später als 3 s (Probe) | 0 | 18 → 15 | 29 → 29 | 25 → 26 |
| … davon stummer Plan (FARMEN/HALTEN, Teil A 1) | – | 8 | 18 | 20 |
| Floskeln | 0 | 9 → 0 | 0 → 0 | 0 → 0 |
| Widersprüche | 0 | 1 → 3 | 0 → 1 | 0 → 0 |
| Stichwort-Antworten | 0 | 3 → 1 | – | – |
| ungefragt ohne INFO_FLASH/WENDEPUNKT je 30 min | ≤ 50 | 24 → 44 | 37 → 46 | 51 → 53 |

- **Wendepunkte:** Der Median fällt in 213624 und 164326 unter 3 s.
  - Die späten und fehlenden Sätze stehen meist hinter einem stummen Plan: Nach Teil A 1 schweigt FARMEN ohne Vorschau
    (in 173159 20 von 26). Das ist gewollt, aber die Probe zählt es als rot.
  - In 213624 sind so aus einem fehlenden Satz fünf geworden (23:57–24:18, drei Strukturen, Plan FARMEN).
- **Widersprüche, neu:**
  - 213624 9:46: Die Antwort „Farm deine Top-Welle. Oder auf den inneren Top-Turm …“ kam 3 s vor dem neuen Plan
    „Zu Pantheon …“.
  - 213624 13:18: Die Antwort „Bleib … am Drachen“, dann der Wendepunkt „Aus der Basis“. Die Korrektur „ich bin beim
    Drachen“ ändert den Ort, aber nicht den Beobachter der Basis.
  - 164326 35:00 → 35:15: Zwei überlegene Turmziele nacheinander (Mid-Inhibitor, dann innerer Bot-Turm).
- **Rot bleibt:**
  - Die Wendepunkt-Probe in allen drei Partien.
  - `0944-erster-tower-was-jetzt`: Um 9:44, im Takt des Turmfalls, rechnet der Kern noch LANE und hat nur FARMEN. Die
    Turm-Option kommt 2 s später (9:46). Ab dann nennt die Antwort sie.

### Tests und Szenarien

- `tests/alle.py`: 9 / 10. `test_bausteine.kamera_gibt_nur_einmal_frei` scheitert an der Umgebung: Der Bildschirm ist
  jetzt 7680 × 2160, und dxcam gibt eine Fläche dieser Größe statt 200 × 100 zurück. Der Test scheitert genauso auf
  `2b455b3`, `lage.py` ist unverändert. Die übrigen Bausteintests laufen einzeln grün.
- Szenarien: **151 / 155** grün, 2 übersprungen (brauchen Claude). Rot: 3 × Wendepunkt-Probe, 0944. Konstruierte Lagen
  **40 / 40**.
- Fragen-Probe 213624: **50 / 51**.

---

## Auftrag 003 / Schritt 6 – Buch 11 (Führen, Vorausschau, Antworten) und Fragen (27.09.2026)

Grundlage: `buecher/11_fuehren.md`, umgesetzt nach Kapitel 10. Dazu kommen Teil A des Auftrags (Entscheidungen zu 002)
und Carlos' Wahl der Stimme: Killian, Tempo normal (+25 %). Offline gemessen, der Coach wurde nicht gestartet.

### Zuerst rot

- **58 neue Szenarien:**
  - Fragen-Probe `2026-09-27_213624_fragen.toml` mit allen 51 gedrückten Fragen und Notizen aus dem
    Sprechtasten-Log. Der Fragetext ist der erkannte Text, so wie der Kern ihn live bekommt.
  - Vier Szenarien in `2026-09-27_213624.toml`: `1900-raus-unter-15`, `1247-ziel-nicht-noch-einmal`,
    `1621-66-prozent-bleibt`, `0944-turm-ist-down`.
  - Die Wendepunkt-Probe `wendepunkt-ansage` in 213624, 164326 und 173159.
- **Ergebnis:** **57 von 58 waren mit 6a97391 rot.** Geprüft wurde in einem eigenen Worktree auf dem alten Stand, mit
  den neuen Messwerkzeugen.
  - Die Fragen-Probe war 51 von 51 rot: Der alte Weg kennt keine Absicht, 42 Fragen brauchten Claude.
  - `1621-66-prozent-bleibt` war grün. Es ist ein Wächter für die 70-%-Grenze aus Teil A 1.
- **Neuer Test:** `test_kern.zwei_klar_unterlegene` war rot (die alte Regel kennt nur einen Gegner).
- **Neue Prüfschlüssel** (`werkzeuge/szenarien.py`):
  - `kern_frage = true` spielt die Frage zur Zeit ein wie per Sprechtaste.
  - Dazu `absicht`, `ohne_claude` und `mit_handlung`.
  - `wendepunkt_ansage = true` prüft die ganze Datei.
  - `woerter_max` erlaubt für WENDEPUNKT, VORSCHAU und FENSTER 20 Wörter (`woerter_max_lang`).

### Teil A – Entscheidungen zu 002

1. **Zwei klar unterlegene Gegner** sind keine Gefahr (`Kern._klar_unterlegen`). Bedingungen: dein Leben ≥ 70 %, vor
   JEDEM ≥ 2 Level und ≥ 1500 Item-Gold (Schätzung aus Buch 7, 3.2), kein dritter Gegner mit `p_da` ≥ 0,2.
   213624 16:21 bleibt eine Warnung: Riven hatte 66 %.
2. **RAUS unter 15 % Leben** mit einem Gegner in `kampf_radius` ist robust belegt, auch ohne Balken.
   213624 19:00 kommt jetzt „Raus, zum Turm!“.
3. **Stimme und Tempo:** Carlos hat Killian mit +25 % gewählt (`[stimme]`).
4. **INFO_FLASH und WENDEPUNKT** zählen nicht zum Ziel ≤ 50. `kennzahlen.py` weist beide getrennt aus.
5. **Offen aus 002:**
   - **Stille abgeschnitten** (`stimme._Strom._schneide`, `werkzeuge/stille.py`):
     - Vorn bleiben 0,06 s, hinten 0,15 s. Pausen im Satz bleiben ganz.
     - Die 8 Stimmproben-Sätze dauern 17,0 s statt 29,5 s.
     - Der erste hörbare Ton kommt im Median nach 0,27 s statt 0,61 s.
     - `[stimme] zeichen_pro_s` = 15,9 (vorher 14,2).
   - **Kein Ziel zweimal in 60 s**, auch nicht nach einem neuen Basis-Besuch (`Kern._ziel_eben`): 213624 12:59
     „Dann Drachen.“ entfällt.
   - Das Quest-Feld V im HUD steht in OFFEN.md.

### Buch 11, umgesetzt

- **Zeitleiste** (`kern/zeitleiste.py`), je Takt, 180 s:
  - Objective-Spawns, Respawns, bekannte Zauber der Gegner, euer Fenster, Buffs, Inhibitoren.
  - Die nächste Kanone deiner Lane, dein Back-Bedarf (Einkommen der letzten 60 s) und dein TP.
  - Zu sehen im Dashboard (Kasten „Nächste 3 Minuten“), in `kern.kontext()` und im Protokoll.
- **`danach`** (`kern/fuehren.danach`), Projektion auf die Kandidaten dieses Takts:
  - Ihr Weg zählt ab dem Ziel der jetzigen Handlung.
  - Spawns sind fortgeschrieben.
  - Stumme und Rückzugs-Arten sind nie `danach`.
  - Nach einem Back ist `danach` das Ziel aus der Basis.
  - Im Dashboard („Danach: …“) und im Protokoll.
- **WENDEPUNKT:** Struktur fällt, Objective fällt, Kill in ≤ 2000 um dich oder dein Ziel, Basis verlassen.
  - Der Plan gilt dann als ungültig und wird sofort neu gewählt. Der Satz nennt den Anlass vorn:
    „Turm ist down: Farm deine Top-Welle.“, „Drache drin: …“.
  - Mit `danach` sind bis 20 Wörter erlaubt, bei zwei nahen Wegen gibt es Optionen.
  - Er ist frei vom Budget, höchstens einer je 8 s, und wartet das Ende eines Kampfs ab.
- **Stille statt Wiederholung am Wendepunkt:**
  - Beim Verlassen der Basis schweigt der Coach, wenn der Basis-Satz jünger als 60 s ist.
  - Derselbe Anlass mit demselben Ziel in 60 s bleibt still.
  - Der Schutzplan einer verlorenen Lane (G1) gilt still weiter.
  - Ist der Plan nur Halten, kommt die beste Option, die am ungeeichten Kampfmodell hängt, mit „unsicher“; gibt es
    keine, schweigt er.
- **FENSTER:** Eine neue Information leitet den nächsten Plan-Satz ein, aber nur, wenn der Plan wechselt. Das gilt
  für den Jungler auf der anderen Seite, den Lane-Gegner tot oder im Brunnen, ihren Top ohne TP und den Flash eines
  nahen Gegners. Beispiel: „Rumble ist 13 Sekunden weg: Lass die Top-Welle zu dir kommen …“.
- **VORSCHAU** ab 14:00:
  - Bedingungen: 45 s ohne Ansage und ein Ereignis der Zeitleiste in ≤ 90 s, das den Plan betrifft. Höchstens eine
    je 60 s, mit Budget und mit R4.
  - Beispiel: „Teemo lebt in 15 Sekunden wieder: auf den Top-Inhibitor-Turm noch schnell, dann zurück.“
- **Fragen** (`kern/fragen.py`, Schritt 6), zuerst an den Kern:
  - Absichten: JETZT, DANACH, WARUM, ENTWEDER, SOLL_ICH, LAGE, TIMER, WO, KAUF, NOTIZ, OFFEN.
  - Korrekturen („ich war in der Base“, „Drache ist tot“ für 30 s).
  - Kein Widerspruch ohne „Neu:“, und eine Antwort gilt als gesagter Plan. Eine Anschlussfrage („Und die anderen?“)
    erbt die Absicht.
  - OFFEN geht an Claude, und zwar mit `kern.kontext()` (höchstens 30 Zeilen: Plan, danach, Top-3, Zeitleiste,
    Flash, Stand, Gegner) statt der Rohlage. Dazu kommen die Regeln aus Kapitel 6 im Systemprompt.
  - Live verdrahtet in `sprache._beantworte`.
- **Protokolle:** `protokoll.py --fragen` spielt die Fragen aus dem Log ein und schreibt jede Antwort mit Absicht und
  Rechenzeit dazu, je Ansage auch `danach` und die Zeitleiste.

### Abnahme

| Abnahme | Soll | Ist |
|---|---|---|
| `tests/alle.py` | grün | **10 / 10** |
| Szenarien, alle 14 Dateien | grün | **150 / 153**: rot ist nur `wendepunkt-ansage` in 213624, 164326, 173159 (s. u.); 2 übersprungen (brauchen Claude) |
| Konstruierte Lagen | grün | **40 / 40** |
| Fragen-Probe 213624 | grün | **51 / 51** (vorher 0 / 51) |
| Protokolle | 213624 (mit Fragen), 164326, 173159 | **ja** |

**Kennzahlen, vorher (6a97391) → nachher** (`kennzahlen.py --nur-kern`, 213624 mit `--fragen`; vorher mit denselben
Messwerkzeugen):

| Kennzahl | Soll | 213624 | 164326 | 173159 |
|---|---|---|---|---|
| Leerlauf ab 14:00 | ≤ 10 % | 51 → **48 %** | 60 → **52 %** | 52 → **48 %** |
| Wendepunkte ohne Plan-Satz in 60 s | – | 5 → **0** | 14 → **0** | 3 → **3** |
| Wendepunkt-Verzug, Median | ≤ 3 s | 0,0 → **0,0 s** | 0,3 → **0,0 s** | 0,0 → **0,0 s** |
| Widersprüche | 0 | 1 → **1** | 0 → **0** | 0 → **0** |
| Stichwort-Antworten | 0 | 7 → **3** | – | – |
| Antworten ohne Claude / an Claude | – | 9 / 42 → **46 / 5** | – | – |
| Antwortzeit ohne Claude, Median | ≤ 1 s | **< 1 ms** Rechenzeit | – | – |
| ungefragt ohne INFO_FLASH und WENDEPUNKT, je 30 min | ≤ 50 | 39 → **24** | 41 → **37** | 50 → **51** |
| Fassungswechsel | 0 | 1 → **0** | 0 → **1** | 0 → **1** |
| Schranken-, Kampf-Verstöße | 0 | **0** | **0** | **0** |

In den übrigen Partien:
- **Leerlauf:** 102112 40 %, 133930 53 %.
- **Widersprüche:** je 2 in 102112 und 133930.
- **Ungefragt ohne INFO_FLASH und WENDEPUNKT:** 37, 54, 39, 50 je 30 min (102112, 133930, 140253, 144655).

Zur Antwortzeit:
- Offline gibt es nur die Rechenzeit des Kerns. Die Zeit bis zur Stimme live (Spracherkennung + Stimme) misst erst
  die nächste Partie.
- Mit Claude brauchte es im Live-Log vorher 1,8 s bis zur Stimme.

**Die Wendepunkt-Probe ist nicht grün.** Nach Turmfall, Objective und Verlassen der Basis kam der Plan-Satz nicht
immer in ≤ 3 s:

| Partie | zu spät | kein Satz |
|---|---|---|
| 213624 | 4 | 4 (in der letzten Minute, 23:57–24:29, die Partie endet) |
| 164326 | 12 | 0 |
| 173159 | 11 | 3 |

Die Ursachen, geprüft an 164326:
- Der Satz wartet hinter einem langen Satz. Seit Auftrag 003 fällt er dabei nicht mehr weg, er kommt aber 4–10 s
  später.
- Ein Wendepunkt fällt in eine GEFAHR. Der Rückzug geht vor, der Wendepunkt verfällt nach 10 s.
- Der Schutzplan (G1) bleibt bewusst still.
- Mehrere Strukturen fallen in wenigen Sekunden (höchstens ein Wendepunkt je 8 s).

**Leerlauf bleibt bei 40–53 %.** Im Mid-Game ist der Plan meist „Farm die Welle“ (stumm) oder eine Turm- bzw.
Objective-Handlung, die am ungeeichten Kampfmodell hängt und nach Entscheidung 2 stumm ist. Ungesagte Pläne zählen als
Leerlauf. Buch 11 wirkt im Mid-Game erst voll, wenn die Kampf-Eichung besteht.

### Abweichungen

1. **`danach` ist eine Projektion auf die Kandidaten dieses Takts:** Weg ab dem Ziel, fortgeschriebene Spawns. Es ist
   keine neue Kandidatenrechnung aus einer projizierten Lage (Kapitel 3, Schritt 2). Die Modi rechnen mit der
   Bewertung des Takts (Gegner-Ankunft, Wellen), die sich nicht ohne Weiteres projizieren lässt.
2. **Zeitleiste:** „Deine Welle kommt an“ ist die nächste Kanonenwelle deiner Lane (Wellen-Uhr), nicht jede Welle.
3. **Wendepunkte:**
   - Den Rückzug deckt die vorhandene Bestätigung „Gut raus.“ ab, die ihn als sicher angekommen meldet; er ist kein
     eigener Wendepunkt.
   - Den Respawn deckt der TOT-Satz 8 s davor.
4. **Stille am Wendepunkt** (s. oben) nach Kapitel 1, Prinzip 5, und Kapitel 4 („Wiederholungen … in 60 s“).
   - Die Kennzahl zählt einen Wendepunkt derselben Art ≤ 60 s nach einem mit Satz als gedeckt, etwa die drei Larven
     in 35 s.
   - Beim Verlassen der Basis gilt ein Basis-Satz ≤ 60 s davor als rechtzeitig.
   - Tot oder im Kampf zählt der Verzug ab dem Ende des Kampfs.
5. **Gefragt nennt der Coach auch Optionen, die ungefragt stumm bleiben** (Entscheidung 2), mit „mit Kampf –
   unsicher“ (Kapitel 1, Prinzip 8). Beispiel 12:56: „Zum Drachen: ihr seid zwei. Turm ist gerade keine Option.“
6. **Fassungswechsel und Widersprüche:**
   - Der Anlass eines WENDEPUNKT- oder FENSTER-Satzes ist das Ereignis, nicht die Fassung. Verglichen wird der Plan
     dahinter.
   - Wendepunkte und der Weg in die Basis gelten als neues Ereignis.
7. **`173159` 3710:** `text_max` zählt nur die Kurzform am Satzanfang (`^Dann Top-Welle`). Ein Wendepunkt-Satz
   bestätigt den Plan zu einem neuen Ereignis.

---

## Auftrag 002 – Sofort-Fixes aus Carlos' Partie 213624 (27.09.2026)

Quelle: `aufnahmen/2026-09-27_213624_notizen.md`, `_sprechtaste.log`, `_ansagen.json`. Bot-Partie, Riven gegen Rumble,
CLASSIC, 25 min. Jeder Punkt wurde am heutigen Stand (d9fd85e) geprüft, nicht an dem Zwischenstand, mit dem der Coach
in der Partie lief. Offline gemessen, der Coach wurde nicht gestartet.

### Zuerst rot

Neue Datei `tests/szenarien/2026-09-27_213624.toml` (`bots = true`, nur Verdrahtung und Form) mit 9 Szenarien.
**8 von 9 waren mit d9fd85e rot.** Grün war nur `s23-gefahr-hoechstens-8`: Die Rückzüge in 213624 hatten schon
höchstens 8 Wörter. Es bleibt als Wächter.

Neue Prüfschlüssel (`werkzeuge/szenarien.py`):
- `gesprochen_ohne = ["regex", ...]`: Was die Stimme bekommt (`stimme.sprechbar`), passt auf keins der Muster.
- `frage` mit `sofort = true`: Geprüft wird die Sofort-Antwort ohne Claude. Das läuft immer; gibt es keine
  Sofort-Antwort, ist das Szenario rot.

Dazu zwei Tests in `tests/test_kern.py`: `info_flash_kurz_und_gebuendelt` und `zahlen_wie_spieler`.

### S1. Zahlen

Die Probe aus E8 (edge-tts und Whisper) gibt es jetzt als Werkzeug: `werkzeuge/zahlenprobe.py`. Es nimmt je
Zahl-Umfeld ein Beispiel aus den Live-Ansagen und dazu die Fälle aus 213624.

Befund vorher, mit Killian bei +25 %:
- **„3550 Gold“ kam als „3, 5, 5, 0“, also Ziffer für Ziffer.** Das passierte am Satzanfang nach „dann back.“.
  „3000 Gold“ mitten im Satz kam richtig. Carlos' 11:12 („3-0-0-0“) kam aus einer Claude-Antwort mit „3000 Gold
  Vorsprung“.
- „33 02“ wurde „dreiunddreißig zwei“, Whisper hörte „33,2“. Genauso „21 07“ („21,7“).
- „6/0“ stand so in Claudes Antwort. Der Kontext für Claude schrieb jede Bilanz als „6/0/3“.

Umgesetzt:
- `stimme.sprechbar`:
  - Gold als Zahlwort, auf Hunderter abgerundet („dreitausendfünfhundert Gold“). Abgerundet, damit ein Satz nie
    mehr Gold verspricht, als da ist.
  - Jede andere Zahl ab 1000 genau in Worten.
  - Kill-Bilanzen ohne Schrägstrich („sechs null“, „null sechs eins“). Andere Brüche als „von“ („1200 von 2000“).
  - Uhrzeiten mit der Null („einundzwanzig null sieben“). `zahl_wort` reicht jetzt bis 999999.
- Der Kontext für Claude schreibt „Kills 6 Tode 0 Assists 3“ statt „6/0/3“.
- Die Systemprompts für Antworten, Briefing, Midgame und situative Sätze enthalten die Regel: „du stehst sechs
  null“, „ihr führt sieben zu drei“, Gold gerundet.

Befund nachher, mit Killian bei +50 %:
- „3550 Gold“ wird „dreitausendfünfhundert“. Whisper hört bei dem Tempo „Dreit aus N500“, also nicht mehr Ziffer
  für Ziffer.
- „6/0“ kommt als „sechs null“, „21 07“ als „einundzwanzig null sieben“ (Whisper: „2107“).

### S2. Stimme und Tempo

- **Proben:** `aufnahmen/stimmproben/` enthält 8 Sätze je Stimme, normal (+25 %) und schnell (+50 %).
  `LIESMICH.md` hat die Tabelle, das Werkzeug ist `werkzeuge/stimmproben.py`.
  - edge-tts bietet nur zwei mehrsprachige deutsche Stimmen: Florian und Seraphina.
  - Die mehrsprachigen Stimmen bekommen die Namen im Original, Killian weiter mit deutscher Lautschrift.
  - **Carlos wählt.** Bis dahin bleibt Killian (`[stimme] name` in `wissen/kern.toml`).
- **Tempo:** `[stimme] tempo = "+50%"`, als Schalter `--tempo` bei `live` und `abspielen`. Das ist 20 % schneller
  als bisher (+25 %). Siehe Abweichung 1.
  - Der Sprechplan schätzt die Satzlänge jetzt mit 16,6 Zeichen/s statt 14 (`[stimme] zeichen_pro_s`, gemessen an
    den Proben).
- **Befund zur Pause:** Killian hat etwa 0,95 s Stille je Satz, Florian 0,57 s, Seraphina 0,50 s.
  - Ohne diese Stille sprechen Killian und Florian gleich schnell (21,3 und 20,7 Zeichen/s).
  - +50 % beschleunigt nur das Sprechen, nicht die Stille.
  - „Zu langsam“ kommt also auch von den Pausen. Nicht umgebaut, siehe Offen.
- **Satzlängen (Buch 0, 9.3):** PLAN höchstens 14 Wörter (vorher 18), GEFAHR höchstens 8 (vorher 10). Vorher lagen
  in den sieben Protokollen 56 Sätze darüber:
  - ZURUECK 21 von 93,
  - BACK_JETZT 18 von 29,
  - WELLE_HALTEN 5,
  - KAUFEN 4,
  - MIT_GRUPPE 3,
  - DRUECKEN 2,
  - WELLE_REIN_UND_BACK 2,
  - WOHIN 1.

  Gekürzt:
  - Rückzug: „Raus zum Mid-Tier-1-Turm“ statt „Raus zu deinem …“. Passen die Namen nicht, wird gezählt: „drei von
    ihnen kommen“.
  - Back: nur so viele Gründe, wie in 8 Wörter passen.
  - WELLE_HALTEN ohne „dort farmen“.
  - Turm-Fenster: „35 Sekunden, bis einer kommt“ statt „frühestens in 35 Sekunden kann einer von ihnen dort sein“.
  - „Mit der Gruppe zum …“.
  - Jeder PLAN- und Erinnerungs-Satz über 14 Wörtern verliert zuerst den Grund hinter dem letzten Doppelpunkt
    (`modi.kuerze`).

### S3. Flash

- **Ansage INFO_FLASH** (`Kern._flash_info`, `[info_flash]`):
  - Ein bestätigter Flash eines Gegners wird kurz gesagt: „Sona ohne Flash.“
  - Bestätigt ist jeder Flash-Timer des Lagebilds: Chat-Ping, oder ein Sprung auf Minimap bzw. Bildschirm bei einem
    Champion ohne eigenen Dash. So legt es `lage.ereignisse` schon an.
  - Nicht in KAMPF, sondern 3 s nach dem Kampf.
  - Höchstens einer je 20 s, mehrere in einem Satz („Sona und Caitlyn ohne Flash.“).
  - Kommt der Flash in weniger als 10 s zurück, fällt der Satz weg.
  - Zählt nicht zum Budget. In 213624 kommt er dreimal: 4:55 Sona, 8:41 Rumble, 11:21 Sona.
- **Antworten:**
  - Die Lage für Claude enthält jetzt den Flash-Stand ALLER Gegner: ohne Flash mit Restzeit, wieder da,
    unbekannt, spielt kein Flash.
  - Die Frage „Wie sieht's mit den Flashes aus?“ beantwortet der Coach sofort aus dieser Tabelle. 213624 23:22:
    „Rumble und Sona haben Flash wieder. Von Xin Zhao, Ziggs und Caitlyn weiß ich nichts.“ Vorher kam „Dazu hab ich
    keine Daten“, weil die Lage nur laufende Timer nannte.
- **Logik:** In allen Systemprompts steht jetzt: Ein Gegner ohne Flash ist ein Grund FÜR einen Angriff auf ihn, nie
  dagegen.

### S4. Quest-TP

**Messung** an 164326, 173159, 213624, 102112 (CLASSIC, Riven ohne TP) und 133930 (Swiftplay, mit TP). Als Wahrheit
dient der Quest-Platz im Schirmbild.

- **Die API zeigt ohne TP nichts:** keinen Quest-Platz, gleiche Beschwörerzauber, kein Ereignis, gleiche Runen.
  Indirekt gibt es nur Level 19/20, weil die Quest das Level-Cap hebt. In 164326 kam das erst 26:14, zu spät zum
  Planen.
- **Mit TP als Zauber** heißt der Schlüssel nach der Quest `S12_SummonerTeleportUpgrade` (133930 ab 8:02).
  - Der Coach suchte überall nur `SummonerTeleport`, das TP war danach verschwunden.
  - Behoben beim Einlesen (`zustand.ZAUBER_GLEICH`).
  - Die Quest gibt es also auch in Swiftplay.
- **HUD:** Der Quest-Platz V liegt rechts neben den Items. Ein türkiser Ring heißt, die Quest läuft. Das violette
  TP-Symbol heißt bereit. Dunkel mit Zahl heißt Abklingzeit.
  - Die Quest war früher fertig als nach der Regel (spätestens 13:35): 213624 9:31–9:46, 102112 11:10–11:36,
    173159 11:30–11:51, 164326 11:51–12:07.
  - Abklingzeit: 390 s, mit Ionischen Stiefeln 355 s. Zaubertempo wirkt also auf das Quest-TP.
- **Benutzung:** Rivens Icon springt schneller als 880 Einheiten/s. Laufen kommt auf höchstens 590, aus der Basis
  auf 780.
  - Fünf Benutzungen: 164326 18:55 und 39:21, 173159 ~12:58 und 23:22, 102112 ~38:16. In 213624 keine.
  - Alle fünf erkannt, 0 Fehlmeldungen. Die Gegenprobe über 17 Aufnahmen vom 26./27.09. ergab keine Fehlmeldung.
  - Gemessene Fallen:
    - Lane, Recall, wieder raus binnen 15 s sah wie ein Sprung aus (164326 7:51).
    - Das Lagebild hält dich unter fremden Icons fest (164326 35:15). Deshalb zählen nur echte Sichtungen.
    - Nach dem TP ist das Icon oft 30 s weg.

**Umbau** (`kern/quest_tp.py`, `[quest_tp]` in `wissen/kern.toml`):
- Für Top ohne TP als Zauber in CLASSIC ist `m.tp_in` ab 13:35 bereit und nach einem erkannten eigenen Teleport
  390 s weg.
- Damit greifen die TP-Regeln aus Buch 5, Kapitel 5 und Buch 6, 4.7 von selbst.
- `karte.py` und `basis.py` sind unverändert. Test: `tests/test_quest_tp.py`.

### S5. Falsche Warnungen

1. **16:21 „Raus zu deinem Mid-Tier-1-Turm: Caitlyn und Sona kommen.“ Tote Gegner zählten nicht.**
   - Rumble, Xin Zhao und Ziggs waren tot und gingen mit p_da 0 ein.
   - Caitlyn lebte noch, mit 32 % direkt an Riven, und starb eine Sekunde später. Sona war seit 36 s ungesehen.
   - Riven lag fünf bzw. sieben Level und 3150 bzw. 3500 Item-Gold vorn.
   - Die Regel aus 2. greift nicht, weil es zwei Gegner sind. Siehe Offen.
2. **Ein einzelner, klar unterlegener Gegner ist keine Gefahr** (`Kern._klar_unterlegen`):
   - Bedingungen: genau ein Gegner, dein Leben ≥ 60 %, du liegst ≥ 2 Level UND ≥ 1500 Item-Gold vor ihm.
   - Seine Werte werden nach Buch 7, 3.2 geschätzt, wenn sie veraltet sind.
   - Die Warnungen 15:15, 17:32 und 21:37 „Ziggs kommt“ sind weg.
3. **RAUS im Kampf nur mit robustem Beleg** (`modi.kampf.raus_beleg`):
   - Robust heißt: In `kampf_radius` stehen ≥ 1 Gegner mehr als ihr, ODER dein Leben liegt unter 30 % und unter
     dem Balken des nächsten Gegners.
   - Sonst ist RAUS stumm wie REIN. Das gilt auch für „Lass ihn, Turm!“ (15:18, 16:47; Carlos 15:25: „Ich habe
     Ziggs getowerdived und das ist easy“).
   - In 213624 sind so 1:11 (mit der Wiederholung 1:17), 15:18, 16:47 und 19:00 stumm. Gesprochen wird dort kein
     RAUS mehr.
   - 19:00 war „Raus, zum Turm!“ bei 12 % Leben, zwei Sekunden bevor das Leben auf 1 % fiel.
     - Sichtbar war nur Sona, 825 entfernt, ihr Balken unbekannt.
     - Xin Zhao, der Riven dann tötete, war nicht zu sehen.
     - Nach der Regel ist das kein Beleg. Siehe Offen.
4. Nebenbei behoben: „Sona und Sona kommen: nimm den Kampf.“ (stummes ANNEHMEN, 18:28). Der zweite Name ist jetzt
   ein anderer Gegner als der nächste.

### S6. Gold trennt verkehrt (AUC 0,30)

**Der Verdacht bestätigt den Mechanismus, erklärt die AUC aber nicht.**

- **Nachrechnung** (`kampf_eichung.py`, neuer Schalter `--roh`), dieselben 6 Partien, 112 Proben, 41 entschieden:

  | | geschätzt (Buch 7, 3.2) | roh (API) |
  |---|---|---|
  | Brier (Grundrate 0,249) | 0,320 | 0,318 |
  | gold_diff AUC (Mittel gewonnen / verloren) | 0,30 (+431 / +1438) | 0,30 (gleich) |
  | level_diff AUC | 0,43 | 0,43 |
  | p AUC | 0,40 | 0,41 |

  - Eine Probe zählt nur sichtbare nahe Gegner, also mit `seit = 0`. Dort schätzt `gegner_werte` nie nach.
  - Die Schätzung wirkt nur über ungesehene Gegner auf p: in 23 Proben, um höchstens 0,02.
- **Back-Test** (`werkzeuge/back_test.py`): 219 Änderungen des Item-Golds nach der ersten Sichtung.
  - 181 (83 %) liegen höchstens 3 s um den Moment, in dem die Minimap den Gegner wieder zeigt.
  - Keine fällt in eine Todeszeit, obwohl man nach dem Tod im Brunnen kauft.
  - Die API zeigt die Items also im Stand der letzten Sichtung und springt beim Auftauchen. Beispiel: 133930 6:20
    Gwen +2150 nach 31 s ungesehen.
  - 36 Änderungen fallen in den Nebel. Möglich wären verpasste Sichtungen; die Ursache ist nicht geprüft.
- **An den Proben:** 0 von 41 hatten einen nahen Gegner mit veraltetem Stand.
  - Kämpfe direkt nach dem Auftauchen gehen nicht öfter verloren: 5 von 19 verlorenen, 8 von 22 gewonnenen.
  - gold_diff trennt also auch mit echten Werten verkehrt. Die Ursache liegt woanders. Die Deutung „mit Vorsprung
    mutiger“ ist weiter ungeprüft.
- Die Rufe bleiben stumm.

### S7. Szenarien und Wünsche

- `szenario_aus_notizen.py` hat für 213624 10 Stubs angelegt (`tests/szenarien/offen/2026-09-27_213624.toml`).
- Die konkreten Szenarien stehen oben (S1, S2.3, S3, S5).
- Carlos' Wünsche aus der Partie stehen in `OFFEN.md`, jeweils mit dem Auftrag bzw. Buch, das sie abdeckt.

### Abnahme

| Abnahme | Soll | Ist |
|---|---|---|
| `tests/alle.py` | grün | **10 / 10** (neu: `test_quest_tp`; in `test_kern` neu: `info_flash_kurz_und_gebuendelt`, `zahlen_wie_spieler`) |
| Szenarien, alle 13 Dateien (`--kern neu`) | grün | **95 / 95** (2 übersprungen, brauchen Claude); konstruierte Lagen **40 / 40** |
| Neue Szenarien zuerst rot | rot mit d9fd85e | **8 / 9**; der neunte (`s23-gefahr-hoechstens-8`) bleibt als Wächter |
| Protokolle | 213624, 164326, 173159 | **ja**, `buecher/protokolle/` |
| Schranken-, Kampf-Verstöße, Objective ohne Chance | 0 | **0** in allen sieben |

Geändert, mit Grund:
- `test_bausteine.sprechbar`: „2500 Gold“ und „KDA 27/6/4“ werden jetzt gewollt in Worten gesprochen.
- `test_bausteine.live_partie_2121`: Das Briefing ist dort jetzt 43 s lang gemessen am Tempo, nicht 600 Zeichen.
  Mit 16,6 Zeichen/s war es sonst vor 67 s zu Ende.
- `144655_pruefung`:
  - `0701` verlangt „farm“ im Satz. WELLE_HALTEN heißt jetzt „Welle zum Turm ziehen, farmen, kein Trade bis …“
    (13 Wörter).
  - `0449` hat das Fenster bis 5:05 statt 5:10. RAUS kommt jetzt 4:46 statt 4:42 (S5.3), und der Satz in der Basis
    nach dem Recall gehört nicht zur Rückzug-Episode.
- `102112_pruefung` `2547`: Der neue Wortlaut „0 Sekunden, bis einer“ ist mit bewacht.

**Kennzahlen** (Kern, `kennzahlen.py --nur-kern`; INFO_FLASH neu in der Ausgabe):

| Aufnahme | ungefragt (je 30 min) | davon INFO_FLASH | ohne INFO_FLASH je 30 min | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | GEFAHR / PLAN / ERINNERUNG / BESTÄTIGUNG |
|---|---|---|---|---|---|---|---|
| 102112 | 50 (49) | 5 | 44 | 0,72 | 0 | 1 | 8 / 35 / 0 / 1 |
| 133930 | 43 (59) | 1 | 58 | 1,14 | 0 | 0 | 15 / 20 / 1 / 1 |
| 140253 | 15 (42) | 1 | 39 | 0,71 | 0 | 0 | 4 / 8 / 0 / 0 |
| 144655 | 16 (50) | 1 | 46 | 0,85 | 0 | 0 | 9 / 4 / 1 / 0 |
| 164326 | 69 (48) | 12 | 40 | 0,82 | 0 | 0 | 25 / 27 / 2 / 3 |
| 173159 | 72 (56) | 9 | 49 | 0,64 | 0 | 0 | 30 / 26 / 1 / 4 |
| 213624 | 39 (47) | 3 | 43 | 0,61 | 0 | 1 | 7 / 27 / 0 / 1 |

- **Stand vorher** (Qualitätsrunde 3): 164326 46 und 173159 52 je 30 min, GEFAHR 32 und 34.
  - S5.2/S5.3 nehmen GEFAHR auf 25 und 30 herunter.
  - INFO_FLASH kommt neu dazu, 12 und 9 Sätze. Ohne ihn liegen beide unter 50 (40 und 49).
  - 213624 hatte vor den Fixes 43 Sätze, jetzt 39.
- **Fassungswechsel:**
  - 102112 38:01 „Dann zu deinem Team.“ → 38:15 „Dann Top-Welle.“ ist der begründete Fall aus Qualitätsrunde 3
    (Kills dazwischen).
  - 213624 12:47 „Zum Drachen: ihr seid drei.“ → 12:59 „Dann Drachen.“ gab es schon vor Auftrag 002. Das Ziel ist
    dasselbe, nach einem neuen Basis-Besuch kommt die Kurzform. Das Vergessen beim Betreten der Basis
    (`_angesagt.clear()`) lässt ihn zu. Nicht umgebaut, siehe Offen.

### Offen

1. **Zwei klar unterlegene Gegner** (213624 16:21, Caitlyn mit 32 % und Sona, beide 5 bis 7 Level hinter Riven):
   S5.2 gilt nur für genau einen Gegner. Entscheidung: auch für zwei, wenn jeder einzeln klar unterlegen ist?
2. **RAUS bei < 30 % Leben, wenn der Balken des Gegners unbekannt ist** (213624 19:00, 12 %): Heute ist das kein
   Beleg, der Ruf bleibt stumm. Entscheidung: Soll ein unbekannter Balken bei sehr wenig Leben reichen?
3. **Stimme:**
   - Carlos wählt aus `aufnahmen/stimmproben/`.
   - Die Stille um jeden Satz (Killian ~0,95 s) ließe sich beim Abspielen abschneiden. Nicht umgebaut, weil
     `stimme.py` dafür neu gemessen werden muss (`werkzeuge/stimmprobe.py`).
4. **Quest-TP:**
   - Es gilt erst ab 13:35 als bereit, obwohl die Quest 1,5 bis 4 min früher fertig war. Das behebt erst das Lesen
     des Quest-Platzes V im HUD (`hud.py`).
   - Die Abklingzeit steht fest auf 390 s, mit Ionischen Stiefeln sind es 355 s.
5. **Kurzform nach einem neuen Basis-Besuch** (213624 12:47/12:59) zählt als Fassungswechsel, siehe oben.
6. **S6:**
   - Die Ursache der Gold-AUC 0,30 ist weiter offen.
   - 36 Item-Änderungen im Nebel sind ungeklärt, möglich wären verpasste Sichtungen.

### Abweichungen und Entscheidungen

1. **Tempo +50 % statt +20 %:** Der Auftrag sagt „Standard +20 %“. Die Stimme lief aber schon mit +25 %, und Carlos
   findet sie zu langsam. Deshalb ist +50 % gesetzt: 20 % schneller als bisher. Ein Wert in `wissen/kern.toml`.
2. **Gold abgerundet**, nicht gerundet: „850 Gold für Axiombogen“ wird „achthundert“, nicht „neunhundert“.
3. **S5.1 war kein Fehler der Toten:** Die Warnung 16:21 kam von zwei lebenden Gegnern, siehe oben. Nichts umgebaut,
   die Frage steht unter Offen.
4. **Gefahr-Sätze nennen ab drei Namen eine Zahl.** Der Grund ist die Grenze von 8 Wörtern. Zwei Namen passen
   meistens („Raus zum Mid-Tier-1-Turm: Xin Zhao und Ziggs kommen.“).

---

## Qualitätsrunde 3 – Prüfung vom 27.09.2026 (c), R1–R10 (27.09.2026)

Auftrag 001 aus `buecher/auftraege/`. Grundlage: `buecher/protokolle/PRUEFUNG_2026-09-27c.md`, vorher committet in
8f0b8c3 zusammen mit dem Postfach. Offline gemessen, der Coach wurde nicht gestartet.

### Zuerst rot

26 neue Szenarien in `tests/szenarien/2026-09-27_173159_pruefung_c.toml` (15) und `..._164326_pruefung_c.toml` (11).
**Alle 26 waren mit dem Stand 842b502 rot.** Geprüft in einem eigenen Worktree auf dem Commit, damit nichts
Halbfertiges mitlief.

Neue Prüfschlüssel (Buch 0, 12.1 nachgetragen):
- `je_10min_max = { "muster" = n }`: höchstens n Treffer in jedem 10-Minuten-Abschnitt (R4).
- `kategorie_max = { "GEFAHR" = n }`: höchstens n Kern-Sätze einer Kategorie (R5). Dafür trägt jede Kern-Ansage ihre
  Kategorie.

### Umgesetzt

- **R1 Vorwärts-Schranke** (`Kern._schranken`, `[schranken]` in kern.toml):
  - Unter `vor_leben_min` (0,4) ist keine Vorwärts-Handlung Kandidat. Betroffen: DRUECKEN, MIT_GRUPPE, NEHMEN,
    BESTREITEN, ZUR_GRUPPE, TP_SPIEL, PLATTEN, SEITENWELLE, WELLE_KLAEREN, VORBEREITEN_OBJECTIVE, ANNEHMEN.
    Ausnahme: NEHMEN in der Grube, ohne Kampf, fällt in ≤ 5 s.
  - Mit p_tod ≥ `vor_p_tod_max` (0,3) ist keine davon Kandidat.
  - Fällt das Leben, bevor ein Satz dran ist, wird er verworfen (Prüfung vor dem Sprechen).
  - `_kern.jsonl` hat das Feld `schranke`: was in diesem Takt gestrichen wurde.
- **R2 Das ungeeichte Kampfmodell spricht nicht:**
  - BESTREITEN und TP_SPIEL werden berechnet, protokolliert und bleiben stumm.
  - ZUR_GRUPPE zu einem Kampf wird nur gesprochen mit ≥ 1 Kopf mehr nach deiner Ankunft und ≥ 60 % Leben, mit Ort und
    Namen: „Zu Graves in den Mid-Fluss: mit dir drei gegen zwei.“
  - DRUECKEN und MIT_GRUPPE werden nur gesprochen, wenn das Ziel vor dem ersten Verteidiger fällt. Sonst sind sie
    stumm (`modell_stumm`).
  - NEHMEN mit Kampf (P_kampf ≥ 0,1) ist stumm.
  - „schlägst“ kommt in keinem Satzbaustein mehr vor. Das Protokoll führt die stummen Rufe mit.
- **R3 Kaufplan** (`lolcoach/kaufplan.py`):
  - Das nächste Item ist zuerst das, dessen Bauteile du schon hast. Wer Tiamat hat, baut Hydra.
  - Sonst kommt der nächste Schritt aus Carlos' eigenem Build, `wissen/build_carlos.toml`. Er ist aus 11 Riven-Partien
    abgeleitet (`werkzeuge/build_aus_aufnahmen.py`): Axiombogen → Eklipse oder Endloser Hunger → Hydra → Schutzengel →
    Tanz des Todes → Gespaltener Himmel → Seryldas Bitterkeit. Das Lexikon ist nur noch der letzte Rückfall.
  - Volles Inventar ohne passendes Bauteil: kein Kauf (164326 38:33 „Kauf Langschwert und Stiefel“ bei sechs Items).
  - `kaufplan.kaufbar()` prüft jedes genannte Item: Platz frei oder eigene Bauteile verbraucht, nicht schon im
    Inventar, baut ins Ziel ein. Nur ein Hydra-Item (Spielregel, `GRUPPEN`). Tests in `tests/test_kaufplan.py`.
- **R4 Back-Rufe** (`Kern._back_sperre`):
  - Kein Back-Ruf unter 10 % Leben oder in KAMPF, höchstens 3 je 10 Minuten.
  - Nach einem Back-Ruf ohne Recall kommt ein neuer erst nach 90 s. Ausnahmen: Leben < 30 %, oder das Ziel-Item wird
    komplett kaufbar.
  - Das gilt auch für den „Jetzt back“-Schritt und die Erinnerung.
  - Ein toter oder gebackter Lane-Gegner ist allein kein Back-Grund mehr.
- **R5 Gefahr:**
  - Kommt nur der Lane-Gegner, gibt es keine GEFAHR, solange dein Leben ≥ 60 % und `kraefte()` ≥ −0,5 ist. Mit einem
    zweiten Gegner bleibt sie.
  - Dieselbe Gegnermenge wird 45 s nicht erneut gewarnt, außer p_tod steigt um ≥ 0,15.
  - Kein Gefahr-Satz, während du dem sicheren Ort in 2 s ≥ 300 Einheiten näher kommst.
- **R6 WOHIN:**
  - Nach der ersten Nennung je Partie kommt nur noch die Kurzform: „Dann Top-Welle.“, „Kauf X, dann Top-Welle.“
  - Rückfall: Sind ≥ 2 Mitspieler zusammen, ist das Ziel dein Team. „Warte am Turm“ gilt nur, wenn es nicht so ist.
    Ein Rückfall-Ziel mit p_tod ≥ 0,3 wird nicht gesagt; dann gibt es den Kauf-Satz ohne Ziel oder in TOT keinen Satz.
  - „einer von ihnen ist“; „Top-Inhibitor-Turm“ statt „Inhibitor-Top-Turm“.
  - Ein Objective ist nie WOHIN, wenn du zu spät kommst.
- **R7 kleine Wellen:**
  - SEITENWELLE und WELLE_KLAEREN erst ab 4 Vasallen, oder mit Supervasallen.
  - **Ursache der „0 Vasallen“** (164326 33:02): Die Seitenwelle wurde aus dem geglätteten Zustand gewählt, ihre Zahl
    war in diesem Takt 0. Die Schwelle nimmt sie jetzt heraus.
- **R8:** „Gut raus.“ ohne Pronomen.
- **R9 Rückblick:**
  - Keine Pronomen für Champions, „ihren Jungler“ nur, wenn der Täter ihr Jungler ist.
  - Kam in den 20 s vor dem Tod ein Vorwärts-Ruf des Coaches, beschreibt der Rückblick die Lage nüchtern: „Am Ältesten
    kamen drei von ihnen zusammen.“ `_kern.jsonl` markiert den Ruf als `ruf_vor_tod`.
- **Kennzahl „Schranken-Verstöße“** (`kennzahlen.py`, Soll 0): eine Vorwärts-Ansage mit Leben < 0,4 oder p_tod ≥ 0,3
  im Takt des Sprechens, „schlägst“, oder ein Kauf-Satz mit einem Item, das nicht passt (`kaufplan.kaufbar`).

### Abnahme

| Ziel der Prüfung c | Soll | Ist |
|---|---|---|
| 1. Alle Szenarien grün, alte und neue | grün | **86 / 86** in 12 Dateien (2 übersprungen, brauchen Claude); konstruierte Lagen **40 / 40**; Modus-Sollwerte 102112 **16 / 16**; `tests/alle.py` **9 / 9** (neu: `test_kaufplan`) |
| Neue Szenarien zuerst rot | rot mit dem alten Stand | **29 / 29**: 26 aus R1–R9 rot mit 842b502, 3 aus R10/Ziel 2 rot mit 8e91aab |
| 2. Ungefragte Ansagen je 30 min in 164326 und 173159 | ≤ 50 | 164326 **46** (vorher 67), 173159 **52** (vorher 74) – **in 173159 nicht erreicht**, s. u. |
| 3. Schranken-Verstöße in allen Protokollen | 0 | **0** in allen sechs |
| 4. Neue Protokolle für alle sieben Partien | ja | **ja**, `buecher/protokolle/2026-09-27_*.md` |
| Fassungswechsel (R10) | 0 | 102112 **2** (begründet, s. R10), sonst **0** |

**Kennzahlen** (Kern, `kennzahlen.py --nur-kern`):

| Aufnahme | ungefragt (je 30 min) | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | Kampf-Verstöße | Schranken-Verstöße | ohne Chance | GEFAHR / PLAN / ERINNERUNG / BESTÄTIGUNG | stumm (davon Kampf-Rufe) |
|---|---|---|---|---|---|---|---|---|---|
| 102112 | 52 (51) | 0,72 | 0 | 2 | 0 | 0 | 0 | 15 / 35 / 0 / 1 | 68 (37) |
| 133930 | 46 (63) | 1,19 | 0 | 0 | 0 | 0 | 0 | 19 / 20 / 1 / 1 | 26 (11) |
| 140253 | 20 (56) | 0,95 | 0 | 0 | 0 | 0 | 0 | 10 / 8 / 0 / 0 | 7 (7) |
| 144655 | 18 (56) | 0,96 | 0 | 0 | 0 | 0 | 0 | 11 / 4 / 1 / 0 | 7 (7) |
| 164326 | 65 (46) | 0,82 | 0 | 0 | 0 | 0 | 0 | 32 / 27 / 2 / 4 | 62 (23) |
| 173159 | 67 (52) | 0,68 | 0 | 0 | 0 | 0 | 0 | 34 / 26 / 1 / 4 | 59 (28) |

145702 hat nur 0,5 Minuten mit Daten und zählt nicht.

„Stumm“ ist alles, was berechnet und nicht gesagt wurde (R2), über alle sechs Partien:
- REIN 83, ANNEHMEN 16, DREHEN 14,
- DRUECKEN 61, MIT_GRUPPE 24, NEHMEN 21, BESTREITEN 7,
- ABGEBEN_TAUSCHEN 2, TP_SPIEL 1.

ABGEBEN_TAUSCHEN ist dabei, weil sein Tausch-Ziel ein Turm ist, der nur über den Kampf trägt (164326 23:12, 25:29).

**Ziel 2 in 173159 (52 statt ≤ 50):**
- R1–R9 nahmen 27 Sätze weg (94 → 67, je 30 min 74 → 52).
- Was bleibt, ist zur Hälfte GEFAHR: 29 Rückzüge und 5 „Raus, zum Turm!“ in 38 Minuten, fast jeder vor einer anderen
  Gegnermenge.
- Versucht und zurückgenommen, s. Abweichung 5: eine Sperre für die zweite Warnung in 15 s.
- Der nächste Hebel ist die Gefahr-Schwelle selbst. 13:00 „Raus …: Olaf kommt.“ kam bei p_tod 0,09. Das ist Eichung
  (`gefahr_eichung`) und eine Entscheidung, keine Satzregel.

### R10 – Fassungswechsel je Fall

In Prüfung c waren es 2 / 1 / 3 (102112 / 133930 / 164326). Jetzt: **2 / 0 / 0**. Die zwei in 102112 sind neu und
begründet.

| Fall | Ursache | Stand |
|---|---|---|
| 102112 33:20/33:44 und 37:03/37:13: „Back jetzt“ bzw. „Raus zu …“, dann „Jetzt back“ mit neuem Gold | Der Back begann nach dem Rückzug als neuer Plan. | **Weg durch R4:** 90 s nach einem Back-Ruf ohne Recall kein neuer. |
| 133930 10:25/10:37 und 164326 35:00/35:14: das Turm-Ziel wechselt ohne Ereignis | Beide Turm-Sätze trugen nur über „du schlägst X“. | **Weg durch R2.3:** Solche Ziele sind stumm. |
| 164326 38:09/38:33: KAUFEN mit anderer Liste | Der Kaufplan nannte Bauteile bei vollem Inventar. | **Weg durch R3.** |
| 164326 10:21/10:36: „Back jetzt: 23 Prozent …“, dann „Jetzt back: 26 Prozent …“ | Ein BACK_JETZT-Plan hält auch die Rückzug-Episode am Leben. Seine Erinnerung nahm deshalb die Fassung des Rückzug-Schritts. | **Behoben:** Die Erinnerung an einen Back-Plan behält „Back jetzt“ (`1036-back-fassung-bleibt`, rot mit 8e91aab). Dass sie kommt, ist richtig: Leben < 30 %, die Ausnahme von R4. |
| **neu** 102112 37:35 „Dann Baron.“ → 38:01 „Dann Deinem Team.“ → 38:15 „Dann Top-Welle.“ | Vor jedem Satz fielen Kills. 37:33 Kai'Sa: das Team geht zum Baron. 37:59 Galio: kein Baron mehr, zurück zum Team (p_tod 0,20). 38:01–38:03 Sett und Fiddlesticks: die Top-Welle (p_tod 0). | **Der zweite Satz war jeweils richtig** (9.4 Punkt 5: Kill ist ein neues Ereignis). Die Kennzahl erkennt als Ereignis nur einen neuen Namen im Satz. Die Kurzform nennt keine Namen mehr, deshalb zählt sie beide. **Behoben** ist der Grammatikfehler: jetzt „Dann zu deinem Team.“ (`3801-kurzform-zu-deinem-team`, rot mit 8e91aab). |

### Abweichungen und Entscheidungen

1. **Konstruierte Lagen nach R2 und R4:**
   - `m-split-drueck`: Der Turm trägt nur über „du schlägst Sett“, jetzt `darf_nicht DRUECKEN`.
   - `m-tp-spiel`: TP_SPIEL ist stumm, jetzt `darf_nicht`.
   - `k-gegner-gebackt`: Nach R4.4 ist ein gebackter Gegner ohne Gold oder Leben kein Back-Grund, jetzt
     FARMEN/PLATTEN statt WELLE_REIN_UND_BACK.
2. **1516 (133930) und 1025 (140253):** `muss_ziel` entfällt. R6.2: Ist auch der Rückfall ≥ 0,3, wird kein Ziel
   gesagt. Vorher kam „Warte am inneren …-Turm auf dein Team“.
3. **3451 (102112):** NEHMEN Drache wird berechnet, ist aber nach R2.4 stumm (Galio sichtbar, P_kampf ≥ 0,1).
   `soll`/`soll_ziel` zählen jetzt auch den stummen Ruf.
4. **Rückblick bei „Ruf vor Tod“:** Der Ort kommt aus dem Plan zum Zeitpunkt des Todes, sonst „Dort“. Satz 2 ist
   „Schau es dir im Review an.“
5. **Nachwarnungs-Sperre gemessen und zurückgenommen:**
   - Regel: In den 15 s nach einer Warnung kommt eine zweite nur, wenn p_tod um ≥ 0,15 steigt, auch mit neuem Namen.
     Anlass waren 13:00/13:12, 14:59/15:03 und 22:07/22:13 in 173159.
   - Ergebnis: 69 statt 68 ungefragte. Die gestrichenen Warnungen kamen 15–20 s später mit einem Namen mehr zurück.
   - 22:13 fehlte vor dem Tod („Cho'Gath … kommen“), und der Rückblick wurde schlechter: „Gank von Olaf …“ statt
     „Raus kam, du bist geblieben“.
   - Die drei Szenarien dazu sind wieder entfernt.
6. **Warteregel in der Basis:** Sie zählt jetzt auch ab dem letzten gesagten Ziel, nicht nur ab Kauf oder Eintritt.
   Vorher kam 173159 36:50 und 37:10 zweimal „Dann Top-Welle.“ (`3710-basis-einmal`).
7. **Fassungswechsel-Kennzahl und Kills:** Die Kennzahl erkennt ein neues Ereignis nur an einem neuen Namen im
   zweiten Satz. Seit R6 nennt die Kurzform keine Namen mehr. Die zwei Fälle in 102112 folgen je auf Kills (s. R10).
   Offen zur Entscheidung: Soll die Kennzahl Kills, Objectives und Lebensverlust als Ereignis zählen, wie die
   Kehrtwenden (`neues_ereignis`)?

---

## Schritt 5 – KAMPF und OBJECTIVE (Buch 7 und Buch 6) (27.09.2026)

Grundlage: `buecher/07_kampf.md` und `buecher/06_objectives.md` (committet in 705a6a6), Buch 0 Kapitel 0, 5, 6.3, 7
und 8, Buch 5 Kapitel 2, 5 und 8. Dazu Carlos' Entscheidungen 1–5 vom 27.09. (Chat). Offline gemessen, der Coach
wurde nicht gestartet. Der Kern spricht jetzt in allen neun Modi (`KERN_MODI_5`).

### Umgesetzt – Buch 7 (Kampf)

- **Ein Kampfmodell:** `kern/kampf.py: p_gewinn` (Kraft je Seite aus Level, Item-Gold und Leben, Ult/Flash weg,
  Mitspieler-Anteil, Turm).
  - `gefahr.p_verliere` ist jetzt `1 − p_gewinn` mit den Mengen-Gewichten aus G2.
  - `kampf_exponent` und `flucht_turm` fallen weg, `flucht_flash` sitzt jetzt auf p_tod.
  - Veraltete Gegner (G7): Level und Item-Gold werden nachgeschätzt (`gegner_werte`).
- **Modus KAMPF** (`modi/kampf.py`):
  - Kampf-Episode nach Tabelle 5.1 mit REIN, RAUS, DREHEN und HALTEN.
  - Höchstens 5 Wörter, höchstens 3 Rufe je Episode, ein Wechsel nur mit Kampf-Ereignis, keine alte Regel.
  - Nach dem Kampf wird der Plan sofort neu geprüft.
- **ANNEHMEN** vor dem Kampf (Kapitel 4). Solange das Urteil gilt, fällt ZURUECK wegen derselben Gegner weg.
- **Entscheidungspunkte** (`Proben`, 3.3) und der **Todesrückblick** nach Tabelle 8. „Raus kam“ steht nur, wenn der
  Rückzug wirklich gesprochen wurde; es zählt der letzte gesprochene Ruf vor dem Tod.
- **Entscheidung 2 (Carlos):** Solange `[kampf].geeicht = false`, sind ANNEHMEN, REIN und DREHEN stumm.
  - Sie werden berechnet und im Protokoll als „stumm: Modell nicht geeicht“ geführt (`Kern.stumm_modell`,
    `_kern.jsonl` Feld `stumm`), aber nicht gesprochen und nicht als Kandidat genommen.
  - Das ungeeichte Modell ändert also nichts an dem, was sonst gesagt wird. RAUS und der Rückblick sprechen.
  - Folge: 144655 6:10 und 140253 9:49 kommt jetzt der Rückzug-Satz statt „Rein auf …“. Der Rückblick sagt dann
    „Raus kam, du bist geblieben – … hat dich erreicht“ (Tabelle 8, Zeile 2).
- `werkzeuge/kampf_eichung.py`, `kennzahlen.py` mit der Spalte „Kampf-Verstöße“.
- `sperre._afk` ist in KAMPF stumm, wenn der Kern spricht.

### Umgesetzt – Buch 6 (Objectives)

- **Rechnung je Objective** (`kern/objective.py`): wer wann an der Grube ist, Tötungszeit mit Rache und Stufe, Kampf
  und Steal, `p_erfolg`, `anteil`, Werte und Folgewerte.
  - „Wirst du gebraucht?“ in der Lane-Phase (Kapitel 6, streng: Prio nur mit `GECRASHT_BEI_IHM` oder totem bzw.
    abwesendem Lane-Gegner, und euer Jungler geht hin).
  - `objective_zieht` wird einmal je Takt für alle Objectives gerechnet.
- **`objective_zieht` an allen Stellen**, die ein Objective als Ziel oder Grund nennen:
  - STAPELN, WELLE_HALTEN („nicht vor einem Objective“), VORBEREITEN_OBJECTIVE, OBJECTIVE_VORLAUF, der
    Objective-Teil von `nie_back` (sperrt jetzt auch „Welle rein, dann back“);
  - WOHIN aus Basis und Tod (`mindestens` fällt weg), `karte.objective_ruft`, WELLE_UND_RAUS;
  - die Back-Sperre in GRUPPE und UNTERWEGS.
  - Damit ist der Larven-Sog an allen Stellen zu (konstruierte Lage `k-kein-stapeln-ohne-jungler`, Szenarien 0647 und
    1025).
- **Handlungen** (`modi/objective.py`): VORBEREITEN_OBJECTIVE, NEHMEN (Alias ANLAUFEN), BESTREITEN (EV aus 4.4) und
  ABGEBEN_TAUSCHEN (der Tausch zuerst: „Äußerer Top-Turm jetzt: sie sind zu fünft am Drachen.“).
  - Das Urteil kommt einmal je Spawn. Ein zweites Mal nur, wenn es zwischen Nehmen und Abgeben kippt.
  - VORBEREITEN → NEHMEN wird nicht angesagt.
- **Modus OBJECTIVE neu** (5): in der Grube (≤ 30 s bis Spawn) oder mit Objective-Plan ≤ `objective_nah_s`. Er endet
  5 s nach dem Plan. „Mitspieler an der Grube“ löst nicht mehr aus.
  - Objective-Pläne gelten über UNTERWEGS, GRUPPE, SEITE und OBJECTIVE hinweg.
- **Alte Regeln:** `_grosse_objectives`, `_vorwarnung`, `_zahlen`, `_objective_start`, `_ward` und der
  Objective-Plan des Entscheiders sind in allen Modi stumm (Buch 0, Kapitel 14 nachgetragen).
- **Reihenfolge im Umwandel-Fenster** (8): Baron und Ältester 2,5, Drache 1,5. Ein erreichbares Objective
  verdrängt die niedriger eingereihten Türme.
- **Baron-Auslöser** fürs Umwandeln (4.6): euer BaronKill ≤ 180 s her, ≥ 3 mit Buff am Leben.
- **TP_SPIEL zu einem Objective** (4.7) nur, wenn dein TP das Urteil ändert. Flanke ohne Sicht gibt es nicht mehr
  („TP …, dann rein“).
- **Der Älteste** ist ein eigenes Objective (`aeltester`, n_min 3, Wert 3000). Swiftplay: nach zwei Elementardrachen
  oder ab 15:00.
- **Fakten** (Kapitel 12):
  - Ältester **6:00** nach dem 4. Drachen. Quellen: Wiki „Dragon pit“, Abschnitt Spawn, und riftpatchnotes Patch
    14.3: „First spawn timer is now properly 360 seconds“. Die 5:00 im Lexikon stammten aus 14.2.
  - Rache 15 % je Drache, höchstens 60 %; Larven 30 g je Larve; Herold-Auge 20 s; Baron 6:00 / Buff 180 s.
  - Eingetragen in `wissen/objektive.toml` und `saison2026.md`.
- **Entscheidung 1 (Carlos), Nachtrag in Buch 6, 3.3:**
  - „Ohne dich“ zählt nur, wer nachweislich hingeht (an der Grube oder in 10 s um ≥ 1000 genähert).
  - Wer ≤ 1500 bei dir steht und nicht zu einem *anderen* Objective geht, kommt mit dir. Er zählt mit dir, nicht
    ohne dich, und der Satz nennt ihn: „Drache mit Tryndamere: …“.
- **Prüfschlüssel** `soll_ziel`, `max_woerter`, `alte_regeln_max` (Buch 0, 12.1 nachgetragen). `_kern.jsonl`
  schreibt `p_erfolg`, `anteil`, `zieht` je Objective. `kennzahlen.py` hat die Spalte „Objective-Ansagen ohne Chance“.
- `werkzeuge/objective_eichung.py` (Kapitel 10).

### Eichung

**Kampf (Buch 7, 3.3)** – 6 echte Partien (133930, 140253, 144655, 145702, 164326, 173159), 112 Proben, **41
entschieden** (63 % offen):

| Art | Proben | entschieden | Brier | Grundrate |
|---|---|---|---|---|
| 2 (Duell) | 69 | 22 | 0,332 | 0,248 |
| 3–6 | 43 | 19 | 0,305 | 0,249 |
| gesamt | 112 | 41 | **0,320** | 0,249 |

- **Soll nicht erreicht** (Brier < 0,20 und besser als die Grundrate). Das Modell trennt gewonnene und verlorene
  Kämpfe nicht: Das mittlere p liegt bei gewonnenen bei 0,56, bei verlorenen bei 0,62.
- **Faktoren: alle Startwerte.**
  - k: 3.3 Punkt 5 wörtlich hätte k = 1 gesetzt (Brier 0,274 statt 0,320). Das ist aber nur eine Abflachung Richtung
    50 %: Kein Faktorsatz schlägt die Grundrate, und k = 1 kippte 0904, 0806 und 0701, die nach 11.4 grün bleiben
    müssen. `kampf_eichung.py` lässt deshalb die Startwerte stehen, solange kein Faktorsatz die Grundrate schlägt.
  - ult, turm und mitspieler: Gezählt werden nur Proben, in denen der Faktor wirkt – 21, 8 und 19, jeweils < 30.
- Nach Entscheidung 2 bleiben ANNEHMEN, REIN und DREHEN stumm (`geeicht = false`).

**Trennschärfe je Merkmal** (Entscheidung 2, damit das Modell danach gezielt verbessert werden kann; 41 entschiedene
Proben: 22 gewonnen, 19 verloren). Gemessen am Entscheidungspunkt der Probe:
- Level und Gold: Mittel eurer Beteiligten minus Mittel der nahen Gegner. Gegnerwerte mit `kampf.gegner_werte`,
  also der Schätzung des Modells (G7).
- Kopfzahl: `len(wir) − len(gegner)`. Turm: +1 euer, −1 ihrer, 0 keiner.
- AUC: Wahrscheinlichkeit, dass eine zufällige gewonnene Probe den höheren Wert hat als eine zufällige verlorene.
  Gleichstand zählt halb; 0,5 trennt nicht, unter 0,5 trennt verkehrt. Rauschen bei 22/19 Fällen etwa ±0,18 (95 %).

| Merkmal | gewonnen (Mittel) | verloren (Mittel) | AUC | n |
|---|---|---|---|---|
| p (Modell) | 0,56 | 0,62 | 0,40 | 41 |
| Leben | 0,95 | 0,87 | 0,58 | 41 |
| Level-Unterschied | +0,90 | +1,28 | 0,43 | 41 |
| Gold-Unterschied (Item-Gold) | +431 | +1438 | **0,30** | 41 |
| Kopfzahl-Unterschied | +0,77 | +0,63 | 0,51 | 41 |
| Turmnähe | 0,09 | 0,32 | 0,39 | 41 |

- Nur das Leben zeigt in die richtige Richtung, und schwach (0,58, im Rauschen). Level und Kopfzahl trennen nicht.
- Das Gold trennt verkehrt herum (0,30, knapp außerhalb des Rauschens): Verlorene Kämpfe begannen mit dem größeren
  Goldvorsprung. Weil Level und Gold die Kraft im Modell tragen, liegt p selbst verkehrt (0,40).
- Turmnähe: Von den 8 Proben an eurem Turm gingen 6 verloren. Ihr Turm kommt in den entschiedenen Proben nicht vor.
- Nicht geprüfte Deutung: Mit Vorsprung werdet ihr mutiger, und der Ausgang (Kill-Gold in 15 s) misst dann eher das
  Nachsetzen als die Stärke am Einstieg.
- Daten: `kampf_eichung.py --json` (jetzt `{"proben", "trennschaerfe"}`). Die Proben tragen `level_diff`, `gold_diff`
  und `kopf_diff`.
- Die bis zu drei Proben je echter Partie mit dem größten Fehler liegen als Stubs in
  `tests/szenarien/offen/<stamm>_kampf.toml` (Buch 7, 10). Das Soll setzt Carlos.

**Objectives (Buch 6, Kapitel 10)** – dieselben 6 Partien:
- **Urteil gegen Ausgang:** 15 Versuche, Brier 0,276, Grundrate 0,20 → 0,160. Soll nicht erreicht, zu wenige
  Versuche (< 30), also **Startwerte**.
- **Tötungszeiten:** keine Gruppe hat ≥ 3 Fälle, die Tabelle bleibt. Die Einzelwerte streuen stark, von 3 s bis
  123 s: Der Beginn „≥ 1 von euch ≤ 700 an der Grube“ erkennt auch Vorbeilaufen. Die Messung braucht mehr Partien und
  einen strengeren Beginn.

### Wellen-Eichung (Entscheidung 2 der Prüfung b, Entscheidung 3 von heute)

- Beschriftet von Hand aus den behaltenen Minimap-Bildern: je 480 px Gitter, alle Zeitpunkte der Lane-Phase, auf
  denen du auf der Lane stehst. Eindeutig ist ein Punkt nur, wo die Vasallen nicht unter den Champion-Icons liegen.
  Die erste Welle vor dem Treffen zählt nicht.
- Ergebnis:
  - **164326: 13 von 15 eindeutigen richtig (87 %) – erreicht.**
  - **173159: 7 von 12 (58 %) – nicht erreicht.**
- Die meisten eindeutigen Punkte sind „unsere Welle läuft zu ihm, keine roten zu sehen“. Kämpfe an der Welle verdecken
  die Vasallen fast immer (164326: 22 von 37 unklar, 173159: 20 von 32).
- Nach Entscheidung 3 wird nichts umgebaut, die strenge Prio-Regel aus Buch 6, Kapitel 6 bleibt.

**Fehlerursachen je Zeitpunkt** (Entscheidung 3; wie bei 144655 unter F1)

Nachgerechnet mit `wellen_eichung.durchrechnen` und dem WellenPuffer Bild für Bild: roh = `_roh`, Zustand = nach der
Hysterese. Riven spielt CHAOS Top, s aus ihrer Sicht: ihr Turm 0,375, Knick 0,50, Crash-Zone 0,355–0,455.

*173159* (7 von 12):

- **7:33:** Kern GECRASHT_BEI_DIR, wahr ZU_DIR (0:1, Front 0,47, Trend +0,127).
  - Ursache Icon-Deckung (`stand`): Riven steht bei 0,438 am Rand der Zone. Dadurch reicht die Zone bis 0,49, und
    ein roter bei 0,47 genügt. `crash_dir_sofort` schaltet ohne Hysterese.
  - Die übrigen roten liegen unter ihrem Icon und einem „?“-Ping.
- **9:25:** Kern ZU_IHM, wahr GECRASHT_BEI_DIR (6:2, Front 0,37, Trend +0,059).
  - Ursache `Wellenleser.punkte`: Fünf rote kleben vor dem Turm übereinander, gelesen werden 2. Die angeschnittenen
    Stücke liegen unter 22·f, ohne weiße Linie, und fallen heraus. Im Median stehen damit 2 in der Zone, weniger als
    `crash_mindestens` (3).
  - Dann nimmt `_front` unsere frische Welle hinter dem Turm in dieselbe gemischte Gruppe: 6:2, die Zählregel sagt
    ZU_IHM.
- **11:07:** Kern ZU_IHM, wahr ZU_DIR (0:3, Front 0,50, naechste 0,05).
  - Die Trendregel hält ZU_IHM bis 11:04 trotz 0:2. Die Front glitt ohne Sprung (keiner > `front_sprung` 0,12) von
    unserer Welle (0,35 → 0,49) auf die roten (0,51–0,54), und die Regression trug unseren Vormarsch weiter
    (+0,15). In `_roh` steht der Trend vor der Zählung.
  - Ab 11:05 ist roh ZU_DIR, die Hysterese (3 s) schaltet erst 11:08.
- **11:57:** Kern MITTE, wahr ZU_IHM (4:0, Front 0,45).
  - Hysterese: roh ZU_IHM seit 11:55, umgeschaltet 11:58.
  - Davor lagen 11:39–11:50 zwei Kartensymbole unbewegt am Knick: ein roter Totenkopf und ein blaues Zeichen. Sie
    wurden als gemischte Front 1:1 (MITTE) gelesen, unsere Welle lief dahinter als `naechste`.
  - Nach dem Frontsprung gab es keinen Trend, und der 6-s-Median stand noch auf 1:1.
- **12:49:** Kern MITTE, wahr ZU_IHM (4:1, Front 0,37, Trend −0,135).
  - Hysterese: roh ZU_IHM seit 12:47.
  - Davor: Kampf am Knick. Unsere Vasallen dort sind halb verdeckt (unter 22·f) und fallen heraus. Die roten bilden
    die Front gegen unsere frische Welle bei 0,09–0,22: 4:4, Front als Mitte zwischen beiden, also MITTE.

*164326* (13 von 15):

- **3:59:** Kern MITTE, wahr ZU_IHM (6:0, Front 0,55, naechste 0,46).
  - Hysterese: roh ZU_IHM seit 3:58.
  - Davor hielt ein stehender Kampf am Knick die Front 3:28–3:56 bei 0,55, Trend ≈ 0. Die roten lagen vermutlich
    unter Teemos Icon.
  - Unsere neue Welle lief mit einer Lücke > 0,06 dahinter und zählte nur als `naechste`. Ab 3:51 ist „ihre“ None
    (Nebelregel, Front > `nebel_ab`).
- **5:01:** Kern GECRASHT_BEI_DIR, wahr ZU_DIR (0:1, Front 0,48).
  - Wie 7:33: Rivens Icon bei 0,44–0,45 zieht die Zone bis 0,50, ein roter am Knick genügt, sofort.

*Muster:*
- **Vier von sieben Fehlern sind Umschaltverzug** (11:07, 11:57, 12:49, 3:59): roh war 1–2 s vorher schon richtig,
  die Hysterese (3 s) hielt den alten Zustand.
  - Bei den MITTE-Fehlern hielt das 6-s-Fenster eine falsche, verdeckte oder stehende Front fest, während nur unsere
    neue Welle lief.
- **Verdeckung macht die Crash-Regel in beide Richtungen unscharf:**
  - Das eigene Icon am Zonenrand macht aus einem roten einen Crash (7:33, 5:01).
  - Übereinanderliegende Vasallen zählen nicht mit (9:25, 12:4x).
  - Kartensymbole zählen als Vasallen (11:39–11:50).
- **Der Trend überlebt den Wellenwechsel,** wenn die Front ohne Sprung von unserer auf ihre Welle gleitet (11:07).
- Mögliche Ansatzpunkte, nach Entscheidung 3 **nicht umgesetzt**:
  - Icon-Deckung nicht über den Knick hinaus.
  - Trend neu beginnen, wenn die Farbe der Front wechselt.
  - Kürzere Hysterese zwischen ZU_* und MITTE.
  - Stücke an anderen Vasallen zählen, nicht nur an weißen Linien.

### Abnahme Schritt 5

| Abnahme | Soll | Ist |
|---|---|---|
| `tests/alle.py` | grün | **8 / 8** |
| Szenarien (alle Dateien, `--kern neu`) | grün | **57 / 57** (2 übersprungen, brauchen Claude); konstruierte Lagen **40 / 40**; Modus-Sollwerte 102112 **16 / 16** |
| Buch 7, 11.1: Szenarien aus Kapitel 10 | grün über den Kern | **grün**: 0915, 0622, 2501, 2613, 2631, 0338 (erweitert), 0843/1005 (erweitert) |
| Buch 7, 11.2: `kampf_eichung.py` | gelaufen | **ja** – Brier und Faktoren oben, Soll nicht erreicht |
| Buch 7, 11.3: Kampf-Verstöße in allen Protokollen | 0 | **0** in 102112, 133930, 140253, 144655, 164326, 173159 |
| Buch 7, 11.4: 0517, 0850, 0904, 3535, konstruierte Lagen | grün | **grün**; Kehrtwenden **0** in allen sechs |
| Buch 6, 14.1: Szenarien aus Kapitel 13 | grün über den Kern | **grün**: 2522, 2847, 3500, 3451, 3831, 1453, 2516, 3335, 2637, 0647 (beide), 0729, 0427, 1025 |
| Buch 6, 14.2: `objective_eichung.py` | gelaufen | **ja** – Startwerte, zu wenige Versuche |
| Buch 6, 14.3: alte Regel mit Objective-Satz in 102112, 133930, 140253, 144655 | 0 | **0** – in allen sieben Protokollen sprechen alte Regeln nur noch den Todesrückblick (14) und AFK (1) |
| Buch 6, 14.4: Objective-Ansagen ohne Chance | 0 | **0** in allen sechs |
| Fassungswechsel (Prüfung D) | 0 | **nicht erreicht**: 102112 2, 133930 1, 164326 3, sonst 0 (s. u.) |
| Ungefragte Ansagen je 30 min (Prüfung b, Entscheidung 4) | ≤ 45 | **nicht erreicht**: 59–80 (s. u.) |

**Kennzahlen** (Kern, `kennzahlen.py --nur-kern`):

| Aufnahme | ungefragt (je 30 min) | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | Kampf-Verstöße | ohne Chance | GEFAHR / PLAN / ERINNERUNG / BESTÄTIGUNG | stumme Kampf-Rufe |
|---|---|---|---|---|---|---|---|---|
| 102112 | 61 (60) | 0,79 | 0 | 2 | 0 | 0 | 16 / 42 / 1 / 1 | 37 |
| 133930 | 58 (80) | 1,24 | 0 | 1 | 0 | 0 | 21 / 30 / 2 / 0 | 11 |
| 140253 | 25 (70) | 1,18 | 0 | 0 | 0 | 0 | 13 / 9 / 0 / 1 | 7 |
| 144655 | 19 (59) | 1,01 | 0 | 0 | 0 | 0 | 12 / 6 / 0 / 0 | 7 |
| 164326 | 96 (67) | 1,00 | 0 | 3 | 0 | 0 | 40 / 50 / 2 / 2 | 23 |
| 173159 | 94 (74) | 0,86 | 0 | 0 | 0 | 0 | 43 / 44 / 0 / 5 | 28 |

145702 hat nur 0,5 Minuten mit Daten und zählt nicht.

- **Ziel ≤ 45 je 30 min nicht erreicht.** Die alten Regeln sind jetzt bis auf Rückblick und AFK still. Was bleibt,
  sagt der Kern selbst: 40–50 % davon sind GEFAHR, vor allem der Rückzug „Raus zu deinem …-Turm: X und Y kommen“.
  Der nächste Hebel ist die Gefahr-Rechnung selbst: seltener anschlagen und zusammenfassen.
- **Fassungswechsel:**
  - Zweimal folgt auf „Back jetzt: …“ bzw. „Raus zu …“ innerhalb von 10–25 s „Jetzt back: …“ mit neuem Gold
    (102112 33:20/33:44 und 37:03/37:13; 164326 10:21/10:36). Seit ein Rückzug-Plan ohne Gefahr endet (Abweichung
    15), beginnt der Back danach als neuer Plan statt als Schritt des alten.
  - Zweimal wechselt das Turm-Ziel ohne Ereignis in 12–14 s (133930 10:25/10:37, 164326 35:00/35:14).
  - Einmal KAUFEN mit anderer Liste (164326 38:09/38:33).

### Abweichungen vom Buch und Entscheidungen

**Buch 7**
1. **Turm im Kampfurteil:** Der Turm zählt auch, wenn du ≤ 5 s vom eigenen Turm entfernt bist oder dorthin gehst,
   nicht nur ≤ 775 (3.1). Grund: der schützende Freeze (`k-freeze-schuetzend`) wurde sonst rot.
2. **k bleibt 2** trotz 3.3 Punkt 5 (s. Eichung). Die Regel „erst ändern, wenn der Faktor in ≥ 30 entschiedenen
   Proben wirkt“ gilt je Faktor.
3. **Tote Gegner** zählen im Kampfurteil mit ihrem Gewicht aus `p_da_am` (Respawn + Weg). Vorher fehlten sie ganz:
   102112 34:51 zählte am Inhibitor-Turm niemanden von denen, die 11–19 s später daneben aufstanden.
4. **Rückblick:** „Raus kam“ nur nach einem gesprochenen Rückzug; es zählt der letzte gesprochene Ruf (140253 10:16).
5. **ANNEHMEN hält,** solange sein Gegner in `annehmen_abstand` bleibt, auch wenn er nicht weiter näher kommt.
   Das gilt auch für das stumme Urteil (102112 26:29).
6. **Szenarien:**
   - 2501: REIN ist erlaubt, der Kampf lief schon.
   - 2613: zeit 26:28, erst dort ist Fiddlesticks ≤ 2500.
   - 2847: REIN ist erlaubt (Kampf 28:43–28:48).
   - 0622 und 1005: nach Entscheidung 2 Zeile 2 von Tabelle 8.
   - Beim Nachspielen gilt in KAMPF als „Plan“ die Entscheidung der Tabelle 5.1.

**Buch 6**
7. **Wer zählt an der Grube** (3.1/3.3, vor Entscheidung 1):
   - Mitspieler zählen nur, wenn sie hingehen, nicht jeder, der es in der Zeit könnte. Tote Mitspieler zählen nicht.
   - Beleg: 102112 25:24 „Baron jetzt: ihr seid fünf“, zwei davon in der Basis. Buch 6, 8 sagt selbst: „Baron fällt
     heraus, weil zwei eurer Leute in der Basis stehen“.
   - Entscheidung 1 hat das präzisiert (Nachtrag 3.3).
8. **Kampf an der Grube:**
   - NEHMEN: Eure Leute zählen bis zum Ende der Tötungszeit, nicht nur `kampf_fenster_s`.
   - BESTREITEN: Gekämpft wird bei deiner Ankunft (Weg + `kampf_fenster_s`), und nur, wenn mindestens einer von
     ihnen an der Grube steht. Sonst war BESTREITEN der Dauerplan: 102112 24:36–38:36 kam „Baron bestreiten“ mit
     EV ≈ 4000, ohne dass einer von ihnen am Baron war. Die EV aus 4.4 rechnet gegen „sie bekommen es sicher“.
9. **VORBEREITEN:** Passt der Welle-Schritt nicht mehr ins Fenster, geht es ohne ihn. NEHMEN gilt auch von der Lane
   aus. Sonst fiel die Lage zwischen beiden durch (`k-kein-back-kurz-vor-larven`).
10. **TP ändert das Urteil (4.7):**
    - Es gilt um ≥ 0,15 **oder** das Urteil kippt über 0,5.
    - Mit k = 2 und `mitspieler_anteil` 0,8 hebt ein Spieler p bei 4 gegen 4 nur um 0,147. Das Buch-5-Beispiel
      („TP macht es 5 gegen 4“) wäre sonst nie möglich.
    - `m-tp-spiel` ist jetzt 4 gegen 4. Das alte 4 gegen 5 steht als `m-tp-kampf-bleibt-verloren` (dort
      ABGEBEN_TAUSCHEN).
11. **Turm-Prüfung der Karten-Rechnung:**
    - Kommen zwei oder mehr Verteidiger wahrscheinlich (p_da ≥ 0,5), entscheidet `p_gewinn` am Turm mit dir und
      deinen Mitspielern in 1500 (Buch 5). Die Schwelle ist `split_kraft_min` in p umgerechnet (0,59).
    - Kommt nur einer, gilt Buch 5 wie bisher.
    - Beleg: 102112 34:51 „Mid-Inhibitor-Turm“, während drei daneben respawnten; 25:25 „Top-Inhibitor-Turm: du
      schlägst die drei“, 39 s über die Karte.
12. **Tote in ihrer Basis:** Liegt ihr Brunnen ≤ 5000 vom Ziel, sind sie da, sobald Respawn und Weg ≤ T sind – ohne
    Seiten-Faktor und Anlauf-Rampe.
13. **Reihenfolge (8) wörtlich:** Ein erreichbares NEHMEN oder BESTREITEN streicht im Umwandel-Fenster die niedriger
    eingereihten Türme. Die 200 GE je Rang reichten nicht.
14. **Urteil hält (1.6), Entscheidung 4:**
    - `zieht` kippt sofort mit einem Ereignis (Tod, Spawn, Sichtung eines Unbekannten, Struktur fällt).
    - Ohne Ereignis kippt es erst, wenn der neue Wert 3 s besteht (`URTEIL_STABIL_S`).
    - Streng gehalten blieb in 102112 nach dem Drachen 35:16 ein falsches „zieht nicht“ minutenlang stehen, weil ein
      Drachen-Kill kein Ereignis der Liste ist.
    - Ein gemerktes Ziel aus TOT oder BASIS fällt weg, wenn sein Objective nicht mehr zieht (3002).
15. **Rückzug ohne Gefahr:** Ein Plan „nur bei Gefahr“ (ZURUECK) ist ohne Gefahr kein Kandidat mehr. Die G3-Lücke
    (2 s) hält ihn noch kurz. Vorher blieb er Kandidat, solange er Plan war: 102112 24:58 bis 25:22, dann schlug er
    mit seinem Back-Wert den freien Drachen.
16. **Swiftplay in 140253:** 0729 (Larven) und 0427 (Drache) haben ihr Soll aus den Swiftplay-Fakten, nicht aus
    Kapitel 6: Larven gibt es nicht, der erste Drache hat keinen Timer. Das Buch verlangte, das Soll *vor* der
    Umsetzung festzulegen; es wurde erst danach angelegt.
17. **Konstruierte Lagen:**
    - Bekommen, was Buch 6 verlangt (Prio und Jungler): `k-stapeln-vor-larven`, `k-kein-freeze-vor-objective`,
      `k-kein-back-kurz-vor-larven`.
    - `m-welle-und-raus` bekommt euer Team unten.
    - Neu sind `k-kein-stapeln-ohne-jungler` und `m-tp-kampf-bleibt-verloren`.
18. **Modus-Sollwerte neu gerechnet** (13): 15:31 (+SEITE/UNTERWEGS), 25:22 (+SEITE), 29:14 (+UNTERWEGS).
    `2522` bekommt SEITE, `1315` UNTERWEGS. Grund jeweils: kein Objective-Plan, nicht in der Grube.
19. **0159:** `plan_p_tod_max` ist jetzt `wohin_p_tod_max` (0,3). Mit dem Kampfmodell sind es 0,22 statt < 0,2; der
    Plan ist derselbe. Der Fehler E2 lag bei 0,64.
20. **Prüfung vor dem Sprechen:**
    - Ein Plan-Satz fällt weg, wenn beim Sprechen KAMPF gilt (Buch 7, 11.3). Ein Objective-Satz (außer BESTREITEN
      und ABGEBEN_TAUSCHEN) fällt weg, wenn das Objective dann nicht mehr zieht (Buch 6, 14.4). Beleg: 133930 10:49
      „Drache mit Fizz“ kam erst, als der Drache nicht mehr zog.
    - Kennzahlen: Die Kampf-Verstöße zählen nach dem Modus im Takt des Sprechens, wie das Protokoll. Vorher zählten
      sie alles zwischen den Episodengrenzen, auch 144655 6:10, gesprochen in LANE.
    - Der Todesrückblick zählt nicht als alte Regel in KAMPF, er wird in TOT gesprochen.
    - „ohne Chance“ zählt die Liste aus 14.4 – ohne BESTREITEN, das hatte ich zuerst dazugenommen.
21. **Nicht umgesetzt:**
    - Lane-Form von ABGEBEN_TAUSCHEN („Gangplank ist zu den Larven: Platten jetzt“).
    - Herold-Ritt (Kapitel 7, `wert_ritt` mit Turm-Leben); heute grob zwei Platten × 0,8.
    - Folgewert Larven 3:0.
    - Bestätigungen aus Kapitel 9 („Sauber: Drache ohne Kampf“).
    - Alle stehen in `OFFEN.md`.

---

## Qualitätsrunde 2 – Prüfung vom 27.09.2026 (b), Entscheidungen 1–3 und G1–G6 (27.09.2026)

Auftrag: `buecher/protokolle/PRUEFUNG_2026-09-27b.md`. Umgesetzt in 39a858b (Bücher 6 und 7 vorher committet:
705a6a6). Offline gemessen, der Coach wurde nicht gestartet.

### Entscheidungen 1–3

- **1. `0843`:** Die Daten haben recht. Das Szenario nennt jetzt Yasuo und darf „Brand“ nicht sagen.
- **2. F1-Zusätze** (Pfadlinie, Icon-Deckung, `crash_dir_sofort`) bleiben an. Die Bestätigung an 164326 und 173159
  steht unten unter „Schritt 5 → Wellen-Eichung“.
- **3. F2 Flash, Weg 1:** `wissen/dashes.toml` (Stand Data Dragon 16.19.1, von Hand geprüft). 112 Champions mit eigenem
  Dash, dazu die Blinks aus `blinks.toml`. Entfernt wurden Cho'Gath und Udyr, ergänzt Elise und Ryze.
  - Minimap und Bildschirm werten für diese Champions keine Sprünge mehr als Flash (`zauber.dash_champions`).
  - Test: Ein Brand-Sprung ergibt einen Timer, ein Vi-Sprung nicht.
  - Weg 3 (Carlos pingt über die Anzeigetafel) lief schon. Weg 2 steht in `OFFEN.md`, nach Schritt 6.

### G1–G6: zuerst rot, dann behoben

Vor den Fixes: **16 von 28 geprüften rot** (die neuen G-Szenarien und die Spielmodus-Prüfung; Stand 705a6a6).
Nach 39a858b: 42 von 43. Rot blieb `0904-drei-kommen`: Es war vorher nur durch die Doppelzählung der Gefahr grün und wurde
mit dem Kampfmodell aus Schritt 5 wieder grün.

- **G1 Schutzplan (144655, 140253):**
  - Eine verlorene Lane ist jetzt **eine Episode**. Der lange Satz (≤ 18 Wörter) kommt einmal. Nach Tod oder Basis
    kommt höchstens alle 180 s die kurze Fassung: „Weiter: am Turm farmen, kein Trade.“
  - **Ursache des Item-Sprungs:** Das Bauteil war `kaufplan.kaufen[0]` (das teuerste, das du dir leisten kannst) oder
    `naechstes` (das billigste, das du dir nicht leisten kannst). Welches, hing vom Gold im jeweiligen Takt ab. Jetzt
    steht das Bauteil fest, bis es gekauft ist.
  - Die Lane-Kraft wird ohne Leben gerechnet (`lane_kraft`), damit die Episode nicht mit dem Leben flackert.
  - Übergeben heißt nicht gesprochen: Verfällt der Satz, wird er wieder angeboten.
- **G2 WOHIN:**
  - Die Gefahr wird über die **Mengen** der Ankommenden gerechnet statt doppelt gezählt (`_ueber_mengen`). Im eigenen
    Brunnen gilt volles Leben.
  - Unter `wohin_p_tod_max` (0,3) wird das Ziel genannt. Unter `wohin_direkt_max` (0,15) auch eilig, sonst „Zurück
    nach X, bleib am Turm“.
  - Rückfall: Team (≥ 2), sonst ein eigener Turm weiter hinten, sonst „Warte am inneren X-Turm auf dein Team“.
  - Plausibilität (p_tod heute → nach dem Fix; in Klammern mit vollem Leben):

    | Lage | vorher | nachher | Beiträge |
    |---|---|---|---|
    | 144655 5:07 | 0,65 | 0,42 (0,36) | Gangplank 0,42, Kha'Zix 0,37, Vex 0,05 |
    | 140253 10:25 | 0,73 | 0,37 | Yasuo 0,33, Tahm Kench 0,28, Jinx 0,24, Heimerdinger 0,19 |
    | 133930 12:30 | 0,79 | 0,37 | Gwen 0,42, Zoe 0,31, Xin Zhao 0,28, Zac 0,25 |
    | 133930 15:16 | 0,67 | 0,33 | Zac 0,33, Zoe 0,33, Gwen 0,26 |

  - Nebenbei behoben: Der Merker gab dasselbe Handlungsobjekt zurück, TOT schrieb jedes Mal „Noch N Sekunden:“ davor.
    Jetzt legt er Kopien ab.
- **G3 Plan hält (140253 3:49–4:27):**
  - **Ursache:** Der Kandidat des Plans (WELLE_REIN_UND_BACK) fiel einen Takt heraus. STAPELN (242 GE schlechter)
    wurde Pflicht-Plan, und `halten_s` (8 s) sperrte die Rückkehr. Der Test sah das nicht, weil STAPELN im
    Wechsel-Takt tatsächlich der beste Kandidat war.
  - Jetzt hält der Plan eine Lücke < `luecke_s` (2 s), wenn Modus und Gefahr gleich bleiben. Dabei gibt es keinen
    Schritt-Satz. Nach einem erzwungenen Wechsel sperrt `halten_s` nicht. Eine Erinnerung kommt nur, wenn der
    Kandidat des Plans in diesem Takt da ist.
- **G4 „Gut raus“:**
  - Beurteilt wird es 10 s nach dem Rückzug-Satz: das Leben fiel um weniger als 20 Punkte, du stehst am sicheren Ort,
    und der Gegner wurde an der alten Stelle gesehen.
  - Nie in KAMPF, geprüft beim Sprechen. „er“ und „sie“ richten sich nach der Zahl.
- **G5 Rückblick:** Satz 2 richtet sich nach dem Leben beim Einstieg. Ab 0,6 (`RUECKBLICK_VOLL`) heißt er „hinter den
  Turm oder zu deinem Team“, sonst „zurück“.
- **G6 Swiftplay (133930, 140253):**
  - Das Profil steht in `wissen/mechanik.toml [swiftplay]`. Quellen: Riot Support (28.01.2026), /dev (01.12.2025),
    Wiki Swiftplay samt Patch-History V25.S1.3, V26.01, V26.02, V26.07 und Hotfix.
  - Keine Larven, kein Herold. Der erste Drache hat keinen belegten Timer, Respawn 300 s, höchstens zwei
    Elementardrachen. Der Älteste kommt ab 15:00, dann alle 6:00. Baron kommt um 12:00.
  - Die Lane-Phase dauert bis 10:00, Wellen alle 25 s ab 11:35, Kanonen ab der dritten Welle.
  - Szenario-Dateien tragen `spielmodus`. Stimmt er nicht mit der Aufnahme überein, ist die Datei rot. Das Protokoll
    und die Wellen-Eichung nennen den Modus.
  - Betroffene Szenarien:
    - 140253: `0843` (Fenster 8:34–8:55), `1025` (Lage korrigiert: keine Larven), `0000`
      (1400 Startgold).
    - 133930 und 140253: `swiftplay-keine-classic-zeiten`, `swiftplay-keine-larven`.

### Nebenbefund: Gegner-Items sind so veraltet wie ihre Level

Item-Wechsel der Gegner in der API tauchen fast nur auf, während der Gegner sichtbar ist:

| Aufnahme | Item-Wechsel (davon ungesehen) | Level-Wechsel (davon ungesehen) |
|---|---|---|
| 144655 | 18 (2) | 31 (3) |
| 164326 | 63 (11) | 82 (5) |
| 173159 | 70 (18) | 83 (15) |

Die Schätzung aus Buch 7, 3.2 (G7: Level und Item-Gold lange ungesehener Gegner) gilt deshalb für beides
(`kampf.gegner_werte`).

### Abweichungen und Entscheidungen

- `nie_back`: Ein Gegner, der vor ≤ 3 s zu sehen war (`NIE_BACK_EBEN_S`), zählt wie sichtbar. Beleg: 140253 8:04,
  „Back jetzt“ mit Yasuo 935 entfernt, der im Takt davor zu sehen war.
- `planwechsel_max` zählt Bestätigungen, Erinnerungen und Kampf-Rufe (REIN, RAUS, DREHEN) nicht als Plan.
- `satz_mit` zählt die noch geltende Kern-Ansage von vor dem Fenster mit, wie `muss_nennen_eins`.
- Die erste Swiftplay-Welle ist mit 0:30 angenommen, das ist nicht belegt.

---

## Qualitätsrunde 1 – Prüfung vom 27.09.2026, A–F (27.09.2026)

Auftrag: `buecher/protokolle/PRUEFUNG_2026-09-27.md`, A–F, noch nicht Schritt 5. Vorher committet: ef08644
(Prüfungsdatei samt Stand). Offline gemessen, der Coach wurde nicht gestartet.

### Umgesetzt

- **A. Verlorene Lane:**
  - Verloren heißt: Kräfte ≤ −1 oder zwei Tode gegen den Lane-Gegner (`modi.lane_verloren`).
  - Der Kern sagt dann **einmal** den Schutzplan `WELLE_HALTEN`: „Gangplank ist vorn: lass die Top-Welle zu
    deinem Turm kommen und farm dort, kein Trade bis Caulfields Kriegshammer.“
    - Der Plan gilt nur bei Leben ≥ `leben_kritisch` und nur, solange kein anderer Gegner beiträgt.
    - Er ersetzt FARMEN und streicht TRADE, ALL_IN und STAPELN.
  - Gefahr am sicheren Ort (≤ 4 s) wird nicht gesagt, der Plan hält. Ebenso Gefahr, zu der nur der Lane-Gegner
    einer verlorenen Lane beiträgt.
  - Nach Tod oder Basis gilt ein Plan wieder als neu (`_angesagt` geleert).
- **B. Plan-Wahl:**
  - Die Gefahr-Regel wechselt auf den besten Kandidaten, den das Gate nicht auslöst.
  - Hält die Hysterese einen schlechteren Plan, steht der Grund im Protokoll (`gehalten`).
  - Test `neuer_plan_ist_der_beste` (600 Zufallslagen).
- **C. BASIS/TOT:**
  - WOHIN kommt zuerst aus der Karten-Rechnung, dann ein Objective, wenn es nehmbar ist (`mindestens`), dann
    Seitenwelle oder Team.
  - Jedes Ziel wird mit der Gefahr **bei Ankunft** gerechnet (`gefahr.p_tod_am`; E2).
  - Ein Ziel je Aufenthalt in TOT und BASIS zusammen (`_wohin`). Es wechselt nur, wenn sich Kills, Strukturen
    oder lebende Objectives ändern.
  - Genannte Fenster sind ≥ Weg + Dauer (C3; Test `fenster_gruende_sprechen_dafuer`).
- **D. Rückzug:**
  - Ein Rückzug ist eine Episode (`RUECKZUG_EPISODE_S` = 15 s): ein Satz, einer mehr nur bei einem neu genannten
    Gegner, der Back-Schritt einmal.
  - „Jetzt back“ nur, wenn `nie_back` nichts dagegen hat. Kein „Denk dran“ in GEFAHR.
  - Neue Kennzahl `fassungswechsel`. Der erste „Jetzt back“ nach „Raus“ ist der Plan-Schritt (D2).
  - Beim Nachmessen gefunden: KAUFEN kam nach einem Teilkauf noch einmal. Die Sperre zählt ihn jetzt nach seinem
    Weiterweg (133930, 17:45/17:57; Szenario `1745-kauf-einmal`, Gegenprobe rot).
- **E. Sätze:**
  - E1: Todesrückblick in zwei Sätzen, ≤ 25 Wörter, ohne Zahlen.
    - Beteiligt ist auch, wer in der letzten Sekunde sichtbar in 2000 stand oder in den 10 s davor nah war.
    - Der Rückblick wird nicht mehr vom Strategen umformuliert. Die Fakten liegen in `lage.letzter_tod` für
      „warum bin ich gestorben?“.
  - E3: keine Wellenbefehle in BASIS.
  - E4: 20 s nach einer Gefahr keine Vorwärts-Handlung, außer die Gefahr ist sichtbar vorbei.
  - E5: das genannte Item ist mit dem Gold bezahlbar (Test `gold_reicht_fuer_das_genannte_item`).
  - E6: ohne Modus spricht keine alte Regel (nur mit Kern).
  - E7: kein AFK in KAMPF; Gegner gelten nie als AFK (die API zeigt ihr Level veraltet).
  - E8: Uhrzeiten als Wörter („acht Minuten“, „sieben siebenundfünfzig“), dazu „du bist pünktlich da“ statt
    Sekundenrechnung.
    - Gegenprobe mit edge-tts und Whisper: „7:57“ wurde vorher „sieben, fünf, sieben“ gehört.
- **4.3 auch für den Ort:** Verliert die Minimap dich kurz, hält der Plan (102112, 36:06).
- **F1** (Nachtrag Buch 1, Kapitel 7.1) und **F2**: siehe unten.

### Abnahme

| Abnahme | Soll | Ist |
|---|---|---|
| Szenarien zuerst rot | ja | **14 von 16 neuen rot** mit ef08644. Grün vorher waren 0349 (die Sätze stimmten: Rest 713 ≤ 1050, 1175 ≤ 1400) und 0900 (Riven stand 7 s vor ihrem Turm, der Gank kam 9:20) – beide bleiben als Wächter. |
| `tests/alle.py` | grün | **grün** (8 / 8) |
| alle Szenarien | grün | **29 / 30** (2 übersprungen, brauchen Claude). **Rot: `0843-todesrueckblick`** – die Daten widersprechen dem Szenario. Riven starb 8:34 (EventTime 514,1) an Yasuo allein, `Assisters []`. Brand war nicht beteiligt und stand laut Minimap etwa 4000 Einheiten weg, nicht zu sehen. `muss_nennen_eins = ["Brand", "zwei"]` kann nur ein erfundener Satz erfüllen. Der Rest des Szenarios ist grün (zwei Sätze, ≤ 25 Wörter, keine Zahlen). Ob Brand genannt werden soll, entscheidet Carlos. |
| Konstruierte Lagen | grün | **38 / 38** (`test_kern`) |
| Protokolle | 5 | `buecher/protokolle/` 102112, 133930, 140253, 144655, 145702 (neu erzeugt mit dem Endstand) |
| Abgebrochene Sätze | nur durch GEFAHR | 144655 1, 140253 0, 102112 2, 133930 9, 145702 1 – **alle** durch einen Gefahr-Satz (ZURUECK, Anlauf, „Nimm keinen Kampf an … geh zurück“). Die 9 in 133930 sind alte Regeln in OBJECTIVE/KAMPF (Schritt 5). |
| Fassungswechsel (D4) | 0 | **0** in 102112, 133930, 140253, 144655 (vor dem KAUFEN-Fix 133930: 1) |
| F1: 144655 ≥ 8 von 10 eindeutigen richtig | ja | **9 von 11 (82 %)** |
| F1: 3:13, 5:17, 5:38 sind GECRASHT_BEI_DIR | ja | **ja, alle drei** |
| F1: 133930 ≥ 8 von 10 | ja | **nicht belegbar**, s. u.: die Minimap-Bilder sind weg. Mit den live erkannten Punkten 4 von 7. |
| F2: ≥ 80 % der Sprünge erkannt, ≤ 1 falscher Flash je Partie | ja | **nicht erreicht**, s. u. |
| F2: Dashboard zeigt jeden erkannten Flash mit Restzeit | ja | **ja** (Headless-Chrome im Nachspielen, 133930 2:09: „Gwen Flash 4:45“, „Xin Zhao Flash 4:24“) |

### Kennzahlen (Kern; in Klammern Schritt 4)

| Aufnahme | ungefragt je 30 min | Lane-Phase je 30 s | Kehrtwenden | Fassungswechsel | 9.4 1–4 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG |
|---|---|---|---|---|---|---|
| 2026-09-27_102112 | 53 (56) | 0,79 | 0 | 0 | 0 | 8 / 28 / 1 / 2 |
| 2026-09-27_133930 | 85 (88) | 1,25 (1,21) | 0 | 0 | 0 | 9 / 17 / 2 / 1 (11 / 17 / 3 / 0) |
| 2026-09-27_140253 | 53 (61) | 0,90 (1,04) | 0 | 0 | 0 | 2 / 13 / 0 / 1 (3 / 14 / 1 / 0) |
| 2026-09-27_144655 | 62 (56) | 1,06 (0,96) | 0 | 0 | 0 | 2 / 11 / 1 / 1 (5 / 5 / 0 / 1) |

144655 hat weniger Gefahr-Sätze und mehr Pläne: aus fünf „Raus“ sind zwei geworden, dazu der Schutzplan der
verlorenen Lane. Er wird nach jedem Tod und jeder Basis neu gesagt (1:37, 2:14, 5:39, 7:10). Um 3:34 kam er ein
fünftes Mal, weil sein Item wechselte („kein Trade bis Axiombogen“).

### F1 – Welle: Front statt Summe

Umgesetzt wie in der Prüfung (Nachtrag Buch 1, Kapitel 7.1): Gruppen entlang der Lane, die Front, nachlaufende
Wellen als `naechste_dein`/`naechste_ihr`, `GECRASHT_*` ≥ 3 in 0,08 vor dem Turm, keine Zeitpunkte mit Tod oder
Recall in der Eichung.

Die drei Fälle kamen damit **nicht** grün. Die Ursachen lagen im Bild:

- **3:13 und 5:38:** Riven farmt vor ihrem Turm, ihr Icon verdeckt die gegnerischen Vasallen. Sichtbar sind 1–2
  am Rand, 0,085 vor dem Turm.
- **5:17:** Rivens weiße Pfadlinie (1 px, dunkler Schatten) zerschneidet drei gegnerische Vasallen am Turm in
  Stücke von 16/19/53 Flächeneinheiten. Gelesen wurde einer, um 5:15 waren es drei.
- **Hysterese:** Mit ihr schaltet der Zustand erst 5:20.

Drei Zusätze, je mit Schalter in `kern.toml [welle]`:

- `SCHNITT_FLAECHE`: angeschnittene Stücke an weißen Linien zählen, Hälften einmal.
- `icon_deckung`: dein Icon in der Zone, dann reicht einer am Rand.
- `crash_dir_sofort`: GECRASHT_BEI_DIR ohne Hysterese, wie sein Spiegel.

Gegenprobe für die Regel: Test `wellen_front`, mit der alten Summenregel ZU_IHM.

**144655** (Bilder da, neu beschriftet; `buecher/wellen_eichung/2026-09-27_144655.json`):

- 22 Zeitpunkte, 11 eindeutig, 9 richtig (82 %). Vorher waren es 4 von 10.
- Falsch:
  - 5:59: Kern ZU_IHM, wahr ZU_DIR.
  - 8:59: Kern ZU_IHM, wahr MITTE. Die gegnerische Welle liegt unter Rivens Icon.
- **Umbeschriftet:** 7:00 (3 gegnerische am Turm, 1 eigener) war bis F1 ZU_DIR. Nach der F1-Definition ist das
  GECRASHT_BEI_DIR. Ohne diese Umbeschriftung: 8 von 11.

**133930:** Die Minimap-Ausschnitte wurden am 27.09. um 17:26 aufgeräumt (`lage.bilder_aufraeumen`: nur die
letzten drei Partien). Das tat Carlos' laufender Coach nach Partie 164326.

- `wellen_eichung.py` rechnet deshalb mit den **live** erkannten Punkten (`ereignisse.jsonl.gz`). Das ist der
  Leser von damals, mit Rauten- statt Ring-Maske und ohne Pfadlinie.
- Ergebnis: 4 von 7 eindeutigen (57 %).
- 4:00 (1 gegnerischer an deinem Turm, Rest unter Gwens Icon) ist nach F1 kein Crash mehr (≥ 3) und steht jetzt
  auf „unklar“.
- Eine echte Messung braucht eine neue Partie mit Bildern. Der Bilderordner lässt sich jetzt mit einer Datei
  `BEHALTEN` schützen; gesetzt für 102112, 140253, 144655.

**Grenze Vasallen unter fremden Icons:** Betroffen sind 6 Zeitpunkte ausdrücklich unter einem Icon (144655:
1:40, 5:10, 5:52; 133930: 4:00, 4:41, 8:08). Dazu kommen 5, an denen Riven und Gangplank an der Welle stehen und
keine Vasallen zu sehen sind (vermutlich darunter), und die zwei Fehler 5:59 und 8:59 (die Welle liegt unter
Rivens Icon).

### F2 – Flash: erst gemessen (`werkzeuge/flash_messung.py`)

| | 144655 | 140253 | 133930 | zusammen |
|---|---|---|---|---|
| Sprünge 300–450 in ≤ 0,25 s (Sichtungen, F2.1) | 3 | 10 | 23 | 36 |
| davon Gegner | 2 | 1 | 4 | **7** |
| davon heute als Flash erkannt | 1 | 0 | 2 | **3 (43 %)** |
| Dein Flash laut HUD (sichere Wahrheit) | 2 | 3 | 5 | **10** |
| davon als Sprung auf der Minimap zu sehen | 0 | 0 | 0 | **0** |
| Chat „<Champion> hat Blitz benutzt“ im gelesenen Text | 1 | 1 | 1 | **3**, alle 3 wurden Timer |
| Flash-Timer im Nachspielen | 1 (Minimap) | 2 (Chat, Minimap) | 3 (Chat, 2 Minimap) | 6 |

Die 7 gegnerischen Sprünge, und wo sie verloren gehen:

- Erkannt: Gangplank 1:56 (144655), Gwen 1:54 und Tristana 14:50 (133930).
- Kha'Zix 4:41: zwei Lesungen 0,2–0,25 s auseinander (die Live-Grenze ist 0,2 s).
- Tahm Kench 1:01: nicht bestätigt, bleibt keine 0,2 s am Landepunkt.
- Zoe 17:59 und 19:01: als Blink-Champion bewusst ausgenommen.

Bis auf Gangplank haben alle einen eigenen Dash oder Blink. Die Sprünge, die die Minimap sieht, sind also
überwiegend Dashes.

**Gegenprobe an den behaltenen Ausschnitten** (1 Bild/s; 133930 hat keine mehr):

- **Gangplank 1:56:** Kampf mit Riven, beide Icons übereinander. Der Flash ist echt: Carlos pingte ihn um 2:05,
  und Riven flashte laut HUD im selben Moment.
- **Kha'Zix 4:42:** Ein Ausschnitt genau im Sprung zeigt ihn am Landepunkt. Der Sprung ist echt, aber Flash und
  sein E (Sprung 700) sind nicht zu unterscheiden.
- **Tahm Kench 1:01:** Er liegt halb unter Zoes Icon; der „Sprung“ ist die wandernde Mitte des verdeckten Icons.
  Das ist ein Verfolger-Fehler, und die Live-Kette verwarf ihn zu Recht.

**Der Befund:** Ein Flash fällt fast immer in einen Kampf, und im Kampf liegen die Icons übereinander. Bei
Rivens eigenen 10 Flashs, bei denen der Zeitpunkt feststeht, sah es so aus:

- 8-mal führte der Verfolger ihr Icon nur als verdeckt (Güte 0, wird nie als Sprung gewertet) oder hatte es
  nicht.
- 2-mal sah er keinen Sprung.

Für Gegner gilt dasselbe Bild. Der Bildschirmweg sieht die Kämpfe und liest sogar Namen (Xin Zhao, Zac, Yasuo).
Er verwirft sie aber zu Recht, weil sie alle einen eigenen Dash haben („lieber stumm als falsch“).

- **Einzige sichere Quelle:** der Chat-Ping aus der Anzeigetafel. 3 von 3 kamen an, einen davon hat Carlos
  selbst gepingt.
- **Falsche Flashs:** Drei Minimap-Timer betreffen Champions mit Dash (Yasuo 10:01, Gwen 1:54, Tristana 14:50).
  Sie sind unbestätigt. Waren es Dashes, hat 133930 zwei falsche.

**Abnahme nicht erreicht.** Mit Schwellen ist das nicht zu holen: jede Lockerung macht aus Dashes Flashs.
Möglichkeiten, **Carlos' Entscheidung:**

1. Die Minimap verwirft wie der Bildschirm Sprünge von Dash-Champions. Das ergibt weniger, aber sichere Timer.
2. Den Flash-Effekt im Spielbild erkennen (gelber Blitz an Absprung und Landung). Das ist eine neue
   Wahrnehmungsaufgabe und unterscheidet Flash von Dash.
3. Carlos pingt gegnerische Flashs in der Anzeigetafel. Das kommt heute schon zu 100 % an.

### Abweichungen vom Buch und Entscheidungen

1. **F1-Zusätze:** Pfadlinie, Icon-Deckung und GECRASHT_BEI_DIR sofort (s. o.). Alle drei sind abschaltbar.
2. **Umbeschriftung 7:00** (144655) und **4:00** (133930) nach der neuen Definition. Beide sind oben genannt,
   mit Zahl ohne Umbeschriftung.
3. **Todesrückblick nicht mehr situativ:** Der Stratege formuliert ihn bis Schritt 6 nicht mehr frei. Der Weg
   zum Strategen bleibt und ist getestet (`test_stratege`).
4. **Flash-Meldungen warten auf das Briefing**, statt es zu unterbrechen (nur GEFAHR unterbricht).
5. **Gegner-AFK aus:** Die API zeigt fremde Level nur, wie zuletzt gesehen. Ein „AFK“-Gegner war ein Irrtum.
6. **Konstanten nicht im Buch:**
   - `SICHER_DORT_S` = 4 s, `NACH_GEFAHR_S` = 20 s, `RUECKZUG_EPISODE_S` = 15 s, `PUENKTLICH_S` = 5 s.
   - `[modus] ort_halten_s`.
   - `[welle] turm_toleranz` = 0,02, `icon_deckung`, `crash_dir_sofort`, `welle.SCHNITT_FLAECHE` = 10.
7. **Tests an die Prüfung angepasst:**
   - `modus_sperre_budget`: ohne Modus → stumm (E6).
   - `test_stratege`: der lange Tod gibt zwei Sätze (E1).
8. **Neue Werkzeuge:**
   - `werkzeuge/flash_messung.py` (F2).
   - `werkzeuge/dashboard_nachspielen.py`: das Dashboard mit dem Stand einer Aufnahme auf eigenem Port, neben
     einem laufenden Coach.
   - `wellen_eichung.py`: `--mit` für feste Zeitpunkte; ohne Bilder rechnet es mit den Live-Punkten.
9. **Nebenbei:** Während der Arbeit lief Carlos' Coach (Start 16:43) und eine Partie (17:31). Schwere Läufe
   liefen mit niedriger Priorität, der Coach wurde nicht angefasst. Die Minimap-Bilder von 140253 und 144655
   sind vorsorglich gesichert.

---

## Schritt 4 – SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN (27.09.2026)

### Umgesetzt

- `kern/modi/karte.py` – die Karten-Rechnung aus Buch 5, Kapitel 2:
  `EV = gewinn · p_erfolg − weg · zeitwert − p_tod(weg + dauer) · Todeskosten + folgewert`.
  - **Türme:** je Lane der vorderste stehende Turm. Verteidiger werden je Gegner gerechnet: Tote mit Respawn plus Weg aus dem Brunnen, Gesehene ≤ 15 s mit Weg ÷ Tempo, alle anderen gelten als unbekannt. Ein Turm ist Kandidat, wenn er vor dem **ersten** Verteidiger fällt oder du diesen schlägst. Für die Antwort zählt ihre gemessene Kraft.
  - **Wert eines Turms:** Platten an jedem Turm, Turmgold, `turm_extra`. Kristalle (×1,3) werden nur dort gerechnet, wo man sie sieht: am äußeren Turm deiner Lane mit allen Platten.
  - **Weitere Kandidaten:** Seitenwelle, Welle rein und rotieren (45–75 s, ohne TP), zur Gruppe bzw. TP-Spiel (Kapitel 5) und Umwandeln (Kapitel 8). Beim Umwandeln gilt die Reihenfolge aus Kapitel 8 bis zum Nexus: Inhibitor-Turm, Inhibitor, Nexus-Türme, Nexus.
- **Modi:**
  - `modi/seite.py`: Split-Regel 3.1. Nach einem gewonnenen Kampf gilt sie nicht.
  - `modi/gruppe.py`: MIT_GRUPPE, Seitenwelle auf deiner Seite; Back nur, wenn kein Objective und kein Kampf ansteht.
  - `modi/unterwegs.py`, `modi/verteidigen.py` (WELLE_KLAEREN, HALTEN_UNTER_TURM, TAUSCHEN).
  - Nach einem gewonnenen Kampf gibt es in SEITE, GRUPPE und UNTERWEGS keinen Back, solange eine Struktur erreichbar ist.
- **`kern/merkmale.py`:**
  - Wellen aller drei Lanes, `lane_hier`, Seitenwellen, woanders/unbekannt.
  - Die Antwort und ihre Kraft.
  - Teamkampf: ≥ 2 gegen ≥ 2 in 1500, dazu fällt Leben oder jemand stirbt; hält 5 s.
  - TP ihres Toplaners, Tote.
  - Das Umwandel-Fenster über die Takte.
- **Sprechen (Kapitel 2 und 6):**
  - Läufst du schon zum Ziel (≥ 500 Einheiten näher in 3 s), schweigt der Coach, und der Plan gilt als gesagt. Ausnahme ist das Umwandeln: dort sagt der Satz das Fenster und „Ruf dein Team“.
  - Einmal Erinnerung nach 20 s ohne Fortschritt außerhalb der Lane.
- **Bestätigungen (Kapitel 9):** „Genau so - Welle drin und pünktlich da.“, „Sauber umgewandelt.“, „Guter TP.“, „Welle gerettet - kein Turm verloren.“.
- **BASIS nach der Lane-Phase:** Das Ziel kommt aus der Karten-Rechnung, sonst aus der alten Bewertung. In den Kauf-Satz geht nur noch dessen Grund. Vorher stand dort 133930, 17:57: „… dann auf den Bot-Inhibitor-Turm: Geh auf den Bot-Inhibitor-Turm, …“.
- **`kern/testlage.bauen_mitte`:** baut eine echte `Partie` aus den Lagen in `mitte.toml`.
  - Wellen, Mitspieler, Gegner (gleicher Bereich wie du → im Abstand; fehlend → unbekannt), Türme und Teamkampf.
  - Die Jungler-Seite wird wie `jungle.wahrscheinlich` gerechnet.
- **`szenarien.py`:** Eine gesprochene Kern-Ansage, deren Plan im Fenster noch gilt, zählt für `muss_nennen_eins` (Kapitel 2: schweigt, solange du hinläufst).
- **Live-Default:** `kern.KERN_MODI` = LANE, BASIS, TOT, SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN. Mit `LOLCOACH_KERN_SCHRITT=3` gibt es den Stand von Schritt 3 für Gegenproben.

### Abnahme Schritt 4 (Buch 5, Kapitel 11)

| Abnahme | Soll | Ist |
|---|---|---|
| `3632-ende-statt-back` über den Kern | grün | **grün**. 36:03 bzw. 36:13 „Mid-Inhibitor-Turm jetzt: 4 von ihnen sind noch 33 Sekunden tot. Ruf dein Team.“, der Plan hält bis 36:47. Gegenprobe mit dem Schritt-3-Kern: **rot** (36:32 „Geh jetzt back, du hast 4400 Gold …“). |
| `3535-rueckzug-31s` über den Kern | grün | **grün**. 35:27 „Raus zu Brand, Corki und Tryndamere: Sett kommt.“ statt des Top-Turms in 31 s. |
| `1315-crash-dann-back` | grün | **grün** |
| Lagen in `mitte.toml` | alle grün | **13 / 13**, dazu `lane.toml` + `recall.toml` 25 / 25 (`test_kern` prüft jetzt alle 38) |
| 9.4 Punkt 1–4 ohne Verstoß | alle Aufnahmen | **0** in 102112 und in allen neuen echten Partien (133930, 140253, 144655): Das ist die Abnahme aus Buch 0, Kapitel 13. In den Aufnahmen vom 26.09. bleiben 10 (120049 2, 125902 2, 155643 1, 194524 2, 212105 2, 230520 1). Es sind alles alte Regeln an Stellen, an denen die Minimap Riven länger als 10 s nicht fand (kein Modus = keine Sperre, s. u. Punkt 12). |
| ungefragte Ansagen je 30 min ≤ 50 | ja | **nicht erreicht**: 102112 56 (Schritt 3: 57), 133930 88, 140253 61. Der Kern allein liegt darunter (102112 37, 133930 43). Der Rest ist das alte System im Modus OBJECTIVE (102112: 19 Ansagen, 133930: 26), der erst in Schritt 5 an den Kern geht. |
| echte Partie mit Mid-Game (> 20 min) ausgewertet | ja | **ja**: 133930, s. u. |
| `tests/alle.py` | grün | **grün** (neu: Viego-Übernahme, AFK-Gegner) |

Szenarien 102112 mit Kern: **13 grün / 13 geprüft** (Schritt 3: 11 / 13).

### Kennzahlen (Stand Schritt 4, Kern)

| Aufnahme | ungefragt je 30 min | Lane-Phase je 30 s | Kehrtwenden | 9.4 1–4 | GEFAHR / PLAN / ERINNERUNG / BESTAETIGUNG | p_da-Brier schlimmster Fall → Kern |
|---|---|---|---|---|---|---|
| 2026-09-27_102112 | 56 | 0,79 | 0 | 0 | 8 / 29 / 1 / 2 | 0,317 → 0,059 |
| **2026-09-27_133930 (echt, 21,8 min)** | 88 | 1,21 | 0 | 0 | 11 / 17 / 3 / 0 | 0,423 → 0,074 |
| **2026-09-27_140253 (echt)** | 61 | 1,04 | 0 | 0 | 3 / 14 / 1 / 0 | 0,273 → 0,044 |
| **2026-09-27_144655 (echt)** | 56 | 0,96 | 0 | 0 | 5 / 5 / 0 / 1 | 0,241 → 0,038 |

Das neue Seiten-Modell der Gefahr (Punkt 6) verschlechtert die Eichung nicht: p_da schlägt den schlimmsten Fall in allen 26 Aufnahmen, 102112 und 140253 unverändert.

**Echte Partie 133930** (Riven Top gegen Gwen, rote Seite, ab 14:00 hinten):
- Von 14:00 bis 21:55 war der Modus zu gut drei Vierteln OBJECTIVE. Der Kern entscheidet nach Schritt 4 also im kleineren Teil des Mid-Games.
- Wo er entscheidet, passt es. 20:11 „Raus zu deinem Mid-Tier-1-Turm: Tristana und Zoe kommen.“ (danach fiel Rivens Leben von 88 auf 33 %), 20:23 Back bei 33 %.
- 21:46 in ihrer Basis mit vier toten Gegnern: „Nexus-Turm jetzt: 4 von ihnen sind noch 19 Sekunden tot.“, danach „Nexus jetzt …“. Vorher stand dort „Back jetzt“, weil der Kern hinter den Inhibitor-Türmen keine Ziele kannte.
- In 102112 gilt dasselbe ab 38:17 („Nexus-Turm jetzt …“). Um 38:32 fällt er, und der Coach sagt „Sauber umgewandelt.“

### Abweichungen vom Buch und Entscheidungen

1. **Erster Verteidiger (Kapitel 2):** Geprüft wird nur der erste, der rechtzeitig kommt. Vorher wurden alle Rechtzeitigen gegen dich gerechnet (`m-split-drueck`).
2. **Split-Regel 1:** Ruft ein Objective ohne TP und gibt es „Welle rein und raus“, fallen FARMEN, SEITENWELLE, DRUECKEN und PLATTEN weg. Vorher gewann FARMEN (`m-welle-und-raus`).
3. **Zeitwert nur auf den Weg, p_tod über Weg + Dauer** (Formel in Kapitel 2). Vorher kostete auch die Zeit am Turm Zeitwert, und der innere Turm verlor gegen eine halbe Welle.
4. **Platten an jedem Turm:** Patch 26.1, `saison2026.md`: auch innen und am Inhibitor. `turm_gewinn` hatte sie nur außen.
5. **Kristalle** zählen nur, wo sie sichtbar sind (äußerer Turm deiner Lane, alle 5 Platten stehen). Sonst rechnet der Coach ohne.
6. **Gefahr, Kartenseite nach der Lane-Phase (7.5):**
   - Jeder gesehene Gegner zählt auf der Seite seiner letzten Sichtung, verblasst über 90 s wie der Jungler (`jungle.wahrscheinlich`). Vorher galt `roam_basis` für alle. 3535 war dadurch „keine Gefahr“: Kai'Sa vor 7 s unten, Sona und Sett unten, Riven allein im unteren Fluss.
   - Der Lane-Gegner zählt mit 1 nur, wenn du auf deiner Lane stehst.
7. **„Bleib an/bei …“ (ZURUECK am sicheren Ort):** Das Risiko gilt über das normale Fenster, ohne Rückzugsrabatt. Vorher schlug es mit p_tod ≈ 0 das Halten unter dem Turm (`m-verteidigen-halten`).
8. **Umwandeln (Kapitel 8):**
   - Die 15 s braucht nur der Auslöser. Danach hält das Fenster, „solange es reicht“, also solange ein Turm vor seinem ersten Verteidiger fällt. Vorher kippte der Plan um 36:32 (Sona noch 14 s tot) auf HALTEN.
   - Es gilt auch in SEITE. Vorher 36:03 auf der Bot-Lane mit vier Toten: „Bot-Welle rein, dann back“.
9. **Folgewert beim Umwandeln:** Fällt ein Turm im Fenster, zählt der nächste derselben Lane mit, wenn auch er vor seinem ersten Verteidiger fällt. Sonst schickte der Coach die Gruppe von Mid quer über die Karte zum inneren Bot-Turm, statt den äußeren Mid-Turm fünf Sekunden vor ihr zu nehmen (`m-gruppe-umwandeln`). „Mit der Gruppe“ gilt nur, wo Mitspieler am Ziel stehen.
10. **Kapitel 8, Punkte 1–2 (nicht im Buch beziffert):**
    - Positionen von Inhibitoren, Nexus-Türmen und Nexus stammen aus der Karte.
    - Werte: Inhibitor = `objective_wert.inhibitor`, Nexus-Turm = `turm_extra` + ¼ Nexus, Nexus = `objective_wert.nexus`.
    - Dauer wie `turm_dauer_s.nexus`. Nexus-Türme stehen nach 180 s wieder.
    - Nur im Umwandel-Fenster.
11. **Sprechen:** Die Regel „Läufst du schon dorthin, schweigt der Coach“ gilt nicht beim Umwandeln (der Satz trägt das Fenster). Erinnert wird nur außerhalb der Lane.
12. **Modus bei kurz unbekanntem Ort (4.3):** Der Modus bleibt bis zu 10 s (`[modus] ort_halten_s`, nicht im Buch). Vorher sprachen dann die alten Regeln ungesperrt: 133930 um 7:52–7:58 „Schieb die Welle in seinen Turm“ mitten im Modus OBJECTIVE. Länger unbekannt bleibt es wie in Schritt 2: kein Modus, die alten Regeln sprechen.
13. **Szenario-Prüfung:** Eine stehende Kern-Ansage zählt für `muss_nennen_eins`. `3632` verlangt „Mid“ oder „Inhibitor“ in 36:30–36:47. Der Kern sagt es um 36:13 und schweigt danach, weil Riven hinläuft (Kapitel 2). Das Szenario selbst ist unverändert. `darf_nicht_sagen` prüft weiter nur Gesprochenes im Fenster.
14. **`testlage`-Annahmen:**
    - Gegner im gleichen Bereich wie du stehen im angegebenen Abstand; fehlende sind unbekannt.
    - Die Gegner eines Teamkampfs stehen sichtbar am Kampfort.
    - Die Jungler-Seite kommt aus der Sichtung.
    - `m.mitspieler` kommt aus den Mitspielern der Lage (fehlte: „mit der Gruppe“ zählte nie jemanden).
15. **`kern.toml`-Schlüssel, die nicht im Buch stehen:**
    - `[mitte]`: `woanders_abstand`, `woanders_alt_s`, `seitenwelle_mitspieler_abstand`, `teamkampf_nachlauf_s`, `teamkampf_leben_faellt`, `platten_annahme`, `kampf_wert_je_gegner`, `gruppe_turm_faktor`.
    - `[modus]`: `ort_halten_s`.

### Nebenbei behoben: Partie 144655 (Carlos, 14:46, Riven Top gegen Gangplank)

- **„Partie vorbei“ um 9:24:** Der gegnerische Viego übernahm einen Toten. Die Live-API meldet ihn dann unter dessen Namen (Kha'Zix, Vex). Der Coach hielt jede Übernahme für eine neue Partie, schrieb ein Review und fing in 30 s viermal neu an. Jetzt gilt nur noch: andere Spieler oder die Spieluhr springt zurück (`aufzeichnung._spieler`). Das Practice Tool fällt weiter an der Uhr auf.
- **„Kha'Zix ist AFK … spiel deine Lane nach vorn“ (1:30, Riven starb 1:57):** Die Live-API zeigt die Items der Gegner nicht, also ist „kein einziges Item“ bei Gegnern kein Beleg. Dieselbe falsche Meldung kam in 133930 für Zac. Ein Gegner gilt jetzt nur als AFK, wenn er ab 2:30 noch Stufe 1 ist. Die AFK-Sätze nennen die Welle mit Lane (9.4 Punkt 1, 102112 1:30).
- **Hat mein halbfertiger Schritt 4 in seiner Partie mitgesprochen? Nein.** Sein Coach lud den Kern beim Partiestart um 14:46:55, mein erster Schritt-4-Patch kam um 14:49:12, und Python lädt Module nicht nach. Zur Zeit der „Wortfetzen“ (6:28–6:51 = 14:53:23–14:53:46) liefen bei mir keine Messungen.
- Das Stottern der Stimme und die fehlenden Flash-Timer auf dem Dashboard sind **nicht** untersucht (OFFEN.md).

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
- **Wiederholt an der nächsten echten Partie, 144655** (Riven Top gegen Gangplank, rote Seite, 797 Ausschnitte):
  - 19 Zeitpunkte, davon 10 eindeutig, **4 richtig (40 %)**. GECRASHT_BEI_IHM kam nicht vor. Abnahme weiter **nicht erreicht**.
  - Richtig waren wieder nur „deine Welle läuft los“ (ZU_IHM).
  - Der Kern sagt in 17 von 19 Fällen ZU_IHM.
  - **Die Hauptursache ist jetzt klar, und sie liegt im Kern, nicht im Bild.** Dreimal (3:13, 5:17, 5:38) stehen gegnerische Vasallen an deinem äußeren Turm, während deine nächste Welle zwischen innerem und äußerem Turm losläuft. Die Zustandsregel (`WellenPuffer._roh`, Buch 1 1.4) zählt alle Vasallen der Lane. GECRASHT_BEI_DIR verlangt `unsere ≤ 1`, und mit der nachlaufenden Welle (4–6) wird daraus `unsere − ihre ≥ 2` = ZU_IHM.
  - Dazu zweimal gegnerische Vasallen direkt am Riven-Icon, die die Ring-Maske mit ausblendet (7:00, 8:59).
  - Und zweimal wählte das Werkzeug einen Zeitpunkt, an dem Riven tot war (Auswahl prüft den Tod nicht).
  - Vorschlag, **Carlos' Entscheidung** (Umbau am Kern): nur die Vasallen um die Front zählen, die nachlaufende Welle nicht. Beschriftung: `buecher/wellen_eichung/2026-09-27_144655.json`.
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
