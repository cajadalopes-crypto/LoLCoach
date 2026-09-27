# Auftrag 003 – Buch 11 (Führen: nächster Schritt, Vorausschau, Antworten) und Schritt 6 (Claude, Chat, 27.09.2026 23:05)

**Worum es geht:** Carlos' Hauptbeschwerde aus 213624. Er hat 15 Mal gefragt, was er jetzt tun soll, und keine
brauchbare Antwort bekommen. Der Coach soll still sein, wenn nichts zu sagen ist. Nach jedem Wendepunkt und im Mid-
und Late-Game soll er aber mit Grund aus dem Spielstand sagen, was jetzt und was danach kommt. Siehe Buch 11, Kapitel 0.

## Teil A – Entscheidungen zu 002_bericht.md

1. **Zwei klar unterlegene Gegner:** Die Regel „keine Gefahr“ gilt auch für zwei, wenn alles zutrifft:
   - Dein Leben ist ≥ 70 %.
   - Du liegst vor **jedem** der beiden ≥ 2 Level **und** ≥ 1500 Item-Gold (bei veralteten Werten gilt die Schätzung
     aus Buch 7, 3.2).
   - Kein dritter Gegner hat `p_da` ≥ 0,2 im Fenster.
2. **RAUS bei unbekanntem Gegnerleben:** Unter 15 % eigenem Leben mit einem Gegner in `kampf_radius` ist RAUS
   robust belegt, auch ohne Balken.
3. **Tempo:** +50 % bleibt, bis Carlos Stimme und Tempo aus den Proben wählt.
4. **INFO_FLASH** zählt nicht zum Ziel ≤ 50 je 30 min. Sie wird in den Kennzahlen getrennt ausgewiesen.
5. **Offen aus 002, jetzt beheben:**
   - Die Stille um jeden Satz kürzen: die Pause am Anfang und Ende der erzeugten Audiodatei abschneiden, höchstens
     0,15 s Rest.
   - Das Ziel nach einem neuen Basis-Besuch nicht in Kurzform wiederholen (213624, 12:47/12:59).
   - Das Quest-Feld im HUD (Taste V) kommt nach `OFFEN.md`, nicht jetzt.

## Teil B – Buch 11

Lies `buecher/11_fuehren.md` vollständig und setze Kapitel 10 in der Reihenfolge um. Dazu gehört Schritt 6 aus
Buch 0 (Fragen), mit den Ergänzungen aus Buch 11, Kapitel 5 und 6.

- Leg jedes Szenario zuerst an und zeig, dass es rot ist. Die Fragen-Probe mit allen 40 Fragen aus 213624 und die
  Wendepunkt-Probe kommen aus Buch 11, Kapitel 7.
- Während der Arbeit prüfst du nur die betroffenen Dateien. Den vollen Lauf machst du einmal am Ende.
- Passt etwas im Buch nicht zum Code, entscheide nach dem Sinn von Buch 11, Kapitel 1, und notiere es unter
  „Abweichungen“.

## Ende

1. Neue Protokolle für 213624 (mit `--fragen`), 164326 und 173159.
2. In messungen.md den Abschnitt „Auftrag 003 / Schritt 6“ anlegen, mit den neuen Kennzahlen: Leerlauf,
   Wendepunkt-Verzug, Widersprüche, Stichwort-Antworten, Antwortzeit.
3. Committen und `003_bericht.md` im Format aus `README.md` schreiben.
4. Starte den Coach nicht.
