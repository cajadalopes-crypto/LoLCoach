"""Alle Aufnahmen durchspielen und die Ansagen des Coaches pruefen - ohne Stimme, ohne Claude.

Was geprueft wird (26.09.2026, beim Gegenlesen von Hand gefunden - jetzt maschinell):
  - Widerspruch: ein "geh rein"/Druck-Satz bis 15 s nach einer Warnung,
  - Hin und Her: "geh zurueck" und bis 12 s danach "halte deine Stellung"/"nimm den Kampf an"/"geh rein"
    (Nachlauf Wukong 25:26-25:48, 26.09. nachts),
  - Doppelung: zweimal dasselbe Thema in 10 s,
  - Vorlage: ein Satz, der woertlich in wissen/makro.toml steht (also nicht gerechnet ist),
  - zu lang: ueber 300 Zeichen (~25 s Sprechzeit; seit 26.09. spricht der Coach zusammenhaengend - Carlos:
    "zusammenhaengende Saetze" -, aber eine Ansage darf nicht alles andere eine halbe Minute blockieren),
  - Sprache: "in 1 Sekunden", "Larven lebt", "fuer Der ...", doppelte Leerzeichen, "None".

    python werkzeuge/ansagen_pruefen.py [aufnahme ...]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lolcoach import aufzeichnung, lage, regeln, sprechplan, stimme, wissen, zustand  # noqa: E402

AUFNAHMEN = Path(__file__).resolve().parent.parent / "aufnahmen"
SPRACHE = [(r"\bin 1 Sekunden\b", "in 1 Sekunden"), (r"Larven lebt\b", "Larven lebt"),
           (r"\bfür Der\b", "für Der"), (r"  ", "doppeltes Leerzeichen"), (r"\bNone\b", "None"),
           (r"\.\.", "zwei Punkte"), (r" ,", "Leerzeichen vor Komma")]
# eigenes Muster, nicht regeln.RUECKZUG: die Pruefung muss auch gegen einen alten Stand laufen (Gegenprobe)
RUECKZUG = re.compile(r"geh (sofort |jetzt |lieber )?zurück|raus da", re.I)


def vorlagen() -> set[str]:
    """Alle festen Saetze aus makro.toml (ohne Platzhalter-Teile), zum Wiedererkennen."""
    aus = set()

    def sammle(x):
        if isinstance(x, dict):
            for v in x.values():
                sammle(v)
        elif isinstance(x, str) and len(x) > 25:
            kopf = re.split(r"\{", x)[0].strip()
            if len(kopf) > 20:
                aus.add(kopf)
    sammle(wissen.lade("makro"))
    return aus


def ansagen(pfad: Path):
    sicht = lage.sicht_fuer(pfad)
    werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
    lb = lage.Lagebild() if sicht else None
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = zustand.partie(d)
        if sicht and p.ich:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p)
        plan.neu(werk.pruefe(p, lb))
        plan.takt(p.zeit)
    return plan.gesagt


def pruefe(pfad: Path) -> dict:
    gesagt = ansagen(pfad)
    feste = vorlagen()
    befunde = {"widerspruch": [], "hinundher": [], "doppelt": [], "vorlage": [], "lang": [], "sprache": []}
    for i, a in enumerate(gesagt):
        t = a.gesprochen or a.zeit
        if re.search(r"Halte deine Stellung|Nimm den Kampf an|nimm den Kampf an|[Gg]eh rein", a.text):
            for b in gesagt[max(0, i - 6):i]:
                if RUECKZUG.search(b.text) and 0 <= t - (b.gesprochen or b.zeit) <= 12:
                    befunde["hinundher"].append((t, b.text, a.text))
                    break
        if a.thema == "druck":
            for b in gesagt[max(0, i - 6):i]:
                if b.thema == "gefahr" and 0 <= t - (b.gesprochen or b.zeit) <= 15:
                    befunde["widerspruch"].append((t, b.text, a.text))
        for b in gesagt[max(0, i - 4):i]:
            if a.thema and b.thema == a.thema and a.thema != "gefahr" and 0 <= t - (b.gesprochen or b.zeit) <= 10:
                befunde["doppelt"].append((t, b.text, a.text))
        if any(a.text.startswith(k) for k in feste):
            befunde["vorlage"].append((t, a.text))
        if len(a.text) > 300:
            befunde["lang"].append((t, a.text))
        for muster, name in SPRACHE:
            if re.search(muster, a.text):
                befunde["sprache"].append((t, name, a.text))
    befunde["anzahl"] = len(gesagt)
    befunde["minuten"] = (gesagt[-1].gesprochen or 0) / 60 if gesagt else 0
    return befunde


def uhr(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pfade = [Path(a) for a in sys.argv[1:]] or sorted(AUFNAHMEN.glob("*.jsonl.gz"))
    for pfad in pfade:
        try:
            b = pruefe(pfad)
        except Exception as e:
            print(f"{pfad.name}: Fehler {type(e).__name__}: {e}")
            continue
        if not b["anzahl"]:
            continue
        je_min = b["anzahl"] / max(1.0, b["minuten"])
        print(f"== {pfad.name}: {b['anzahl']} Ansagen in {b['minuten']:.0f} min ({je_min:.1f}/min); "
              + ", ".join(f"{k} {len(v)}" for k, v in b.items() if isinstance(v, list)))
        for k in ("widerspruch", "hinundher", "doppelt", "sprache"):
            for x in b[k][:4]:
                print(f"   {k} {uhr(x[0])}: " + " | ".join(x[1:]))
        vorl = {}
        for t, text in b["vorlage"]:
            vorl[text[:50]] = vorl.get(text[:50], 0) + 1
        for text, n in sorted(vorl.items(), key=lambda x: -x[1])[:6]:
            print(f"   vorlage {n}x: {text}")
