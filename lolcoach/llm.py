"""Claude als Analyst - vorerst ueber das Abo, per Claude-Code-Kommandozeile.

`claude -p` antwortet in Sekunden, nicht in Millisekunden. Deshalb gehoert
das Modell NIE in den Echtzeitweg: dort entscheidet das Regelwerk. Das Modell
formuliert das "Warum", wo Zeit ist, und macht die Post-Game-Analyse.

Spaeter austauschbar gegen die API (eigener Schluessel): nur `frage` aendert sich.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class LLMFehler(Exception):
    pass


def _programm() -> str:
    """claude auf dem PATH, sonst die neueste von der Desktop-App mitgebrachte."""
    if pfad := shutil.which("claude"):
        return pfad
    # Die Desktop-App ist ein MSIX-Paket: ihr AppData ist nur fuer sie selbst
    # umgeleitet, von aussen liegt es unter Packages\Claude_*\LocalCache.
    orte = [Path(os.environ.get("APPDATA", "")) / "Claude" / "claude-code"]
    orte += Path(os.environ.get("LOCALAPPDATA", ""), "Packages").glob("Claude_*/LocalCache/Roaming/Claude/claude-code")
    kandidaten = sorted((exe for ort in orte for exe in ort.glob("*/claude.exe")),
                        key=lambda p: [int(x) if x.isdigit() else 0 for x in p.parent.name.split(".")])
    if not kandidaten:
        raise LLMFehler("claude nicht gefunden (weder PATH noch Desktop-App)")
    return str(kandidaten[-1])


def frage(prompt: str, system: str | None = None, modell: str = "sonnet", timeout: float = 120,
          aufwand: str | None = None) -> str:
    """Gemessen am 26.09.2026 ueber das Abo: sonnet 4-11 s je Frage, haiku 20-60 s (!).
    Schlank: eigener Systemprompt statt des grossen Claude-Code-Prompts, keine
    Werkzeuge, keine MCP-Server, keine Projektdateien (Arbeitsordner = Temp),
    Frage ueber stdin (lange Lagen sprengen sonst die Kommandozeile)."""
    befehl = [_programm(), "-p", "--model", modell, "--output-format", "json", "--tools", "",
              "--no-session-persistence", "--strict-mcp-config", "--disable-slash-commands"]
    if system:
        befehl += ["--system-prompt", system]
    if aufwand:
        befehl += ["--effort", aufwand]
    try:
        lauf = subprocess.run(befehl, input=prompt, capture_output=True, text=True, encoding="utf-8",
                              timeout=timeout, cwd=tempfile.gettempdir())
    except subprocess.TimeoutExpired as e:
        raise LLMFehler(f"keine Antwort nach {timeout:.0f} s") from e
    try:
        antwort = json.loads(lauf.stdout)
    except json.JSONDecodeError as e:
        raise LLMFehler((lauf.stderr or lauf.stdout)[:300]) from e
    if antwort.get("is_error"):
        text = antwort.get("result", "")
        if "login" in text.lower():
            text += "  ->  einmal im Terminal `claude` starten und /login ausfuehren"
        raise LLMFehler(text)
    return antwort.get("result", "")
