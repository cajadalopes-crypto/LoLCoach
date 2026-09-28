# Bericht zu Auftrag 014 – Stratege: erst die Schutzschicht, dann live

Fertig am 29.09.2026. Der Coach wurde nicht gestartet.

**Das Tor aus A5 ist knapp verfehlt.** Beim Strategen ist „falsch“ in der alten Menge um 3,3 höher als beim Kern,
erlaubt sind 2. **Deshalb gibt es kein Teil B;** der Sprechweg des Live-Coachs ist unverändert. Die Tabellen stehen
in `buecher/protokolle/STRATEGE_PROBE_014.md`, die Einzelheiten in `buecher/messungen.md` („Auftrag 014“).

## Commits

- `f50dd2c`: Teil A (Lage, Prüfung, Systemprompt, Unit-Test), die Probe mit Rohdaten und Urteilen, messungen.md,
  OFFEN.md.
- Dazu kommt der Commit mit Auftrag und Bericht.

## Teil A – eingebaut

- **A1 Lage** (`kern.kontext()`, damit auch schon für die heutigen Claude-Antworten):
  - „Master Yi: zuletzt gesehen vor 288 s in seiner Basis, jetzt unbekannt, kann überall sein“ bzw. „jetzt sichtbar
    …“.
  - Neue Zeile „DEINE ZAUBER: Flash in 173 s; TP bereit; Ult nicht bereit“.
  - „NACH VORN VERBOTEN (Leben 36 %). Erlaubt: …“ bzw. „ZU RISKANT, NICHT VORSCHLAGEN: …“.
  - „Wert“ statt „EV“.
- **A2 `stratege.pruefe`** verwirft:
  - Sätze nach vorn trotz R1 oder zu einem zu riskanten Objective,
  - innere Begriffe,
  - Entwarnung für einen Gegner, der länger als 20 s nicht zu sehen war,
  - fremde Champions,
  - TP, Flash oder Ult, die nicht bereit sind.

  Beim ersten Verwerfen wird einmal neu gefragt, beim zweiten gilt der Kern-Satz. Dazu der Unit-Test
  `stratege_pruefung` mit den Mustern aus 013.
- **A3/A4:** `stratege.STRATEGE_SYSTEM` (keine Umkehr in 30 s ohne neue Lage, Ton, ≤ 25 Wörter). Der Stratege sieht
  seine letzten zwei Sätze.

## Teil A – Tor

Es gab 100 Momente: die 70 aus 013 und 30 neue aus 164326 und 173159, nur zum Prüfen. Vier frische Kritiker haben sie
bewertet, Challenger und Carlos je zweimal; gezählt wird das Mittel.

| Tor | alt (70) | neu (30) | |
|---|---|---|---|
| „gefährlich“ Stratege ≤ Kern | 0,2 ≤ 1,5 | 0,0 ≤ 2,8 | ja |
| Vorwärts trotz R1 / innere Begriffe nach A2 | 0 / 0 | 0 / 0 | ja |
| „falsch“ Stratege ≤ Kern + 2 | **12,5 vs. 9,2** | 4,2 vs. 3,2 | **nein** |
| Gewinnquote Stratege ≥ 65 % | 78 % | **81 %** | ja |

- **Sprechprüfung:** Beim ersten Versuch wurden 5 von 100 Sätzen verworfen; die Wiederholung war jedes Mal gültig.
- **Latenz:** erster Satz im Median 1,7 s (p90 3,2 s), mit Wiederholung bis zum gültigen Satz p90 7,5 s.
- **Abo:** 105 Aufrufe, ohne Grenze, ohne Fehler.
- **Gegenüber 013:** „gefährlich“ beim Strategen fiel von 3 auf 0–0,2, die Gewinnquote stieg von 70 % auf 78–81 %.

**Warum „falsch“ noch zu hoch ist.** Diese Stellen haben alle vier Kritiker markiert:
- Der Stratege stellt **Mitspieler an falsche Orte**: „mit Sett und Kai'Sa auf den Bot-Turm“, Sett stand in der Basis.
- Er **rechnet Gold falsch**: „Kontroll-Auge und Hydra“, das Gold reicht nicht für beides.
- Er **nennt Sichtbarkeit falsch**: „Pantheon seh ich nicht“, obwohl er sichtbar war.
- Er übersieht, dass der **Drache schon genommen** war.

All das steht in der Lage und ließe sich prüfen wie A2. Den Prompt habe ich nicht auf die Kritik hin nachgebessert.

**Ohne Tor nicht gebaut (Teil B):** Fragen an den Strategen, Stratege an Wendepunkten, Stratege im Leerlauf,
Wellen-Sätze nur als Fallback, Generalprobe, Protokollquelle „stratege“.

## Offen / zu entscheiden

1. **Nächster Schritt?** A2 um drei Prüfungen erweitern: Mitspieler-Orte, sichtbar/unsichtbar, Gold für genannte
   Käufe. Dazu der Fehlalarm „Nimm die Welle“ und die Länge (Median 30 Wörter statt ≤ 25). Dann das Tor mit frischen
   Kritikern neu messen. Die 30 neuen Momente wären dann schon gesehen; eine frische Prüfmenge bräuchte eine weitere
   Partie.
2. **Oder** das Tor bei „falsch“ so lassen, wie es ist: Der Stratege gewinnt 78–81 % und ist nie gefährlicher als der
   Kern. Dann wäre Teil B der nächste Auftrag.
