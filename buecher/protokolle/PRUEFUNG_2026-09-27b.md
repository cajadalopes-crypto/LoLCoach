# Protokoll-Prüfung 27.09.2026, zweite Runde (Claude, Chat)

Geprüft wurden die fünf neuen Protokolle nach der Qualitätsrunde 1 (`0c87425`) und der Abschnitt „Qualitätsrunde 1“ in
`messungen.md`. Dazu eine Stichprobe der Aufnahmen.

**Urteil: deutlich besser, aber noch nicht freigegeben.**

**Was jetzt trägt:**

- Kein Hin und Her mehr beim Rückzug: Fassungswechsel und Kehrtwenden sind in allen Partien 0.
- Der Todesrückblick ist brauchbar:
  - 140253, 8:34: „Du bist mit einem Drittel Leben an deinem Turm gegen Yasuo geblieben. Mit so wenig Leben kein
    Kampf: erst back.“
  - 133930, 3:41: „Gank von Zac. Fehlt Zac länger als 20 Sekunden: bleib hinter deiner Welle.“
- Eine verlorene Lane bekommt einen Plan.
- Die Uhrzeiten sind hörbar.
- Der Nexus wird angesagt, wenn er fällt (133930, 21:48).

Übrig sind die Punkte G1–G7 und danach Schritt 5.

---

## Entscheidungen zu den offenen Fragen aus der Qualitätsrunde 1

1. **`0843` – die Daten haben recht, das Szenario war falsch.** Mein Fehler: Ich hatte „Brand und Yasuo kommen“ für
   den Tod genommen. Das Szenario bekommt:
   - `muss_nennen_eins = ["Yasuo"]`
   - `darf_nicht_sagen += ["Brand"]`

   Der heutige Satz ist richtig so.
2. **F1-Zusätze** (Pfadlinie, Icon-Deckung, `crash_dir_sofort`): **alle drei bleiben an.**
   - Bestätigt werden sie an den zwei neuen echten Partien 164326 und 173159. Beide laufen im Modus CLASSIC, Riven Top,
     42 bzw. 37 Minuten, mit Bildern (`BEHALTEN` ist gesetzt).
   - Soll dort: ≥ 8 von 10 eindeutigen richtig.
   - Bis das erreicht ist, gilt Buch 6, Kapitel 6: Prio nur mit `GECRASHT_BEI_IHM` oder totem bzw. abwesendem
     Lane-Gegner.
3. **F2 Flash: Weg 1 und Weg 3 jetzt, Weg 2 später.**
   - **Weg 1:** Die Minimap wertet keine Sprünge von Champions mit eigenem Dash oder Blink.
     - Die Liste kommt nach `wissen/` (mit Stand), aus den Fähigkeiten in Data Dragon, von Hand geprüft.
     - Lieber weniger Timer als falsche.
   - **Weg 3:** Carlos pingt Flashs über die Anzeigetafel (Tab, Klick auf den Flash des Gegners). Das kommt heute schon
     zu 100 % an. Der Coach sagt dazu nichts, das Dashboard zeigt den Timer.
   - **Weg 2** (der Flash-Effekt im Spielbild) kommt nach `OFFEN.md`, nach Schritt 6.
4. **Ansagen über 50 je 30 Minuten:** Das ist erwartet. Es sind die alten Regeln in OBJECTIVE und KAMPF, und sie
   verschwinden mit Schritt 5. Nach Schritt 5 ist das Ziel ≤ 45.

## G1. Der Schutzplan klingt wie eine Schallplatte

Der Satz ist gut, aber er kommt zu oft und ist zu lang:

- **144655:** acht Mal in neun Minuten (1:37, 2:14, 3:34, 5:39, 6:10, 7:10, 8:15, 9:03), dazu 10:03 und 10:15 in
  145702. Das sind jeweils 22 Wörter, also mehr als 18.
- **Das Item springt:** Caulfields Kriegshammer → Axiombogen → Caulfields → Brutalisierer → Axiombogen → Brutalisierer.
- **140253** und **133930** zeigen dasselbe Muster.

**Soll:**

1. **Die lange Fassung** (≤ 18 Wörter) kommt einmal je Lane-Verlust-Episode. Die Episode endet, wenn die Kraft wieder
   ≥ 0 ist oder das Bauteil gekauft wurde.
   - Beispiel: „Gangplank ist vorn: Welle zu deinem Turm ziehen, dort farmen, kein Trade bis Caulfields.“
2. **Die kurze Fassung** (≤ 8 Wörter) kommt nach Tod oder Basis, höchstens einmal je `schutz_erinnern_s` (180 s).
   - Beispiel: „Weiter: am Turm farmen, kein Trade.“
3. **Das Item im Satz steht fest.** Es ist das nächste Bauteil aus dem Kaufplan zu Beginn der Episode und wechselt
   erst mit dem Kauf. Die Items wechseln heute, weil der Kaufplan je Takt neu wählt. Der Grund dafür gehört in
   messungen.md.

**Szenarien:**

| id | Aufnahme | fenster | Prüfung |
|---|---|---|---|
| `0137-schutzplan-sparsam` | 144655 | 1:30–9:10 | höchstens 3 Sätze mit „ist vorn“ oder „am Turm farmen“ (neuer Schlüssel `text_max = {"ist vorn|am Turm farmen" = 3}` oder gleichwertig); `max_woerter` 18 |
| `0238-schutzplan-sparsam` | 140253 | 2:30–4:00 | höchstens 1 Satz mit „ist vorn“ |

## G2. WOHIN schickt in den Tod – noch viermal

E2 ist nicht gelöst. Der Kern **rechnet** die Gefahr bei Ankunft, sagt das Ziel aber trotzdem, auch als Rückfall:

| Aufnahme | Zeit | Satz | p_tod |
|---|---|---|---|
| 144655 | 5:06 | „Lauf direkt nach Top, sonst verpasst du die Welle.“ | 0,67 |
| 140253 | 10:25 | „geh zur Mid-Welle: dort nimmt sie sonst niemand.“ | 0,73 |
| 133930 | 12:30 | „geh zur Top-Welle: dort nimmt sie sonst niemand.“ | 0,79 |
| 133930 | 15:16 | dasselbe | 0,67 |

**Soll:**

1. Ein WOHIN-Ziel mit `p_tod_am ≥ wohin_p_tod_max` (0,3) wird **nicht** gesagt.
2. Gibt es ein sichereres Ziel, gilt das, in dieser Reihenfolge:
   - eigene Gruppe mit ≥ 2,
   - eigener Turm auf der Seite des Ziels, dann mit Schutz-Zusatz: „Zurück nach Top, bleib am Turm: Kha'Zix war zuletzt
     oben.“
3. „Lauf direkt“ und „sonst verpasst du …“ gibt es nur bei `p_tod_am < 0,15`.
4. Gibt es kein Ziel unter der Schwelle: „Warte am Turm auf dein Team: vier von ihnen sind oben.“ Das Ziel ist der
   eigene innere Turm auf der Seite, auf der die wenigsten Gegner zuletzt gesehen wurden.
5. **Plausibilität:**
   - In messungen.md steht für jeden der vier Fälle, welche Gegner wie viel zu p_tod beitragen.
   - Ist ein Wert unplausibel, zum Beispiel 0,67 für den Weg zum eigenen äußeren Turm um 5:06, wird die Ursache
     behoben, nicht nur die Schwelle.

**Szenarien:** `0506-wohin-sicher` (144655), `1025-wohin-nicht-in-den-tod` (besteht; muss jetzt auch ohne „Larven“
ein sicheres Ziel nennen), `1230-wohin-sicher` und `1516-wohin-sicher` (133930). Prüfung jeweils:

- darf_nicht_sagen „nimmt sie sonst niemand“, „Lauf direkt“
- `muss_ziel`

## G3. 140253, 3:49–4:27: drei Pläne in 38 Sekunden

- **3:49:** „Mid-Welle rein, dann back: 1050 Gold für Axiombogen …“ (EV +339)
- **4:01:** „Stapel die Mid-Welle bis zur Kanone um 4 50 …“. STAPELN hat EV +171, WELLE_REIN_UND_BACK +275 steht
  daneben. **B gilt hier nicht.**
- **4:27:** „Mid-Welle rein, dann zum Drachen …“

Danach um 4:43 steht Riven mit 19 % im Fluss.

**Soll:**

- Herausfinden, warum der Test `neuer_plan_ist_der_beste` diesen Fall nicht trifft. Möglich wären ein Plan-Schritt,
  ein Wechsel über ERINNERUNG oder ein Sonderweg für STAPELN. Die Ursache gehört in messungen.md.
- Die Ursache wird behoben.
- Szenario `0349-ein-plan` (140253, 3:45–4:35): höchstens ein Planwechsel ohne Ereignis; um 4:01 kein STAPELN.

## G4. Bestätigungen zur falschen Zeit

| Aufnahme | Zeit | Satz | Problem |
|---|---|---|---|
| 133930 | 7:01 | „Gut raus – da war er.“ | Modus KAMPF |
| 144655 | 4:39 | „Gut raus – da war er.“ | 13 s später stand Riven auf 19 % |
| 140253 | 6:11 | „… da war er.“ | Es kamen drei („da waren sie“) |

**Soll:**

- In KAMPF gibt es nie eine Bestätigung.
- „Gut raus“ nur, wenn das Leben in den 10 s nach dem Rückzug-Satz um < 20 Punkte fiel **und** der sichere Ort
  erreicht ist.
- Einzahl und Mehrzahl stimmen.

**Szenarien:** `0701-keine-bestaetigung-im-kampf` (133930) und `0439-kein-gut-raus` (144655), jeweils darf_nicht_sagen
„Gut raus“.

## G5. Rückblick: der zweite Satz muss zum ersten passen

133930, 14:57: „Du bist **mit vollem Leben** an deinem Turm geblieben, Tristana und Zoe zusammen töten dich dort. Bei
zwei Gegnern: **back**, bevor sie in Reichweite sind.“ Mit vollem Leben ist Back die falsche Lehre.

**Soll:** Satz 2 richtet sich nach dem Leben beim Einstieg.

- **≥ 60 %:** „Bei zwei Gegnern: hinter den Turm oder zu deinem Team, bevor sie in Reichweite sind.“
- **< 60 %:** Back.

**Szenario:** `1457-rueckblick-passt` (133930), darf_nicht_sagen „back“.

## G6. Zwei der Partien sind Swiftplay, nicht Summoner's Rift Ranked

`gameData.gameMode` lautet für **133930 und 140253 `SWIFTPLAY`**, für 102112, 144655, 164326 und 173159 `CLASSIC`.

Swiftplay startet anders: 1400 Gold und Level 3 um 0:00 (140253: alle Gegner springen bei 0:00 von 1 auf 3). Auch
Wellen, Objectives und Gold laufen vermutlich anders. Der Coach sagt dort aber Zeiten aus `saison2026.md`, zum Beispiel
„Drache um 5 00“ oder „Larven um 8 00“.

**Soll:**

1. Die Swiftplay-Regeln für 2026 nachschlagen (Wiki, Patchnotes; mit Quelle und Stand). Gemeint sind Startgold,
   Startlevel, Wellen, Objective-Zeiten und Gold/XP.
2. Die Regeln kommen als eigener Abschnitt nach `saison2026.md`, dazu ein Profil in `mechanik.toml` bzw. `kern.toml`,
   das der Coach nach `gameMode` lädt.
3. Solange ein Wert für Swiftplay nicht belegt ist, sagt der Coach dort **keine** Spawn-Zeiten.
4. Kopf jedes Protokolls und jeder Szenario-Datei:
   - Das Protokoll nennt den Modus.
   - Die Szenario-Datei nennt `spielmodus = "SWIFTPLAY"`.
   - Die Eichungen (Buch 6, 10; Buch 7, 3.3; Welle) weisen die Modi getrennt aus.
5. Die Szenarien aus 133930 und 140253 werden darauf geprüft, ob eine Zahl darin nur für CLASSIC gilt. Betroffene
   Szenarien werden korrigiert und in messungen.md genannt.

## G7. Veraltete Gegner-Level – Nachtrag zu Buch 7

Claude Codes Befund stimmt: Kha'Zix springt in 144655 um 3:34 von 1 auf 4, Brand in 140253 von 3 auf 5 auf 7. Buch 7
ist korrigiert (Nebenbefund, Kapitel 2 und 3.2: Schätzung für lange nicht gesehene Gegner). Umgesetzt wird das mit
Schritt 5.

---

## Reihenfolge ab jetzt

1. Entscheidungen 1–3 umsetzen.
2. G1–G6 umsetzen, jeweils zuerst das Szenario rot. Commit.
3. Schritt 5 nach Buch 6 und Buch 7 (beide Bücher liegen uncommittet in `buecher/`). Commit.
4. Neue Protokolle für 102112, 133930, 140253, 144655, 145702 **und die neuen 164326 und 173159**. F1-Eichung an
   164326 und 173159.
5. Nächste Prüfung durch mich. Freigabe erst, wenn G1–G7 und Schritt 5 in allen Protokollen halten.
