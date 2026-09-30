# Auftrag 036 – Die Warnungsflut abstellen: Gefahr aus dem Modell (Claude, Chat, 30.09.2026 23:20)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.

## Wo dieser Auftrag läuft

**In einer Cloud-Sitzung** (Repository `cajadalopes-crypto/LoLCoach`), auf dem Zweig `stufe6-gefahr`, der gepusht
wird. Das Repository mit Schreibrechten anhängen.

- **Zuerst `stufe5-abnahme` in `main` mergen**, falls noch nicht geschehen; 036 baut darauf auf.
- **In der Cloud fehlen `daten/`, `aufnahmen/` und die Modelle.** Deshalb:
  - Der Umbau und die Tests mit konstruierten Lagen werden hier gebaut.
  - **Die Schwelle wird hier nicht gewählt.** Sie steht als Wert in `wissen/kern.toml`, zusammen mit einem
    Werkzeug, das sie an den Prüfpartien selbst bestimmt.
  - **Gemessen wird bei Carlos**, mit `python werkzeuge/abnahme_035.py`. Das braucht kein Claude Code.

## Der Befund aus 035

Die Abnahme ist durchgelaufen (`buecher/challenger/phase5_messung.md`). **TOR NICHT ERREICHT.** Ein einziger
Fehler erklärt fast alles:

**Von 30.000 geprüften Lagen sind 26.198 Warnungen — 87 %.** Der Coach sagt fast immer „Zurück zum Turm" oder
„Zurück zur Mitte der Lane". Die Formen `klar`, `geteilt` und `unklar` kommen zusammen nur in 3741 Lagen vor. Das
Challenger-Gehirn kommt also kaum zu Wort: Gefahr hat in `vorrang.py` obersten Vorrang und verdrängt alles.

**Und die Warnungen sagen nichts vorher:**
- Tod in 60 s nach einer Warnung: **20,0 %**
- Grundrate ohne Warnung: **19,7 %**

Eine Warnung, die die Todeswahrscheinlichkeit um 0,3 Punkte hebt, ist Rauschen. Sie kostet aber jede andere Ansage.

**Die Folge in der Challenger-Treue:**

| Politik | Treffer | Wert |
|---|---:|---:|
| Coach (fest) | 14,8 % | −0,47 |
| immer farmen | 13,5 % | −0,77 |
| **häufigste je Rolle und Minute** | **32,7 %** | **+0,45** |

Der Coach schlägt „immer farmen" knapp und verliert klar gegen die einfachste denkbare Regel. Das Tor verlangt,
dass er alle drei Vergleiche deutlich schlägt.

**Die Ursache:** Die Gefahr-Entscheidungen aus 032 (vor allem J4, J5, J9) sind Handregeln, etwa „Jungler seit
mehr als 60 s nicht gesehen". Das trifft in echten Partien fast immer zu. Genau davor warnt Buch 17: Handregeln
sind nicht das Können.

## 1. Gefahr kommt aus dem Modell (Hauptteil)

Das Gefahr-Modell aus 031 ist da und misst deutlich besser als Ort und Minute allein (Log-Loss 0,366 gegen 0,498).
Es wird bisher nicht benutzt, um zu entscheiden, **ob** gewarnt wird.

1. **Jede Gefahr-Entscheidung fragt zuerst das Modell.** Sie feuert nur, wenn die Todeswahrscheinlichkeit in 60 s
   deutlich über der Grundrate der Lage liegt.
   - Die Schwelle steht in `wissen/kern.toml` als `gefahr_schwelle`, mit einem vorläufigen Wert.
   - **Neues Werkzeug `werkzeuge/challenger/gefahr_schwelle.py`:** Es probiert die Schwelle an den Prüfpartien
     durch und wählt die, für die gilt: **Tod nach Warnung mindestens doppelt so wahrscheinlich wie ohne Warnung**
     und **Warnungen höchstens 15 % aller Ansagen**. Es schreibt den Wert in `kern.toml` und gibt die Zahlen aus.
   - Carlos startet es einmal vor der Messung. Es braucht kein Claude Code.
2. **Die Handregeln bleiben als Zusatzbedingung,** nicht als Auslöser. Was sie melden, muss das Modell bestätigen.
3. **Ohne Modellwert wird nicht gewarnt,** außer bei R1 (wenig Leben). Nicht raten.
4. **`vorrang.py`:** Gefahr steht weiterhin vorn, aber nur eine bestätigte Gefahr. Sonst entscheidet der
   Aktionswert.
5. **Nie Schweigen bleibt:** Fällt eine Warnung weg, spricht die beste positive Anweisung.

## 2. Verdrahtung nachziehen

- **Stillstand 80 %, Soll 95 %** und **Basis 83 %, Soll 95 %.** Die Ursachen stehen in `makro_messen.py`; je Fehlfall
  eine Zeile im Bericht.

## 3. Die roten Szenarien

Unter `--kern makro` sind 121 von 383 rot, unter `--kern neu` nur 14. Ein großer Teil davon dürfte an der
Warnungsflut liegen.
- **Erst Teil 1 bauen, dann neu messen.** Was dann noch rot ist, wird einzeln beurteilt:
  - Prüft das Szenario eine alte Formulierung, die es unter `makro` nicht mehr gibt? Dann umschreiben.
  - Prüft es eine Sache, die der neue Entscheider wirklich falsch macht? Dann ist es ein Befund.
- Je Szenario eine Zeile. Nichts stillschweigend löschen.

## 4. Neu messen (bei Carlos, ohne Claude Code)

Zwei Befehle in PowerShell:
```
python werkzeuge\challenger\gefahr_schwelle.py
python werkzeuge\abnahme_035.py
```
- **Tor:** Der Coach schlägt „häufigste je Rolle und Minute" bei Treffer **und** Wert.
- Erreicht er das nicht, sag klar, woran es liegt, statt zu schrauben, bis die Zahl passt.

## Ende

- **`buecher/challenger/phase6_bericht.md`:** Zeile 1 „Guthaben: 0,00 $", dann die Tor-Tabelle vorher und nachher,
  die gewählte Schwelle mit Begründung, die Szenario-Zeilen.
- Committen und den Zweig `stufe6-gefahr` pushen. Starte den Coach nicht.
