# Auftrag 018 – Was Carlos' Graves-Partie zeigt (Claude, Chat, 29.09.2026 19:30)

**Erst nach 017 und 019.** Die Objective-Symbole (Teil 1) gehen direkt in das Lagebild aus 019 (`welt.py`). Keine Testpartien, geprüft wird an Aufnahmen. Starte den Coach nicht.

Carlos hat von sich aus gespielt: `aufnahmen/2026-09-29_183125` (Graves Top gegen Garen, Botpartie, 39 min).

**Achtung:** Der Coach lief dabei auf dem halbfertigen Stand von 017 (gestartet 18:30, `017_in_arbeit`, 13 Dateien
ungesichert geändert). Bei jedem Fund prüfst du zuerst, ob er mit dem fertigen 017 noch auftritt. Nachgespielt wird mit
dem fertigen Stand.

## 1. Objectives auf der Minimap lesen

- 17:21–18:16: Der Coach sagt „Ob der Herold noch steht, weiß ich nicht“. Carlos: „Das lila Symbol ist doch zu sehen.“
- Carlos hat recht. Drache, Baron, Herold und die Larven haben auf der Minimap ein Symbol, solange sie leben. Das darf
  der Coach lesen (eigene Sicht).
- **Bauen:**
  - Symbole erkennen: Vorlagen aus echten Bildern in `aufnahmen/*_bilder`, Farbe und Form, feste Orte.
  - Den Stand „lebt / genommen / nicht da“ an Kern und Stratege geben.
- **Prüfen:** an den Minimap-Bildern mehrerer Partien gegen die Ereignisse der API (ObjectiveKilled / DragonKill usw.).
  Trefferquote in `messungen.md`.

## 2. Nach dem Respawn sofort ein Plan

- 18:34 „Was mache ich, sobald ich lebe?“ bekam „Du lebst in 11 Sekunden wieder: du lebst in 11 Sekunden.“
- Danach kam über eine Minute in der Basis keine Anweisung (Notiz 19:35).
- **Prüfen:** Tritt das mit dem fertigen 017 (Respawn-Kette 12 s vorher) noch auf? Falls ja, beheben.
- **Szenarien:** 18:34, 19:12, 19:35.

## 3. Sicherer Turm = der nächste stehende

- 19:48 „Bleib unter eurem Mid-Inhibitor-Turm“, obwohl fast alle Türme davor noch standen.
- **Fix:** Wer sich zurückziehen oder warten soll, bekommt den nächsten **stehenden** eigenen Turm auf dem Weg. Mit
  Name der Lane und Stufe (äußerer/innerer).

## 4. Kaufen: Einzigartige Gruppen und Elixiere

- 35:04–36:37:
  - „Kauf Schwarzes Beil“, obwohl es mit „Lord Dominiks Grüße“ nicht geht. Laut Carlos teilen sich beide eine
    einzigartige Gruppe im Laden.
  - Danach „nichts zu kaufen“ bei 1000 Gold, obwohl Elixiere gehen. Die belegen keinen Platz, sie wirken beim Kauf.
- **Fix:**
  - Einzigartige Gruppen aus den Item-Daten lesen (Data Dragon oder CommunityDragon; prüfen, welches Feld es
    enthält). Nichts vorschlagen, was mit dem Inventar kollidiert.
  - Elixiere (und andere Käufe ohne Platz) als Option, wenn Gold über ist und kein Item passt.
  - Stand und Quelle in `wissen/`.
- **Szenarien** aus 35:04, 35:38, 36:23.

## 5. Kampf in der Nähe: helfen oder nicht, mit Grund

- 26:15: Beim Drachen wird gekämpft. Carlos: „Ich könnte Kog'Maw hier wegholen.“ Der Coach sagte, unter den Turm zu
  gehen.
- Das ist Anlass I6 aus Buch 13. Der Stratege soll dort **helfen oder nicht helfen** sagen, mit Grund.
- **Grundlage:** Zahlen, die der Kern exakt hat:
  - wer lebt;
  - Leben und Level;
  - wer Flash oder Ult hat (soweit bekannt);
  - Weg bis zum Kampf.
- **Kill-Check auf das Ziel,** wenn Graves genannt wird (`combo.py` kann Graves).
- **Weiter gilt:**
  - kein Rein-Ruf ohne Kill-Check;
  - unter R1 nichts nach vorn.
- **Szenario** 26:15 mit der Soll-Aussage des Challenger-Kritikers.

## 6. Ansage beim Tod kurz halten

- 38:10 bis 38:36: Ein langer Satz lief weiter, als Carlos tot war. „Geh zurück“ kam, als er schon fast wieder lebte.
- **Fix:**
  - Beim Tod wird jeder laufende Satz sofort abgebrochen.
  - Der Tod-Satz hat höchstens 12 Wörter.
  - Kein „geh zurück“ an einen Toten.
  - Nach dem Tod kommt die Respawn-Kette (Teil 2).

## 7. Top-Wellen-Reflex (37:55)

„Kennst du auch andere Makro-Plays als ständig zur Top-Lane?“ Prüf die Häufigkeit von „Top-Welle“ im Nachspiel von
183125 mit dem fertigen 017. Kommt sie noch als Standard-Ziel ohne Grund, beheb es (Teil 0.6 aus 017).

## Ende

1. Szenarien zuerst rot, dann die Fixes. Voller Lauf.
2. Nachspiel `NACHSPIEL_2026-09-29_183125.md` mit den Maßen aus 017 (Soll-Liste, Füllsätze, Widersprüche, Latenz,
   Abdeckung, Sicherheit).
3. `018_bericht.md`. Committen. Starte den Coach nicht.
