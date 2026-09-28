"""Protokoll einer Partie: jede ungefragte Ansage mit der Lage, in der sie fiel - zum Lesen ohne Spiel.

Spielt eine Aufnahme wie live nach (`--kern neu`, Stimme in Spielzeit wie stimme.Nachgespielt) und schreibt nach
`buecher/protokolle/<stamm>.md` je Ansage: Zeit, Modus, Plan des Kerns, Ort, Leben, Gold, was gesagt wurde (und
von wem: Kern oder alte Regel) und die zwei naechstbesten Optionen des Kerns mit EV. Ein abgebrochener Satz ist
markiert.

Seit Auftrag 003 (Buch 11, 10.6) je Ansage auch `danach` und die Zeitleiste; mit `--fragen` werden die Fragen aus
`<stamm>_sprechtaste.log` zur Zeit eingespielt (wie per Sprechtaste), ihre Antworten stehen mit im Protokoll.

    python werkzeuge/protokoll.py                       # juengste Aufnahme
    python werkzeuge/protokoll.py 2026-09-27_102112 2026-09-27_140253
    python werkzeuge/protokoll.py 2026-09-27_213624 --fragen
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nachspielen as ns  # noqa: E402
from lolcoach import aufzeichnung  # noqa: E402
from lolcoach.kern.modus import bereich_worte  # noqa: E402

ZIEL = Path(__file__).resolve().parent.parent / "buecher" / "protokolle"


def _option(h) -> str:
    satz = h.satz or h.grund or ""
    return f"{h.art} (EV {h.ev:+.0f}, p_tod {h.p_tod:.2f})" + (f" „{satz}“" if satz else "")


def schnappschuss(a, p, werk, kern) -> dict:
    """Die Lage in dem Takt, in dem `a` an die Stimme ging."""
    m = kern.m
    plan = kern.fuehrer.plan
    kand = sorted(kern.kandidaten or [], key=lambda h: -h.ev)
    gewaehlt = plan.als() if plan is not None else None
    rest = [h for h in kand if h.art != gewaehlt][:2]
    leben = m.leben if m is not None and m.leben is not None else (werk.b.leben if werk.b is not None else None)
    # Buch 4, 4 (Auftrag 008): welche Groesse die Wahl gegen die Zweitbeste entschied - ohne sie gerechnet kippt sie
    entscheidend = None
    if plan is not None and rest and m is not None:
        from lolcoach.kern import fuehren
        k = fuehren.entscheidend(plan.handlung, rest[0], m, kern.cfg)
        entscheidend = f"{k} (ohne ihn kippt die Wahl zu {rest[0].art})" if k else "mehrere Groessen zusammen"
    return {
        "zeit": a.gesprochen, "modus": kern.modus.aktuell or "–",
        "ort": bereich_worte(m.bereich) if m is not None else "Ort unbekannt",
        "leben": None if leben is None else round(leben * 100),
        "gold": None if p.gold is None else int(p.gold),
        "plan": None if plan is None else (plan.art, plan.handlung.ev, plan.handlung.p_tod),
        "gefahr": kern.gefahr, "optionen": [_option(h) for h in rest],
        "danach": getattr(kern, "danach_text", None), "entscheidend": entscheidend,
        "zeitleiste": [f"{ns.uhr(e.zeit)} {e.text}" for e in (getattr(kern, "zeitleiste", None) or [])[:5]],
    }


def protokoll(stamm: str, kern: str = "neu", fragen: bool = False) -> Path:
    import fuehrmass
    pfad = ns.pfad_zu(stamm)
    liste = [(f["zeit"], f["text"], i) for i, f in enumerate(fuehrmass.fragen_aus_log(stamm))] if fragen else None
    lagen: dict[int, dict] = {}
    gesehen = [0]
    info = {}

    def beim_takt(p, werk, kern_, plan):
        if p.ich and not info:
            g = p.gegenueber()
            info.update(champion=p.ich.champion, gegner=g.champion if g else "?", team=p.mein_team)
        for a in plan.gesagt[gesehen[0]:]:
            lagen[id(a)] = schnappschuss(a, p, werk, kern_)
        gesehen[0] = len(plan.gesagt)

    lauf = ns.durchspielen(pfad, kern_stellung=kern, beim_takt=beim_takt, fragen=liste)
    minuten = lauf.sekunden_mit_daten / 60
    ungefragt = [a for a in lauf.gesagt if a.schluessel != "antwort"]
    n = len(ungefragt)
    vom_kern = sum(1 for a in ungefragt if a.schluessel.startswith("kern:"))
    zeilen = [
        f"# Protokoll {stamm}",
        "",
        f"{info.get('champion', '?')} gegen {info.get('gegner', '?')} ({'blau' if info.get('team') == 'ORDER' else 'rot'}), "
        f"**Spielmodus {lauf.spielmodus or '?'}** · {minuten:.1f} min mit Daten · nachgespielt mit `--kern {kern}` "
        f"(werkzeuge/protokoll.py)",
        "",
        f"**{n} ungefragte Ansagen** ({n / minuten * 30 if minuten else 0:.0f} je 30 min), davon {vom_kern} vom Kern, "
        f"{n - vom_kern} von alten Regeln · mitten im Satz abgebrochen: {len(lauf.abbrueche)}",
        "",
        "Je Ansage: Spielzeit · Modus · Ort · Leben · Gold, dann was gesagt wurde (Schluessel = Kern oder alte Regel), der "
        "Plan des Kerns und seine zwei naechstbesten Optionen. Ausserhalb der Kern-Modi (OBJECTIVE, KAMPF) hat der Kern "
        "keinen Plan.",
        "",
    ]
    if fragen:
        zeilen.insert(-1, f"Fragen aus dem Sprechtasten-Log eingespielt: {len(lauf.antworten)} - je Frage die Antwort "
                          f"des Kerns (Absicht, ohne Claude oder „braucht Claude“), markiert mit **Frage**.")
        zeilen.insert(-1, "")
    eintraege = [(lagen.get(id(a), {}).get("zeit", a.gesprochen or a.zeit), a) for a in lauf.gesagt]
    # Entscheidung 2 (27.09.): Kampf-Rufe des ungeeichten Modells - berechnet, nicht gesprochen
    eintraege += [(s["zeit"], s) for s in (lauf.kern.stumm_modell if lauf.kern is not None else [])]
    eintraege.sort(key=lambda x: x[0] if x[0] is not None else 0.0)
    stumm_n = sum(1 for _, a in eintraege if isinstance(a, dict) and "frage_ohne" not in a)
    if stumm_n:
        zeilen.insert(-1, f"Stumm (Modell nicht geeicht, Entscheidung 2): {stumm_n} Kampf-Rufe (ANNEHMEN, REIN, DREHEN) "
                          f"berechnet, nicht gesprochen - unten mit „stumm“ markiert.")
        zeilen.insert(-1, "")
    # Fragen, die Claude braucht, stehen offline ohne Antwort (nicht in `gesagt`) - hier mit ihrer Absicht
    for r in lauf.antworten:
        if not r.get("text"):
            eintraege.append((r["zeit"], {"frage_ohne": r}))
    eintraege.sort(key=lambda x: x[0] if x[0] is not None else 0.0)
    for t_, a in eintraege:
        if isinstance(a, dict) and "frage_ohne" in a:
            r = a["frage_ohne"]
            zeilen.append(f"### {ns.uhr(r['zeit'])} · Frage")
            zeilen.append(f"- **Frage** ({r.get('absicht') or '?'}, braucht Claude): „{r['frage']}“")
            zeilen.append("")
            continue
        if isinstance(a, dict):
            zeilen.append(f"### {ns.uhr(a['zeit'])} · {a.get('modus') or '–'} · stumm: Modell nicht geeicht")
            zeilen.append(f"- **Stumm** (`kern:{a['art']}`): „{a['text']}“")
            zeilen.append("")
            continue
        la = lagen.get(id(a), {})
        t = la.get("zeit", a.gesprochen or a.zeit)
        leben = f"{la['leben']} %" if la.get("leben") is not None else "Leben ?"
        gold = f"{la['gold']} Gold" if la.get("gold") is not None else "Gold ?"
        kopf = f"### {ns.uhr(t)} · {la.get('modus', '–')} · {la.get('ort', '?')} · {leben} · {gold}"
        zeilen.append(kopf + (" · GEFAHR" if la.get("gefahr") else ""))
        abgebrochen = " *(mitten im Satz abgebrochen)*" if a.ganz is False else ""
        if a.schluessel == "antwort":
            r = next((x for x in lauf.antworten if f"„{x['frage']}“ – {x['text']}" == a.text), {})
            zeilen.append(f"- **Frage** ({r.get('absicht') or '?'}, {r.get('quelle', '?')}, "
                          f"{1000 * r.get('dauer', 0):.0f} ms): {a.text}")
        else:
            zeilen.append(f"- **Gesagt** (`{a.schluessel}`): „{a.text}“{abgebrochen}")
        if la.get("plan"):
            art, ev, pt = la["plan"]
            zeilen.append(f"- **Plan:** {art} (EV {ev:+.0f}, p_tod {pt:.2f})")
        else:
            zeilen.append("- **Plan:** –")
        if la.get("danach"):
            zeilen.append(f"- **Danach:** {la['danach']}")
        if la.get("entscheidend") and a.schluessel.startswith("kern:"):
            zeilen.append(f"- **Entscheidend:** {la['entscheidend']}")
        if la.get("optionen"):
            zeilen.append("- **Naechstbeste:** " + " · ".join(f"{i}. {o}" for i, o in enumerate(la["optionen"], 1)))
        if la.get("zeitleiste"):
            zeilen.append("- **Zeitleiste:** " + " · ".join(la["zeitleiste"]))
        zeilen.append("")
    ZIEL.mkdir(parents=True, exist_ok=True)
    ziel = ZIEL / f"{stamm}.md"
    ziel.write_text("\n".join(zeilen), encoding="utf-8")
    return ziel


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    kern = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--kern=")), "neu")
    staemme = args or [sorted(aufzeichnung.ORDNER.glob("*.jsonl.gz"))[-1].name.removesuffix(".jsonl.gz")]
    for stamm in staemme:
        print(protokoll(stamm, kern, fragen="--fragen" in sys.argv))


if __name__ == "__main__":
    main()
