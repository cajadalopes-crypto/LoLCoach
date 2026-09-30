# Auftrag 031 – Challenger-Gehirn, Stufe 2: Modelle und Handbuch (Claude, Chat, 30.09.2026 16:45)

**Guthaben: 0 $.** Keine Testpartien, starte den Coach nicht.

**Darf parallel zu 028 laufen.** Daher gilt:
- Nur neue Dateien unter `werkzeuge/challenger/`, `buecher/challenger/` und `daten/challenger/`.
- Nichts in `lolcoach/` ändern.
- Nur die eigenen Pfade committen.
- Rechnen mit niedriger Priorität. Die GPU (RTX 4070) darf genutzt werden.
- Bibliotheken per pip sind erlaubt, etwa LightGBM, scikit-learn oder PyTorch.

**Grundlage:**
- `buecher/17_makro_gehirn.md`, Teil A und Teil C (Stufe 2);
- `buecher/challenger/phase1_bericht.md`, `merkmale.md`, `aufteilung.json`.

**Die Aufteilung aus 030 ist fest:** Geprüft wird nur an Prüfspielern und Prüfzeit.

## 0. Zwei Entscheidungen aus 030 (Claude/Chat), zuerst umsetzen, dann die Momente neu bauen

1. **„Unterwegs“ bekommt ein Ziel:** Zone, Grube oder Mitspieler, und zwar der Ort am Ende des 60-s-Fensters bzw.
   des Ereignisses. Makro ist vor allem „wohin“. Ohne Ziel ist die Aktion wertlos.
2. **„Nahe sichtbar“:**
   - In der Lane-Phase (bis 14:00, beide in derselben Lane-Zone) gilt der Lane-Gegner bis **1800** als sichtbar,
     denn Vasallen geben Sicht und der Bildschirm ist breiter als 1200.
   - Sonst bleibt es bei 1200.
   - Die neue Trefferquote kommt in den Bericht.

Neue Partien aus dem laufenden Download kommen mit.

## 1. Die Modelle (trainiert auf Training, gemessen auf Prüfung)

| Modell | Frage | Messung | Muss schlagen |
|---|---|---|---|
| **Siegchance V** | Wie steht das Spiel? (nur Wissbares) | Kalibrierung je Minutenbereich, Brier, Log-Loss | Gold-Abstand allein |
| **Aktionswert Q** | Was bringt Aktion a jetzt? Siegchance-Änderung in 120 s, dazu Todesrisiko | Genauigkeit der Vorhersage; Plausibilitätsprüfungen (unten) | „jede Aktion gleich“ |
| **Challenger-Policy π** | Was tut ein High-Elo-Spieler dieser Rolle hier? Gewichtung Challenger 3, GM 2, Master 1 | Top-1 und Top-3 | häufigste Aktion je Rolle und Minute |
| **Jungler-Karte** | Wo ist der Gegner-Jungler (etwa 12 Zonen)? Aus „zuletzt gesehen“, Alter, Minute, Scoreboard | Log-Loss | Verteilung je Minute |
| **Gefahr** | Todeswahrscheinlichkeit in 30/60 s bei Lage + Aktion | Kalibrierung | Minute + Ort allein |

**Wichtig beim Aktionswert:** Vergleiche nur ähnliche Lagen, sonst misst du nicht die Aktion, sondern die Lage
(„wer backt, ist oft schon vorn“).
- Methode frei, zum Beispiel reiche Lage-Merkmale plus doppelt robuste Schätzung.
- Ehrlich angeben, wo das Ergebnis unsicher ist.

**Plausibilitätsprüfungen** für Q und Gefahr. Sie sind Prüfungen und fließen **nicht** ins Training ein:
- Wenig Leben, Gegner nah: Back schlägt Bleiben.
- Nach einem Ace mit Baron oben: Baron oder Objective schlägt Farmen.
- Allein Split ab Minute 25, drei Gegner unbekannt: hohes Todesrisiko.
- Objective in 60 s, Team dort: zum Objective schlägt die Seitenwelle.
- Weitere zehn, die du aus den Daten selbst findest.

Fällt eine Prüfung durch, wird das Modell untersucht, nicht die Prüfung geändert.

## 2. Klarheit: Kommando, zwei Optionen oder „unklar“

Q und π werden zu einem Urteil je Lage kombiniert:
- **klar:** Die beste Aktion liegt im Wert deutlich vorn, und High-Elo-Spieler tun sie oft.
- **geteilt:** zwei Optionen, beide mit Grund.
- **unklar:** sagen, welche Info fehlt.

Schwellen werden auf der Prüfung festgelegt. Angegeben wird, wie oft jede Stufe vorkommt.

## 3. Ketten und Umwandlung

- Was tun die Rollen in den 120 s **vor** einem genommenen Objective, im Vergleich zu einem verlorenen?
- Was nach einem gewonnenen Kampf, Kill, Turm oder Objective, und was bringt es?
- Häufige Ketten mit Wert, zum Beispiel „Welle → Back → Grube“.
- Das ist der Stoff für die Rückwärtsplanung in Stufe 3.

## 4. Challenger-Handbuch

- **`buecher/challenger/handbuch.md`:** lesbar für Carlos, nach den 13 Bereichen aus Buch 17, Teil A.
- Nur Aussagen mit n ≥ 200 und klarem Signal. Jede mit Zahl, Fallzahl und Beispiel-Kommando.
- Keine Aussage ohne Beleg, nichts erfinden.

## 5. Schnittstelle für Stufe 4

- `werkzeuge/challenger/gehirn.py` mit
  `bewerte(lage) -> Liste von (Aktion, Ziel, Wert, p_highelo, Gefahr, Klarheit, Grund-Stichworte)`.
- Unter 20 ms je Aufruf auf der CPU.
- **Liste der Merkmale:** welche live verfügbar sind (Live-API, Minimap, HUD) und welche nicht, mit Vorschlag für
  Ersatz. Zum Beispiel: Gegner-Items live nur über das Scoreboard der Live-API.

## Ende

- **`buecher/challenger/phase2_bericht.md`:**
  - Zeile 1: „Guthaben: 0,00 $ (Abo-Aufrufe: N)“;
  - je Modell die Messung gegen den Vergleich;
  - Plausibilitätsprüfungen, Klarheits-Anteile, die zehn stärksten Handbuch-Aussagen, Probleme.
- Knapp. Committen, nur eigene Dateien. Starte den Coach nicht.
