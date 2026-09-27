# Auftrag 001 – Qualitätsrunde 3 (Claude, Chat, 27.09.2026 21:20)

Lies `buecher/protokolle/PRUEFUNG_2026-09-27c.md` vollständig und setze R1–R10 um.

1. Committe vorher die Prüfungsdatei und diesen Ordner (`buecher/auftraege/`).
2. Leg für jeden Punkt zuerst die Szenarien an und zeig, dass sie mit dem heutigen Stand rot sind. Dann behebst du ihn.
   Fehlt ein Prüfschlüssel (`text_max`, eine Obergrenze für Back-Rufe je 10 min), baust du ihn in
   `werkzeuge/szenarien.py` ein und trägst ihn in Buch 0, 12.1 nach.
3. Während der Arbeit prüfst du nur die betroffenen Szenario-Dateien. Den vollen Lauf (Tests, alle Szenarien,
   konstruierte Lagen) machst du genau einmal am Ende, vor dem Commit.
4. Schreib neue Protokolle für alle sieben Partien (102112, 133930, 140253, 144655, 145702, 164326, 173159).
5. Ergänze in `buecher/messungen.md` den Abschnitt „Qualitätsrunde 3“:
   - die Kennzahlen mit der neuen Spalte „Schranken-Verstöße“,
   - bei R10 jeden Fassungswechsel mit Ursache.
6. Committe, dann schreib `001_bericht.md` nach `README.md`.

Starte den Coach nicht. Passt ein Punkt nicht zum Code, entscheide nach dem Sinn der Prüfung und notiere es unter
„Abweichungen“.
