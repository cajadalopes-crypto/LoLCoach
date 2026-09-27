# Buch 6 – Objectives 2026

Stand 27.09.2026, Patch 26.19. Fakten aus `wissen/lexikon/saison2026.md` und dem Wiki (am 27.09. geprüft, Quellen am
Ende). Bei Widerspruch gilt der neuere, belegte Wert; `saison2026.md` wird dann mitkorrigiert (Kapitel 12).

Dieses Buch füttert:

- `kern/modi/objective.py` (Schritt 5)
- `kern/objective.py` (neu: die Rechnung je Objective, von allen Modi benutzt)
- `[objective]` und `[objective_wert]` in `wissen/kern.toml`

**Für Claude Code:**

- Lies zuerst Buch 0, Kapitel 0, 5, 6.3, 7 und 8, dann Buch 5, Kapitel 2, 5 und 8, und Buch 7, Kapitel 3 (das
  Kampfurteil, das dieses Buch benutzt).
- Stellen, die ein anderes Buch ändern, sind mit **„Ändert Buch X, Y“** markiert. Alles andere ergänzt.
- Jede Zahl steht in `kern.toml` (Kapitel 11), keine im Code.

---

## 0. Befund: was heute schiefgeht

Aus den Protokollen vom 27.09. (`buecher/protokolle/`):

1. **Der Larven-Sog.** In zwei echten Partien schickte der Coach Carlos zu den Larven, ohne dass etwas dafür sprach:
   - 144655, 6:47: „Stapel die Top-Welle … dann crashen und zu den Larven.“ Gangplank hatte ihn zweimal allein
     getötet, Kha'Zix war oben. Um 9:15 stand Riven mit 19 % mitten in einem Kampf an der Grube.
   - 140253 (Riven Mid), 6:47: „… dann zu den Larven: Spawn 8 00, du bist 7 01 dort.“ Das ist eine Minute zu früh,
     und die Mid-Welle ist verloren. Um 10:25 kam, während er tot war: „zu den Larven: Larven leben“, mit p_tod 0,97.

   **Ursache:** Ein Objective zieht, sobald es lebt oder bald spawnt. Ob euer Team es nehmen kann und ob **du** dafür
   gebraucht wirst, prüft niemand. Das steckt an vier Stellen: STAPELN (Buch 1, 3.3), OBJECTIVE_VORLAUF (Buch 3),
   WOHIN (Buch 3) und `karte.objective_ruft` (Buch 5).
2. **Die falsche Grube.** Der Coach sagte Baron, als der Drache frei war (25:22, 28:47). Die Ursache ist ein
   Code-Fehler, Baron kommt immer zuerst. Die Sperre aus Schritt 2 verdeckt das, gelöst ist es nicht.
3. **Zahlen ohne Handlung.** 102112 25:16 und 33:35: „Ihr seid 4 gegen 3 … aber kein Turm ist von dir aus
   rechtzeitig zu erreichen.“
4. **Gründe gegen das eigene Ziel.** 26:37: „Geh auf den Top-Inhibitor-Turm, 39 Sekunden von dir: Sett ist noch
   29 Sekunden tot.“
5. **OBJECTIVE verdrängt Wichtigeres.**
   - 38:31, in ihrer Basis, alle fünf tot, der Nexus-Turm fällt. Trotzdem gilt Modus OBJECTIVE, weil ein Mitspieler
     an einer Grube stand, und die alte Regel sagt: „Drückt jetzt den Mid-Inhibitor-Turm.“
   - 34:51, an der Drachengrube, der Drache lebt, drei tot: „Geh auf den Mid-Inhibitor-Turm, 19 Sekunden …“
6. **Drei Sätze statt einem.** 14:53: „Nimm keinen Kampf an, ihr seid nur zu dritt: … Gib den Herold lieber ab. Geh
   zurück zu deinem Top-Tier-1-Turm.“

## 1. Prinzipien

1. **Ein Objective ist ein Teamziel. Gezählt wird, was DU daran änderst.**
   - Zuerst fragt der Coach: Kann euer Team es nehmen, bevor sie es verhindern?
   - Dann fragt er: Wie viel wahrscheinlicher wird es, wenn du hingehst?
   - Nimmt das Team es sicher ohne dich, ist dein Weg dorthin verschenkt.
2. **Fenster schlägt Zahl.** „5 gegen 3“ sagt nichts, wenn die drei in 5 s da sind. Es zählt, wer bis zum Ende der
   Tötungszeit an der Grube sein kann, auf beiden Seiten.
3. **Kein Objective ohne Welle.**
   - Erst die eigene Welle rein oder sicher (Buch 1), dann los.
   - Ankunft rechtzeitig (Kapitel 4.1), nie eine Minute vorher.
4. **Abgeben ist ein Plan.** Geht ein Objective verloren, sagt der Coach, was ihr dafür bekommt. Ein bloßes „nicht
   hingehen“ ist keine Handlung.
5. **Große Objectives sind anders.**
   - Seelenpunkt, Seele, Ältester und Baron entscheiden Spiele. Dort ist Bestreiten auch bei knapp unter
     Gleichstand richtig.
   - Kleine Drachen gibt man ab, wenn der Tausch gleich viel bringt.
6. **Ein Satz je Entscheidung.** Er enthält Handlung, Objective und den einen Grund dafür. Das Urteil hält, bis ein
   Ereignis es kippt: Tod, Spawn, Sichtung eines Unbekannten, eine Struktur fällt.

## 2. Die Objectives 2026

| Objective | Spawn | Wiederkehr / Ende | Belohnung | Warum es zählt |
|---|---|---|---|---|
| Drache | 5:00 | 5:00 nach Tod | 75 g Kill-Gold, Drachen-Buff dauerhaft; Elemental Rift nach dem 2. Drachen | stapelt zur Seele |
| Seele | 4. Drache eines Teams | – | starker Dauer-Buff | spielentscheidend |
| Ältester | nach der Seele (Zeit: Kapitel 12, prüfen) | 6:00 | 850 g, 3250 XP global, Hinrichtung | spielentscheidend |
| Leerenlarven | 8:00, einmal 3 Stück | verschwinden 14:45 (im Kampf 14:55) | 30 g je Larve an den Killer; „Hunger der Leere“ erst mit dem 3. Stapel | Tempo gegen Strukturen, nur bei 3:0 |
| Herold | 15:00, einmal | verschwindet 19:45 (im Kampf 19:55) | 100 g; Auge liegt 20 s am Grubeneingang; Ritt mit Ramme: 3000 Echtschaden an einem Turm, verbraucht dessen Kristall | Platten und Turm auf einer Seite |
| Baron | 20:00 | 6:00 nach Tod; Buff 180 s | 850 g, 3250 XP; stärkere Vasallen | spielentscheidend ab Minute 25 |

- **Rache der Drachen** (Wiki „Dragon Slayer“, Stand 26.1): Ein Drache nimmt je Drachen, den das **angreifende**
  Team schon hat, 15 % weniger Schaden, höchstens 60 %. Ein Team mit drei Drachen braucht also rund doppelt so lange
  wie ein Team ohne Drachen.
- Larven, Herold und Baron teilen sich die obere Grube (`GRUBEN` in `bewertung.py`). Drache und Ältester liegen in
  der unteren.
- **Für Carlos (Top):** Larven und Herold liegen auf seiner Kartenseite. Den Drachen erreicht er als Toplaner fast
  nie zu Fuß, dafür spielt er TP oder tauscht oben (Kapitel 6).

## 3. Die Rechnung je Objective (`kern/objective.py`)

### 3.1 Eingänge

`ObjectiveLage` bekommt diese Felder dazu:

| Feld | Bedeutung | Quelle |
|---|---|---|
| `wir_an[k]` | Zeit, bis `k` von euch an der Grube sein können. Das ist die k-kleinste Ankunft unter euch, du eingeschlossen. Tote: Respawn + Weg aus dem Brunnen | Minimap-Orte der Mitspieler, Tempo 380 · `WEGFAKTOR` |
| `jungler_wir` | euer Jungler: lebt, Ankunft an der Grube, Abstand vor 10 s und jetzt | wie oben |
| `die_an` | je Gegner die frühestmögliche Ankunft an der Grube | `karte.verteidiger(m, grube)` |
| `drachen` | Drachen je Team, `drache_nr` = eure Drachen + 1 bzw. ihre + 1 | Ereignisse `DragonKill` |
| `smite_wir`, `smite_die` | der jeweilige Jungler lebt und kann bis zum Ende an der Grube sein | `wir_an`, `die_an` |
| `wert_uns`, `wert_ihnen` | Kapitel 3.4 | – |

**Neu in `gefahr.py`:** `p_da(g, T, ort)` rechnet mit der Ankunft an `ort`, nicht bei dir. Das ist dieselbe Formel wie
Buch 0, 7.5. Mit `ort = None` ist es die heutige Ankunft bei dir. Für WOHIN gilt `ort` = Ziel und der Start im
Brunnen zur Respawnzeit.

**Ältester:** `MerkmalBau` kennt heute nur `drache`, `baron`, `herold` und `larven`. Nach dem 4. Drachen eines Teams
heißt das Objective der unteren Grube `aeltester`. `OBJ_GRUBE["aeltester"] = "drache"`. Ein `DragonKill` mit
`DragonType = "Elder"` tötet es.

### 3.2 Tötungszeit

```
n*       = argmin über n ≥ n_min(schl) von ( wir_an[n] + dauer(schl, n) )      # wie viele von euch warten lohnt
t0       = wir_an[n*]                                                          # Beginn
dauer    = tabelle(schl, spalte(zeit), n*)                                     # Kapitel 11, [objective.dauer]
           · stufe_faktor                                                      # 0,8, wenn euer Durchschnittslevel >= stufe_ref(spalte) + 3
           / (1 − min(0,6; 0,15 · drachen(angreifendes Team)))                 # nur Drache und Ältester (Rache, Kapitel 2)
t1       = t0 + dauer                                                          # Ende
```

- Die Tabelle gilt pro `n` ab `n_min`, der letzte Wert gilt für größere `n`. Fehlt eine Spalte, ist das Objective in
  dieser Spielzeit kein Kandidat. Baron und Ältester haben `n_min = 3`, alles andere `n_min = 1`.
- **Solo** geht also, wenn `n* = 1` am besten ist und das Fenster reicht. Beispiel 3500: Riven auf Level 20 um 35:00,
  angenommen zwei Drachen: `dauer` ≈ 16 · 0,8 / 0,7 ≈ 18 s. Der erste Gegner braucht ~30 s, also ist Solo richtig.

### 3.3 Erfolg, Risiko, dein Anteil

```
Störer        = alle Gegner mit p_da(g, T = t1 + puffer_s, ort = Grube) > 0
P_kampf       = 1 − Π_g (1 − p_da(g, t1 + puffer_s, Grube))
p_gewinn      = kampf.p_gewinn(m, ort = Grube, fenster_s = [objective].kampf_fenster_s,
                               gewichte = {g: p_da(g, …)})                     # Buch 7, 3.2 – EIN Kampfmodell
p_steal       = steal_mit_smite, wenn smite_die und smite_wir; steal_ohne_smite, wenn smite_die und nicht smite_wir; sonst 0
p_erfolg      = (1 − P_kampf · (1 − p_gewinn)) · (1 − p_steal)

p_erfolg_ohne = dieselbe Rechnung ohne dich (du fehlst in wir_an und im Kampf)
anteil        = p_erfolg − p_erfolg_ohne                                       # was DU daran änderst
```

Für eine Handlung, die **dich** zum Objective bringt (`VORBEREITEN_OBJECTIVE`, `NEHMEN`, `ZUR_GRUPPE` mit
Objective-Ziel, `WOHIN` mit Objective-Ziel):

```
gewinn   = anteil · wert_uns + folgewert
EV       = gewinn − p_tod(du, T = weg + dauer, ort = Grube) · todeskosten − weg · zeitwert
```

- Die Zeitkosten fallen **nur auf den Weg**, wie in der Karten-Rechnung (Buch 5, Abweichung 3). Die Zeit an der
  Grube steckt im Risiko.
- `todeskosten` (Buch 0, 7.3) enthält heute `objective_risiko` × Wert des nächsten Objectives. Für eine Handlung
  **an** diesem Objective wird dieser Anteil herausgenommen, sonst zählt es doppelt.
- 140253 10:25 („zu den Larven“ mit p_tod 0,97) fällt so, weil `p_tod(du, …, ort = Grube)` den Weg aus dem Brunnen
  rechnet und `anteil` klein ist. Das ist die Abnahme dafür.

### 3.4 Werte (GE für euer Team, Startwerte)

- `wert_uns(Drache)`: `drache`. Ist `drache_nr` für euch 3 (Seelenpunkt), gilt `drache_seelenpunkt`, bei 4
  `drache_seele`.
- `wert_ihnen`: dasselbe aus ihrer Sicht. Das ist der Schaden, wenn **sie** es nehmen.
- Larven: `larven`. Den Zuschlag `larven_seite` gibt es nur, wenn ihr alle drei nehmt **und** jemand von euch danach
  eine Seitenlane drückt. Er gilt nur als `folgewert` (Kapitel 4.6), nicht zusätzlich im Wert.
- Herold: `herold`, dazu `folgewert` = bester `wert_ritt` (Kapitel 7) · 0,8.
- Baron: `baron`, dazu `folgewert` aus dem Baron-Fenster (Kapitel 4.6).

## 4. Handlungen

Handlungen tragen `Ziel("objective", OBJ_NAME[schl], pos, weg)` und `h.daten["objective"] = schl`, wie heute in
`lane.py`.

### 4.1 Der zentrale Test: `objective_zieht(m, o)`

Ein Objective darf **dich** nur ziehen, wenn alles gilt:

1. `p_erfolg` zur Spawnzeit (bzw. jetzt, wenn es lebt) ≥ `vorbereiten_p_min`.
2. `anteil · wert_uns + folgewert` > 0, also nach Abzug deiner Kosten ein positiver EV.
3. **Du wirst gebraucht** (Kapitel 6, bis Minute 14; danach entscheidet 1 und 2).

**Ändert Buch 1, 3.3 (STAPELN), Buch 3 (OBJECTIVE_VORLAUF, WOHIN), Buch 5 (`karte.objective_ruft`, `WELLE_UND_RAUS`,
`ZUR_GRUPPE`):** Diese Stellen nennen ein Objective als Ziel oder Grund **nur**, wenn `objective_zieht` gilt. Sonst
behandeln sie das Objective, als gäbe es keins. Das beendet den Larven-Sog an allen vier Stellen gleichzeitig.

### 4.2 `VORBEREITEN_OBJECTIVE` (eine Art in allen Modi)

Die Namen `VORBEREITEN` und `VORBEREITEN_OBJECTIVE` werden zu einem: `VORBEREITEN_OBJECTIVE`.

- **Entsteht, wenn:**
  - Das Objective spawnt in `abfahrt_s` bis `objective_vorlauf_s` (60 s). `abfahrt_s = ankunft_vorlauf_s(schl) +
    weg + welle_s`. `welle_s` ist die Zeit bis zum Crash deiner Welle (Buch 1), sonst 0.
  - Und `objective_zieht` gilt.
- **Bleibt, bis:**
  - Spawn + 10 s, danach geht es über in `NEHMEN` (ohne neue Ansage).
  - Abbruch: `p_erfolg` < `abbruch_p` (0,4), euer Jungler stirbt, dein Leben < `leben_min` (0,6) ohne Back-Schritt,
    oder ein Ereignis kippt `objective_zieht`.
  - Das Entstehungsfenster gilt nur für den Anfang. Danach wird der Plan nicht mehr fallengelassen, nur weil der
    Spawn näher rückt.
- **Schritte:** Welle rein (wenn nicht schon drin), bei Bedarf back (Buch 3, `OBJECTIVE_VORLAUF`), hin.
- **Ankunft:** `spawn − ankunft_vorlauf_s(schl)`. Früher nicht, außer bei großen Objectives (Sicht, 30 s).
- **Satz:** „Top-Welle rein, dann zu den Larven: dein Jungler ist oben.“

### 4.3 `NEHMEN` (Schritte „hin“, „nehmen“)

`ANLAUFEN` und `NEHMEN` sind **eine** Handlung mit zwei Schritten. `ANLAUFEN` bleibt als Alias, damit alte Szenarien
(`soll = ["ANLAUFEN", "NEHMEN"]`) gelten. Der Wechsel von „hin“ zu „nehmen“ wird nicht angesagt.

- **Kandidat, wenn:** Das Objective lebt oder spawnt in ≤ Weg + `ankunft_vorlauf_s`, `p_erfolg ≥ nehmen_p_min`, und
  der EV aus 3.3 ist > 0.
- **Satz:** Der Grund muss für die Handlung sprechen und ist aus `P_kampf` abgeleitet, nicht aus dem Buch:
  - `P_kampf` < 0,1: „Drache jetzt: drei von ihnen sind tot, keiner kommt rechtzeitig.“
  - Sonst mit dem Kampf: „Drache jetzt: ihr seid vier, Jinx ohne Flash.“
  - Solo: „Drache allein: der Erste von ihnen braucht noch 30 Sekunden.“

### 4.4 `BESTREITEN`

- **Kandidat, wenn:**
  - Das Objective lebt.
  - Sie sind zuerst dort, oder `P_kampf ≥ bestreiten_kampf_ab` (0,5).
  - `p_gewinn` an der Grube ≥ `bestreiten_p_min`, bei großen ≥ `bestreiten_p_min_gross`. Groß heißt: `drache_nr ≥ 3`
    für **eine** der beiden Seiten, Ältester oder Baron.
- **EV** gegenüber „abgeben“, wo sie es sicher bekommen:

  ```
  EV(BESTREITEN) = p_gewinn · (wert_uns + wert_ihnen) − (1 − p_gewinn) · todeskosten_team − weg · zeitwert
  todeskosten_team = Summe der zwei höchsten todeskosten_spieler(s) unter euch Beteiligten
  todeskosten_spieler(s) = kill_gold(s) + respawn(s) · zeitwert
  ```

  Für dich gilt die volle `todeskosten` aus Buch 0, 7.3, ohne das umkämpfte Objective.
- **Satz:** „Drache bestreiten: ihr seid vier mit Ults, Jinx ohne Flash.“

### 4.5 `ABGEBEN_TAUSCHEN`

- **„Sie nehmen es“ heißt:** ≥ 2 Gegner sichtbar in `grube_radius`, oder vor ≤ 10 s dort gesehen, **und**
  `BESTREITEN` ist kein Kandidat.
- **Der Tausch:**
  - Nach der Lane-Phase: der beste Kandidat der Karten-Rechnung (Buch 5, 2). Das Fenster für jedes Ziel ist
    `karte.verteidiger(ziel)`, gerechnet mit ihren Leuten **ab dem Ende ihrer Tötungszeit, von der Grube aus**
    (`restliche_dauer_ihre = dauer(n_ihre) − Zeit, seit sie dort sind`).
  - In der Lane-Phase: `PLATTEN` oder `DRUECKEN` auf deiner Lane, wenn sein Toplaner fehlt (Kapitel 6).
- **Ohne Tausch:** kein ABGEBEN-Satz. Dann gilt `ZURUECK` (bei Gefahr) oder der stille Plan.
- **Satz** in Buch-0-Form, der Tausch zuerst: „Äußerer Top-Turm jetzt: sie sind zu viert am Drachen.“ Das ersetzt
  14:53 (drei Sätze) durch einen.

### 4.6 Nach dem Objective

Nimmt euer Team es, gibt es höchstens **einen** Folgesatz, und nur, wenn er eine neue Tätigkeit verlangt:

- **Baron:** Eigener Auslöser für das Umwandeln (Buch 5, 8): `BaronKill` ≤ 180 s her und ≥ 3 von euch mit Buff
  leben. Dann öffnen sich die hinteren Ziele, auch ohne die Überzahl-Regel.
- **Herold:** Das Auge hast **du** (dein Inventar in der API; genauen Item-Namen und ID aus Data Dragon nehmen): Dann
  gilt Kapitel 7. Hat es ein Mitspieler, gibt es keinen Satz.
- **Larven 3:0:** `folgewert` `larven_seite` auf Turm-Kandidaten deiner Seite. Satz nur, wenn der Plan dadurch
  wechselt: „Larven drin: jetzt Top drücken.“
- **Drache:** kein Folgesatz. Der Plan geht weiter (Welle, Back).

### 4.7 `TP_SPIEL` zu einem Objective

Buch 5, Kapitel 5 gilt (Bedingungen und Ziel). Zusätzlich muss dein TP das Urteil ändern:
`p_gewinn(mit dir) − p_gewinn(ohne dich) ≥ tp_unterschied_min`.

**Ändert Buch 5, 5:** Flanke („hinter sie“) nur, wenn ein eigener Vasall oder Turm dort auf der Minimap sichtbar
ist. Wards kennt der Coach erst mit Buch 4. Sonst Ziel = eigener Turm oder Mitspieler, Satz „TP an …, dann rein“.

## 5. Modus OBJECTIVE – ändert Buch 0, 5.1

**Neu:** OBJECTIVE gilt, wenn eins davon zutrifft:

1. Du stehst in der Grube (`bereich == grube:*`), und das Objective lebt oder spawnt in ≤ `grube_modus_s` (30 s).
2. Dein **aktueller Plan** (aus dem vorigen Takt) ist `VORBEREITEN_OBJECTIVE`, `NEHMEN` oder `BESTREITEN`, und du
   bist ≤ `objective_nah_s` von der Grube.

**Bleibt** (gegen Schaukeln):

- OBJECTIVE endet erst, wenn der Plan ≥ `objective_verlassen_s` (5 s) kein Objective-Plan mehr ist, oder dein Weg
  > `objective_nah_s` + 10 s.
- Objective-Pläne gelten in UNTERWEGS, GRUPPE, SEITE und OBJECTIVE. Ein Wechsel zwischen diesen Modi verwirft sie
  nicht (Buch 0, 5.2: „Der Plan bleibt, wenn er im neuen Modus noch gültig ist“; `plan.py` Punkt 1 anpassen).

**Bleibt wie bisher:** Auf der eigenen Lane in der Lane-Phase gilt LANE, mit `VORBEREITEN_OBJECTIVE` als Handlung.

**Fällt weg:** „≥ 1 Mitspieler an der Grube“ als Auslöser. Dieser Auslöser brachte 38:31 in ihrer Basis den Modus
OBJECTIVE. `[objective_wert].mindestens` fällt ebenfalls weg. Wo es noch gelesen wird (`modus.py`,
Qualitätsrunde C.2 `basis.wohin`), gilt stattdessen `objective_zieht`.

**Kandidaten in OBJECTIVE:**

- `NEHMEN`, `BESTREITEN`, `ABGEBEN_TAUSCHEN`, `VORBEREITEN_OBJECTIVE`, `ZURUECK`
- `BACK_JETZT` nach Buch 3
- `karte.halten` als stiller Grundplan (für die Gefahr-Rechnung, wie FARMEN)
- **und alle Turm-Handlungen der Karten-Rechnung** (`DRUECKEN`, `MIT_GRUPPE`). Alles steht in **einer** Liste nach EV
  (Kapitel 8).

Wards: Bis Buch 4 gibt es in OBJECTIVE keinen Ward-Satz, auch nicht aus der alten Regel.

**Alte Regeln nach Schritt 5 (ändert Buch 0, 14):** `_grosse_objectives`, `_vorwarnung`, `_zahlen`,
`_objective_start` und `_ward` sind in **allen** Modi stumm, nicht nur in OBJECTIVE. Sonst sagen sie in SEITE, GRUPPE
oder UNTERWEGS weiter „Nehmt Baron …“.

## 6. Wirst du gebraucht? (Lane-Phase, bis 14:00)

**Prio** heißt, bis F1 (Welle: Front statt Summe) abgenommen ist, nur eins davon:

- Deine Welle ist `GECRASHT_BEI_IHM`.
- Dein Lane-Gegner ist tot oder im Brunnen.

Die Wellen-Eichung liegt heute bei 40–56 %, `ZU_IHM` ist fast immer „wahr“ und zählt deshalb nicht.

**Euer Jungler geht hin** heißt: `jungler_wir` lebt, seine Ankunft ≤ Spawn + 5 s, **und** er ist ≤ 3000 von der Grube
entfernt oder hat sich ihr in 10 s um ≥ 1000 genähert.

| Lage | Rat | Beispiel-Satz |
|---|---|---|
| Objective auf deiner Seite, du hast Prio, euer Jungler geht hin | Welle rein, dann hin | „Top-Welle rein, dann zu den Larven: dein Jungler ist oben.“ |
| Objective auf deiner Seite, **er** hat Prio | bleib und farm; geht er hin, nimm Platten (`ABGEBEN_TAUSCHEN` in der Lane-Form) | „Gangplank ist zu den Larven: Platten jetzt.“ |
| Euer Jungler geht nicht hin | kein Objective; kein Satz | – |
| Drache (andere Seite), TP bereit | Welle rein, TP bereithalten (Buch 5, `TP_SPIEL`) | „Drache in 30 Sekunden: Welle rein und TP bereithalten.“ |
| Sein Toplaner fehlt (TP bot oder zu den Larven) | Platten oder Turm oben | „Gangplank ist unten: Platten jetzt.“ |
| Lane verloren (`kraefte()[0] ≤ −1` oder ≥ 2 Tode gegen ihn) | nie ein Objective aus der Lane heraus | – |

**Mid** (Carlos spielt manchmal Riven Mid, 140253): Beide Gruben liegen nah, die Regel ist dieselbe. Prio bedeutet
hier: Mid-Welle `GECRASHT_BEI_IHM` oder Mid-Gegner tot bzw. im Brunnen.

## 7. Herold: wohin mit dem Ritt

Nur wenn **du** das Auge hast.

```
wert_ritt(turm) = Σ Plattengold der Platten, die 3000 Echtschaden + Kristall-Schaden fallen lassen
                  + (wenn der Turm dadurch fällt: Turmgold + turm_extra)
```

- **Turm-Leben 2026** (Wiki Turret, am 27.09. aus einer Zusammenfassung abgelesen; Claude Code prüft die Zahlen vor
  dem Rechnen und schreibt sie mit Stand nach `wissen/mechanik.toml`): außen 9000, innen 5000, Inhibitor-Turm 4750,
  Nexus-Turm 3500.
- Platten fallen bei 10/25/45/70/100 % fehlendem Leben. Bei einem vollen äußeren Turm sind 3000 Schaden 33 %, das sind
  zwei Platten. Bei einem inneren Turm sind es 60 %, also drei Platten.
- Der Ritt **verbraucht den Kristall** (Wiki Turret: „The Rift Herald Mercenary's attacks and charge can also
  consume Overgrowth“). Dessen Schaden kommt zu den 3000 dazu.
- Das Ziel wählt die Karten-Rechnung, mit `wert_ritt` als Gewinn und dem Weg samt Ritt als Dauer.
- **Satz:** „Herold auf den äußeren Top-Turm: zwei Platten, Gangplank ist unten.“

## 8. Welches Ziel, wenn mehrere leben?

- Es gibt keine feste Reihenfolge und nie „Baron zuerst“.
- Objective-Handlungen und die Kandidaten der Karten-Rechnung (Türme, Seitenwellen, Umwandeln) stehen in **einer**
  Liste. Die Plan-Regeln wählen (Buch 0, 8.2, mit Hysterese).
- **Ändert Buch 5, 8 und `karte.ORDNUNG`:** Im Umwandel-Fenster bekommen Objectives einen Platz in der Reihenfolge:
  Baron und Ältester 2,5 (zwischen Inhibitor und innerem Turm), Drache 1,5 (zwischen innerem und äußerem Turm).
  Larven und Herold stehen nicht darin (Lane-Phase bzw. Ritt).
- **Beispiele:**
  - 25:22: Der Drache ist 17 s entfernt, drei Gegner sind tot, Tryndamere ist dabei → `NEHMEN` Drache. Baron fällt
    heraus, weil zwei eurer Leute in der Basis stehen und `n_min = 3` nicht rechtzeitig erreicht wird.
  - 28:47: Baron mit höchstens zwei von euch → kein Kandidat. Drache oder Mid-Inhibitor-Turm, je nach EV.
- **Zielwechsel:** Gesagt wird er nur mit Ereignis (Tod, Spawn, Fall, Sichtung eines Unbekannten) **und** wenn der
  Unterschied die Plan-Hysterese übersteigt.

## 9. Sprechen

- **Kategorie PLAN**, höchstens 18 Wörter, ein Satz: Handlung, Objective, **ein** Grund dafür.
- **Grund-Regeln. Ändert Buch 0, 9.3, und damit die bestehenden Sätze in `lane.py` („du brauchst {weg} Sekunden“),
  `karte.py` und das Beispiel in Buch 5, 3.2:**
  - Nennt der Grund ein Fenster („noch 25 Sekunden tot“), muss es ≥ dein Weg + Dauer sein. Sonst ist das **Ziel**
    falsch gewählt, nicht nur der Satz.
  - Höchstens zwei Namen. Ab drei wird gezählt: „drei von ihnen sind tot“.
  - Keine Zahlen zum Selbstrechnen („du brauchst 14, Spawn in 22“). Stattdessen die Folge: „du bist pünktlich
    dort“ bzw. „lauf direkt, sonst zu spät“.
  - Keine Information ohne Handlung („aber kein Turm ist erreichbar“). Gibt es keine Handlung, schweigt der Coach.
- **Wiederholung:** Das Urteil zu einem Objective höchstens einmal je Spawn. Ein zweites Mal nur, wenn es mit
  Ereignis kippt (`NEHMEN` ↔ `ABGEBEN_TAUSCHEN`).
- **Bestätigung** (Buch 3, `[bestaetigung]`): „Sauber: Drache ohne Kampf.“ oder „Guter Tausch: Turm für Drache.“ Nur
  wenn Carlos der Ansage gefolgt ist, höchstens einmal je 180 s.

## 10. Eichen an den Aufnahmen (`werkzeuge/objective_eichung.py`, neu; Pflicht vor der Abnahme)

1. **Tötungszeit.**
   - Für jedes `DragonKill`, `HordeKill` (Larven), `HeraldKill` und `BaronKill` eures Teams gilt: Beginn ist der erste
     Zeitpunkt nach Spawn, ab dem ≥ 1 von euch ≤ `eichung_nah` (700) an der Grube steht und bleibt. Dauer = Kill −
     Beginn.
   - Beim Drachen wird die gemessene Dauer vorher mit dem Rache-Faktor (Kapitel 3.2) bereinigt, sonst zählt er doppelt.
   - Die Ergebnisse gruppiert nach Objective, `n` (Median der Anwesenden) und Spalte, als Median mit Anzahl in
     messungen.md.
   - Die Tabelle wird nur dort angepasst, wo ≥ 3 Fälle vorliegen.
2. **Urteil gegen Ausgang.**
   - Eine Probe je **Versuch**, am Beginn aus Punkt 1. Ein Versuch ist auch, wenn ≥ 2 von euch ≤ `eichung_nah` stehen
     und kein Kill folgt.
   - Ausgang 1: euer Team nimmt es in 60 s ohne eigenen Tod an der Grube. Sonst 0.
   - Nur echte Partien (`bots = false`).
   - Gemessen wird der Brier-Wert, Soll < 0,20 und besser als die Grundrate.
   - `puffer_s`, `steal_*` und die Schwellen werden nur verändert, wenn ≥ 30 Versuche vorliegen. Sonst bleiben die
     Startwerte, und messungen.md sagt das.

## 11. Parameter (`wissen/kern.toml`)

```toml
[objective]
stand = "Buch 6, 27.09.2026 - Startwerte (Schaetzung), an Aufnahmen kalibrieren (Kapitel 10)"
# objective_vorlauf_s: aus [modus] (60 s), nicht doppelt fuehren
ankunft_vorlauf_s = { larven = 10, herold = 10, drache = 15, gross = 30 }   # gross: drache_nr >= 3, Aeltester, Baron
grube_modus_s = 30
objective_verlassen_s = 5
puffer_s = 3
steal_mit_smite = 0.15
steal_ohne_smite = 0.5
vorbereiten_p_min = 0.5
nehmen_p_min = 0.65
abbruch_p = 0.4
leben_min = 0.6
bestreiten_kampf_ab = 0.5
bestreiten_p_min = 0.55
bestreiten_p_min_gross = 0.45
kampf_fenster_s = 15
tp_unterschied_min = 0.15
stufe_faktor = 0.8
stufe_ref = { bis_14 = 7, bis_25 = 12, danach = 16 }
rache_je_drache = 0.15
rache_max = 0.6
baron_fenster_s = 180
baron_umwandeln_mindestens = 3
herold_folge_anteil = 0.8
eichung_nah = 700
verhindern = true                  # wert_ihnen zaehlt in BESTREITEN

[objective.dauer]                  # Toetungszeit [s]; Liste ab n_min, der letzte Wert gilt fuer groessere n; fehlende Spalte = kein Kandidat
n_min = { drache = 1, larven = 1, herold = 1, baron = 3, aeltester = 3 }
drache = { bis_14 = [45, 25, 18], bis_25 = [28, 16, 11], danach = [16, 10, 7] }
larven = { bis_14 = [40, 25, 18], bis_25 = [30, 18, 13] }
herold = { bis_25 = [45, 28, 20] }
baron = { bis_25 = [50, 38, 30], danach = [32, 24, 18] }
aeltester = { danach = [28, 20, 15] }

[objective_wert]
stand = "Buch 6, 27.09.2026 - Startwerte (Schaetzung)"
drache = 600
drache_seelenpunkt = 900
drache_seele = 1500
aeltester = 3000
larven = 500
larven_seite = 200                 # nur als folgewert, Kapitel 3.4
herold = 400                       # geaendert (vorher 700): der Ritt zaehlt jetzt als folgewert, Kapitel 7
baron = 2500
inhibitor = 1000
turm_extra = 250
nexus = 10000
```

`[objective_wert].mindestens` und `dauer_s` aus Schritt 2 fallen weg (Kapitel 5).

## 12. Fakten nachtragen

- `saison2026.md`, Abschnitt Objectives, korrigieren und mit Quelle versehen:
  - Larven: 30 g je Larve (90 g für alle drei); „Hunger der Leere“ erst ab dem 3. Stapel; verschwinden 14:45 (im
    Kampf 14:55).
  - Herold: Auge 20 s am Grubeneingang, der Ritt verbraucht Kristalle.
  - Rache: 15 % je Drache des angreifenden Teams, höchstens 60 %.
  - Baron: Wiederkehr 6:00, Buff 180 s.
- **Ältester:** Das Lexikon sagt „5:00 nach der Seele“. Riftpatchnotes (Patch 14.3) sagt 360 s. Claude Code schlägt
  im Wiki nach, trägt den belegten Wert ein und notiert die Quelle.

## 13. Szenarien

Die Szenarien gehören nach `tests/szenarien/<aufnahme>_buch6.toml`. Jede Lage wird beim Anlegen durch Nachspielen
geprüft und festgeschrieben. Weicht sie ab, wird das Szenario mit Begründung korrigiert (messungen.md).

**Neue Prüfschlüssel** (in `szenarien.py` und Buch 0, 12.1 nachtragen):

- `soll_ziel`: Der Plan nennt dieses Ziel (Teilstring von `Ziel.name` oder `daten["objective"]`).
- `max_woerter`: Kein gesprochener Satz im Fenster ist länger.
- `alte_regeln_max`: So viele gesprochene Sätze alter Regeln im Fenster sind höchstens erlaubt.
- `ziele_max`: kommt aus der Qualitätsrunde.

| id | Aufnahme | zeit / fenster | Soll | darf nicht |
|---|---|---|---|---|
| `2522-kein-baron-drache-lebt` | 102112 | besteht | grün über den **Kern**, nicht über die Sperre | – |
| `2847-baron-statt-drache` | 102112 | besteht | grün über den Kern | – |
| `3500-drache-solo` | 102112 | besteht, ohne `frage` | NEHMEN, soll_ziel „Drache“ | – |
| `3451-drache-an-der-grube` | 102112 | 34:51 / 34:48–35:05 | modus OBJECTIVE; NEHMEN; soll_ziel „Drache“ | sagen „Mid-Inhibitor“ |
| `3831-nexus-nicht-inhib` | 102112 | 38:31 / 38:31–38:50 | modus in [GRUPPE, SEITE, UNTERWEGS]; DRUECKEN; soll_ziel „Nexus“ | sagen „Mid-Inhibitor“ |
| `1453-herold-ein-satz` | 102112 | 14:53 / 14:50–15:10 | ansagen_max 1; max_woerter 18 | NEHMEN, BESTREITEN, ANLAUFEN; sagen „Nimm keinen Kampf“ |
| `2516-keine-zahl-ohne-rat` | 102112 | 25:16 (±5 s) | – | sagen „kein Turm ist“ |
| `3335-keine-zahl-ohne-rat` | 102112 | 33:35 (±5 s) | – | sagen „kein Turm ist“ |
| `2637-grund-nicht-dagegen` | 102112 | 26:37 / 26:30–26:45 | – | sagen „39 Sekunden von dir“ |
| `0647-mid-larven-zu-frueh` | 140253 | 6:47 / 6:45–7:10 | KAUFEN; soll_ziel „Mid“ | sagen „Larven“ |
| `0729-larven-nur-mit-jungler` | 140253 | 7:29 | Beim Nachspielen prüfen, ob Diana nach Kapitel 6 „hingeht“; das Soll (VORBEREITEN_OBJECTIVE ja/nein) wird **vor** der Umsetzung festgeschrieben und in messungen.md begründet | – |
| `0427-drache-nur-mit-team` | 140253 | 4:27 | wie 0729, mit Kapitel 6 für den Drachen (Jungler geht hin, Prio Mid, Leben ≥ 60 %) | – |
| `0647-kein-stapeln-bei-gefahr` | 144655 | aus der Qualitätsrunde | erweitert: soll FARMEN, WELLE_HALTEN, ZURUECK oder BACK_JETZT | STAPELN, VORBEREITEN_OBJECTIVE; sagen „Larven“ |
| `1025-wohin-nicht-in-den-tod` | 140253 | aus der Qualitätsrunde | bleibt grün | sagen „Larven“ |

**Die Modus-Sollwerte aus Buch 0, 5.3** (29:14, 24:40, 25:22) werden mit der neuen Eintrittsregel neu gerechnet.
Jede Änderung steht mit Grund in messungen.md.

## 14. Abnahme Schritt 5 (Teil Objectives)

1. Alle Szenarien aus Kapitel 13 sind grün über den Kern.
2. `objective_eichung.py` ist gelaufen. Tötungszeiten, Brier-Wert und Fallzahlen stehen in messungen.md.
3. In den Protokollen von 102112, 133930, 140253 und 144655 steht keine alte Regel mehr mit einem Objective-Satz
   (`alte_regeln_max = 0` für die fünf Regeln aus Kapitel 5).
4. **Kennzahl „Objective-Ansagen ohne Chance“** in `kennzahlen.py`, Soll 0:
   - Gezählt wird jede Ansage einer Handlung mit Objective-Ziel oder -Grund: `VORBEREITEN_OBJECTIVE`, `NEHMEN`,
     `STAPELN` mit Objective, `WELLE_UND_RAUS`, `ZUR_GRUPPE` oder `WOHIN` mit Objective.
   - Sie verstößt, wenn zur Ansagezeit `objective_zieht` falsch war.
   - Dafür schreibt der Kern `p_erfolg`, `anteil` und `objective_zieht` nach `_kern.jsonl`.

---

Quellen (Stand 27.09.2026):

- [Patch 26.1](https://www.leagueoflegends.com/en-us/news/game-updates/patch-26-1-notes/)
- [Wiki Dragon Slayer](https://wiki.leagueoflegends.com/en-us/Dragon_Slayer)
- [Wiki Baron Nashor](https://wiki.leagueoflegends.com/en-us/Baron_Nashor)
- [Wiki Rift Herald](https://wiki.leagueoflegends.com/en-us/Rift_Herald)
- [Wiki Voidgrub](https://wiki.leagueoflegends.com/en-us/Voidgrub)
- [Wiki Turret](https://wiki.leagueoflegends.com/en-us/Turret)
- [Wiki Elder Dragon](https://wiki.leagueoflegends.com/en-us/Elder_Dragon)
- [riftpatchnotes Dragons](https://www.riftpatchnotes.com/lol/system/dragons)
