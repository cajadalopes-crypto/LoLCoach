# Auftrag 005 – Selbstprüfung mit einem unabhängigen Kritiker, zwei Runden (Claude, Chat, 28.09.2026 00:15)

Nur nach Auftrag 004. Ziel: Die Sätze finden und beheben, die ein Challenger-Toplaner als falsch oder nutzlos
ablehnen würde, ohne dass ich jede Runde selbst lesen muss.

## Ablauf je Runde

1. **Kritiker starten.** Das ist ein eigener Agent **ohne** Wissen über den Code.
   - **Rolle:** „Du bist Challenger-Toplaner (Riven-Main) und Coach. Du hörst einem Live-Coach zu, der einem Spieler
     Ansagen macht.“
   - **Er bekommt:**
     - die Protokolle 164326, 173159, 213624 (mit Fragen), 144655 und 102112 aus `buecher/protokolle/`,
     - Carlos' Notizen aus `aufnahmen/2026-09-27_213624_notizen.md`,
     - die drei Prüfungen `PRUEFUNG_2026-09-27*.md` als Beispiele dafür, was ich ablehne.
   - **Auftrag an ihn:** Jede gesprochene Ansage und jede Antwort bewerten, mit **ok / schwach / falsch**, einem Grund
     aus der Lage im Protokoll und dem Satz, den ein Challenger stattdessen sagen würde (oder „schweigen“).
   - **Keine Geschmacksfragen.** „Falsch“ heißt: sachlich falsch, gefährlich, widersprüchlich, sinnlos oder an der
     Frage vorbei.
2. **Klassen bilden.** Die Befunde nach Ursache gruppieren, zum Beispiel „Floskel“, „Ziel falsch“, „Grund passt
   nicht“, „zu spät“, „Wiederholung“. Zu jeder Klasse gehören Anzahl und Beispiele. Die Klassen kommen nach
   `buecher/auftraege/005_kritik_runde<N>.md`.
3. **Beheben**, nur Klassen mit „falsch“ und ≥ 2 Fällen. Für jede Klasse gilt:
   - Ein Szenario aus einem echten Fall, zuerst rot.
   - Dann der Fix im Sinne der Bücher.
   - Braucht ein Fix eine Grundsatzentscheidung (neue Regel, die einem Buch widerspricht), kommt sie nach
     `005_frage.md` und wird **nicht** gebaut.
4. **Nachmessen.** Alle Szenarien, die Tests und die konstruierten Lagen bleiben grün, danach neue Protokolle.
5. **Runde 2** mit einem **neuen** Kritiker-Agenten auf den neuen Protokollen. Danach wird nichts mehr gebaut, nur
   noch gezählt.

## Grenzen

- **Keine Schranke lockern.** Das betrifft R1 (Leben/Risiko), R2 (stummes Kampfmodell außerhalb der
  Überlegenheits-Regel) und die harten Grenzen aus `CLAUDE.md`.
- **Keine neuen Funktionen**, die in keinem Buch stehen.
- **Bot-Partien** (102112, 213624) prüfen nur Form und Verdrahtung. Kampfurteile gegen Bots zählen nicht als
  „falsch“.

## Ende

1. In messungen.md den Abschnitt „Auftrag 005“ anlegen, mit der Tabelle der Klassen: vorher, nach Runde 1, nach
   Runde 2; „falsch“ und „schwach“ je 30 min, je Partie.
2. Committen und `005_bericht.md` schreiben.
3. Starte den Coach nicht.
