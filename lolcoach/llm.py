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


def _json_oder_nichts(zeile: str) -> dict | None:
    try:
        return json.loads(zeile)
    except ValueError:
        return None


def frage(prompt: str, system: str | None = None, modell: str = "sonnet", timeout: float = 120,
          aufwand: str | None = None, bilder: list[bytes] | None = None) -> str:
    """Gemessen am 26.09.2026 ueber das Abo: sonnet 4-11 s je Frage, haiku 20-60 s (!).
    Schlank: eigener Systemprompt statt des grossen Claude-Code-Prompts, keine
    Werkzeuge, keine MCP-Server, keine Projektdateien (Arbeitsordner = Temp),
    Frage ueber stdin (lange Lagen sprengen sonst die Kommandozeile).
    `bilder`: JPEG-Bytes (Spielbildschirm), gehen als Bild-Bloecke mit - dann ueber
    stream-json (gemessen: Bild + Frage in 4,5 s)."""
    befehl = [_programm(), "-p", "--model", modell, "--tools", "",
              "--no-session-persistence", "--strict-mcp-config", "--disable-slash-commands"]
    if bilder:
        import base64
        inhalt = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                "data": base64.b64encode(b).decode()}} for b in bilder]
        eingabe = json.dumps({"type": "user", "message": {"role": "user", "content": inhalt + [
            {"type": "text", "text": prompt}]}}) + "\n"
        befehl += ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"]
    else:
        eingabe = prompt
        befehl += ["--output-format", "json"]
    if system:
        befehl += ["--system-prompt", system]
    if aufwand:
        befehl += ["--effort", aufwand]
    try:
        lauf = subprocess.run(befehl, input=eingabe, capture_output=True, text=True, encoding="utf-8",
                              timeout=timeout, cwd=tempfile.gettempdir())
    except subprocess.TimeoutExpired as e:
        raise LLMFehler(f"keine Antwort nach {timeout:.0f} s") from e
    try:
        if bilder:   # stream-json: die letzte Zeile vom Typ "result" traegt die Antwort
            antwort = next(e for e in map(_json_oder_nichts, reversed(lauf.stdout.splitlines()))
                           if e and e.get("type") == "result")
        else:
            antwort = json.loads(lauf.stdout)
    except (json.JSONDecodeError, StopIteration) as e:
        # das Ende zeigen, nicht den Anfang: vorn steht bei stream-json nur die Init-Zeile (Generalprobe 26.09.)
        ende = (lauf.stderr or "").strip()[-300:] or " | ".join(lauf.stdout.strip().splitlines()[-2:])[-400:]
        raise LLMFehler(f"Rueckgabe {lauf.returncode}: {ende or 'leer'}") from e
    if antwort.get("is_error"):
        text = antwort.get("result", "")
        if "login" in text.lower():
            text += "  ->  einmal im Terminal `claude` starten und /login ausfuehren"
        raise LLMFehler(text)
    return antwort.get("result", "")


_SATZENDE = __import__("re").compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ\"„])")


def saetze(text: str) -> tuple[list[str], str]:
    """(fertige Saetze, Rest). Abkuerzungen wie "z. B." trennen keinen Satz."""
    import re
    teile = _SATZENDE.split(text)
    fertig, rest = [], teile[-1]
    stueck = ""
    for t in teile[:-1]:
        stueck = f"{stueck} {t}".strip() if stueck else t.strip()
        if re.search(r"(^|\s)\w{1,2}\.$", stueck):
            continue          # endet auf "z." oder "B." - gehoert zum naechsten Stueck
        if stueck:
            fertig.append(stueck)
        stueck = ""
    if stueck:
        rest = f"{stueck} {rest}"
    return fertig, rest


_TEIL = __import__("re").compile(r"[,;]\s|\s[–-]\s")
TEIL_AB_WOERTERN = 4


def erster_teil(text: str) -> tuple[str | None, str]:
    """Der erste Teilsatz, sobald er fertig ist: bis zum ersten Komma (oder Gedankenstrich) nach mindestens
    `TEIL_AB_WOERTERN` Woertern - die Stimme kann ihn sprechen, waehrend der Satz noch entsteht (gemessen
    27.09.: der erste ganze Satz kam 0,5-0,8 s nach dem ersten Text). "1,5" trennt nicht (kein Leerzeichen)."""
    for m in _TEIL.finditer(text):
        kopf = text[:m.start() + (1 if text[m.start()] in ",;" else 0)].strip()
        if len(kopf.split()) >= TEIL_AB_WOERTERN:
            return kopf, text[m.end():]
    return None, text


# Vorgestartete Claude-Prozesse: der Start kostet 0,6-0,9 s (gemessen 27.09.), bevor die Frage ueberhaupt
# rausgeht. Ein Prozess mit --input-format stream-json wartet auf stdin - er wird beim Druck auf die Sprechtaste
# (oder nach der letzten Antwort) gestartet und bekommt dann nur noch die Frage. Stirbt der Coach, schliesst sich
# die Leitung, und der wartende Prozess beendet sich selbst (gemessen: 0,7 s).
_VORRAT: dict[tuple, tuple[subprocess.Popen, float]] = {}
_VORRAT_SCHLOSS = __import__("threading").Lock()
VORRAT_HOECHSTENS = 15 * 60      # Sekunden: aelter wird er ersetzt, nicht benutzt


def _strom_befehl(modell: str, system: str | None, aufwand: str | None) -> list[str]:
    befehl = [_programm(), "-p", "--model", modell, "--tools", "", "--no-session-persistence",
              "--strict-mcp-config", "--disable-slash-commands", "--output-format", "stream-json", "--verbose",
              "--include-partial-messages", "--input-format", "stream-json"]
    if system:
        befehl += ["--system-prompt", system]
    if aufwand:
        befehl += ["--effort", aufwand]
    return befehl


def _starte(befehl: list[str]) -> subprocess.Popen:
    return subprocess.Popen(befehl, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", cwd=tempfile.gettempdir())


def vorhalten(modell: str = "sonnet", system: str | None = None, aufwand: str | None = None) -> None:
    """Haelt einen wartenden Prozess fuer genau diese Einstellung bereit (nichts, wenn schon einer frisch wartet)."""
    import time
    schluessel = (modell, system, aufwand)
    with _VORRAT_SCHLOSS:
        alt = _VORRAT.get(schluessel)
        if alt is not None and alt[0].poll() is None and time.monotonic() - alt[1] < VORRAT_HOECHSTENS:
            return
        try:
            _VORRAT[schluessel] = (_starte(_strom_befehl(modell, system, aufwand)), time.monotonic())
        except (LLMFehler, OSError):
            _VORRAT.pop(schluessel, None)
            return
    if alt is not None:
        _schliessen(alt[0])


def _schliessen(lauf: subprocess.Popen) -> None:
    try:
        lauf.stdin.close()     # wartet er noch: beendet sich selbst
    except OSError:
        pass
    try:
        lauf.wait(timeout=0.01)
    except subprocess.TimeoutExpired:
        __import__("threading").Timer(3.0, lambda: lauf.poll() is None and lauf.kill()).start()


def _aus_vorrat(schluessel: tuple) -> subprocess.Popen | None:
    import time
    with _VORRAT_SCHLOSS:
        eintrag = _VORRAT.pop(schluessel, None)
    if eintrag is None:
        return None
    lauf, seit = eintrag
    if lauf.poll() is not None or time.monotonic() - seit >= VORRAT_HOECHSTENS:
        _schliessen(lauf)
        return None
    return lauf


def frage_strom(prompt: str, bei_satz, system: str | None = None, modell: str = "sonnet", timeout: float = 60,
                aufwand: str | None = None, bilder: list[bytes] | None = None, nachladen: bool = False) -> str:
    """Wie `frage`, aber gestreamt: jeder fertige Satz geht sofort an `bei_satz(satz)` - der Coach kann den
    ersten Satz sprechen, waehrend der Rest noch entsteht (gemessen 26.09.: erster Satz nach 2,7-3,1 s,
    ganze Antwort nach 5,1-5,2 s). Der erste Teilsatz geht schon vor dem Satzende raus (`erster_teil`), und
    ein vorgehaltener Prozess spart den Start (`vorhalten`). `nachladen`: danach gleich wieder einen
    vorhalten. Gibt die ganze Antwort zurueck."""
    import threading
    schluessel = (modell, system, aufwand)
    lauf = _aus_vorrat(schluessel) or _starte(_strom_befehl(modell, system, aufwand))
    inhalt: list[dict] = []
    if bilder:
        import base64
        inhalt = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                "data": base64.b64encode(b).decode()}} for b in bilder]
    eingabe = json.dumps({"type": "user", "message": {"role": "user", "content": inhalt + [
        {"type": "text", "text": prompt}]}}) + "\n"
    uhr = threading.Timer(timeout, lauf.kill)
    uhr.start()
    try:
        lauf.stdin.write(eingabe)
        lauf.stdin.close()
        puffer, ergebnis, gesendet = "", None, False
        for zeile in lauf.stdout:
            e = _json_oder_nichts(zeile)
            if not e:
                continue
            if e.get("type") == "stream_event":
                ev = e.get("event", {})
                if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                    puffer += ev["delta"]["text"]
                    fertige, puffer = saetze(puffer)
                    if not gesendet and not fertige:
                        teil, puffer = erster_teil(puffer)
                        fertige = [teil] if teil else []
                    for satz in fertige:
                        gesendet = True
                        bei_satz(satz)
            elif e.get("type") == "result":
                ergebnis = e
        lauf.wait(timeout=5)
    finally:
        uhr.cancel()
        if nachladen:
            threading.Thread(target=vorhalten, args=schluessel, daemon=True).start()
    if ergebnis is None:
        raise LLMFehler(f"keine Antwort (Rueckgabe {lauf.returncode})")
    if ergebnis.get("is_error"):
        raise LLMFehler(ergebnis.get("result", ""))
    if puffer.strip():
        bei_satz(puffer.strip())
    return ergebnis.get("result", "")
