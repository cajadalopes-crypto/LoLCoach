"""Post-Game-Bericht aus einer Aufnahme.

Nur aus den API-Daten, Sekunde fuer Sekunde: was bei jedem eigenen Tod
vorher los war (Leben, ungenutztes Gold, wer beteiligt war), der
Lane-Vergleich zu festen Minuten, Objectives, Gold-Management, CS-Loecher
und was der Coach live gesagt haette. Auf Wunsch schreibt Claude die
Analyse eines Coaches dazu.

Ausgabe: Markdown neben der Aufnahme (`<aufnahme>_bericht.md`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import aufzeichnung, llm, regeln, sprechplan, stimme
from .ansicht import uhr
from .zustand import DRACHE_DE, Partie, gegenteam, partie as baue_partie, struktur

MINUTEN = (5, 10, 15, 20, 25, 30)
GOLD_GEHORTET = 1500      # so viel ungenutztes Gold ...
GOLD_DAUER = 60           # ... so lange lebendig mit sich herumgetragen = verschenkt
CS_LOCH = 120             # so lange lebendig ohne einen einzigen CS (vor 20:00)
CS_AB = 90                # vorher ist noch keine Welle da


@dataclass
class Tod:
    zeit: float
    taeter: str
    helfer: list[str]
    gank: bool
    leben_vorher: float | None     # Anteil 0..1, 10 s vor dem Tod
    gold: float | None             # ungenutztes Gold im Moment des Todes
    level_diff: int | None         # eigenes Level minus Lane-Gegner
    itemgold_diff: int | None


@dataclass
class Auswertung:
    partien: list[Partie]
    ende: Partie
    ergebnis: str
    tode: list[Tod] = field(default_factory=list)
    horten: list[tuple[float, float, float]] = field(default_factory=list)   # (von, bis, max Gold)
    cs_loecher: list[tuple[float, float]] = field(default_factory=list)
    ansagen: list[regeln.Ansage] = field(default_factory=list)


def _anteil_leben(p: Partie) -> float | None:
    m = p.werte.get("maxHealth")
    return p.werte.get("currentHealth", 0.0) / m if m else None


def werte_aus(pfad: str | Path, ich: str | None = None) -> Auswertung:
    partien = [p for p in (baue_partie(d, ich) for d in aufzeichnung.lies(pfad)) if p.ich]
    if not partien:
        raise ValueError("Aufnahme ohne eigenen Spieler (Replay? dann --ich setzen)")
    ende = partien[-1]
    spielende = next((e for e in ende.ereignisse if e.art == "GameEnd"), None)
    a = Auswertung(partien, ende, spielende.daten.get("Result", "?") if spielende else "abgebrochen")

    # Was live gesagt wurde, steht neben der Aufnahme; sonst nachspielen (ohne Minimap)
    gespeichert = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_ansagen.json")
    if gespeichert.exists():
        a.ansagen = [regeln.Ansage(**x) for x in json.loads(gespeichert.read_text(encoding="utf-8"))]
    else:
        werk, plan = regeln.Regelwerk(), sprechplan.Sprechplan(stimme.Stumm())
        for p in partien:
            plan.neu(werk.pruefe(p))
            plan.takt(p.zeit)
        a.ansagen = plan.gesagt

    j_gegner = ende.jungler(gegenteam(ende.mein_team))
    horten_seit = cs_seit = None
    letzter_cs = (0.0, -1)
    for i, p in enumerate(partien):
        vor = partien[i - 1] if i else None
        # --- Tode
        if vor and p.ich.tot and not vor.ich.tot:
            kill = next((e for e in reversed(p.ereignisse)
                         if e.art == "ChampionKill" and e.opfer is p.ich and e.zeit > vor.zeit - 3), None)
            zehn_vorher = next((q for q in reversed(partien[:i]) if q.zeit <= p.zeit - 10), None)
            g = vor.gegenueber()
            helfer = [h for h in (p.spieler_namens(n) for n in (kill.daten.get("Assisters", []) if kill else [])) if h]
            taeter = kill.taeter if kill else None
            roh_name = kill.daten.get("KillerName", "?") if kill else "?"
            turm = struktur(roh_name)
            a.tode.append(Tod(
                zeit=p.zeit,
                taeter=taeter.champion if taeter else (f"den Turm ({turm.lane} {turm.stufe})" if turm else roh_name),
                helfer=[h.champion for h in helfer],
                gank=bool(j_gegner and vor.ich.rolle != "JUNGLE"
                          and any(s is not None and s.name == j_gegner.name for s in [taeter, *helfer])),
                leben_vorher=_anteil_leben(zehn_vorher) if zehn_vorher else None,
                gold=vor.gold,
                level_diff=vor.ich.level - g.level if g else None,
                itemgold_diff=vor.ich.item_gold - g.item_gold if g else None,
            ))
        # --- Gold horten (lebendig, viel Gold, lange)
        if p.gold is not None and p.gold >= GOLD_GEHORTET and not p.ich.tot:
            horten_seit = horten_seit or (p.zeit, p.gold)
            horten_seit = (horten_seit[0], max(horten_seit[1], p.gold))
        elif horten_seit:
            if p.zeit - horten_seit[0] >= GOLD_DAUER:
                a.horten.append((horten_seit[0], p.zeit, horten_seit[1]))
            horten_seit = None
        # --- CS-Loecher (lebendig und kein CS, nur Lane-Phase)
        if p.ich.cs != letzter_cs[1] or p.ich.tot or p.zeit < CS_AB:
            if cs_seit and p.zeit - cs_seit >= CS_LOCH and p.zeit < 1200:
                a.cs_loecher.append((cs_seit, p.zeit))
            cs_seit, letzter_cs = (None if p.ich.tot else p.zeit), (p.zeit, p.ich.cs)
    return a


def _bei_minute(a: Auswertung, minute: int) -> Partie | None:
    return next((p for p in a.partien if p.zeit >= minute * 60), None)


def markdown(a: Auswertung) -> str:
    e, ich = a.ende, a.ende.ich
    g = e.gegenueber()
    dauer_min = e.zeit / 60
    team_kills = e.kills(e.mein_team) or 1
    bots = sum(1 for s in e.spieler if s.bot)
    art = f" (Bot-Partie: {bots} Bots)" if bots else ""
    z = [f"# {ich.champion} gegen {g.champion if g else '?'} - {a.ergebnis}{art}", ""]
    z.append(f"**{uhr(e.zeit)}** · {ich.kills}/{ich.tode}/{ich.assists} · "
             f"{ich.cs} CS ({ich.cs / dauer_min:.1f}/min) · "
             f"Killbeteiligung {(ich.kills + ich.assists) / team_kills:.0%} · Level {ich.level}")
    z.append("")

    if g:
        z += ["## Lane gegen " + g.champion, "",
              "| Minute | CS du | CS " + g.champion + " | Level | Itemgold-Vorsprung |", "|---|---|---|---|---|"]
        for m in MINUTEN:
            p = _bei_minute(a, m)
            if not p:
                break
            q = p.gegenueber()
            z.append(f"| {m} | {p.ich.cs} | {q.cs} | {p.ich.level}:{q.level} | {p.ich.item_gold - q.item_gold:+d} |")
        z.append("")

    z += [f"## Deine Tode ({len(a.tode)})", ""]
    if not a.tode:
        z.append("Keiner.")
    for t in a.tode:
        teile = [f"**{uhr(t.zeit)}** gegen {t.taeter}" + (f" + {', '.join(t.helfer)}" if t.helfer else "")]
        if t.gank:
            teile.append("Gank des Junglers")
        if t.leben_vorher is not None and t.leben_vorher < 0.35:
            teile.append(f"10 s vorher nur {t.leben_vorher:.0%} Leben")
        if t.gold and t.gold >= 1000:
            teile.append(f"mit {t.gold:.0f} ungenutztem Gold")
        if t.level_diff:
            teile.append(f"Level {t.level_diff:+d} zum Lane-Gegner")
        if t.itemgold_diff and abs(t.itemgold_diff) >= 500:
            teile.append(f"Items {t.itemgold_diff:+d} Gold")
        z.append("- " + " · ".join(teile))
    z.append("")

    z += ["## Objectives", ""]
    for team, wer in ((e.mein_team, "Ihr"), (gegenteam(e.mein_team), "Gegner")):
        drachen = ", ".join(DRACHE_DE.get(d, d) for d in e.drachen(team)) or "keine"
        tuerme = sum(1 for x in e.kills_von("TurretKilled") if x.team == team)
        weitere = [f"{sum(1 for x in e.kills_von(art) if x.team == team)}× {name}"
                   for art, name in (("HordeKill", "Larve"), ("HeraldKill", "Herold"), ("BaronKill", "Baron"))]
        z.append(f"- **{wer}:** Drachen {drachen} · {tuerme} Türme · " + " · ".join(weitere))
    z.append("")

    if a.horten or a.cs_loecher:
        z += ["## Verschenkte Stärke", ""]
        for von, bis, gold in a.horten:
            z.append(f"- {uhr(von)}-{uhr(bis)}: bis zu {gold:.0f} Gold ungenutzt mit dir herumgetragen")
        for von, bis in a.cs_loecher:
            z.append(f"- {uhr(von)}-{uhr(bis)}: {bis - von:.0f} s am Leben, aber kein einziger CS")
        z.append("")

    z += [f"## Was der Coach gesagt hat ({len(a.ansagen)})", ""]
    z += [f"- {uhr(x.gesprochen)} {x.text}" for x in a.ansagen]
    z.append("")
    return "\n".join(z)


SYSTEM = (
    "Du bist ein Challenger-Coach fuer League of Legends und wertest eine Partie deines Schuelers aus "
    "(Ziel: Diamond+). Du bekommst einen Bericht aus den Spieldaten. Schreib auf Deutsch, direkt, wie "
    "im Voice-Chat nach dem Spiel. Nenne die DREI wichtigsten Lektionen, jede mit: was passiert ist "
    "(mit Spielzeit), warum es ein Fehler oder eine gute Entscheidung war, und was er naechstes Mal "
    "konkret tut. Nur was die Daten stuetzen - keine erfundenen Details. Hoechstens 250 Woerter. "
    "Wenn die Ueberschrift 'Bot-Partie' sagt, sag kurz, was davon auf echte Gegner uebertragbar ist."
)


def schreibe(pfad: str | Path, ich: str | None = None, mit_llm: bool = True) -> Path:
    a = werte_aus(pfad, ich)
    text = markdown(a)
    if mit_llm:
        try:
            analyse = llm.frage(text, system=SYSTEM)
            text = text.replace("## Was der Coach gesagt hat", "## Analyse (Claude)\n\n" + analyse.strip()
                                + "\n\n## Was der Coach gesagt hat", 1)
        except llm.LLMFehler as f:
            text += f"\n_Keine Claude-Analyse: {f}_\n"
    ziel = Path(pfad).with_name(Path(pfad).name.removesuffix(".jsonl.gz") + "_bericht.md")
    ziel.write_text(text, encoding="utf-8")
    return ziel
