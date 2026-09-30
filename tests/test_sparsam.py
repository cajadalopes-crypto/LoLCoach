"""Sparprotokoll (Buch 16, 2): ohne LOLCOACH_API=1 keine API - auch mit Schluessel; die Werkzeuge reichen die
Freigabe nicht an ihre Unterprozesse weiter. Ruft nie die echte API."""
import os
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER.parent / "werkzeuge"))


def ohne_freigabe_keine_api():
    from lolcoach import llm_api
    os.environ.pop("LOLCOACH_API", None)
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-nie-benutzt"            # ein Schluessel ist da ...
    os.environ["LOLCOACH_LLM_WEG"] = "api"                             # ... und der Weg sagt API
    try:
        assert not llm_api.aktiv()
        try:
            llm_api._anfrage("x", None, "schnell", None, None, 10)
        except llm_api.APIFehler as e:
            assert "LOLCOACH_API" in str(e)
        else:
            raise AssertionError("_anfrage ohne Freigabe lief durch")
        # mit Freigabe, aber erreichtem Budget: ebenfalls gesperrt (Ausnahme mit Betrag, Buch 16, 4)
        os.environ["LOLCOACH_API"] = "1"
        os.environ["LOLCOACH_API_BUDGET"] = "0"
        assert not llm_api.aktiv()
        try:
            llm_api._anfrage("x", None, "schnell", None, None, 10)
        except llm_api.APIFehler as e:
            assert "Budget" in str(e)
        else:
            raise AssertionError("_anfrage ueber dem Budget lief durch")
    finally:
        for k in ("LOLCOACH_API", "LOLCOACH_API_BUDGET", "ANTHROPIC_API_KEY", "LOLCOACH_LLM_WEG"):
            os.environ.pop(k, None)


def werkzeuge_reichen_nicht_weiter():
    # nachspielen entfernt die Freigabe beim Import - ein Unterprozess, der es importiert, sieht sie nicht
    code = "import os, sys; sys.path.insert(0, 'werkzeuge'); import nachspielen; print(os.environ.get('LOLCOACH_API'))"
    env = {**os.environ, "LOLCOACH_API": "1", "LOLCOACH_API_BUDGET": "5"}
    aus = subprocess.run([sys.executable, "-c", code], cwd=HIER.parent, env=env, capture_output=True, text=True)
    assert aus.stdout.strip() == "None", (aus.stdout, aus.stderr[-500:])
    import generalprobe
    u = generalprobe.probe_umgebung({"LOLCOACH_API": "1", "LOLCOACH_API_BUDGET": "3", "PATH": "x"})
    assert u == {"PATH": "x"}, u


def startdatei_setzt_freigabe():
    text = (HIER.parent / "Coach starten.cmd").read_text(encoding="utf-8")
    assert "set LOLCOACH_API=1" in text


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for test in (ohne_freigabe_keine_api, werkzeuge_reichen_nicht_weiter, startdatei_setzt_freigabe):
        test()
        print(f"{test.__name__} OK")
