# Bericht zu Auftrag 015 – Stratege live, Prüfung erweitert

Fertig am 29.09.2026. Der Coach wurde nicht gestartet; die Generalprobe lief mit ihrem eigenen Coach-Prozess gegen den
nachgebauten Client. Einzelheiten stehen in `buecher/messungen.md` („Auftrag 015“), die Tabelle der 100 Momente in
`buecher/protokolle/STRATEGE_PROBE_015.md`.

## Commits

- `946dfb0`:
  - Prüfung und Teil B (`lolcoach/stratege_live.py`), Schalter, Unit-Tests;
  - Stub im Nachspielen, Stub-Protokolle, Probe mit Generalprobe-Belegen;
  - Anleitung, messungen.md, OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## 1. Prüfung erweitert – Verwerfen und Einspringen

Neue Gründe zum Verwerfen, jeder mit Unit-Test aus 014:
- Mitspieler am falschen Ort,
- Gold (Restpreis nach den Bauteilen im Inventar),
- Sichtbarkeit falsch herum,
- Objective nicht da.

Außerdem gilt „Nimm die Welle“ nicht mehr als Vorwärts-Rat, und Antworten werden hart auf ganze Sätze bis
30 Wörter gekürzt.

Die 100 Momente aus 014 liefen noch einmal durch, ohne neue Kritik:
- **Beim ersten Versuch verworfen: 9 von 100.** Der erste Lauf verwarf 17, das waren meist Fehlalarme der neuen
  Prüfungen; ich habe sie behoben.
- **Der Kern springt 1-mal ein (1 %)**, weit unter der Grenze von 15 %.
- **Latenz:** erster Satz im Median 2,1 s (p90 3,4 s); bis zum gültigen Satz, mit Wiederholung, p90 8,1 s.

## 2. Teil B – eingebaut

- **B1 Fragen:** Echte Fragen gehen an den Strategen, Satz für Satz an die Stimme. Timer, Wo, Stand, Kauf,
  „Was meinst du damit?“ und Notizen bleiben beim Kern.
- **B2 Wendepunkte:** Turm, Objective, Respawn, Basis-Ankunft oder zwei Kills in 10 s: Der Stratege ersetzt den
  Plan-Satz des Kerns. Kommt nach 4 s kein gültiger Satz, spricht der Kern. Warnungen gehen immer vor.
- **B3 Leerlauf:** ab 14:00 nach 45 s Stille, höchstens einmal je 45 s.
- **B4:** Die Wellen-Sätze des Kerns kommen nur noch als Fallback.
- **B5:**
  - Die Szenarien laufen weiter mit dem Kern.
  - Im Nachspielen ersetzt ein Stub das Abo: `protokoll.py --stratege-stub`.
  - **Sprechmenge** mit Stratege: 47–78 ungefragte Sätze je 30 min, ohne ihn 40–81. Das Soll ≤ ~75 ist bis auf 133930
    (78, vorher 81) und 164326 (77, vorher 74) gehalten.
- **B6:** Jede Partie schreibt `aufnahmen/<Partie>_stratege.jsonl` mit Quelle, Latenz und verworfenen Sätzen samt
  Grund.
- **Ausfall:** Kommt vom Abo 30 s lang nichts oder ein Fehler, steht einmal „Stratege: Ausfall“ im Log. Danach
  spricht 120 s lang nur der Kern, Carlos hört nichts davon.

## Generalprobe (`--breite 3840 --links 1920`, 164326 ab 22:00, echtes Claude)

- **Anlässe:** 5 in 3 min. Viermal sprach der Stratege, einmal der Kern, weil der erste Satz 4,6 s brauchte.
- **Latenz:**
  - erster gültiger Satz nach 1,0 / 1,4 / 2,2 / 2,3 s;
  - vom Anlass bis zum gesprochenen ersten Teil 1–3 s Spielzeit, plus etwa 0,45 s bis zum Ton.
- **Verworfen:** keiner. Fehler der Probe: keine.
- **Ausfall nachgestellt:** Nach 4 s sprach der Kern, danach nur noch der Kern, ohne Satz an Carlos.
- **Behoben:** Ein Satzteil kam einmal vor dem vorigen.
- **Außerdem:** Im zweiten Lauf meldete die Minimap-Texterkennung einmal einen Windows-Fehler; mit dem Strategen hat
  das nichts zu tun.

## Tests

- Szenarien 305 / 309, 3 übersprungen. Rot sind nur die alten Fälle (3× Wendepunkt-Probe, 0944).
- `tests/alle.py` 10 / 10, konstruierte Lagen 40 / 40.

## Was Carlos vor der Partie wissen muss

- **Starten wie immer:** Doppelklick auf `Coach starten.cmd` (oder `python -m lolcoach`). Der Stratege ist an; im
  Fenster steht „Makro-Stratege: an“.
- **Neu:** Deine Fragen und die Momente nach Turm, Objective, Respawn oder Kills beantwortet Claude. Timer, Flash,
  Stand und Kauf sagt weiter der Coach allein. Braucht Claude zu lange, spricht der Coach wie bisher.
- **Ausschalten, falls es klemmt:** das Fenster schließen und neu starten mit
  `python -m lolcoach live --ohne-stratege`. Dauerhaft: in `wissen/kern.toml` unter `[stratege]` die Zeile
  `aktiv = true` auf `false` setzen.
- **Nach der Partie:** Was der Stratege gesagt und die Prüfung verworfen hat, steht in
  `aufnahmen/<Partie>_stratege.jsonl`.
