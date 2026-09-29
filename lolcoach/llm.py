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


_API_AUS_BIS = [0.0]


def _ueber_api():
    """Das Modul llm_api, wenn Claude ueber die API laufen soll (und sie nicht eben ausgefallen ist)."""
    import time
    if time.monotonic() < _API_AUS_BIS[0]:
        return None
    try:
        from . import llm_api
        return llm_api if llm_api.aktiv() else None
    except Exception:
        return None


def _api_ausfall(e: Exception) -> None:
    """Die API faellt aus: einmal im Log, 120 s lang das Abo (Buch 14, A.3: Ersatz)."""
    import time
    if time.monotonic() >= _API_AUS_BIS[0]:
        print(f"  Claude-API: Ausfall ({type(e).__name__}: {str(e)[:100]}) - 120 s lang ueber das Abo", flush=True)
    _API_AUS_BIS[0] = time.monotonic() + 120.0


def _abo_modell(modell: str) -> str:
    """Auf dem Abo gibt es nur sonnet (haiku antwortete ueber die Kommandozeile nicht, Auftrag 017)."""
    return "sonnet" if modell in ("schnell", "stark", "haiku") or modell.startswith("claude-") else modell


def frage(prompt: str, system: str | None = None, modell: str = "sonnet", timeout: float = 120,
          aufwand: str | None = None, bilder: list[bytes] | None = None) -> str:
    """Gemessen am 26.09.2026 ueber das Abo: sonnet 4-11 s je Frage, haiku 20-60 s (!).
    Schlank: eigener Systemprompt statt des grossen Claude-Code-Prompts, keine
    Werkzeuge, keine MCP-Server, keine Projektdateien (Arbeitsordner = Temp),
    Frage ueber stdin (lange Lagen sprengen sonst die Kommandozeile).
    `bilder`: JPEG-Bytes (Spielbildschirm), gehen als Bild-Bloecke mit - dann ueber
    stream-json (gemessen: Bild + Frage in 4,5 s).
    Auftrag 019: mit API-Schluessel ([llm] weg = "api") zuerst ueber die API; faellt sie aus, das Abo."""
    if (api := _ueber_api()) is not None:
        try:
            return api.frage(prompt, system=system, modell=modell, timeout=min(timeout, 60), bilder=bilder)
        except Exception as e:
            _api_ausfall(e)
    modell = _abo_modell(modell)
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
# Auftrag 017, 0.2: ein gerade gestarteter Prozess ist noch nicht bereit (die CLI braucht ~2 s bis zur ersten
# Antwort-Bereitschaft) - kommen zwei Anfragen kurz hintereinander, bekam die zweite einen halb gestarteten. Der
# Stratege haelt deshalb zwei vor; genommen wird immer der aelteste.
_VORRAT: dict[tuple, list[tuple[subprocess.Popen, float]]] = {}
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


def vorhalten(modell: str = "sonnet", system: str | None = None, aufwand: str | None = None,
              anzahl: int = 1) -> None:
    """Haelt `anzahl` wartende Prozesse fuer genau diese Einstellung bereit (nichts, wenn schon genug frisch warten)."""
    import time
    if _ueber_api() is not None:
        return                       # Auftrag 019: ueber die API braucht es keinen wartenden Abo-Prozess
    schluessel = (modell, system, aufwand)
    weg = []
    with _VORRAT_SCHLOSS:
        liste = _VORRAT.setdefault(schluessel, [])
        frisch = [e for e in liste if e[0].poll() is None and time.monotonic() - e[1] < VORRAT_HOECHSTENS]
        weg = [e for e in liste if e not in frisch]
        liste[:] = frisch
        while len(liste) < anzahl:
            try:
                liste.append((_starte(_strom_befehl(modell, system, aufwand)), time.monotonic()))
            except (LLMFehler, OSError):
                break
    for e in weg:
        _schliessen(e[0])


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
        liste = _VORRAT.get(schluessel) or []
        eintrag = liste.pop(0) if liste else None       # der aelteste - er ist am ehesten bereit
    if eintrag is None:
        return None
    lauf, seit = eintrag
    if lauf.poll() is not None or time.monotonic() - seit >= VORRAT_HOECHSTENS:
        _schliessen(lauf)
        return None
    return lauf


def frage_strom(prompt: str, bei_satz, system: str | None = None, modell: str = "sonnet", timeout: float = 60,
                aufwand: str | None = None, bilder: list[bytes] | None = None, nachladen: bool | int = False,
                messung: dict | None = None, bei_fertig=None, wissen: str | None = None) -> str:
    """Wie `frage`, aber gestreamt: jeder fertige Satz geht sofort an `bei_satz(satz)` - der Coach kann den
    ersten Satz sprechen, waehrend der Rest noch entsteht (gemessen 26.09.: erster Satz nach 2,7-3,1 s,
    ganze Antwort nach 5,1-5,2 s). Der erste Teilsatz geht schon vor dem Satzende raus (`erster_teil`), und
    ein vorgehaltener Prozess spart den Start (`vorhalten`). `nachladen`: danach gleich wieder einen
    vorhalten. Gibt die ganze Antwort zurueck."""
    import threading
    import time as _t
    if (api := _ueber_api()) is not None:
        # Auftrag 019: ueber die API (schneller, parallel moeglich); geht nichts raus, bevor sie ausfaellt, das Abo
        gesagt = [False]

        def weiter(s):
            gesagt[0] = True
            bei_satz(s)
        try:
            return api.frage_strom(prompt, weiter, system=system, modell=modell, timeout=min(timeout, 30),
                                   bei_fertig=bei_fertig, messung=messung, bilder=bilder, wissen=wissen)
        except Exception as e:
            _api_ausfall(e)
            if gesagt[0]:
                raise LLMFehler(f"API brach mitten in der Antwort ab: {e}")
    modell = _abo_modell(modell)
    if wissen:                     # Auftrag 021: das Abo kennt keinen zwischengespeicherten Block - er haengt am System
        system = f"{system or ''}\n\n{wissen}"
    t0 = _t.monotonic()
    schluessel = (modell, system, aufwand)
    lauf = _aus_vorrat(schluessel)
    warm = lauf is not None
    lauf = lauf or _starte(_strom_befehl(modell, system, aufwand))
    if messung is not None:            # Auftrag 017, 0.2: wo die Zeit hingeht
        messung.update(warm=warm, prompt_zeichen=len(prompt), start_s=_t.monotonic() - t0)
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
        puffer, ergebnis, gesendet, fertig_gemeldet = "", None, False, False
        for zeile in lauf.stdout:
            e = _json_oder_nichts(zeile)
            if not e:
                continue
            if e.get("type") == "stream_event":
                ev = e.get("event", {})
                if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                    if messung is not None and "erstes_token_s" not in messung:
                        messung["erstes_token_s"] = _t.monotonic() - t0
                    puffer += ev["delta"]["text"]
                    fertige, puffer = saetze(puffer)
                    if not gesendet and not fertige:
                        teil, puffer = erster_teil(puffer)
                        fertige = [teil] if teil else []
                    for satz in fertige:
                        gesendet = True
                        bei_satz(satz)
                elif ev.get("type") == "message_stop" and bei_fertig is not None and not fertig_gemeldet:
                    # Auftrag 017, 0.2: der Text ist fertig - das "result" kommt erst ~1 s spaeter (post_turn_summary)
                    fertig_gemeldet = True
                    if messung is not None:
                        messung["text_fertig_s"] = _t.monotonic() - t0
                    if puffer.strip():
                        bei_satz(puffer.strip())
                    puffer = ""
                    bei_fertig()
            elif e.get("type") == "result":
                ergebnis = e
                if messung is not None:
                    messung["ende_s"] = _t.monotonic() - t0
                    messung["api_ms"] = e.get("duration_api_ms")
                    u = e.get("usage") or {}
                    messung["eingabe_token"] = sum(u.get(k) or 0 for k in (
                        "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                    messung["cache_token"] = u.get("cache_read_input_tokens")
        lauf.wait(timeout=5)
    finally:
        uhr.cancel()
        if nachladen:
            threading.Thread(target=vorhalten, args=(*schluessel, int(nachladen)), daemon=True).start()
    if ergebnis is None:
        raise LLMFehler(f"keine Antwort (Rueckgabe {lauf.returncode})")
    if ergebnis.get("is_error"):
        raise LLMFehler(ergebnis.get("result", ""))
    if puffer.strip():
        bei_satz(puffer.strip())
    return ergebnis.get("result", "")
