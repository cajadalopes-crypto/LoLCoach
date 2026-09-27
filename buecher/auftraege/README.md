# Auftraege zwischen Claude (Chat, Projektleitung) und Claude Code

Dieses Postfach ersetzt das Kopieren durch Carlos. Carlos hat es am 27.09.2026 so eingerichtet.

## Ablauf

1. **Claude (Chat) legt einen Auftrag an:** `NNN_auftrag.md`, fortlaufend nummeriert (001, 002, ...).
2. **Claude Code prüft das Postfach** regelmäßig (`/loop`). Gibt es einen `NNN_auftrag.md` ohne `NNN_bericht.md` und
   ohne `NNN_in_arbeit`, dann:
   - legt er zuerst `NNN_in_arbeit` an (Inhalt: Startzeit),
   - arbeitet den Auftrag vollständig ab,
   - schreibt `NNN_bericht.md` und löscht `NNN_in_arbeit`,
   - committet Auftrag und Bericht.
3. **Fehlt eine Entscheidung,** schreibt Claude Code sie in `NNN_frage.md` und arbeitet an allem weiter, was nicht
   davon abhängt. Er wartet nicht untätig. Die Antwort kommt als nächster Auftrag.
4. **Claude (Chat) prüft den Bericht** und die Protokolle und legt den nächsten Auftrag an. Er sagt Carlos Bescheid,
   wenn es etwas für ihn gibt, etwa „jetzt wieder live testen“.

## Regeln

- **Aufträge in diesem Ordner gelten als von Carlos freigegeben** (Carlos, 27.09.2026). Die harten Grenzen aus
  `CLAUDE.md` gelten weiter. Den Coach startet niemand, solange umgebaut wird.
- **Der Bericht ist kurz**, höchstens eine Bildschirmseite. Er enthält:
  - die Commits,
  - Tests und Szenarien (grün/rot/übersprungen),
  - die Kennzahlen-Tabelle,
  - was offen ist und was entschieden werden muss.

  Die Einzelheiten gehören nach `buecher/messungen.md`.
- **Nichts wird überschrieben.** Ein neuer Auftrag bekommt eine neue Nummer.
