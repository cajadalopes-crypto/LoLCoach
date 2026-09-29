"""Claude ueber die API (Buch 14, A.3; Auftrag 019) - schneller als das Abo ueber die Kommandozeile.

- Schluessel aus `geheim/claude_api_key.txt` (nie ausgeben, nie loggen) oder ANTHROPIC_API_KEY.
- Zwei Modelle ([llm] in wissen/kern.toml): "schnell" (Claude Haiku 4.5, ohne Nachdenken) und "stark" (Claude Sonnet
  5.5, Nachdenken aus: thinking between_tools, effort low - das adaptive Nachdenken kostete ueber das Abo 4-7 s).
- Streaming; System-Prompt und Wissen als zwischengespeicherter Block (cache_control); gesprochen wird beim Textende.
- Kostenzaehler je Partie: `KOSTEN` (Datei setzt __main__ bzw. das Nachspiel: <partie>_kosten.json).
- Ersatz: faellt die API aus oder fehlt der Schluessel, nimmt `llm` das Abo (Kommandozeile).
- Sonnet 5.5 laeuft mit dem serverseitigen Ersatz bei Ablehnungen (fallbacks "default").
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
MODELLE = {"schnell": "claude-haiku-4-5", "stark": "claude-sonnet-5-5"}
ALIAS = {"haiku": "schnell", "sonnet": "stark", "opus": "stark"}
# $ je 1 Mio. Tokens: Eingabe, Ausgabe, Cache lesen, Cache schreiben (5 min) - Stand 25.09.2026 (Anthropic-Preisliste)
PREISE = {"claude-haiku-4-5": (1.00, 5.00, 0.10, 1.25), "claude-sonnet-5-5": (2.00, 10.00, 0.20, 2.50)}
_CLIENT = None
_SCHLOSS = threading.Lock()


class APIFehler(RuntimeError):
    pass


def _cfg() -> dict:
    try:
        from . import wissen
        return dict(wissen.lade("kern").get("llm", {}))
    except Exception:
        return {}


def schluessel() -> str | None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"].strip()
    datei = WURZEL / "geheim" / "claude_api_key.txt"
    try:
        k = datei.read_text(encoding="utf-8").strip()
        return k or None
    except OSError:
        return None


def aktiv() -> bool:
    """Laeuft Claude ueber die API? ([llm] weg = "api" und ein Schluessel ist da, das SDK installiert.)"""
    if os.environ.get("LOLCOACH_LLM_WEG", _cfg().get("weg", "api")) != "api" or schluessel() is None:
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def modell_id(modell: str) -> str:
    c = _cfg()
    rolle = ALIAS.get(modell, modell)
    if rolle in ("schnell", "stark"):
        return c.get(rolle, MODELLE[rolle])
    return modell


def _client():
    global _CLIENT
    with _SCHLOSS:
        if _CLIENT is None:
            import anthropic
            _CLIENT = anthropic.Anthropic(api_key=schluessel(), max_retries=1)
        return _CLIENT


class Kosten:
    """Tokens und Dollar je Partie, je Modell - thread-sicher, nach jedem Aufruf in `datei` geschrieben."""

    def __init__(self):
        self.datei: Path | None = None
        self.je_modell: dict[str, dict] = {}
        self._schloss = threading.Lock()

    def dazu(self, modell: str, usage) -> float:
        ein, aus, lesen, schreiben = PREISE.get(modell, (3.0, 15.0, 0.3, 3.75))
        n_ein = getattr(usage, "input_tokens", 0) or 0
        n_aus = getattr(usage, "output_tokens", 0) or 0
        n_lesen = getattr(usage, "cache_read_input_tokens", 0) or 0
        n_schreiben = getattr(usage, "cache_creation_input_tokens", 0) or 0
        dollar = (n_ein * ein + n_aus * aus + n_lesen * lesen + n_schreiben * schreiben) / 1e6
        with self._schloss:
            e = self.je_modell.setdefault(modell, {"aufrufe": 0, "eingabe": 0, "ausgabe": 0, "cache_lesen": 0,
                                                   "cache_schreiben": 0, "dollar": 0.0})
            e["aufrufe"] += 1
            e["eingabe"] += n_ein
            e["ausgabe"] += n_aus
            e["cache_lesen"] += n_lesen
            e["cache_schreiben"] += n_schreiben
            e["dollar"] = round(e["dollar"] + dollar, 6)
            self._speichern()
        return dollar

    def summe(self) -> float:
        return round(sum(e["dollar"] for e in self.je_modell.values()), 4)

    def _speichern(self) -> None:
        if self.datei is None:
            return
        try:
            self.datei.write_text(json.dumps({"summe_dollar": self.summe(), "je_modell": self.je_modell}, indent=1),
                                  encoding="utf-8")
        except OSError:
            pass


KOSTEN = Kosten()


def _anfrage(prompt: str, system: str | None, modell: str, wissen: str | None, bilder: list[bytes] | None,
             max_tokens: int) -> dict:
    mid = modell_id(modell)
    sys_bloecke = []
    if system:
        sys_bloecke.append({"type": "text", "text": system})
    if wissen:
        sys_bloecke.append({"type": "text", "text": wissen})
    if sys_bloecke:
        sys_bloecke[-1]["cache_control"] = {"type": "ephemeral"}      # System + Wissen: stabiler Anfang
    inhalt: list[dict] = []
    if bilder:
        import base64
        inhalt = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                "data": base64.b64encode(b).decode()}} for b in bilder]
    k = {"model": mid, "max_tokens": max_tokens,
         "messages": [{"role": "user", "content": inhalt + [{"type": "text", "text": prompt}]}]}
    if sys_bloecke:
        k["system"] = sys_bloecke
    if mid.startswith("claude-sonnet-5-5"):
        k["thinking"] = {"type": "between_tools"}                     # kein Nachdenken: Latenz (Auftrag 017/019)
        k["output_config"] = {"effort": "low"}
        k["betas"] = ["server-side-fallback-2026-07-01"]
        k["fallbacks"] = "default"
    return k


def frage_strom(prompt: str, bei_satz, system: str | None = None, modell: str = "schnell", timeout: float = 30,
                bei_fertig=None, wissen: str | None = None, messung: dict | None = None, bilder=None,
                max_tokens: int = 400) -> str:
    """Gestreamt wie `llm.frage_strom`: fertige Saetze an `bei_satz`, am Textende `bei_fertig()`. Wirft APIFehler."""
    import anthropic
    from .llm import erster_teil, saetze, stille_zeile
    t0 = time.monotonic()
    k = _anfrage(prompt, system, modell, wissen, bilder, max_tokens)
    beta = "betas" in k
    c = _client().with_options(timeout=timeout)
    puffer, gesendet, text, frueh = "", False, "", False
    try:
        strom = c.beta.messages.stream(**k) if beta else c.messages.stream(**k)
        with strom as s:
            for stueck in s.text_stream:
                if messung is not None and "erstes_token_s" not in messung:
                    messung["erstes_token_s"] = time.monotonic() - t0
                text += stueck
                puffer += stueck
                fertige, puffer = saetze(puffer)
                if not gesendet and not fertige:
                    teil, puffer = erster_teil(puffer)
                    fertige = [teil] if teil else []
                for satz in fertige:
                    gesendet = True
                    bei_satz(satz)
                if bei_fertig is not None and not frueh and stille_zeile(puffer):
                    frueh = True                         # Auftrag 023, 4: nicht auf die PLAN-Zeile warten
                    if messung is not None:
                        messung["text_fertig_s"] = time.monotonic() - t0
                    bei_fertig()
            if puffer.strip():
                bei_satz(puffer.strip())
            if messung is not None and not frueh:
                messung["text_fertig_s"] = time.monotonic() - t0
            if bei_fertig is not None and not frueh:
                bei_fertig()
            m = s.get_final_message()
    except anthropic.APIError as e:
        raise APIFehler(f"{type(e).__name__}: {getattr(e, 'message', e)}") from None
    KOSTEN.dazu(m.model if getattr(m, "model", None) in PREISE else k["model"], m.usage)
    if messung is not None:
        messung.update(ende_s=time.monotonic() - t0, modell=k["model"], eingabe_token=m.usage.input_tokens,
                       cache_token=getattr(m.usage, "cache_read_input_tokens", 0))
    if m.stop_reason == "refusal":
        raise APIFehler("abgelehnt (refusal)")
    return text


def frage(prompt: str, system: str | None = None, modell: str = "stark", timeout: float = 60,
          bilder: list[bytes] | None = None, wissen: str | None = None, max_tokens: int = 2000) -> str:
    """Ohne Satz-Rueckruf (Briefing, Spielakte, Review)."""
    return frage_strom(prompt, lambda s: None, system=system, modell=modell, timeout=timeout, wissen=wissen,
                       bilder=bilder, max_tokens=max_tokens)
