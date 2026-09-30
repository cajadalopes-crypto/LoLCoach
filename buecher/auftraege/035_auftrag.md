# Auftrag 035 – Challenger-Gehirn, Stufe 5: Die Abnahme (Claude, Chat, 30.09.2026 21:50)

**Guthaben: 0 $** bis Teil 3. Keine Testpartien, starte den Coach nicht.
**Läuft bei Carlos** (lokal, mit `daten/`, `aufnahmen/`, Modellen und Windows).

## 0. Vorbereiten

1. **Den Zweig aus 034 holen und in `main` bringen:**
   ```
   git fetch origin
   git merge origin/stufe4-einbau
   ```
2. **Die drei offenen Punkte aus 034** (entschieden von Claude/Chat):
   - **Messwerkzeuge auf `--kern makro`:** `szenarien.py`, `protokoll.py`, `kennzahlen.py` und `nachspielen.py`
     messen den neuen Entscheider. Der alte Stand bleibt über `--kern neu` vergleichbar.
   - **Briefing zu Spielbeginn:** bleibt bei Claude. Es ist kein Kommando im Spiel, sondern eine Zusammenfassung
     vor dem Anpfiff, ohne Zeitdruck. Es bleibt an die Spielakte gebunden und erfindet nichts.
   - **Reihenfolge der Kommandos:** Der feste Wert je Klasse ist wieder eine Handregel und widerspricht dem
     Grundsatz, dass die Daten entscheiden. **Neu:** Gefahr steht immer vorn, danach ordnet der Aktionswert des
     Gehirns. Wo eine Entscheidung keinen Wert hat, gilt ihr fester Wert als Ersatz. Beide Reihenfolgen werden in
     Teil 2 gemessen, die bessere bleibt.

## 1. Verdrahtung (ohne Guthaben)

- **Generalprobe** mit `--kern makro`: Läuft der ganze Weg?
- **Laufzeit je Takt mit dem echten Gehirn.** Soll: unter 50 ms. 034 schätzt etwa 6 ms.
- **Nachspiel von Carlos' Aufnahmen** (Stub, alle Testpartien), ausgewertet mit `werkzeuge/makro_protokoll.py`:
  - Anweisungs-Lücke, Stillstand, Basis, Negativ allein, Hin und Her, Widerspruch, Füllsätze (Definitionen aus 027);
  - wie oft eine Entscheidung wegen fehlender Wahrnehmung schweigt;
  - wie oft die Vorlage statt Claude spricht.
- Diese Zahlen prüfen die **Verdrahtung**, nicht das Können.

## 2. Das Können: Challenger-Treue (Hauptteil, ohne Guthaben)

**Die Frage:** Rät der Coach in einer echten High-Elo-Lage das, was der Spieler dort getan hat, der gewonnen hat?

- **Grundlage:** die zurückgelegten Prüfpartien aus 030 (`aufteilung.json`), die kein Modell je gesehen hat.
- **Neues Werkzeug** `werkzeuge/challenger/treue.py`:
  - Es baut die `MakroLage` **aus einem Entscheidungsmoment der Riot-Daten**, nicht aus der Live-Wahrnehmung.
  - Was die Riot-Daten nicht hergeben (Wellen, Wards, Büsche), bleibt leer. Entscheidungen, die das brauchen,
    schweigen und werden **nicht** als Fehler gezählt, sondern getrennt ausgewiesen.
  - Je Moment: das Kommando des Coachs gegen die Aktion des Spielers, dazu die Folge.
- **Gemessen wird:**
  - **Treffer:** Das Kommando entspricht der Aktion. Bei „geteilt" zählt es, wenn eine der zwei Optionen passt.
  - **Treffer nur bei Siegern** und nur bei Challenger-Spielern, getrennt ausgewiesen.
  - **Der Wert:** Wie viel Siegchance bringen die empfohlenen Aktionen gegenüber dem, was wirklich gespielt wurde?
  - **Abdeckung:** In wie vielen Momenten sagt der Coach überhaupt etwas?
- **Verglichen wird gegen:**
  - „immer farmen";
  - die häufigste Aktion je Rolle und Minute;
  - den alten Kern (`--kern neu`), soweit er sich an dieselben Lagen anlegen lässt.
- **Dazu die Reihenfolge-Frage aus Teil 0:** dieselbe Messung mit fester Reihenfolge und mit Aktionswert. Die
  bessere bleibt, die Zahlen stehen im Bericht.

## 3. Sicherheit, Szenarien und die Abo-Runde

1. **Szenarien** mit `--kern makro`. Die 14 bekannten Roten werden je einzeln beurteilt: Ist die Bewertung mit dem
   neuen Entscheider noch richtig, oder war das Szenario an die alten Regeln gebunden? Je Szenario eine Zeile.
2. **Sicherheit:** 0 Verstöße. Die Sperre des alten Kerns muss jede Quelle abfangen.
3. **Erst wenn Teil 1 und 2 stehen,** die Abo-Runde mit drei Partien (091311, 134020, 164809), wie im Sparprotokoll:
   echter Claude-Text, danach die Kritiker.

## Tor Stufe 5

| Maß | Soll |
|---|---|
| Challenger-Treue | schlägt alle drei Vergleiche deutlich |
| Sicherheit | 0 |
| Widerspruch (automatisch) | ≤ 1 je Partie |
| Füllsätze | ≤ 5 % |
| Anweisungs-Lücke p90 / längste | ≤ 20 s / ≤ 35 s |
| Stillstand, Basis | ≥ 95 % |
| Laufzeit je Takt | < 50 ms |
| Guthaben | 0 $ |

## Ende

- **`buecher/challenger/phase5_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)";
  - „TOR ERREICHT" oder „TOR NICHT ERREICHT";
  - die Tabelle oben, die Treue-Zahlen gegen die drei Vergleiche, die Reihenfolge-Entscheidung;
  - zehn Beispiel-Momente aus den Prüfpartien: Lage, Kommando des Coachs, was der Challenger tat;
  - für 134020 dieselben Notiz-Stellen: 028 neben 035.
- Committen und pushen. Starte den Coach nicht.

**Erst wenn das Tor steht, entscheidet Carlos über eine echte Partie.**
