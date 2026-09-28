# Buch 5 – Mid-Game als Toplaner

Stand 27.09.2026 · für Claude Code, Umbau-Schritt 4 (Modi `SEITE`, `GRUPPE`, `UNTERWEGS`, `VERTEIDIGEN`) ·
setzt Buch 0, 1 und 3 voraus · Wissen dazu: `wissen/lexikon/grundlagen.md` (Top-Lane im Detail, Splitpush,
Teamfight und Kartenzustand) und `saison2026.md`.

---

## 0. Worum es geht

Ab 14:00, oder sobald ein Außenturm deiner Lane fällt, hast du keine feste Lane mehr. Die Frage ist dann nicht
mehr „was mache ich mit meiner Welle“, sondern:

> **Wo auf der Karte schafft meine Zeit gerade den meisten Wert – und wer bestraft mich dafür?**

In 102112 hat der Coach genau das nie beantwortet:

- 28:01–32:24 stand Riven mit bis zu 3244 Gold 54 % der Zeit in der eigenen Basis, ohne Ziel.
- 36:32 riet er zu „back“, obwohl vier Gegner tot waren und nur noch ihr Mid-Inhibitor-Turm stand.
- 35:35 schickte er Riven von der Drachengrube 31 s zu einem Turm auf der anderen Kartenseite.

Toplaner verlieren Mid-Games meist auf eine von zwei Arten:

- sie stehen auf der falschen Seite der Karte, wenn ihr Team kämpft,
- sie laufen ohne Welle und ohne Plan mit der Gruppe mit, während Seitenwellen ihre Türme fressen.

Beides lässt sich mit den Daten, die wir haben, erkennen.

**2026 dazu** (`saison2026.md`):

- Platten bleiben bis zum Turmfall. Außentürme sind im Mid-Game also noch Gold wert.
- Unberührte Türme bauen Kristalle auf. Der erste Treffer macht viel Echtschaden, deshalb sind unberührte
  Türme gute Split-Ziele.
- Ab Ende der Top-Quest (spätestens 13:35) hat **jeder** Toplaner TP, auch der gegnerische.
- Wellen kommen alle 25 s (ab 30:00 alle 20 s).

---

## 1. Was wir messen – neu für Schritt 4

| Merkmal | Inhalt | Quelle |
|---|---|---|
| `wellen[lane]` | `WellenStand` für **alle drei** Lanes (Buch 1, 1.2), nicht nur deine | `WellenPuffer` je Lane aus `Lagebild.welle` |
| `seitenwelle[lane]` | eine Welle mit ≥ `seitenwelle_min` Vasallen läuft auf **euren** Turm, kein Mitspieler ≤ 3000 dort | `wellen` + `mitspieler` |
| `gegner_orte` | je Gegner: tot (noch s), gesehen vor ≤ 10 s (wo), unbekannt | `Bewertung.gegner` |
| `woanders` | wie viele Gegner ≤ 10 s alt **weit weg von dir** gesehen wurden (> 6000) oder tot sind | daraus |
| `teamkampf` | ≥ 2 Mitspieler und ≥ 2 Gegner sichtbar in `teamkampf_radius` voneinander, **und** Leben fällt (HUD-Leiste oder Tode). Dazu Ort, Zahlen, seit wann. | `mitspieler`, HUD, Ereignisse |
| `tp_gegner_top` | TP des gegnerischen Toplaners: bereit / weg bis … | `zauber` (Pings, Minimap-Sprünge) |
| `ziele_karte` | alle Kandidaten-Ziele mit Weg und Fenster: vorderster Turm je Lane (vorhanden: `bewertung.ziele`), Seitenwellen, Objectives (`m.objectives`), Gruppe | – |

**`teamkampf` ist neu und wichtig**, für den TP (Kapitel 5) und für „Gruppe braucht dich“ (Kapitel 4). Liefert die
HUD-Leiste kein Leben, gilt ein Kampf erst beim ersten Tod. Dann ist er für TP meist schon zu spät. Deshalb soll
es früh erkannt werden.

---

## 2. Die Karten-Rechnung: ein Ziel wählen

Für jedes Ziel `z` in `ziele_karte` rechnet der Kern:

```
EV(z) = gewinn(z) · p_erfolg(z)  −  weg(z) · zeitwert  −  p_tod(weg + dauer) · todeskosten  +  folgewert(z)
```

| Ziel | `gewinn` | `dauer` | Besonderheit |
|---|---|---|---|
| Turm drücken | Platten (bis Turmfall) + Turmgold global + `turm_extra`; ×1,3 bei unberührtem Turm (Kristalle) | Platten/Turmleben ÷ deinen Turmschaden, grob `turm_dauer_s` je Stufe | nur, wenn der erste Verteidiger (`verteidiger_ab`) später kommt als `weg + dauer`, oder du ihn schlägst |
| Seitenwelle | Wellenwert × Wellen im Stapel + verhinderter Turmschaden (`seitenwelle_turmschutz`, wenn sie sonst Platten/Turm frisst) | Weg + ~10 s | gut, wenn sonst niemand dort ist |
| Gruppe / Objective | Buch 6 (`OBJECTIVE`), bis dahin `[objective_wert]` × p(ihr nehmt es) | – | nur, wenn du **rechtzeitig** da bist |
| Back | Buch 3 (Gold, Leben) | Kanal + Weg | Hortregel ab `horten_ab` |

**Gewählt wird nicht jeden Takt neu.** Der Plan hält (Buch 0, 8), bis das Ziel erreicht, ungültig oder deutlich
schlechter ist.

**Gesagt wird das Ziel**, wenn der Plan neu ist oder du ohne Plan herumstehst: in der Basis (Buch 0, Warteregel)
oder > 20 s ohne Ortswechsel außerhalb der Lane. Läufst du schon dorthin, schweigt der Coach.

---

## 3. SEITE – auf einer Seitenlane nach der Lane-Phase

### 3.1 Bleiben oder gehen? Die Split-Regel

Seite halten (`DRUECKEN` oder `SEITENWELLE` auf dieser Lane) ist Kandidat, wenn **alle** drei gelten:

1. **Kein Objective ruft dich.**
   - Ohne eigenes TP: nichts auf der anderen Seite spawnt in ≤ `rotation_vorlauf_s` (60 s).
   - Mit TP bereit darfst du bis zum Kampfbeginn bleiben (Kapitel 5).
   - Objectives auf **deiner** Seite (Herold, Baron): vorher Welle rein und hin, Buch 6.
2. **Du kannst die Antwort schlagen.** „Antwort“ ist, wer dich wahrscheinlich stoppen kommt: der Gegner mit dem
   kürzesten Weg, meist ihr Toplaner. Es gilt `kraft_gegen([antwort]) ≥ split_kraft_min` (1,2), **oder** es
   braucht ≥ 2 Gegner, um dich zu stoppen. Dann ist dein Split auch gut, wenn sie mit zwei kommen, denn dein Team
   ist 4 gegen 3.
3. **Tiefe-Regel.** Hinter ihrem vordersten Turm dieser Lane nur, wenn einer der beiden Fälle zutrifft:
   - ≤ `tiefe_unbekannt_max` (1) Gegner sind unbekannt,
   - oder `woanders ≥ tiefe_woanders_min` (3), also drei sind ≤ 10 s alt woanders gesehen oder tot.

   Sonst Welle bis zur Flussmitte der Lane, dann halten. Das Gefahr-Modell (7.5) greift zusätzlich, Tiefe steigert
   p_da.

### 3.2 Die Handlungen

| Art | Kandidat, wenn | Ziel | Satz (Beispiel) |
|---|---|---|---|
| `DRUECKEN` | Split-Regel erfüllt, Turm vor dem ersten Verteidiger erreichbar | konkreter Turm | „Drück den inneren Top-Turm: Sett ist unten, 25 Sekunden Fenster.“ |
| `SEITENWELLE` | Welle dieser Lane `ZU_DIR` / `GROSS_ZU_DIR` oder `seitenwelle` | die Welle | „Hol die Top-Welle: acht Vasallen laufen in deinen Turm.“ |
| `PLATTEN` | wie Buch 1, 3.6 – Platten gibt es auch nach 14:00 | Turm | „Platte am äußeren Top-Turm: Sett ist noch 20 Sekunden tot.“ |
| `WELLE_UND_RAUS` | Objective auf der anderen Seite in 45–75 s, **kein** TP: Welle crashen, dann rotieren | Welle, dann Ort | „Top-Welle rein, dann zum Drachen: Spawn 20:00, du brauchst 35 Sekunden.“ |
| `ZUR_GRUPPE` | `teamkampf` oder Objective, bei dem du den Unterschied machst, und du bist rechtzeitig da | Ort/Grube | „Zum Drachen, jetzt: ihr seid dort 4 gegen 5, mit dir 5 gegen 5.“ |
| `TP_SPIEL` | Kapitel 5 | Ort | „TP zum Drachen, hinter sie: der Kampf fängt gerade an.“ |
| `BACK_JETZT` / `WELLE_REIN_UND_BACK` | Buch 3 mit dem `WellenStand` **dieser** Lane | Basis | wie Buch 3 |
| `ZURUECK` | Gefahr-Modell | sicherer Ort | „Raus zu deinem inneren Top-Turm: drei von ihnen fehlen.“ |

**Wichtig gegen den alten Fehler:** Auf einer Seitenlane heißt die Welle „deine Top-Welle“ nur auf Top. Steht
Carlos auf Bot, ist es „die Bot-Welle“. „Seinen Turm“ gibt es nicht mehr, sondern „den äußeren Bot-Turm“.

---

## 4. GRUPPE – mit dem Team unterwegs

Carlos steht mit ≥ 2 Mitspielern zusammen, meist Mid oder am Fluss.

| Art | Kandidat, wenn | Satz |
|---|---|---|
| `MIT_GRUPPE` | Struktur in Reichweite, Überzahl oder gleich + Fenster (`verteidiger_ab`) | „Mit der Gruppe auf den inneren Mid-Turm: Sona und Galio sind tot.“ |
| `SEITENWELLE` | `seitenwelle[lane]` auf **deiner** Seite (Top, weil du Toplaner bist), **und** nichts in ≤ `seitenwelle_frei_s` (30 s) bei der Gruppe | „Hol die Top-Welle: neun Vasallen am äußeren Top-Turm, Drache erst in 2 Minuten.“ |
| `BACK_JETZT` | Buch 3; in der Gruppe nur, wenn gerade kein Objective und kein Kampf ansteht | „Back jetzt, 2800 Gold: nichts steht an, Baron erst 26:00.“ |
| `ANLAUFEN` | Objective – Schritt 5 (Buch 6); bis dahin wie Schritt 2 (Objective-Auswahl) | – |

**Gegen das „ARAM-Mid“:** Stehen 4–5 von euch in der Mitte ohne Ziel, während eine Seitenwelle an euren Turm
läuft, wird `SEITENWELLE` gewählt. Das gilt für den, dessen Seite es ist. Der Coach redet nur mit Carlos, also
für Carlos, wenn es Top ist oder er der Nächste ist.

---

## 5. TP_SPIEL (Top, eigenes TP bereit)

**Kandidat, wenn alles gilt:**

- `teamkampf` erkannt oder Objective läuft,
- ≥ 2 eigene beteiligt,
- du bist > 25 s zu Fuß entfernt,
- der Kampf dauert voraussichtlich noch ≥ `tp_kampf_rest_s` (6 s). Grob heißt das: Er läuft ≤ 3 s, oder es ist
  ein Objective-Start mit Gegnern in der Nähe.
- **und** deine Ankunft ändert die Zahlen: mit dir mindestens gleich viele, oder der Carry lebt.

**Nicht,** wenn:

- der Kampf schon kippt: ≥ 2 eigene tot und keine Gegner-Tode,
- oder das Ziel-Objective ist schon unter 30 %. Das ist nicht messbar, deshalb gilt ersatzweise: Objective lebt
  seit > 20 s mit ≥ 2 von euch dort.

**Ziel:**

- Ward, Vasall oder Turm **hinter** den Gegnern, wenn es gibt (Flanke).
- Sonst der nächste eigene Turm. Dann heißt der Satz „TP an den Turm, dann rein“.

**Satz:** „TP zum Drachen, hinter sie: ihr seid 4 gegen 5.“

**Gegen-TP:** Hat ihr Toplaner **kein** TP (`tp_gegner_top` weg), ist der Satz „Sett hat kein TP bis 24:10: der
Kampf ist 5 gegen 4“ als Grund wertvoll. Umgekehrt: Hat er TP und du nicht, gilt `WELLE_UND_RAUS` früher,
`rotation_vorlauf_s` + 15.

---

## 6. UNTERWEGS

Carlos ist im Fluss, im Jungle oder Mid ohne Gruppe. Der Kern wählt das beste Ziel aus Kapitel 2. Er sagt es
nur, wenn

- der Plan neu ist,
- **oder** Carlos seit > 20 s nicht in Richtung des Ziels läuft. Dann ist es eine Erinnerung, einmal.

Dazu kommt eine Ward-Stelle auf dem Weg als Schritt, wenn Kontroll-Auge oder Trinket bereit ist. Die Ward-Stellen
selbst liefert Buch 4. Bis dahin gibt es diesen Schritt nicht.

---

## 7. VERTEIDIGEN

Eintritt nach Buch 0, 5.1, in der Fassung aus Schritt 2.

| Art | Kandidat, wenn | Satz |
|---|---|---|
| `WELLE_KLAEREN` | gegnerische Welle, auch Supervasallen, an eurem Turm/Inhibitor, du bist ≤ 15 s entfernt, ≤ 1 Gegner dort sichtbar | „Klär die Mid-Welle am Inhibitor-Turm: Supervasallen, keiner von ihnen dort.“ |
| `HALTEN_UNTER_TURM` | ≥ 2 Gegner belagern, ihr seid dort weniger | „Bleib hinter dem Turm, nicht rein: zu dritt gegen fünf. Klär nur, was kommt.“ |
| `TAUSCHEN` | Verteidigung aussichtslos (`kraft_gegen` < 0,6) **und** ein gleichwertiges Ziel woanders ist in ≤ 20 s erreichbar | „Die Mid-Seite ist verloren – drück den äußeren Top-Turm, dort ist keiner.“ |

### Nachtrag 7.1 – Belagerung der eigenen Basis (Auftrag 007, 28.09.2026)

Entschieden von Carlos (Antwort auf `005_frage.md`, 2). Anlass war 173159, 36:50: „Zwei eurer Türme weg. Dann
Top-Welle.“ Der Gegner hatte den Ältesten-Buff und belagerte die Basis.

**Auslöser**, eines davon reicht:
- ≥ 3 Gegner sichtbar in 3000 um euren Inhibitor-Turm, Inhibitor oder Nexus;
- ≥ 2 eigene Türme (oder Inhibitoren) fallen in 30 s;
- der Gegner hat den Baron- oder Ältesten-Buff, und ≥ 3 von ihnen stehen in eurer Hälfte.

**Wirkung:**
- Der Modus ist VERTEIDIGEN, auch aus der Ferne (nicht in der Lane-Phase).
- `WELLE_KLAEREN` und `HALTEN_UNTER_TURM` gelten dann ohne die Grenze von 15 s. Der Weg zählt als Kosten über die Dauer.
- Gibt es keinen solchen Kandidaten, heißt es `ZUR_GRUPPE` zum belagerten Ort: „Zurück, verteidige euren
  Mid-Inhibitor: drei von ihnen an eurem Mid-Inhibitor.“

**Ausnahme Nexus-Rennen:** Du bist selbst in ihrer Basis, einer ihrer Inhibitoren ist weg, und ≥ 2 von euch sind dort.
Dann fällt ihr Nexus vor ihrer Ankunft an eurem, und die Belagerung holt dich nicht zurück.

**Abweichung:** „≥ 3 auf einer Lane in eurer Hälfte“ wird als „≥ 3 in eurer Hälfte“ gelesen. Die Lane-Zuordnung
unbekannter Positionen ist zu unsicher.

Parameter: `[modus] belagerung_radius`, `belagerung_gegner`, `belagerung_tuerme_s`, `belagerung_gewinn`.

---

## 8. Umwandeln: nach einem gewonnenen Kampf

Das ist der 36:32-Fall und die Abnahme von Schritt 4. Nach jedem Kampf fragt ein Challenger „Was nehmen wir
jetzt?“, bevor er „back“ sagt.

**Auslöser:**

- ≥ `umwandeln_ueberzahl` (2) Gegner mehr tot als eigene,
- **und** der kürzeste Respawn ≥ `umwandeln_fenster_min_s` (15 s),
- **und** du lebst mit ≥ 30 % Leben.

**Dann gelten `DRUECKEN` und `MIT_GRUPPE` vor `BACK_JETZT`**, solange das Fenster reicht. Maßgeblich ist
`verteidiger_ab`: Respawn plus Weg vom Brunnen.

Reihenfolge der Ziele, das erste erreichbare gewinnt:

1. Nexus-Türme und Nexus, wenn ein Inhibitor offen ist,
2. Inhibitor-Turm, dann Inhibitor,
3. Baron / Ältester (Schritt 5),
4. innerer Turm,
5. Drache,
6. äußerer Turm.

Jeweils muss gelten: dein Weg + Dauer < Fenster.

**Gold im Beutel wartet.** Back kommt als nächster Plan-Schritt, wenn das Fenster zu ist.

**Satz:** „Mid-Inhibitor-Turm jetzt: vier von ihnen sind noch 14 Sekunden tot.“

Wenn kein Mitspieler nachkommt und du allein bist: „… ruf dein Team.“ Die Grenze für allein: 2 Gegner leben und
können rechtzeitig kommen → nur Turm, kein Inhibitor-Dive.

---

## 9. Bestätigungen (Buch 3, Kapitel 5)

| Moment | erkennbar | Satz |
|---|---|---|
| Welle rein, dann rotiert | Plan `WELLE_UND_RAUS` erfüllt, Ankunft vor dem Spawn | „Genau so – Welle drin und pünktlich da.“ |
| Umgewandelt | Plan `DRUECKEN`/`MIT_GRUPPE` nach einem Kampf, Struktur gefallen | „Sauber umgewandelt.“ |
| Guter TP | Plan `TP_SPIEL`, danach ≥ 1 Gegner-Tod und du lebst | „Guter TP.“ |
| Seitenwelle gerettet | Plan `SEITENWELLE`, die Welle erreichte den Turm nicht oder du hast sie abgeräumt | „Welle gerettet – kein Turm verloren.“ |

---

## 10. Parameter für `wissen/kern.toml`

```toml
[mitte]
stand = "Buch 5, 27.09.2026 - Startwerte (Schaetzung), an Szenarien kalibrieren"
seitenwelle_min = 6
seitenwelle_frei_s = 30
seitenwelle_turmschutz = 150    # GE: verhinderter Platten-/Turmschaden
turm_dauer_s = { aussen = 25, innen = 20, Inhib = 18, nexus = 15 }   # allein, grob; Buch 8-10 je Champion
kristall_faktor = 1.3
rotation_vorlauf_s = 60
split_kraft_min = 1.2
tiefe_unbekannt_max = 1
tiefe_woanders_min = 3
teamkampf_radius = 1500
tp_kampf_rest_s = 6
tp_zu_fuss_ab_s = 25
umwandeln_ueberzahl = 2
umwandeln_fenster_min_s = 15
ohne_plan_s = 20
```

---

## 11. Szenarien

### 11.1 Aus Aufnahmen (vorhanden)

| Szenario | Datei |
|---|---|
| `3632-ende-statt-back` (Kapitel 8) | Hauptdatei 102112 |
| `3535-rueckzug-31s` (sicherer Ort) | Hauptdatei 102112 |
| `3100-basis-braucht-ziel` | Hauptdatei 102112 |
| `1315-crash-dann-back` | `_buch3.toml` |

### 11.2 Konstruiert

`tests/szenarien/konstruiert/mitte.toml`. Das Format ist erweitert um `wellen`, `mitspieler`, `gegner`, `tuerme`,
`teamkampf` (Kopfkommentar der Datei). `kern/testlage.py` braucht dafür eine Erweiterung.

### 11.3 Aus echten Partien

Aus Carlos' nächsten echten Partien werden Momente nach 14:00, zu denen er eine Notiz gesprochen hat, Stubs.
`werkzeuge/szenario_aus_notizen.py` gibt es schon. Beschriften: Claude im Chat.

**Abnahme Schritt 4:**

- `3632` und `3535` über den Kern grün,
- `1315` grün,
- alle Lagen in `mitte.toml` grün,
- 9.4 Punkt 1–4 ohne Verstoß in allen Aufnahmen,
- ungefragte Ansagen je 30 min über die ganze Partie ≤ 50,
- mindestens eine echte Partie mit Mid-Game (> 20 min) ausgewertet.
