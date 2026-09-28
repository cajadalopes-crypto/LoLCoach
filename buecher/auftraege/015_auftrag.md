# Auftrag 015 – Stratege live einbauen, Prüfung erweitern (Claude, Chat, 29.09.2026 00:10)

## Entscheidung zum Tor aus 014

Das Tor „falsch ≤ Kern + 2“ ist in der alten Menge knapp verfehlt (+3,3). Ich gebe Teil B trotzdem frei, aus drei
Gründen:
- **Frische Menge:** In der Menge, die nur zum Prüfen diente (164326/173159), ist es erfüllt (+1,0).
- **Streuung:** Die Streuung der Kritiker liegt laut 013 bei etwa ±5 Fällen.
- **Sicherheit:** Die eigentliche Sicherheitsbedingung ist deutlich erfüllt. „Gefährlich“ liegt beim Strategen bei
  0–0,2, beim Kern bei 1,5–2,8.

Die Sachfehler aus 014 folgen Mustern, die sich prüfen lassen. Sie kommen deshalb in `stratege.pruefe`, nicht in den
Prompt. Entscheiden soll danach Carlos' nächste Partie, nicht eine weitere Offline-Runde.

## 1. Prüfung erweitern (`stratege.pruefe`)

Neue Gründe zum Verwerfen, jeder mit Unit-Test aus den Fällen in `STRATEGE_PROBE_014.md`:
1. **Mitspieler am falschen Ort:** Ein Mitspieler wird als Begleiter genannt („mit Sett …“, „Sett und Kai'Sa
   stehen …“), ist aber tot, in der Basis oder laut Lage weit weg vom genannten Ort (Ankunft > 15 s).
2. **Gold:** Die Kauf-Empfehlung kostet zusammen mehr als dein Gold. Bauteile zählen mit ihrem Preis.
3. **Sichtbarkeit falsch herum:**
   - „X seh ich nicht“ oder „X unsichtbar“, obwohl X jetzt sichtbar ist.
   - Umgekehrt ein Ort als aktuell für einen Unsichtbaren.
4. **Objective-Stand:** Drache, Baron, Herold oder die Larven als Ziel, obwohl nicht da (genommen, noch nicht
   gespawnt), es sei denn mit der Spawn-Zeit aus der Lage.
5. **Fehlalarm beheben:** „Nimm die Welle“, „hol die Welle“ und „farm die Welle“ auf der eigenen Seite sind kein
   Vorwärts-Rat.
6. **Länge:** Über 30 Wörter wird hart gekürzt, auf ganze Sätze. Der Prompt bleibt bei ≤ 25.

Lass die 100 Momente aus 014 einmal mit der erweiterten Prüfung laufen, ohne neue Kritik. Zu berichten:
- wie viele Sätze jetzt verworfen werden,
- wie oft der Kern einspringen muss,
- die Latenz bis zum gültigen Satz.

Muss der Kern in mehr als 15 % der Fälle einspringen, trotzdem weiter mit Teil B, aber im Bericht deutlich sagen.

## 2. Teil B aus 014, unverändert

Bau B1 bis B6 aus `014_auftrag.md` ein:
- **B1:** Fragen an den Strategen, Faktfragen und KLAEREN beim Kern.
- **B2:** Wendepunkte, der Kern warnt immer zuerst. Fallback, wenn der erste Satz länger als 4 s braucht oder verworfen
  wird.
- **B3:** Leerlauf ab 14:00, höchstens einmal je 45 s.
- **B4:** Die Wellen-Sätze des Kerns nur noch als Fallback.
- **B5:** Messen, mit der Generalprobe (`--breite 3840 --links 1920`) und echtem Claude an zwei Wendepunkten.
- **B6:** Protokoll mit Quelle „stratege“ und verworfenen Sätzen.

Dazu kommen zwei Punkte:

- **Schalter:** `wissen/kern.toml` oder die Kommandozeile, z. B. `--ohne-stratege`. Damit schaltet Carlos auf den
  alten Weg zurück, falls live etwas klemmt.
- **Ausfall:** Kommt vom Abo 30 s lang nichts oder ein Fehler, macht der Coach still mit dem Kern weiter. Er sagt
  nicht „Claude hat einen Fehler gemeldet“, nur einmal leise im Protokoll.

## Ende

1. Voller Lauf (Szenarien, Tests, konstruierte Lagen), Generalprobe.
2. Bericht: Verwerfen und Einspringen, Latenz live in der Generalprobe, was Carlos vor der Partie wissen muss (wie er
   startet und den Schalter bedient).
3. Committen. Starte den Coach nicht.
