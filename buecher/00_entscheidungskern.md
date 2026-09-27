# Buch 0 – Der Entscheidungskern

Stand 27.09.2026 · für Claude Code, das den LoLCoach umbaut · Grundlage: Code-Stand vom 27.09.2026
und die Aufnahme `2026-09-27_102112` (Riven gegen Sett), mit dem heutigen Code nachgespielt.

Dieses Buch sagt, **wie der Coach entscheidet**. Die folgenden Bücher (Kapitel 15) sagen, **was er über
League wissen muss**. Ohne dieses Buch würde jedes weitere Buch nur neue Alarme erzeugen.

---

## 0. So benutzt du dieses Buch (Claude Code)

- Lies es ganz, bevor du etwas änderst. Die harten Grenzen aus `CLAUDE.md` gelten unverändert.
- Arbeite den Umbauplan (Kapitel 13) **Schritt für Schritt** ab. Pro Schritt:
  1. umsetzen,
  2. `python tests/alle.py` und `python werkzeuge/szenarien.py` laufen lassen,
  3. die Abnahme-Zahlen messen,
  4. das Ergebnis in `buecher/messungen.md` eintragen,
  5. committen,
  6. Carlos in drei, vier Sätzen sagen, was sich für ihn ändert und was er testen soll.

  Nie zwei Schritte auf einmal.
- Widerspricht die Wirklichkeit (Aufnahme, API, Bild) diesem Buch, gilt die Wirklichkeit. Trag den
  Widerspruch in `buecher/messungen.md` unter „Abweichungen vom Buch“ ein und entscheide dann. Umgeh das
  Buch nicht stillschweigend.
- Mit **Startwert** markierte Zahlen sind Schätzungen. Sie gehören nach `wissen/kern.toml`, nie in den Code.
  Jeder Wert trägt seinen `stand` und wird an Szenarien kalibriert.
- **Neue Arbeitsweise, ab sofort:** Eine Beschwerde von Carlos wird zuerst ein Szenario (Kapitel 12). Erst
  danach folgt eine Änderung am Modell, die dieses Szenario grün macht, ohne andere rot zu machen. Keine
  Einzelflicken mehr in Form von „Live 27.09.: …“-Sonderfällen an einzelnen Regeln. Diese Arbeitsweise
  gehört in Schritt 1 auch nach `CLAUDE.md`.

---

## 1. Befund

### 1.1 Was gut ist und bleibt

Die Wahrnehmung ist sorgfältig gebaut und gemessen. Sie bleibt, wie sie ist:

- `liveapi`, `zustand`, `aufzeichnung` (Schnappschuss als reine Funktion, Nachspielen)
- `lage`, `minimap`, `hud`, `welle`, `platten`, `zauber`, `texterkennung`, `lebensbalken`
  - Minimap: 0 Verwechslungen bei der Sichtprobe
  - Lebensbalken: 90 % der Werte auf ±2 % genau
- `jungle` (Jungler-Tracker; Seitenprognose mit Brier 0,183 gegen 0,250 beim Raten)
- `combo`, `faehigkeiten`, `rechnung`, `kaufplan`, `bewertung.kill_gold`, `kopfgeld`, `todeszeit`
- `bewertung.bewerte` als **Datenschicht**
- `stimme`, `sprache`, das Dashboard und die Review-Oberfläche

Kurz: Der Coach **sieht** genug. Er **entscheidet** schlecht.

### 1.2 Was falsch läuft – gemessen

Die Aufnahme 102112 wurde mit dem heutigen Code nachgespielt (`regeln.Regelwerk` + `sprechplan.Sprechplan`,
stumm, wie in `werkzeuge/sinnpruefung.py`):

| Messgröße | Wert | Ziel |
|---|---|---|
| ungefragte Ansagen | **112** in ~30,5 Minuten mit Daten | ≤ 45 je 30 min |
| Ankunftswarnungen „… bei dir“ | 22 | nur, wenn sie deine Handlung ändern |
| Ansagen zu Flash (Schlüssel `zauber`, `ohneflash`, `flashzurueck`; ein Textfilter auf „Flash“ findet 29) | 23 | Dashboard; gesprochen nur, wenn sie den Plan ändern |
| Kehrtwenden (vor ↔ zurück in ≤ 30 s) | 8 | 0 ohne neues Ereignis |

Beispiele aus derselben Partie. Die Lage stammt jeweils aus dem Nachspielen.

- **5:17** – Riven hat 37 % Leben, kein Flash. Fiddlesticks wurde vor 30 s im oberen Fluss gesehen, Sett ist
  seit eben tot.
  - Ansage: „Schieb die Welle in seinen Turm und nimm die Platte mit.“
  - Um 5:37 kommt Fiddlesticks.
- **8:56–9:24** – Sett, Galio und Fiddlesticks laufen zusammen auf Riven zu. Die Ansagen in dieser Zeit:
  - „nimm den Kampf an“
  - „Halte deine Stellung“
  - „Geh zurück“
  - „Bleib an deiner Welle, Fiddlesticks und Galio zusammen sind schwächer als du“
- **25:22** – Der Drache lebt, Riven ist 17 s von ihm entfernt, zwei Mitspieler stehen in der Basis.
  - Ansage: „Nehmt jetzt Baron Nashor, ihr seid 5 gegen 2.“
- **35:35** – Riven steht an der Drachengrube.
  - Ansage: „Geh jetzt zurück zu deinem Top-Tier-3-Turm, das sind 31 Sekunden.“
- **36:32** – Vier Gegner sind seit 14–20 s tot. Vom gegnerischen Team steht nur noch der Mid-Inhibitor-Turm,
  Riven ist 10 s davon entfernt.
  - Ansage: „Geh jetzt back, du hast 4400 Gold.“
  - Das war das Fenster, in dem das Spiel zu Ende geht.
- **Live, Antworten über Claude:**
  - 26:01: „Geh sofort auf Sett drauf.“ Sett war 10.700 Einheiten entfernt.
  - 30:04–31:59: Riven steht in der Basis, die Antworten lauten nur „schieb die Welle in seinen Turm“.
- **Datenlücke:** Die Aufnahme hat von **15:55 bis 24:24** keinen Schnappschuss. Der Coach war 8,5 Minuten
  blind und stumm, genau in der Zeit, in der 17:19–21:46 sechs Objectives fielen. Das Review schreibt
  trotzdem bei jedem dieser Ereignisse „Du warst oben“, weil es die letzte bekannte Position einfriert.

### 1.3 Die Ursachen

1. **Kein Modus.** `Regelwerk.pruefe` lässt jeden Takt 24 Regeln laufen, egal ob Carlos auf der Lane, in
   der Basis, an der Drachengrube oder mitten im Kampf steht. Jede Regel kennt nur ihren Auslöser. Welche
   Frage in dieser Lage überhaupt zählt, weiß keine.
2. **Auswahl nach Vorrang, kein Plan.** `Sprechplan.takt` wählt `max(prio, gefahr, zeit)`. Es gewinnt der
   lauteste Alarm, nicht der wertvollste Rat. Ein Plan, an dem der Coach festhält, existiert nicht.
   `Entscheider` ist nur eine der 24 Regeln (`_plan`). Daraus entstehen die Kehrtwenden.
3. **Reflexe mit Flicken.** Fast jede Regel trägt Sonderfälle mit „Live …“-Kommentar: Teamruf-Sperre,
   Widerspruchswächter, Themen-Sperre, Rückzugs-Sperre, „Ach nee“. Jeder Flicken behandelt ein Symptom und
   erzeugt den nächsten Randfall. Der Systemprompt für Claude wächst auf dieselbe Weise.
4. **Schlimmster Fall statt Wahrscheinlichkeit.** Die Ankunft rechnet „frühestens“ (`GegnerLage.ankunft`).
   Jeder Gegner, der gerade nicht zu sehen ist, wird zur Gefahr. Das Ergebnis sind 22 „… bei dir“ und ein
   Coach, der gleichzeitig ängstlich und leichtsinnig ist. Die Jungler-Seitenprognose
   (`jungle.wahrscheinlich`) existiert und ist geeicht, geht aber nicht als Wahrscheinlichkeit in die
   Entscheidung ein.
5. **Zwei konkrete Objective-Fehler.**
   - `regeln._lebende_objectives` liefert immer die Reihenfolge `("baron", "drache", "herold", "larven")`.
     Damit ist `objs[0]` jedes Mal Baron, sobald er lebt, egal wo Carlos und sein Team stehen.
   - `komponist.zahlen` prüft danach `b.zum_objective`. Das ist die Laufzeit zu `b.objective`, dem
     *nächsten* Objective aus `bewertung.naechstes_objective` (um 25:22 der Drache), nicht die Laufzeit
     zu Baron.
6. **Niemand misst den Rat.** Gemessen werden Minimap, Balken, Kill-Gold und Stimm-Latenz. Einen Test der
   Form „in dieser Lage wäre der richtige Call X“ gibt es nicht. `ansagen_pruefen` findet Widersprüche,
   `sinnpruefung` findet unpassende Orte. Ob der Rat gut ist, prüft keines von beiden.
7. **Claude improvisiert.** Fragen gehen mit bis zu 80 Zeilen Rohlage an Claude, dazu „Deine letzten
   Ansagen“. Claude beißt sich an alten Ansagen fest („schieb die Welle in seinen Turm“, zehn Minuten lang)
   und erfindet Spielfakten, etwa das Verkaufen eines Schmuckstücks oder „Setts Q setzt Marker“.
8. **Bots als Datengrundlage.** 16 von 18 Aufnahmen sind Bot-Partien. Die zwei echten Partien sind 9 und
   1 Minute lang. Alles, was „rechnet“, ist gegen Bots geeicht. Gegen Bots stimmt „Nimm den Kampf an,
   Fiddlesticks ist 5 Level unter dir“, gegen Menschen nicht.

### 1.4 Warum das Reasoning-Dokument nicht gereicht hat

`Reasoning/LoL Reasoning.txt` listet über 300 **Eingänge** einer Entscheidung. Die Datei endet mit einer
Kette:

> Zustand → Welle → Prio → Tempo → Information → Gegner-Vorhersage → Aktionen → Gegenantwort → Erwartungswert

`FAKTOREN.md` hat die Eingänge verdrahtet. Die Kette selbst wurde nie gebaut:

- welche Frage in welcher Lage zählt,
- welche Handlungen zur Wahl stehen,
- wie man zwischen ihnen wählt und dabei bleibt.

Faktoren sind Zutaten, kein Rezept. Dieses Buch baut das Rezept. Die sechs Schlussfragen der Datei werden
Pflichtfelder jeder Handlung (Kapitel 7.6):

> Wer ist stärker? Wer ist zuerst da? Was sehen wir nicht? Welche Welle verlieren wir? Was bekommt der
> Gegner? Was gewinnen wir nach dem Play?

---

## 2. Leitsätze

1. **Eine Entscheidung, eine Stimme.** Je Takt gibt es genau einen gültigen Plan. Alles Gesagte folgt aus
   ihm oder ändert ihn.
2. **Erst der Modus, dann die Frage.** In der Basis zählt nicht, was Sett auf der Lane tut.
3. **Jeder Rat hat ein konkretes Ziel**: Lane und Turm, Objective, Gegner mit Namen oder ein Ort. Verboten
   sind „die Welle“, „die Türme“ und „seinen Turm“ ohne Angabe, welcher gemeint ist.
4. **Plan vor Reflex.** Ein Plan wird gehalten, bis er erfüllt ist, ungültig wird, eine Gefahr ihn bricht
   oder eine Alternative *deutlich* mehr wert ist.
5. **Wert statt Vorrang.** Handlungen werden in derselben Währung verglichen (Gold-Äquivalent, Kapitel 7).
6. **Unbekannt bleibt unbekannt.** Ohne gelesenes Gegnerleben gibt es kein „er hat nur 840 Leben“. Ohne
   Beleg gibt es keinen Kill-Ruf.
7. **Schweigen ist ein Rat.** Solange der Plan steht und nichts ihn ändert, redet der Coach nicht. Infos
   ohne Folgen für die Handlung gehören aufs Dashboard.
8. **Der Kern entscheidet, Claude formuliert.** Claude bekommt die Entscheidung mit Gründen und Zahlen,
   nicht die Rohlage.
9. **Gemessen wird der Rat.** Jede Änderung muss Szenarien grün machen, ohne andere rot zu machen.
10. **Echte Partien sind die Wahrheit.** Bot-Partien taugen für Verdrahtung und Wahrnehmung, nicht zum
    Eichen von Kampf- und Makro-Urteilen.

---

## 3. Zielarchitektur

```
 Wahrnehmung (bleibt)            Datenschicht (bleibt, wird ergänzt)     NEU: lolcoach/kern/
 ─────────────────────           ─────────────────────────────────       ────────────────────────────────────────────
 liveapi → zustand.Partie  ─┐
 lage.Lagebild (Minimap,    ├──> bewertung.bewerte → Bewertung ──> merkmale.Merkmale (+ Verlauf 20 s, Bereich,
   HUD, Welle, Platten,     │                                       Lane-Phase, Gefahr-Modell)
   Zauber, Balken)          │                                           │
 jungle.Jungletracker  ─────┘                                           ▼
                                                                    modus.Modus  (EIN Modus je Takt, Hysterese)
                                                                        │
                                                                        ▼
                                                                    modi/<modus>.py → 2–8 Handlungen (Kandidaten)
                                                                        │
                                                                        ▼
                                                                    wert.bewerte(h, m)  → EV in Gold-Äquivalent
                                                                        │
                                                                        ▼
                                                                    plan.Plan  (halten / wechseln / Gefahr)
                                                                        │
                                                         ┌──────────────┴──────────────┐
                                                         ▼                             ▼
                                              sprechen.Sprecher → Ansage      Dashboard: Modus, Plan, Top-3
                                              (höchstens 1 je Takt)           Optionen mit Grund
                                                         │
                                                         ▼
                                              sprechplan / stimme (bleiben als Transport:
                                              Unterbrechen, Vorwärmen, „Ach nee“)
```

Paket `lolcoach/kern/`. Der Name ist bewusst **nicht** `gehirn/`, denn `gehirn.py` gibt es schon für
Spielakte und Briefing.

| Datei | Inhalt |
|---|---|
| `kern/__init__.py` | `Kern`: ein Objekt je Partie. `takt(p, lagebild) -> list[Ansage]`, `stand() -> dict` für Dashboard und Protokoll |
| `kern/merkmale.py` | `Merkmale` aus `Bewertung` + Verlauf (Kapitel 4) |
| `kern/gefahr.py` | Wahrscheinlichkeitsmodell für Gegner in der Nähe (Kapitel 7.5) |
| `kern/modus.py` | Modus-Erkennung mit Hysterese (Kapitel 5) |
| `kern/handlung.py` | `Handlung`, `Ziel`, die Arten (Kapitel 6) |
| `kern/wert.py` | Erwartungswert (Kapitel 7) |
| `kern/plan.py` | Plan halten/wechseln (Kapitel 8) |
| `kern/sprechen.py` | wann und wie gesprochen wird (Kapitel 9) |
| `kern/modi/*.py` | je Modus: Kandidaten erzeugen (Kapitel 6.3) |
| `kern/fragen.py` | Fragen an den Kern, Kontext für Claude (Kapitel 10, Schritt 6) |
| `wissen/kern.toml` | alle Schwellen und Startwerte mit `stand` (Kapitel 7.7) |
| `werkzeuge/szenarien.py`, `werkzeuge/kennzahlen.py`, `werkzeuge/szenario_aus_notizen.py` | Messen (Kapitel 12) |
| `tests/szenarien/*.toml` | Sollwerte (Kapitel 12) |

**Einbindung:** in `__main__._verfolge`, Funktion `schritt_coach`, über einen Schalter
`--kern alt|schatten|neu`:

| Schalterstellung | Verhalten |
|---|---|
| `alt` | wie heute |
| `schatten` | Das alte System spricht. Der Kern rechnet mit und schreibt je Takt `aufnahmen/<stamm>_kern.jsonl` (Zeit, Modus, Plan, Top-3, „würde sagen“). |
| `neu` | Der Kern spricht. In den Modi, die er schon beherrscht, sind die alten Regeln stumm. In den übrigen Modi laufen die alten Regeln mit Modus-Sperre weiter (Kapitel 14). |

Default in Schritt 1–2 ist `alt`, ab Schritt 3 `neu`. Nachspielen (`abspielen`, `szenarien`,
`sinnpruefung`) muss jede Stellung können.

**Verdrahtung, damit nichts doppelt läuft:**

- Es gibt zwei Schleifen, die denselben Takt fahren: `__main__._verfolge` (live und `abspielen`) und
  `werkzeuge/sinnpruefung.durchspielen` (eigene Schleife). `werkzeuge/szenarien.py` benutzt eine davon.
  Beide rufen den Kern an derselben Stelle wie `werk.pruefe`.
- Bis Schritt 8 berechnet das alte `Regelwerk.pruefe` die Bewertung (`werk.b`) und aktualisiert den
  Jungletracker (`werk.entscheider.jungle.neu`). Der Kern **liest** `werk.b` und `werk.entscheider.jungle`
  und ruft `bewerte()` kein zweites Mal. In Schritt 8 zieht der Kern diese Aufrufe zu sich (siehe dort).
- Ab Schritt 2 schreibt der Kern in **jeder** Stellung `_kern.jsonl` (zuerst nur den Modus). „`alt`“ heißt
  also: Die Ansagen kommen aus dem alten System, einschließlich der Änderungen, die Schritt 2 an ihm vornimmt.

---

## 4. Datenvertrag: was der Kern liest

### 4.1 Eingang

Der Kern liest die `Bewertung` des Takts (plus `Partie`, `Lagebild`, `Jungletracker`) und rechnet nichts
nach, was dort schon steht. Er benutzt:

- **Zeit und eigener Zustand:** `zeit`, `ich`, `leben`, `leben_abs`, `gold`, `pos`, `ort`, `mein_tempo`,
  `flash`, `zweiter`, `ult`, `bereit`
- **Karte:** `zum_turm`, `turm_name`, `unter_gegnerturm`, `unter_eigenem_turm`, `tiefe`
- **Gegner:** `gegner` (je `GegnerLage`: `sichtbar`, `seit`, `pos`, `abstand`, `ankunft`, `tempo`, `flash`,
  `ult`, `level_vorsprung`, `gold_vorsprung`, `kommt_naeher`, `leben`), `lane`, `jungler`, `tote_gegner`,
  `tote_eigene`
- **Welle und Objectives:** `welle`, `prio`, `platten_gegner`, `platten_eigen`, `objective`,
  `zum_objective` (Achtung, Kapitel 1.3 Punkt 5), `kampf`
- **Mitspieler und Kosten:** `mitspieler`, `mitspieler_nah`, `tod_kostet`, `shutdown_ich`, `kauf`,
  `tode_kurz`
- **Methoden:** `kraefte()`, `kraft_gegen()`
- **Ziele:** `bewertung.ziele(b)`, die Tabelle der Türme und Verteidigungsaufgaben von deiner Position aus

### 4.2 Neu in `Merkmale`

`Merkmale` ist dünn und rechnet nur, was fehlt:

| Feld | Bedeutung | Quelle |
|---|---|---|
| `bereich` | `lane_eigen`, `lane:<Top/Mid/Bot>`, `fluss_oben`, `fluss_unten`, `jungle_eigen_oben/unten`, `jungle_fremd_oben/unten`, `basis_eigen`, `basis_fremd`, `grube:<objective>` | `pos` + Kartengeometrie; `minimap.ort` liefert heute schon die Wörter, abbilden statt neu erfinden |
| `lane_phase` | `True`, solange `zeit < lane_phase_bis_s` **und** beide Außentürme deiner Lane stehen | `bewertung.stehende_tuerme`, `kern.toml` |
| `verlauf` | Ringpuffer der letzten 20 s: eigenes Leben, Position, sichtbare Gegner in 1200 | je Takt |
| `leben_trend` | Änderung des eigenen Lebens in den letzten 3 s | `verlauf` |
| `im_kampf` | sichtbarer Gegner in `kampf_radius` **und** (`leben_trend` ≤ −10 % **oder** sein Balken fällt) | `verlauf`, `GegnerLage.leben` |
| `objectives` | **alle** lebenden oder bald spawnenden Objectives, je mit *eigener* Laufzeit, Spawn/lebt, wer von euch nah ist | `zustand.Partie.naechster_spawn`, `bewertung.GRUBEN` |
| `team_nah(ziel, radius)` | Mitspieler in der Nähe eines Punkts | `mitspieler` |
| `fenster_gegner` | für jedes Objective und jedes Turm-Ziel: bis wann niemand vom Gegner dort sein kann (tote: Respawn + Weg vom Brunnen) | die innere Funktion `verteidiger` in `bewertung.ziele` als Modulfunktion herausziehen (z. B. `bewertung.verteidiger_ab(b, ziel, weg)`) und von `ziele` und Kern gemeinsam nutzen |
| `gefahr` | je Gegner `p_da(fenster)` (Kapitel 7.5) | `gefahr.py` |
| `daten_frisch` | letzter Schnappschuss ≤ 2 s alt **und** Minimap ≤ 5 s alt | `Partie`, `Lagebild` |

### 4.3 Unbekanntes

Jedes Merkmal darf `None` sein. Jede Handlung erklärt in `braucht`, welche Merkmale sie zwingend
voraussetzt. Fehlt eins, **wird sie nicht Kandidat**. Sie wird nicht „geraten“.

Wenn `daten_frisch` falsch ist, gilt (innerhalb der Schleife, z. B. Minimap weg, Schnappschuss alt):

- Der Kern spricht keine neuen Pläne.
- Nach 20 s ohne Daten sagt er einmal: „Ich sehe das Spiel gerade nicht – ich melde mich, sobald die Daten
  wieder da sind.“

**Achtung:** Kommt von der API gar nichts mehr, läuft der Takt nicht. `_live_quelle` liefert dann nichts und
beendet die Partie nach 120 s (`__main__._live_quelle`). Der Kern wird in dieser Zeit nie gerufen. Für diesen
Fall braucht es einen **Wachhund nach Wanduhr** außerhalb der Schnappschuss-Schleife, im Live-Weg:

- Er meldet sich nach 20 s ohne Schnappschuss, solange das Spielfenster noch da ist.
- Er protokolliert Beginn und Ende der Lücke in der Aufnahme.

Das hätte die 8,5 Minuten Stille in 102112 hörbar gemacht, und das Review wüsste, wo die Lücke ist.

---

## 5. Modus: „Was ist gerade dein Job?“

### 5.1 Die neun Modi

| Modus | Eintritt (vereinfacht) | Kernfrage |
|---|---|---|
| `TOT` | du bist tot | Was ging schief (einmal)? Was kaufst du, wohin nach dem Respawn? |
| `KAMPF` | `im_kampf` | Rein, halten oder raus – und wer ist das Ziel? |
| `OBJECTIVE` | ein Objective lebt oder spawnt in ≤ `objective_vorlauf_s`, **und** eins davon gilt: du stehst an der Grube (≤ `objective_nah_s`) **und nicht** auf deiner eigenen Lane in der Lane-Phase; der Plan zielt darauf; ≥ 1 Mitspieler ist an der Grube. Auf der eigenen Lane in der Lane-Phase bleibt es `LANE` mit der Handlung `VORBEREITEN_OBJECTIVE`. | Nehmen, bestreiten, abgeben oder tauschen? |
| `VERTEIDIGEN` | eine **tatsächliche** Bedrohung an einer eigenen Struktur, **und** du bist ≤ 15 s davon entfernt. Bedrohung heißt: ≥ 2 Gegner sichtbar in 2500 um den eigenen Turm/Nexus, **oder** die gegnerische Welle steht an eurem Inhibitor-Turm/Nexus einer Lane ohne Inhibitor (`welle.py`) und kein Mitspieler ist dort. Ein fehlender Inhibitor allein reicht nicht. | Welle klären, Turm halten oder woanders tauschen? |
| `BASIS` | `bereich == basis_eigen`, lebend | Was kaufst du, und wohin gehst du? |
| `LANE` | `lane_phase` **und** `bereich == lane_eigen` | Was machst du mit Welle, Gegner und Gold in den nächsten 30 s – und wer kann dich bestrafen? |
| `SEITE` | nicht `lane_phase`, auf Top- oder Bot-Lane | Wie lange kannst du hier Druck machen, bevor dich jemand erwischt oder dein Team dich braucht? |
| `GRUPPE` | nicht `lane_phase`, ≥ `gruppe_mindestens` Mitspieler in `gruppe_radius` | Was nimmt die Gruppe als Nächstes – und braucht es jemanden auf einer Seitenlane? |
| `UNTERWEGS` | alles andere (Fluss, Jungle, Mid ohne Gruppe) | Wohin – und lohnt ein Ward auf dem Weg? |

### 5.2 Priorität und Hysterese

- **Priorität** (die erste passende Zeile gewinnt, in der Reihenfolge der Tabelle):
  `TOT > KAMPF > OBJECTIVE > VERTEIDIGEN > BASIS > LANE > SEITE > GRUPPE > UNTERWEGS`
- „Entfernt“ heißt immer: **deine Laufzeit** (Luftlinie × `WEGFAKTOR` / `mein_tempo`, wie `bewertung`), nicht
  Luftlinie in Einheiten.
- **Hysterese:** Ein neuer Modus gilt erst, wenn er `modus.hysterese_s` (Startwert 1,5 s) lang ununterbrochen
  Kandidat war.
  - Ausnahmen: `TOT` und `KAMPF` gelten sofort.
  - `KAMPF` endet erst nach `kampf_ende_s` (Startwert 3 s) ohne Kampfmerkmale.
- **Moduswechsel = Planprüfung.** Der Plan bleibt, wenn er im neuen Modus noch gültig ist. Beispiel:
  Der Plan „Welle rein, back, Brutalisierer, zurück nach oben“ läuft von `LANE` über `BASIS` weiter.
- Der Modus steht auf dem Dashboard und in `_kern.jsonl`. Ab Schritt 2 bekommt Claude ihn in **jeder**
  Frage als erste Zeile.

```python
class Modus:
    def neu(self, m: Merkmale) -> str:
        roh = self._roh(m)                         # erste passende Zeile der Tabelle
        if roh in ("TOT", "KAMPF") or roh == self.aktuell:
            return self._setze(roh, m.zeit)
        if self.aktuell == "KAMPF" and m.zeit - self._kampf_zuletzt < cfg.kampf_ende_s:
            return self.aktuell
        if self.kandidat != roh:
            self.kandidat, self.kandidat_seit = roh, m.zeit
        if m.zeit - self.kandidat_seit >= cfg.hysterese_s:
            return self._setze(roh, m.zeit)
        return self.aktuell
```

### 5.3 Sollwerte aus 102112 (für den Modus-Test)

| Zeit | Soll | Zeit | Soll |
|---|---|---|---|
| 1:30 | LANE | 15:31 | OBJECTIVE oder KAMPF |
| 3:00 | LANE | 24:40 | OBJECTIVE oder UNTERWEGS |
| 5:17 | LANE | 25:22 | OBJECTIVE oder UNTERWEGS |
| 6:06 | BASIS | 29:14 | OBJECTIVE |
| 7:24 | LANE (Larven in 36 s, aber du stehst auf deiner Lane in der Lane-Phase) | 30:04 | BASIS |
| 12:00 | LANE | 35:00 | OBJECTIVE (hat Vorrang vor VERTEIDIGEN) |
| 13:30 | BASIS | 36:32 | GRUPPE oder UNTERWEGS |
| 14:53 | SEITE oder OBJECTIVE (Lane-Phase endet 14:00) | 37:54 | BASIS oder VERTEIDIGEN |

Ein Prüfer hat die erste Fassung dieser Tabelle nachgerechnet: Mit den alten Eintrittsregeln kamen 7:24 als
OBJECTIVE und 35:00–37:54 als VERTEIDIGEN heraus (der Mid-Inhibitor fehlte seit 33:18). Die Regeln in 5.1
sind deshalb enger gefasst. Rechne die Tabelle in Schritt 2 mit den echten Regeln nach. Weicht etwas ab,
entscheide nach der Kernfrage des Modus und notiere es.

---

## 6. Handlungen

### 6.1 Die Datenstruktur

```python
@dataclass
class Ziel:
    art: str                 # "turm" | "objective" | "gegner" | "ort" | "lane" | "gruppe" | "basis"
    name: str                # gesprochen: "den Mid-Inhibitor-Turm", "den Drachen", "Sett", "deine Top-Welle"
    pos: tuple[float, float] | None
    weg: float | None        # deine Laufzeit in s

@dataclass
class Handlung:
    art: str                 # Katalog 6.3, z. B. "WELLE_REIN_UND_BACK"
    ziel: Ziel | None        # Pflicht, außer bei HALTEN/FARMEN
    modus: str
    dauer: float             # s, bis die Handlung erledigt ist
    gewinn: float = 0.0      # GE bei Erfolg
    p_erfolg: float = 1.0
    p_tod: float = 0.0
    verlust: float = 0.0     # GE bei Tod (Todeskosten, Kapitel 7.3)
    ev: float = 0.0          # von wert.py gesetzt
    grund: str = ""          # der eine entscheidende Grund, mit Zahl
    fragen: dict = field(default_factory=dict)   # die sechs Fragen (7.6)
    braucht: frozenset = frozenset()
    abbruch: list = field(default_factory=list)  # Funktionen m -> str|None (Grund, warum ungültig)
    schritte: list[str] = field(default_factory=list)  # Folge: ["Welle rein", "back", "Brutalisierer", "zurück Top"]
```

### 6.2 Regeln für alle Handlungen

- **Ziel ist konkret.** Das Ziel stammt aus `Merkmale` oder `bewertung.ziele`. Der Satzbaustein nennt
  Lane und Turm, Objective oder Namen. Eine Handlung ohne auflösbares Ziel wird nicht Kandidat.
- **Nur, was du von deiner Position aus kannst.** Befehle auf einen Gegner gelten nur, wenn er ≤ 3500
  Einheiten entfernt ist oder du ihn vor seinem Fenster erreichst.
  Beispiele für Verstöße: „Geh auf Sett“ mit Sett auf der anderen Kartenseite, „Nehmt Baron“, wenn du nicht
  rechtzeitig dort sein kannst.
- **Team-Handlungen** („ihr nehmt X“) sind nur Kandidat, wenn **du** Teil davon bist. Sonst sind sie
  Information: „Dein Team kann Baron nehmen – du bist 40 s weg: drück solange Bot.“
- **Kill-Ruf (`ALL_IN`) braucht einen Beleg.** Mindestens eine der drei Bedingungen muss gelten:
  - sein Leben ist frisch gelesen (≤ 1 s),
  - die Combo-Rechnung reicht (Faktor `combo_kill` aus `denker.kampf_faktoren`),
  - klare Überlegenheit: `kraefte()[0]` ≥ `kill_ueberlegen` (Startwert 3,0). `kraefte()` liefert
    `(wert, gruende)` auf der Skala „1 Level ≈ 1, 600 Gold ≈ 1“ und gilt nur gegen den Lane-Gegner.

  Gesagt wird der tragende Beleg, nicht eine Sammlung. Sagt die Rechnung „reicht knapp nicht“, heißt die
  Handlung nicht Kill (11:33: „Das ist ein Kill: dein Combo macht 110, Sett hat noch 130“).
- **Mehrere Gegner:** Wer in Reichweite ist oder im Fenster ankommt, wird gemeinsam gerechnet
  (`kraft_gegen(set)`, ein **Verhältnis**: > 1 heißt, deine Seite gewinnt; 99,0 heißt, es ist keiner da).
  „Zusammen schwächer als du“ darf nur fallen, wenn `kraft_gegen(set)` ≥ `ueberzahl_sicher` ist
  (Startwert 2,5) **und** dein Leben ≥ 70 % ist.

### 6.3 Katalog je Modus

**In allen Modi außer TOT und BASIS** ist `ZURUECK` Kandidat, sobald das Gefahr-Modell (7.5) anschlägt. Das Ziel
ist der sichere Ort aus 7.5. `ZURUECK` wird in den Tabellen unten nicht jedes Mal wiederholt.

Die Spalte „Kandidat, wenn“ ist bewusst grob. Die Feinheiten liefern die Bücher 1–10 (Kapitel 15). Satzformen
stehen in Kapitel 9.3.

**LANE** (Buch 1–4 verfeinern):

| Art | Kandidat, wenn | braucht | Ziel |
|---|---|---|---|
| `FARMEN` | immer (Grundplan, meist stumm) | – | deine Lane |
| `TRADE` | Lane-Gegner sichtbar ≤ 1000, `denker.urteil(b).art` ∈ {trade, kill, kill_schnell} | `lane` | Lane-Gegner |
| `ALL_IN` | Kill-Beleg (6.2), P_tod klein | `lane` + Beleg | Lane-Gegner |
| `ZURUECK` | P_tod(jetzt) × Verlust ≥ Gefahr-Schwelle | `gefahr` | sicherer Ort (7.5) |
| `WELLE_REIN_UND_BACK` | Welle lässt sich in ≤ 15 s crashen **und** (Gold ≥ nächste Stufe **oder** Leben < 50 %) | `welle`, `kauf` | deine Welle, dann Basis |
| `BACK_JETZT` | Welle kommt zu dir oder ist sicher, Gold ≥ nächste Stufe oder Leben kritisch | `kauf` | Basis |
| `PLATTEN` | Lane-Gegner tot/weg ≥ Dauer, P_tod klein, Platten übrig | `platten_gegner` | der konkrete Turm |
| `WELLE_HALTEN` | Welle an deinem Turm, du stärker/gleich, Gegner-Jungler weit weg (Freeze, Buch 1) | `welle` | deine Welle |
| `VORBEREITEN_OBJECTIVE` | Objective auf deiner Seite in ≤ 60 s | `objectives` | Welle, dann Grube |
| `ROAM` | Buch 5; bis dahin kein Kandidat | – | – |
| `WARD` | als Plan-Schritt, nie allein | – | konkrete Stelle |

**BASIS / TOT:**

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `KAUFEN` | immer in BASIS; in TOT ≤ 8 s vor dem Respawn | Items aus `kaufplan` (Namen aus Data Dragon, inkl. Kontroll-Auge, wenn keins im Inventar) |
| `WOHIN` | immer zusammen mit `KAUFEN`, ein Satz | das beste Ziel aus `WOHIN`-Kandidaten (siehe UNTERWEGS) |
| `TODESRUECKBLICK` | einmal je Tod, ≥ 14 s Todeszeit | – (bestehende `todesanalyse`) |

**Warteregel BASIS:** Steht er nach dem Kauf > 20 s lebend in der Basis, wird der dann beste `WOHIN`-Plan
gesagt, danach alle 30 s, solange er bleibt, höchstens dreimal. Das ist die Ausnahme von Kapitel 8.2 Punkt 5:
In der Basis ist Untätigkeit selbst das Problem (31:00–32:00 in 102112).

**SEITE:**

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `DRUECKEN` | Turm erreichbar vor dem ersten Verteidiger (`bewertung.ziele`), P_tod klein | der konkrete Turm |
| `WELLE_UND_RAUS` | Welle ist wertvoll, aber Gegner fehlen oder das Team braucht dich bald | deine Seitenwelle, dann Ort |
| `ZUR_GRUPPE` | Objective oder Kampf beim Team, das dich braucht (Kapitel 7.4) | Gruppe/Grube |
| `TP_SPIEL` | Teleport bereit, Kampf beim Team mit dir als Unterschied | Ort |
| `ZURUECK`, `BACK_JETZT` | wie LANE | wie LANE |

**GRUPPE / UNTERWEGS:**

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `DRUECKEN` / `MIT_GRUPPE` | Struktur erreichbar im Fenster, Überzahl | konkreter Turm/Inhibitor/Nexus |
| `SEITENWELLE` | große Welle auf einer Seite, niemand von euch dort, sicher | Lane |
| `ANLAUFEN` | Objective lebt/spawnt, du bist rechtzeitig dort, `Kampflage.urteil()` ∈ {nehmen, offen} | Grube |
| `BACK_JETZT` | Gold ≥ großer Spike und kein Fenster offen | Basis |
| `WARD` | als Schritt auf dem Weg | Stelle |

**OBJECTIVE:**

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `VORBEREITEN` | Spawn in > 20 s: Welle rein, back, Sicht | Welle/Grube |
| `NEHMEN` | lebt, kein Gegner vor Ende der Tötungszeit dort (`fenster_gegner` > geschätzte Dauer) **oder** `Kampflage.urteil()` = nehmen | Grube |
| `BESTREITEN` | lebt, Gegner zuerst dort, aber ihr gewinnt den Kampf | Grube/Gegner |
| `ABGEBEN_TAUSCHEN` | Gegner zuerst, ihr verliert den Kampf → gleichwertiges Ziel auf der anderen Seite | Turm/Objective |
| `ZURUECK` | wie LANE | sicherer Ort |

**KAMPF** (nur sprechen, wenn es den Ausgang ändert):

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `REIN` | du gewinnst den Kampf, Ziel in Reichweite | Gegner mit Namen |
| `RAUS` | du verlierst ihn | Fluchtweg/Ort |
| `HALTEN` | unklar – stumm | – |

**VERTEIDIGEN:**

| Art | Kandidat, wenn | Ziel |
|---|---|---|
| `WELLE_KLAEREN` | Supervasallen/Welle am Turm, du rechtzeitig | Lane |
| `HALTEN_UNTER_TURM` | Gegner belagern, du allein unterlegen | Turm |
| `TAUSCHEN` | Verteidigung aussichtslos, gleichwertiges Ziel woanders | Turm/Objective |

---

## 7. Wert: alles in einer Währung

### 7.1 Die Währung

**GE (Gold-Äquivalent).** Gold zählt 1:1, Erfahrung wird mit `xp_ge` umgerechnet, Zeit mit
`zeitwert(phase)`. Mehr Genauigkeit braucht es nicht. Es geht um **Rangfolgen**, nicht um exakte Beträge.

### 7.2 Die Formel

```
EV(h) = p_erfolg(h) · gewinn(h)
      − p_tod(h) · todeskosten
      − dauer(h) · zeitwert(phase)
      + folgewert(h)          # was die Handlung für die nächsten 60 s freischaltet (Kauf, Objective, Welle)
```

### 7.3 Todeskosten

```
todeskosten = kill_gold(ich)                                  # was der Gegner für dich bekommt: Basis + Kopfgeld
                                                              #   (bewertung.kill_gold; kopfgeld() allein ist nur der
                                                              #   Aufschlag über 300)
            + todeszeit · zeitwert(phase)                     # bewertung.todeszeit
            + verlorene_wellen · wellenwert                   # eigene Welle(n), die währenddessen in den Turm laufen
            + objective_risiko                                # Wert des nächsten Objectives × p(Gegner nimmt es,
                                                              #   solange du tot bist) – Startwert 0,5, wenn es lebt
                                                              #   oder innerhalb todeszeit + 30 s spawnt
```

Die vorhandene `denker.erwartung` rechnet eine grobe Form davon (`kopfgeld + tod_kostet·10 + 300`). Sie geht
in `wert.py` auf.

### 7.4 Gewinne

| Posten | Wert | Quelle |
|---|---|---|
| Welle | Vasallengold der Welle + Erfahrung · `xp_ge` | `wissen/mechanik.toml` [gold], [wellen], [xp] |
| Platte | Plattengold, ab 11:00 mit Abzug | `mechanik.toml` [gold] `platte`, `platte_abzug_*` |
| Turm | Turmgold (Platten lokal + global je Spieler + `erster_turm_bonus`) + `turm_extra` (Kartenzugang) | `mechanik.toml` [gold] `turm_*`, `kern.toml` |
| Kill | `bewertung.kill_gold` + Folgewert (Welle/Platten im Todesfenster des Gegners) | vorhanden |
| Kauf | `min(gold, kauf.kosten) · kauf_faktor` + fehlendes Leben · `heil_faktor` | `kaufplan`, `kern.toml` |
| Objectives | Tabelle `[objective_wert]` | `kern.toml` (Startwerte) |
| Information | Buch 4 (Wards); bis dahin 0 | – |

### 7.5 Gefahr: Wahrscheinlichkeit statt schlimmster Fall

Für jeden lebenden Gegner `g` und ein Fenster `T` (Standard `gefahr.fenster_s` = 10 s, bei längeren
Handlungen deren Dauer) gilt:

```
t_min = g.ankunft                                  # frühestens (vorhanden, 90 % gedeckt)
rampe(x) = clip(x / anlauf_spielraum_s, 0, 1)      # x = T − t_min

g sichtbar:            p_da = 1, wenn t_min ≤ T und (g.kommt_naeher oder abstand ≤ 1500), sonst rampe(T − t_min)
g unsichtbar, seit ≤ 45 s:
                       p_da = p_seite(g) · rampe(T − t_min)
g unbekannt (> 45 s):  p_da = p_seite(g) · unbekannt_faktor
g tot:                 p_da = 0, außer respawn + Weg vom Brunnen ≤ T

p_seite(Jungler)            = jungle.wahrscheinlich(zeit)[deine Kartenseite]      # geeicht, Brier 0,183
                              # Schlüssel sind nur 'oben'/'unten'. Auf Mid, in der Flussmitte oder in der
                              # Basis: max(oben, unten).
p_seite(dein Lane-Gegner)   = 1, wenn er fehlt
                              # Der Brunnen steckt schon in g.ankunft (lage.brunnen_seit) - nicht doppelt rechnen.
p_seite(Mid/Support ab 4:00) = roam_basis (Startwert 0,3)
p_seite(andere)             = 0 in der Lane-Phase, danach roam_basis
```

Wer dich wirklich tötet, ist die **Menge** der Ankommenden, nicht ein Einzelner:

```
p_verliere(S) = 1 / (1 + kraft_gegen(S) ** k)             # Startwert k = 2: Verhältnis 1 -> 0,5; 2 -> 0,2; 0,5 -> 0,8
                                                          # (kraft_gegen ist ein Verhältnis; 99,0 = niemand da -> ~0)
                · (flucht_flash wenn Flash bereit) · (flucht_turm wenn zum_turm ≤ 5 s)
p_tod(h)      ≈ 1 − Π_g (1 − p_da(g, T) · p_verliere({g} ∪ sichtbare Nahe))
```

**Gefahr wird gesagt**, wenn beides zutrifft:

- `p_tod · todeskosten ≥ gefahr.schwelle_ge` (Startwert 120) **und** `p_tod ≥ gefahr.p_min` (Startwert 0,15),
- es gibt eine Handlung (`ZURUECK`, `BACK_JETZT`, `WELLE_UND_RAUS`) mit höherem EV.

Sonst gibt es keine Ansage, auch wenn jemand „frühestens in 8 s“ da sein könnte.

**Umgekehrt ist Sicherheit ein Rat.** Wird der Jungler auf der anderen Kartenseite gesehen, fällt `p_da`
für viele Sekunden auf fast 0. Das ist oft der wertvollste Satz der Lane-Phase: „Fiddlesticks ist unten
– 25 Sekunden Fenster: Platte am äußeren Top-Turm.“

**Sicherer Ort** (Ziel von `ZURUECK`) ist der Ort mit der kürzesten Laufzeit unter drei Möglichkeiten:
eigener stehender Turm, eigene Basis, eigene Gruppe mit ≥ 2 Mitspielern. Ein Rückzug zu einem Turm, der
31 s entfernt ist, während zwei Mitspieler 8 s entfernt stehen, ist falsch (35:35).

**Eichung.** `werkzeuge/kennzahlen.py` misst an Aufnahmen, ob in `T` tatsächlich ein Gegner in 1500
Einheiten auftauchte. Daraus folgt der Brier-Wert für `p_da` im Vergleich zum schlimmsten Fall
(`p = 1`, wenn `t_min ≤ T`). Abnahme in Schritt 3: `p_da` schlägt den schlimmsten Fall.

### 7.6 Die sechs Fragen als Pflichtfelder

Jede Handlung füllt `fragen` aus, und `grund` wählt daraus die **eine** Antwort, die den Ausschlag gibt:

| Frage | Feld | Beispiel |
|---|---|---|
| Wer ist stärker? | `staerker` | „du 2 Level vorn“ / „gegen beide zusammen nicht“ |
| Wer ist zuerst da? | `zuerst` | „Sona frühestens in 20 s, du tötest ihn in ~12 s“ |
| Was sehen wir nicht? | `unsichtbar` | „Fiddlesticks seit 30 s, zuletzt oberer Fluss (65 % oben)“ |
| Welche Welle verlieren wir? | `welle_verlust` | „deine Top-Welle (7 Vasallen) läuft in deinen Turm“ |
| Was bekommt der Gegner? | `gegner_bekommt` | „Drache, während du tot bist“ |
| Was gewinnen wir nach dem Play? | `danach` | „mit 1400 Gold Brutalisierer vor den Larven um 8:00“ |

Dashboard und Claude bekommen alle sechs. Gesprochen wird nur `grund`.

### 7.7 Startwerte für `wissen/kern.toml`

```toml
stand = "Buch 0, 27.09.2026 - Startwerte (Schaetzung), an Szenarien kalibrieren"

[modus]
hysterese_s = 1.5
kampf_radius = 1000
kampf_ende_s = 3.0
lane_phase_bis_s = 840          # 14:00, wie makro.toml [sicht] lane_phase_bis und der Wellentakt-Wechsel in mechanik.toml
gruppe_radius = 2000
gruppe_mindestens = 2
objective_vorlauf_s = 60
objective_nah_s = 25

[zeitwert]                      # GE je Sekunde deiner Zeit
bis_14 = 8
bis_25 = 12
danach = 15
xp_ge = 0.5

[gefahr]
fenster_s = 10
anlauf_spielraum_s = 25
unbekannt_faktor = 0.35
roam_basis = 0.3
schwelle_ge = 120
p_min = 0.15
kampf_exponent = 2.0            # p_verliere = 1 / (1 + kraft_gegen ** k)
flucht_flash = 0.6
flucht_turm = 0.5
ueberzahl_sicher = 2.5          # kraft_gegen-Verhaeltnis
kill_ueberlegen = 3.0           # kraefte()[0], Skala Level/600 Gold

[plan]
hysterese_ge = 150
hysterese_anteil = 0.3
stabil_s = 2.0
halten_s = 8.0
erinnern_nach_s = 15

[sprechen]
abstand_s = 12
max_je_minute = 3
ziel_je_30min = 45
max_woerter = 18
max_woerter_gefahr = 10

[kauf]
kauf_faktor = 0.25
heil_faktor = 1.0               # GE je fehlendem Lebenspunkt beim Back (grob)

[objective_wert]                # fuer dein Team; Startwerte, Buch 6 eicht sie
drache = 600
drache_seele = 1500
larven = 500
herold = 700
baron = 2500
aeltester = 3000
inhibitor = 1000
turm_extra = 250
nexus = 10000
```

### 7.8 Durchgerechnet: 5:17 in Partie 102112

**Lage:**

- Riven L6, 37 % Leben, Flash weg (48 s), 1258 Gold. Der Lane-Plan sieht Brutalisierer ab 1337 vor.
- Sett ist seit eben tot (noch 14 s). Welle 7:4 für Riven.
- Fiddlesticks wurde vor 30 s im oberen Fluss gesehen. `p_seite(oben)` ist hoch, weil die letzte Sichtung
  oben war.

**Kandidaten** (die Zahlen sind illustrativ, Größenordnung Startwerte):

| Handlung | Gewinn | p_tod | Todeskosten | Dauer | EV (grob) |
|---|---|---|---|---|---|
| `PLATTEN` (Welle rein + Platte + back) | Platte + Welle ≈ 300 | ~0,25 (Jungler oben wahrscheinlich; Fiddlesticks ist zwar erst L4, aber mit Furcht gegen 37 % ohne Flash, und Sett ist in 14 s wieder da) | Kopfgeld + 20 s · 8 + Welle ≈ 550 | ~18 s | 0,75 · 300 − 0,25 · 550 − 144 ≈ **−57** |
| `WELLE_REIN_UND_BACK` | Welle ≈ 120 + Kauf (Brutalisierer-Spike, Folgewert) ≈ 200 | ~0,1 (8 s am Stück, dann weg) | 550 | ~8 s | 0,9 · 320 − 0,1 · 550 − 64 ≈ **+169** |
| `FARMEN` (bleiben) | Welle ≈ 120 | ~0,25 | 550 | 20 s | ≈ **−208** |

**Plan:** `WELLE_REIN_UND_BACK`, Ziel „deine Top-Welle, dann Basis“, `grund` = „37 Prozent ohne Flash,
Fiddlesticks war oben“.

**Satz:** „Top-Welle schnell rein und back: 37 Prozent ohne Flash, Fiddlesticks war zuletzt oben.“

Fiddlesticks kam um 5:37. In diesem Moment ist Riven schon im Recall.

---

## 8. Plan: halten statt hin und her

### 8.1 Die Datenstruktur

```python
@dataclass
class Plan:
    handlung: Handlung
    seit: float
    gesagt: float | None = None       # wann angesagt
    schritt: int = 0                  # Index in handlung.schritte
    erinnert: bool = False
```

### 8.2 Regeln (in dieser Reihenfolge, je Takt)

1. **Ungültig?** Jede Funktion in `handlung.abbruch` wird geprüft. Liefert eine einen Grund, fällt der Plan.
   Beispiele:
   - Welle gecrasht und du bist schon auf dem Weg: der Schritt ist erledigt, nicht der Plan.
   - Objective genommen.
   - Ziel tot.
   - Du bist woanders, als der Plan annimmt.
2. **Gefahr?** Wenn `p_tod(plan) · todeskosten ≥ schwelle_ge` und eine sicherere Handlung mehr EV hat, folgt
   **sofort** der Wechsel. Kategorie GEFAHR, darf unterbrechen.
3. **Erfüllt?** Der Plan geht zum nächsten Schritt. Eine Ansage kommt nur, wenn der Spieler jetzt etwas
   Neues tun muss („Welle ist drin – jetzt back.“).
4. **Besser?** Ein Wechsel erfolgt nur, wenn alle drei Bedingungen gelten:
   - `EV(neu) − EV(plan) ≥ max(hysterese_ge, hysterese_anteil · |EV(plan)|)`,
   - der Unterschied hält `stabil_s` lang,
   - seit dem letzten Wechsel sind ≥ `halten_s` vergangen.
5. **Nicht ausgeführt?** (Ausnahme: Warteregel BASIS in 6.3.) Wenn der Spieler nach `erinnern_nach_s` nichts vom Plan tut (Position und Zustand
   ändern sich nicht in die Richtung), erinnert der Coach **einmal** mit dem Grund. Danach wird neu bewertet,
   ob der Plan noch der beste ist.

### 8.3 Was das in 102112 geändert hätte (8:56–9:24)

Bei jedem Schritt wird der bestehende Plan gegen die neue Lage geprüft:

- **8:56:** Galio sichtbar im Fluss, Sett im Fluss vor 56 s gesehen, Fiddlesticks unbekannt.
  `p_tod(FARMEN)` ist mäßig, der Plan bleibt `FARMEN`, der Coach schweigt.
- **9:04:** Alle drei sind ≤ 2300 Einheiten entfernt und kommen näher. `p_tod(FARMEN)` springt hoch.
  GEFAHR → `ZURUECK` mit Ziel „dein äußerer Top-Turm“.
  - Satz: „Raus zum Top-Turm: Sett, Galio und Fiddlesticks kommen.“
- **9:24:** Riven hat 70 % Leben, Galio ist sichtbar, Fiddlesticks seit 22 s weg. `ZURUECK` ist erfüllt,
  Riven steht am Turm. Der neue Plan heißt `FARMEN` am Turm.
  - Ob gesprochen wird: Die Handlung ändert sich nicht (bleib am Turm), also ist kein Satz nötig.
  - Kein „zusammen schwächer als du“.

---

## 9. Sprechen

### 9.1 Kategorien

| Kategorie | Wann | Darf unterbrechen |
|---|---|---|
| `GEFAHR` | Planwechsel aus Kapitel 8.2 Punkt 2 | ja |
| `PLAN` | neuer Plan (8.2 Punkt 1 oder 4) oder ein Schritt, der eine neue Tätigkeit verlangt (8.2 Punkt 3) | nur Unterbrechbares |
| `ERINNERUNG` | 8.2 Punkt 5, einmal | nein |
| `ANTWORT` | Frage per Sprechtaste | wie heute |
| `INFO` | Flash-Timer, Items, Level, CS, Gegner-Kauf, Objective-Timer, situative Sätze des Stratege | **nur Dashboard.** Gesprochen nur als `grund` eines Plans oder bei Nachfrage. |
| `TECHNIK` | Minimap nicht erkannt (`minimap_gesund`), Datenlücke (4.3), „Coach verbunden“ | ja; zählt nicht zum Budget |

Heute gehen zwei Wege am Sprechplan-Filter vorbei: `stratege` wirft Sätze mit `plan.einwerfen` ein
(Briefing, Midgame-Plan, situative Sätze), und `minimap_gesund` ruft `sprecher.sage` direkt. Ab Schritt 3
gilt: Das Briefing bleibt, einmal zu Spielbeginn. Midgame-Plan und situative Sätze laufen als `INFO` durch
den Kern, oder als `grund`, wenn sie zum Plan passen. `minimap_gesund` wird `TECHNIK`.

### 9.2 Budget

- Zwischen zwei Ansagen außer GEFAHR und ANTWORT liegen ≥ `sprechen.abstand_s` (12 s). Höchstens
  `max_je_minute` (3) Ansagen je 60 s.
- Ziel sind ≤ 45 ungefragte Ansagen je 30 Minuten. Das Briefing zählt nicht.
- Ist das Budget voll, wird ein PLAN nicht gesagt, sondern nur angezeigt. Er wird gesagt, sobald wieder
  Platz ist **und** er dann noch gilt.

### 9.3 Form

- **PLAN:** `<Handlung> <Ziel>: <Grund mit Zahl>.` Höchstens 18 Wörter. Beispiel: „Mid-Inhibitor-Turm jetzt:
  vier von ihnen sind noch 15 Sekunden tot.“
- **GEFAHR:** höchstens 10 Wörter, die Handlung zuerst. Beispiel: „Raus zum Top-Turm: Sett, Galio und
  Fiddlesticks kommen.“
- **BASIS:** Kauf und Ziel in einem Satz. Beispiel: „Kauf Seryldas Bitterkeit und ein Kontroll-Auge, dann Mid:
  Drache in 50 Sekunden.“
- Die Satzanfänge bleiben vorgewärmt (`komponist.anfaenge`). Sie werden auf die neuen Formen umgestellt.

### 9.4 Verbote (prüft `werkzeuge/kennzahlen.py`)

1. Kein Satz ohne auflösbares Ziel: „die Welle“, „die Türme“, „seinen Turm“ ohne Lane.
2. Keine Lane- oder Wellenbefehle außerhalb von `LANE`/`SEITE`, außer als Weg („geh Top, deine Welle …“).
3. Kein Befehl auf einen Gegner, der > 3500 entfernt oder tot ist.
4. Keine Team-Befehle, an denen du nicht teilnehmen kannst.
5. Keine Kehrtwende (vor ↔ zurück in ≤ 30 s) ohne neues Ereignis.
   - **vor** sind die Plan-Arten `TRADE`, `ALL_IN`, `PLATTEN`, `DRUECKEN`, `MIT_GRUPPE`, `ANLAUFEN`,
     `NEHMEN`, `BESTREITEN` und `REIN`.
   - **zurück** sind `ZURUECK`, `RAUS`, `BACK_JETZT`, `WELLE_UND_RAUS`, `HALTEN_UNTER_TURM` und
     `ABGEBEN_TAUSCHEN`.
   - Für das alte System (nur Text) gelten `regeln.RUECKZUG` und `regeln.BACK` als zurück. Als vor gilt
     „Geh rein|nimm den Kampf an|Halte deine Stellung|Bleib an deiner Welle|Trade|Spiel auf|Geh auf|Drück|Nehmt“.

   Als neues Ereignis gilt:
   - neuer Gegner sichtbar,
   - Kill oder Tod,
   - dein Leben fällt um > 15 %,
   - ein Objective ist gefallen.
6. Kein Satz, der dem Plan widerspricht. Ein Planwechsel ist selbst ein Plan-Satz.
7. Kein „geh back“ in der Basis, kein „geh zurück zu deiner Basis“ in der Basis.

### 9.5 Dashboard

Der Kasten „Jetzt“ zeigt Modus, Plan mit Grund und die Top-3-Handlungen mit EV und je einem Grund. So sieht
Carlos jederzeit die Alternativen, auch wenn nur eine gesprochen wird. Das passt auch zu Riots Leitlinie für
Drittanbieter-Tools, wichtige Entscheidungen hervorzuheben und mehrere Optionen zu zeigen, statt sie
abzunehmen.

### 9.6 Verhältnis zu `sprechplan` / `stimme`

`stimme` bleibt unverändert. `sprechplan` bleibt Transport:

- Unterbrechen,
- „noch wahr“-Prüfung während des Sprechens,
- „Ach nee“ bei einem Planwechsel mitten im Satz,
- Vorwärmen.

Die **Auswahl** (`max(prio, …)`, Themen-Sperren, Widerspruchstabellen) entfällt für Kern-Ansagen. Der Kern
liefert höchstens eine Ansage je Takt. Sie ist eine normale `regeln.Ansage` mit diesen Werten:

| Kern-Kategorie | `prio` | Sonstiges |
|---|---|---|
| GEFAHR | `SOFORT` | `thema="gefahr"` |
| PLAN | `WICHTIG` | – |
| ERINNERUNG | `HINWEIS` | – |
| TECHNIK | `SOFORT` | – |

- `schluessel = "kern:<art>"`.
- `pruefe` = eine Funktion, die wahr bleibt, solange der Kern-Plan noch derselbe ist. Sie ersetzt
  `_noch_wahr` für Kern-Ansagen.
- `sprechplan.takt` bekommt eine Weiche: Ansagen mit `schluessel.startswith("kern:")` laufen an Themen-Sperre,
  Widerspruchs- und Rückzugs-Sperre **vorbei**. Das Budget prüft der Kern selbst. Transport, Unterbrechen und
  „Ach nee“ bleiben.

---

## 10. Fragen und Claude

### 10.1 Weiterleitung

`kern/fragen.py` ordnet jede Frage einer von sieben Absichten zu und leitet sie weiter. Die Absicht `FAKT`
ist nicht dasselbe wie die Sprech-Kategorie `INFO`.

| Absicht | Beispiele | Antwort aus |
|---|---|---|
| `JETZT` | „Was soll ich machen?“, „nächstes To-do?“, „Macroplay?“ | Plan + Ziel + Grund, sofort, ohne Claude |
| `WARUM` | „Warum?“, „Wieso soll ich …?“ | Plan-Grund + EV-Vergleich mit der Nummer zwei, sofort |
| `SOLL_ICH` | „Soll ich Drache solo machen?“, „Kann ich ihn killen?“ | Der Kern bewertet das Genannte als Handlung gegen den Plan: „Ja/Nein, weil …“, sofort |
| `WO` | „Wo ist der Jungler?“ | vorhandene Sofort-Antwort + `p_seite` |
| `FAKT` | Flash, Items, Timer, Platten | vorhandene Sofort-Antworten |
| `KAUF` | „Was soll ich kaufen?“ | `kaufplan`, sofort |
| `OFFEN` | alles andere, Abwägungen, Erklärungen | Claude mit `kern.kontext()` |

### 10.2 `kern.kontext()` für Claude

Höchstens 25 Zeilen, in dieser Reihenfolge:

1. Modus und Bereich („BASIS – du stehst in eurer Basis“).
2. Plan: Handlung, Ziel, Grund, die sechs Fragen.
3. Top-3-Handlungen mit EV und Grund.
4. Nur die Gegner und Mitspieler, die für diesen Modus zählen, mit Ort und Zeit.
5. Relevante Timer (Objective, Flash des Lane-Gegners, wenn LANE).
6. Gold, Kaufplan, eigene Zauber.

Was nicht mehr hineinkommt:

- **„Deine letzten Ansagen“.** Ausnahme: Die Frage bezieht sich darauf („was meinst du damit“). Dann kommt
  nur die letzte.
- **Die Rohlage `antworten.lage_text`** geht nicht mehr an Fragen. Sie wird noch von `stratege` benutzt
  (Midgame-Plan, situative Sätze). In Schritt 6 bekommt auch der Stratege `kern.kontext()`, danach kann
  `lage_text` weg.

### 10.3 Regeln im Systemprompt (ersetzen die heutigen Flicken-Sätze)

- „Der Kern hat entschieden (PLAN). Erkläre und formuliere; widersprich nur mit einem Grund, der in der Lage
  steht, und nenne dann beides.“
- „Spielfakten (Items, Preise, Fähigkeiten, Regeln) nur aus der mitgegebenen Liste oder dem
  Lexikon-Abschnitt; sonst ‚weiß ich nicht sicher‘.“
- „Ziel immer konkret (Lane, Turm, Objective, Name).“

### 10.4 Korrekturen von Carlos

Aussagen wie „ich bin in der Base“, „die Welle ist schon drin“ oder „Sett ist unten“ werden erkannt und
behandelt:

- Sie gelten 30 s als **Merkmal-Überschreibung** und lösen eine Neubewertung aus.
- Die Antwort bestätigt die Korrektur und gibt den neuen Plan.
- Jede Korrektur landet als Szenario-Kandidat in `tests/szenarien/offen/`.

Das hat niedrige Priorität, gehört zu Schritt 6 und kann entfallen, wenn die Wahrnehmung solche Fälle nach
Schritt 4 nicht mehr erzeugt.

---

## 11. Review nach Wirkung

1. **Datenlücken zuerst.** Das Review listet Zeiträume ohne Schnappschuss oder Minimap. In diesen Zeiträumen
   gibt es **keine** Aussagen über Position oder Verhalten. Heute schreibt `verlauf.py` „Du warst oben“ aus
   einer eingefrorenen Position.
2. **Lektion = Entscheidungsmoment.** Eine Lektion hat:
   - Zeit, Ort, Modus,
   - was passiert ist,
   - die bessere Handlung,
   - den geschätzten Verlust in GE,
   - einen Beleg.

   Die bessere Handlung kommt aus dem Kern: Der Kern läuft über die Aufnahme, und Momente, in denen die
   tatsächliche Handlung stark von seinem besten EV abweicht, sind Lektionskandidaten.
3. **Rangfolge nach GE-Verlust, nicht nach Häufigkeit.** Gewohnheiten (Kontroll-Auge, CS/min, Wardscore)
   stehen in einem eigenen kurzen Block. Sie werden Fokus nur, wenn sie der größte GE-Verlust sind.
   - Wenn derselbe Gewohnheits-Fokus dreimal nicht umgesetzt wurde, wiederholt das Review ihn nicht zum
     vierten Mal. Stattdessen wird er **live** eingebaut, z. B. `KAUFEN` nennt das Kontroll-Auge zuerst.
4. **Bot-Partien kennzeichnen.** Lektionen aus Bot-Partien tragen den Hinweis „gegen Bots – begrenzt
   übertragbar“. Der Fokus fürs Briefing kommt bevorzugt aus echten Partien.
5. **Sollwert für 102112:**
   - Die Lücke 15:55–24:24 wird genannt.
   - „Kontroll-Auge“ ist **nicht** Lektion 1.
   - Oben stehen:
     - das verpasste Ende-Fenster 36:32 (vier Tote, nur Mid-Inhib-Turm steht, Riven 10 s entfernt),
     - die Lage 28:01–32:24: Gold gehortet, 54 % der Zeit in der Basis, ohne Ziel. Dazu der Hinweis, dass
       der Coach selbst kein Ziel nannte.

---

## 12. Messen

### 12.1 Szenarien

`tests/szenarien/<aufnahme>.toml`. Das erste Beispiel liegt bei:
`tests/szenarien/2026-09-27_102112.toml`.

```toml
aufnahme = "2026-09-27_102112"
bots = true

[[szenario]]
id = "0517-platte-ohne-flash"
zeit = "5:17"                         # oder: fenster = ["8:50", "9:30"]
quelle = "Nachspielen 27.09.: Ansage 5:17, Gank 5:37"
lage = "…"                            # für Menschen
modus = ["LANE"]                      # erlaubte Modi (nur Kern)
soll = ["WELLE_REIN_UND_BACK", "BACK_JETZT"]   # Plan-Art des Kerns zur Zeit (±2 s)
darf_nicht = ["PLATTEN", "ALL_IN"]    # Plan-Arten, die im Fenster nicht vorkommen dürfen
darf_nicht_sagen = ["Platte"]         # Text, der in [zeit−2, zeit+15] nicht gesprochen werden darf
warum = "…"                           # die Begründung, Challenger-Sicht
```

**Weitere Schlüssel:**

| Schlüssel | Bedeutung |
|---|---|
| `kehrtwenden_max` | Obergrenze für Kehrtwenden im Fenster |
| `ansagen_max` | Obergrenze für Ansagen im Fenster |
| `frage` | Frage wie per Sprechtaste; geprüft wird die Antwort (zählt erst ab Schritt 6 zur Abnahme, außer ein Schritt sagt anderes) |
| `muss_nennen_eins` | Liste; die Antwort oder Ansage enthält mindestens eins davon |
| `muss_ziel` | `true`: eine gesprochene Zeile im Fenster nennt ein auflösbares Ziel |
| `muss_item` | `true`: die Antwort nennt ein Item aus der Ladenliste |
| `typ = "review"` | prüft das Review statt der Live-Ansagen, mit den Schlüsseln der nächsten vier Zeilen |
| `datenluecke = [von, bis]` | das Review nennt diese Lücke ausdrücklich (Zeitspanne ±10 s) |
| `lektion_1_nicht` | keiner dieser Texte steht in Titel oder „was“ der ersten Lektion |
| `oben_eins` | mindestens einer dieser Texte steht in Lektion 1 oder 2; Zeitangaben gelten als Präfix („28:0“ = 28:00–28:09) |
| `keine_position_in_luecke` | keine Zeitleisten-Zeile und kein Beleg im Lückenzeitraum enthält eine Ortsangabe („Du warst …“) |
| `[[modus_soll]]` | außerhalb der Szenarien: `zeiten` + erlaubte `modus`; Grundlage der Modus-Quote (5.3) |

**Läufer `werkzeuge/szenarien.py`:**

- Spielt die Aufnahme nach, wie `sinnpruefung.durchspielen`.
- `soll` ist erfüllt, wenn in **irgendeinem** Takt im Bereich zeit ±2 s der Kern-Plan eine der Arten hat.
  `darf_nicht` ist verletzt, wenn es **irgendein** Takt im Fenster ist.
- Texte werden ohne Unterschied von Groß- und Kleinschreibung verglichen.
- **Claude:** Standardmäßig ruft der Läufer Claude nicht auf. Dann gilt:
  - Teile, die eine Claude-Antwort bräuchten (`frage` bis Schritt 6, `typ = "review"`), stehen als
    „übersprungen“ in der Ausgabe.
  - Alle übrigen Teile desselben Szenarios werden trotzdem geprüft.
  - Mit `--mit-claude` wird Claude echt aufgerufen (kostet Zeit und Kontingent).
  - Ab Schritt 6 beantwortet der Kern `JETZT`/`WARUM`/`SOLL_ICH` selbst. Diese Fragen brauchen dann kein
    Claude mehr.
- Hält an den Zeitpunkten an und prüft jede Zeile gegen das **alte** System (nur Textprüfungen) und gegen den
  **Kern** (alles).
- Ausgabe: je Szenario grün/rot mit Grund. Am Ende steht die Quote.
- `--nur alt|kern` wählt das System.
- Das Ergebnis geht mit Datum nach `buecher/messungen.md`.

### 12.2 Neue Szenarien entstehen aus Carlos' Notizen

Die Sprechtaste kennt „Notiz …“ schon. `werkzeuge/szenario_aus_notizen.py` liest `aufnahmen/*_notizen.md`
und legt für jede Notiz einen Stub in `tests/szenarien/offen/<stamm>.toml` an. Der Stub enthält:

- Zeit und Notiztext,
- was der Coach ±20 s gesagt hat,
- die Lage aus der Bewertung: Ort, Leben, Gold, Welle, Gegner mit Ort und Zeit, Objectives.

Beschriftet werden die Stubs später, von Claude (Chat) mit Carlos, mit `soll`/`darf_nicht`/`warum`. Danach
wandern sie nach `tests/szenarien/`.

**Das ist der wichtigste Kanal, über den der Coach klüger wird.**

### 12.3 Kennzahlen (`werkzeuge/kennzahlen.py`)

Je Aufnahme, altes System und Kern nebeneinander:

- ungefragte Ansagen je 30 Minuten mit Daten
- Kehrtwenden ohne neues Ereignis (9.4 Punkt 5)
- Verstöße gegen 9.4, je Nummer
- Anteil GEFAHR / PLAN / ERINNERUNG
- `p_da`-Brier gegen den schlimmsten Fall (7.5)
- Datenlücken > 5 s (Beginn, Ende)
- Szenario-Quote

Die Grundlinie steht in Kapitel 1.2. `werkzeuge/sinnpruefung.py` geht darin auf.

### 12.4 Echte Partien

Ab sofort zählt für jede Abnahme **mindestens eine echte Partie** (Normal oder Ranked). Wenn der Coach nervt,
spielt Carlos mit `--stumm` und nimmt nur auf. Die Notizen per Sprechtaste gehen auch stumm.

---

## 13. Umbauplan

Jeder Schritt lässt den Coach spielbar zurück.

### Schritt 1 – Messen, nichts am Verhalten ändern

**Umsetzen:**

- `werkzeuge/szenarien.py` (nur Textprüfungen am alten System), `werkzeuge/kennzahlen.py`,
  `werkzeuge/szenario_aus_notizen.py`.
- `tests/szenarien/2026-09-27_102112.toml` laden. Jede `lage` per Nachspielen bestätigen. Weicht eine ab,
  wird das Szenario korrigiert und die Abweichung notiert.
- Grundlinie für die 5 jüngsten Aufnahmen messen und in `buecher/messungen.md` schreiben.
- **Datenlücke 15:55–24:24 in 102112 klären.** Ist sie Absturz, Neustart, Fensterwechsel oder API? Quellen:
  `_absturz_mitschreiben`, `*_sprechtaste.log`, Konsole. Beheben, wenn es ein Fehler des Coachs ist. In jedem
  Fall den Wachhund aus Kapitel 4.3 bauen (Wanduhr, „Ich sehe das Spiel gerade nicht …“, Lücke in der
  Aufnahme protokollieren). Das darf in Schritt 1 schon Verhalten ändern.
- `CLAUDE.md` ergänzen:
  - Verweis auf `buecher/`,
  - die neue Arbeitsweise (Beschwerde → Szenario → Modelländerung),
  - `--kern` in der Befehlsliste.
- `OFFEN.md` ergänzen: „In Arbeit: Buch 0, Schritt 1“. Alte offene Einzelpunkte, die der Kern ersetzt,
  werden als „ersetzt durch Buch 0“ markiert, nicht gelöscht.

**Abnahme:**

- Die Läufer laufen.
- Die Grundlinie ist eingetragen.
- Das alte System fällt bei mindestens 6 der 102112-Szenarien durch. Das ist erwartet und der Beleg, dass
  die Tests greifen.
- `tests/alle.py` ist grün.

**Carlos:** 2–3 echte Partien, gern `--stumm`. Jede Situation, in der er einen Rat gebraucht hätte, per Notiz
festhalten.

### Schritt 2 – Modus und Sofortmaßnahmen am alten System

**Umsetzen:**

- `kern/merkmale.py`, `kern/modus.py`, `wissen/kern.toml` mit den Abschnitten [modus] und [sprechen]
  (die anderen Abschnitte kommen in Schritt 3).
- Modus auf dem Dashboard, in `_kern.jsonl` und als erste Zeile jeder Claude-Frage.
- **Modus-Sperre** für die alten Regeln nach der Tabelle in Kapitel 14.
- **Objective-Fehler** (1.3 Punkt 5):
  - Objective-Auswahl nach Erreichbarkeit und Wert statt fester Reihenfolge,
  - die Laufzeit immer zum *genannten* Objective.
- Team-Befehle nur, wenn du rechtzeitig dort sein kannst. Sonst als Info mit Alternative.
- Kill-Ruf nur mit Beleg (6.2).
- Budget in `sprechplan`:
  - `abstand_s` für alles außer SOFORT,
  - `INFO`-Themen (Flash, Items, Level, CS) nur noch aufs Dashboard, außer Lane-Gegner/Jungler in `LANE`.
- Claude-Kontext:
  - „Deine letzten Ansagen“ nur noch, wenn die Frage darauf zeigt,
  - Modus + Bereich oben,
  - Lane-Gegner und Lane-Welle nur in `LANE`/`SEITE` oder wenn sie ≤ 3500 entfernt sind.

**Abnahme:**

- Modus-Sollwerte aus 5.3 zu ≥ 90 % getroffen.
- Die Textprüfungen (`darf_nicht_sagen`) der Szenarien `2522-kein-baron-drache-lebt`, `2847-baron-statt-drache`,
  `3535-rueckzug-31s` und `3004-basis-kauf-und-ziel` sind grün. `2601-frage-to-do` sollte durch den neuen
  Claude-Kontext schon grün werden; Pflicht ist es erst in Schritt 6.
- ≤ 70 ungefragte Ansagen je 30 min in 102112.
- Kehrtwenden ≤ 4.
- Generalprobe läuft.

**Carlos:** echte Partien mit Stimme, Notizen.

### Schritt 3 – Der Kern übernimmt LANE, BASIS, TOT

**Umsetzen:**

- `kern/handlung.py`, `wert.py`, `gefahr.py`, `plan.py`, `sprechen.py`, `modi/lane.py`, `modi/basis.py`,
  `modi/tot.py`.
- `--kern neu` wird Default. In diesen drei Modi sprechen die alten Regeln nicht mehr.
- Gefahr-Modell statt „frühestens“ (7.5), geeicht mit `kennzahlen.py`.

**Abnahme:**

- `0517-platte-ohne-flash`, `0850-kein-hin-und-her`, `0904-drei-kommen`, `3100-basis-braucht-ziel`
  grün (Kern). Bei `3004-basis-kauf-und-ziel` sind alle Teile außer der `frage` grün (die kommt in Schritt 6).
- Kehrtwenden = 0.
- In der Lane-Phase ≤ 1 ungefragte Ansage je 30 s im Mittel.
- `p_da` schlägt den schlimmsten Fall im Brier-Wert.
- Mindestens eine echte Partie ausgewertet.

**Parallel:** Buch 1 (Welle), Buch 2 (Trading, Top-Matchup-Logik) und Buch 3 (Recall/Tempo/Kauf) liefern die
Feinheiten für `modi/lane.py` und neue Szenarien.

### Schritt 4 – SEITE, GRUPPE, UNTERWEGS, VERTEIDIGEN

**Umsetzen:** `modi/seite.py`, `gruppe.py`, `unterwegs.py`, `verteidigen.py` auf Basis von `bewertung.ziele`.

**Abnahme:** `3632-ende-statt-back` und `3535-rueckzug-31s` über den Kern grün, 9.4 Punkt 1–4 verstoßfrei in 102112 und allen neuen echten Partien.

**Parallel:** Buch 5 (Mid-Game Top: Seite, TP, Gruppe gegen Split, Cross-Map).

### Schritt 5 – OBJECTIVE und KAMPF

**Umsetzen:** `modi/objective.py`, `modi/kampf.py`. Grundlage sind `bewertung.kampf_um` / `Kampflage`,
jetzt mit `fenster_gegner` und Objective-Dauer.

**Abnahme:** `2522-kein-baron-drache-lebt`, `2847-baron-statt-drache` und `3500-drache-solo` (ohne dessen
`frage`) über den Kern grün, nicht über die Sperre.

**Parallel:** Buch 6 (Objectives), Buch 7 (Kampf).

### Schritt 6 – Fragen

**Umsetzen:** `kern/fragen.py` (10.1–10.3), optional 10.4.

**Abnahme:** alle `frage`-Szenarien grün, ohne dass Claude für `JETZT`/`WARUM`/`SOLL_ICH` gebraucht wird.

### Schritt 7 – Review nach Wirkung

**Umsetzen:** Kapitel 11.

**Abnahme:** Szenario `review-102112` grün.

### Schritt 8 – Aufräumen

**Umsetzen:**

- **Vorher umziehen**, was `Regelwerk.pruefe` heute nebenbei erledigt, sonst bricht es beim Löschen:
  - den `bewertung.bewerte`-Aufruf,
  - `entscheider.jungle.neu` (den Jungletracker),
  - `rueckblick.merke` (die Todesanalyse),
  - die Haken `lage.jungle` und `lage.entscheider`, die `antworten.sofort` benutzt (ersetzen durch
    `lage.kern`),
  - die Übergabe `trade_hinweis` / `ult_warnungen` aus der Spielakte,
  - `puffer_sichern` beim Tod (`schritt_coach`).

  Das alles wandert in `Kern.takt` bzw. `Kern.__init__`.
- Danach `regeln.py`, `entscheider.py` und die Satzfabriken in `komponist.py`, die niemand mehr ruft,
  entfernen.
- `makro.toml` auf das reduzieren, was noch gelesen wird.
- `FAKTOREN.md` in „Merkmale und wo sie in Entscheidungen eingehen“ umschreiben.
- Die Tests der alten Regeln durch Szenarien ersetzen.

**Abnahme:** alles grün, keine toten Module.

---

## 14. Was mit den 24 alten Regeln passiert

„Sperre“ gilt ab Schritt 2 (die Regel spricht nur in diesen Modi). „Ersetzt“ gibt den Schritt an, ab dem der
Kern sie übernimmt.

| Regel (`Regelwerk._…`) | Sperre: spricht nur in | Ersetzt durch | Schritt |
|---|---|---|---|
| `_grosse_objectives` | alle außer TOT, KAMPF | Merkmal für OBJECTIVE/SEITE/GRUPPE, gesprochen als Grund | 5 |
| `_vorwarnung` | LANE, SEITE, GRUPPE, UNTERWEGS, BASIS | `VORBEREITEN_OBJECTIVE` / `VORBEREITEN` | 3/5 |
| `_zahlen` | alle außer TOT, KAMPF; nur wenn du rechtzeitig am genannten Ziel bist | `DRUECKEN` / `NEHMEN` mit `fenster_gegner` | 4/5 |
| `_jungler_tot` | LANE, SEITE | senkt `p_da` → Planwechsel, wenn EV es trägt | 3 |
| `_lane_tot` | LANE | `PLATTEN` / `WELLE_REIN_UND_BACK` | 3 |
| `_level` | LANE | Grund in `TRADE`/`ALL_IN` | 3 |
| `_items` | LANE, SEITE, nur Lane-Gegner nah | Grund; sonst Dashboard | 3/4 |
| `_gold` | LANE, SEITE, UNTERWEGS (nie BASIS) | `BACK_JETZT` / `WELLE_REIN_UND_BACK` | 3 |
| `_cs` | stumm (Dashboard, Review) | Review | 3 |
| `_tod` | TOT | `TODESRUECKBLICK` | 3 |
| `_jungler_gesehen` | LANE, SEITE | Gefahr-Modell; Sicherheit als Plan-Grund | 3 |
| `_lane_fehlt` | LANE | Gefahr-Modell | 3 |
| `_leben` | LANE, SEITE, UNTERWEGS | `BACK_JETZT` / `ZURUECK` | 3 |
| `_zauber` | Dashboard; gesprochen nur Lane-Gegner/Jungler in LANE/SEITE | INFO; Grund in Plänen | 3 |
| `_anlauf` | LANE, SEITE, UNTERWEGS, GRUPPE, OBJECTIVE | GEFAHR aus dem Gefahr-Modell | 3/4 |
| `_ward` | LANE, UNTERWEGS, OBJECTIVE | `WARD` als Plan-Schritt | 3/5 |
| `_recall_fenster` | LANE, SEITE | `WELLE_REIN_UND_BACK` | 3 |
| `_tief_ohne_sicht` | LANE, SEITE | Gefahr-Modell | 3/4 |
| `_kontrollauge` | BASIS, TOT | Teil von `KAUFEN` | 3 |
| `_objective_start` | OBJECTIVE, UNTERWEGS, GRUPPE | `ANLAUFEN` / `NEHMEN` / `ABGEBEN_TAUSCHEN` | 5 |
| `_fenster` | LANE, SEITE, Lane-Gegner ≤ 3500 | `TRADE` / `ALL_IN` | 3 |
| `_plan` (Entscheider) | je Plan-Art: Lane-Pläne nur LANE/SEITE, `wohin` nur außerhalb LANE | `kern.plan` | 3–5 |
| `_wiedereinstieg` | TOT | `KAUFEN` + `WOHIN` vor dem Respawn | 3 |
| `_afk` | alle, einmal | Merkmal (Teamstärke) | 8 |
| `stratege` (über `plan.einwerfen`: Briefing, Midgame-Plan, situative Sätze) | Briefing einmal; der Rest nur außerhalb von KAMPF und GEFAHR | Briefing bleibt; Midgame-Plan und situative Sätze als `INFO` oder als `grund` (9.1) | 3/6 |
| `minimap_gesund` (`sprecher.sage` direkt) | alle | `TECHNIK` (9.1) | 3 |

---

## 15. Die weiteren Bücher

Jedes Buch hat dieselbe Form:

1. Prinzipien (kurz, für Menschen und als Claude-Kontext)
2. Für jede Handlung seines Modus: wann sie Kandidat ist, was sie braucht, welche Größen ihr EV verschieben,
   Satzform
3. Neue Parameter für `kern.toml` (mit Stand)
4. Szenarien mit Sollwerten und Begründung

| Buch | Thema | Füttert |
|---|---|---|
| 1 | Welle: Slow-Push, Freeze, Crash, Bounce, Kanonenwellen, Wellenwert | `modi/lane.py`, `WELLE_*` |
| 2 | Lane: Trading, Kill-Schwellen, Level-Spikes, Top-Matchup-Logik | `TRADE`, `ALL_IN` |
| 3 | Recall, Tempo, Kauf: Back-Fenster, Spike-Schwellen, Wiedereinstieg | `BACK_*`, `KAUFEN`, `WOHIN` |
| 4 | Jungler-Wahrscheinlichkeit und Sicht: Pfade 2026, Ward-Stellen mit Informationswert | `gefahr.py`, `WARD` |
| 5 | Mid-Game als Toplaner: Seite, Teleport, Gruppe gegen Split, Cross-Map-Tausch, Ende | `modi/seite.py`, `gruppe.py`, `unterwegs.py` |
| 6 | Objectives 2026: Larven, Herold, Drache, Seele, Baron, Ältester – Werte, Dauer, Setup | `modi/objective.py`, `[objective_wert]` |
| 7 | Kampf und Teamfight als Bruiser: Ziele, Flanke, wann raus | `modi/kampf.py` |
| 8–10 | Riven, Camille, Graves: Combos, Spikes, Matchups als Parameter | `combo`, `lane_kurve`, `modi/lane.py` |
| 11 | Wie ein Coach lehrt: Review, Fokus, Wiederholung | `review.py` |

Reihenfolge: 1 → 3 → 2 → 4 → 5 → 6 → 7 → 8 → 9/10 → 11. Nach jedem Buch spielt Carlos, die Notizen werden
Szenarien, erst dann folgt das nächste Buch.

---

## Anhang A – Begriffe

| Begriff | Bedeutung |
|---|---|
| **Modus** | was gerade dein Job ist (Kapitel 5) |
| **Handlung** | eine konkrete Option mit Ziel, Wert und Grund (Kapitel 6) |
| **Plan** | die gewählte Handlung, die gehalten wird (Kapitel 8) |
| **GE** | Gold-Äquivalent, die gemeinsame Währung (Kapitel 7) |
| **p_da** | Wahrscheinlichkeit, dass ein Gegner im Fenster bei dir ist (Kapitel 7.5) |
| **Kehrtwende** | vor ↔ zurück in ≤ 30 s ohne neues Ereignis |
| **Szenario** | Lage aus einer Aufnahme mit Sollwert (Kapitel 12) |

## Anhang B – 36:32 in Partie 102112, mit dem neuen Kern

**Lage:**

- Riven L20, 99 % Leben, 4461 Gold, auf der Mid-Lane an der Stelle des gefallenen äußeren Mid-Turms.
- Fiddlesticks, Galio, Kai'Sa und Sona sind tot (noch 20, 19, 17 und 14 s). Sett steht oben.
- Von den gegnerischen Türmen steht nur noch der Mid-Inhibitor-Turm (dazu die Nexus-Türme). Riven ist ~10 s
  davon entfernt.
- Brand, Corki und Tryndamere sind im eigenen unteren Jungle.

**Modus:** UNTERWEGS. Keine zwei Mitspieler in 2000. Mit `DRUECKEN` wird der Plan zu GRUPPE, sobald das Team
nachzieht.

**Kandidaten:**

| Handlung | Einschätzung |
|---|---|
| `DRUECKEN` (Mid-Inhibitor-Turm, dann Inhibitor) | `fenster_gegner` ≈ Respawn 14 s + Weg aus dem Brunnen ≈ 10 s = ~24 s. Riven braucht 10 s Weg + ~8 s am Turm. Gewinn: Turm + Inhibitor + Nexus-Druck, Spiel fast entschieden. Folgewert sehr hoch. |
| `BACK_JETZT` | +4461 Gold in Items, aber das Fenster ist danach zu. |
| `SEITENWELLE` | klein |

**Plan:** `DRUECKEN`. `grund` = „vier von ihnen sind noch 14 Sekunden tot“.

**Satz:** „Mid-Inhibitor-Turm jetzt: vier von ihnen sind noch 14 Sekunden tot. Ruf dein Team.“

Danach folgt `BACK_JETZT` als nächster Schritt, wenn das Fenster zu ist.
