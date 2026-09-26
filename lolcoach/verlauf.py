"""Spielverstaendnis: die ganze Partie als Zeitleiste mit Schluesselmomenten.

Carlos: "Ich will einen Coach, der das Spiel genauestens versteht - damit wir nach
dem Spiel ein Review machen koennen und du mir sagst, wo ich was falsch gemacht
habe. Kein denkloser AI-Slop, sondern was mich wirklich voranbringt."

Hier wird nichts geraten: alles kommt aus der Aufnahme (Live-API je Sekunde),
dem Lagebild (Minimap-Positionen, Mitspieler-Leiste, Chat, Zauber-Timer) und den
Ansagen. Jeder Moment traegt seine Fakten mit - die Analyse (review.py) darf nur
behaupten, was hier steht.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import ansicht, aufzeichnung, lage, minimap, regeln
from .ansicht import uhr
from .zustand import DRACHE_DE, Partie, gegenteam, partie as baue_partie, struktur

KAMPF_LUECKE = 12.0      # Kills mit hoechstens so viel Abstand gehoeren zu einem Kampf
SCHWUNG_FENSTER = 120.0  # Sekunden
SCHWUNG_AB = 1500        # Itemgold-Unterschied, der sich im Fenster bewegt


@dataclass
class Moment:
    art: str                 # tod, kampf, objective, schwung, horten, cs_loch, lane
    von: float
    bis: float
    titel: str
    fakten: list[str] = field(default_factory=list)
    gewicht: int = 1         # grobe Wichtigkeit 1..5 (fuer Reihenfolge und Auswahl)
    ort: tuple[float, float] | None = None   # Kartenposition des Geschehens, wenn bekannt


@dataclass
class Sekunde:
    """Was in dieser Sekunde galt - Grundlage fuer Wiedergabe und Gespraech."""
    zeit: float
    gold: float | None
    leben: float | None           # eigenes Leben 0..1
    itemgold_diff: int            # Team gegen Team
    kills: tuple[int, int]
    positionen: dict[str, tuple[float, float, float, bool]]  # Name -> (x, y, Alter s, sichtbar)
    tot: list[str]
    wellen: dict[str, str] = field(default_factory=dict)   # Lane -> Stand in Worten (aus Sicht des Spielers)


@dataclass
class Verlauf:
    datei: str
    ich: str
    champion: str
    gegner: str | None
    ergebnis: str
    dauer: float
    team: str
    spieler: list[dict]
    momente: list[Moment]
    sekunden: list[Sekunde]
    ansagen: list[dict]
    notizen: list[str]
    spielakte: str | None
    ereignisse: list[tuple[float, str]] = field(default_factory=list)   # (Spielzeit, Satz) aus der API


def _abstand(a, b) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def baue(pfad: str | Path, ich: str | None = None) -> Verlauf:
    pfad = Path(pfad)
    sicht = lage.sicht_fuer(pfad)
    lb = lage.Lagebild()
    partien: list[Partie] = []
    sekunden: list[Sekunde] = []
    positionen_je_zeit: list[dict] = []
    for w, d in aufzeichnung.lies_mit_zeit(pfad):
        p = baue_partie(d, ich)
        if not p.ich:
            continue
        if sicht:
            for wb, s in sicht.zwischen(w, lage.champions(p)):
                lb.neu(p.zeit - (w - wb), s, p)
            lb.ereignisse(lambda wb: p.zeit - (w - wb), sicht.ereignisse(), p)
        pos = {}
        for s in p.spieler:
            if (g := lb.gesehen(s)) and not s.tot:
                pos[s.name] = (round(g[1], 4), round(g[2], 4), round(p.zeit - g[0], 1), lb.sichtbar(s))
        m = p.werte.get("maxHealth")
        wir, die = p.mein_team, gegenteam(p.mein_team)
        wellen = {l: z.worte(wir) for l in ("Top", "Mid", "Bot") if (z := lb.welle(l, p.zeit))}
        sekunden.append(Sekunde(p.zeit, p.gold, round(p.werte.get("currentHealth", 0) / m, 2) if m else None,
                                p.item_gold(wir) - p.item_gold(die), (p.kills(wir), p.kills(die)), pos,
                                [s.name for s in p.spieler if s.tot], wellen))
        partien.append(p)
    if not partien:
        raise ValueError(f"{pfad.name}: keine Partie mit eigenem Spieler")
    ende = partien[-1]
    spielende = next((e for e in ende.ereignisse if e.art == "GameEnd"), None)
    g = ende.gegenueber()

    momente = []
    momente += _tode(partien, sekunden, lb)
    momente += _kaempfe(partien, sekunden)
    momente += _objectives(partien, sekunden)
    momente += _schwuenge(sekunden)
    momente += _lane(partien)
    momente += _verschenkt(partien)
    momente.sort(key=lambda m: m.von)

    stamm = pfad.name.removesuffix(".jsonl.gz")
    ansagen_datei = pfad.with_name(stamm + "_ansagen.json")
    notiz_datei = pfad.with_name(stamm + "_notizen.md")
    akte_datei = pfad.with_name(stamm + "_spielakte.md")
    return Verlauf(
        datei=pfad.name, ich=ende.ich.name, champion=ende.ich.champion, gegner=g.champion if g else None,
        ergebnis=spielende.daten.get("Result", "?") if spielende else "abgebrochen", dauer=ende.zeit,
        team=ende.mein_team,
        spieler=[{"name": s.name, "champion": s.champion, "id": s.champion_id, "team": s.team, "rolle": s.rolle,
                  "freund": s.team == ende.mein_team, "ich": s is ende.ich, "bot": s.bot,
                  "kda": f"{s.kills}/{s.tode}/{s.assists}", "cs": s.cs, "level": s.level} for s in ende.spieler],
        momente=momente, sekunden=sekunden,
        ansagen=json.loads(ansagen_datei.read_text(encoding="utf-8")) if ansagen_datei.exists() else [],
        notizen=notiz_datei.read_text(encoding="utf-8").splitlines() if notiz_datei.exists() else [],
        spielakte=akte_datei.read_text(encoding="utf-8") if akte_datei.exists() else None,
        ereignisse=[(e.zeit, satz.split("  ", 1)[-1]) for e in ende.ereignisse
                    if (satz := ansicht.ereignis(ende, e))],
    )


def _sekunde(sekunden: list[Sekunde], zeit: float) -> Sekunde | None:
    kandidaten = [s for s in sekunden if s.zeit <= zeit]
    return kandidaten[-1] if kandidaten else None


def _lage_worte(sek: Sekunde | None, partie: Partie, bezug: tuple[float, float] | None) -> list[str]:
    """Wo standen alle, aus Sicht des Spielers - nur Gesehenes."""
    if not sek:
        return []
    zeilen = []
    fehlend = []
    for s in partie.gegner():
        if s.name in sek.tot:
            continue
        pos = sek.positionen.get(s.name)
        if not pos:
            fehlend.append(f"{s.champion} (nie gesehen)")
            continue
        x, y, alter, sichtbar = pos
        ort = minimap.ort(x, y, partie.mein_team)
        if sichtbar:
            weite = f", {_abstand((x, y), bezug):.2f} Kartenbreiten von dir" if bezug else ""
            zeilen.append(f"{s.champion} sichtbar {ort}{weite}")
        elif alter > 8:
            fehlend.append(f"{s.champion} (zuletzt vor {int(alter)} s {ort})")
        else:
            zeilen.append(f"{s.champion} vor {int(alter)} s {ort}")
    if fehlend:
        zeilen.append("auf der Karte nicht zu sehen: " + ", ".join(fehlend))
    nahe_freunde = []
    for s in partie.team(partie.mein_team):
        if s is partie.ich or s.name in sek.tot:
            continue
        pos = sek.positionen.get(s.name)
        if pos and bezug and pos[3] and _abstand(pos[:2], bezug) < 0.18:
            nahe_freunde.append(s.champion)
    if bezug:
        zeilen.append("Mitspieler in deiner Naehe: " + (", ".join(nahe_freunde) if nahe_freunde else "keiner"))
    return zeilen


def _eigene_position(sek: Sekunde | None, partie: Partie) -> tuple[float, float] | None:
    if not sek:
        return None
    pos = sek.positionen.get(partie.ich.name)
    return (pos[0], pos[1]) if pos and pos[2] < 5 else None


def _tode(partien: list[Partie], sekunden: list[Sekunde], lb) -> list[Moment]:
    aus = []
    for i in range(1, len(partien)):
        p, v = partien[i], partien[i - 1]
        if not (p.ich.tot and not v.ich.tot):
            continue
        kill = next((e for e in reversed(p.ereignisse)
                     if e.art == "ChampionKill" and e.opfer is p.ich and e.zeit > v.zeit - 3), None)
        fakten = []
        taeter = kill.taeter if kill else None
        roh = kill.daten.get("KillerName", "?") if kill else "?"
        helfer = [h.champion for h in (p.spieler_namens(n) for n in (kill.daten.get("Assisters", []) if kill else [])) if h]
        if taeter:
            wer = taeter.champion
        elif st := struktur(roh):
            wer = f"den Turm ({st.lane} {st.stufe})"
        else:
            wer = roh
        fakten.append(f"Getoetet von {wer}" + (f", beteiligt: {', '.join(helfer)}" if helfer else " (allein)"))
        j = p.jungler(gegenteam(p.mein_team))
        if j and p.ich.rolle != "JUNGLE" and (taeter is j or j.champion in helfer):
            fakten.append(f"Der gegnerische Jungler {j.champion} war beteiligt (Gank)")
        # Vorgeschichte: 15 s und 5 s vorher
        for vorher in (15, 5):
            sek = _sekunde(sekunden, p.zeit - vorher)
            if sek:
                teile = [f"{vorher} s vorher:"]
                if sek.leben is not None:
                    teile.append(f"dein Leben {int(sek.leben * 100)} %")
                if sek.gold is not None:
                    teile.append(f"{int(sek.gold)} Gold unausgegeben")
                ort = _eigene_position(sek, p)
                if ort:
                    teile.append("du warst " + minimap.ort(*ort, p.mein_team))
                lane = {"TOP": "Top", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Bot"}.get(p.ich.rolle)
                if lane and sek.wellen.get(lane):
                    teile.append(f"deine Lane-Welle: {sek.wellen[lane]}")
                fakten.append(" ".join(teile))
        sek5 = _sekunde(sekunden, p.zeit - 5)
        fakten += _lage_worte(sek5, p, _eigene_position(sek5, p))
        g = v.gegenueber()
        if taeter:
            fakten.append(f"Level: du {v.ich.level}, {taeter.champion} {taeter.level}; "
                          f"Itemgold: du {v.ich.item_gold}, {taeter.champion} {taeter.item_gold}")
        if timer := [t for t in lb.zauber.timer.values() if t.seit <= p.zeit <= t.zurueck + 1 and
                     (taeter and t.name == taeter.name)]:
            fakten.append("Bekannte Zauber-Timer des Taeters: " + ", ".join(f"{t.zauber} weg" for t in timer))
        # Folgen: was verlor dein Team in der Zeit, in der du tot warst?
        folgen = [e for e in p.ereignisse if p.zeit <= e.zeit <= p.zeit + max(20, p.ich.respawn) + 5
                  and e.team == gegenteam(p.mein_team) and e.art in ("TurretKilled", "DragonKill", "BaronKill",
                                                                      "HeraldKill", "HordeKill", "InhibKilled")]
        spaeter = partien[min(len(partien) - 1, i + int(max(20, p.ich.respawn)) + 5)]
        folgen = [e for e in spaeter.ereignisse if p.zeit <= e.zeit <= spaeter.zeit
                  and e.team == gegenteam(p.mein_team) and e.art in ("TurretKilled", "DragonKill", "BaronKill",
                                                                      "HeraldKill", "HordeKill", "InhibKilled")]
        if folgen:
            fakten.append("Waehrend du tot warst, holte der Gegner: " + ", ".join(_objective_name(e) for e in folgen))
        fakten.append(f"Todesdauer {int(p.ich.respawn)} s")
        aus.append(Moment("tod", p.zeit - 15, p.zeit, f"Tod gegen {wer}", fakten,
                          gewicht=3 + (1 if folgen else 0) + (1 if p.zeit > 900 else 0),
                          ort=_eigene_position(sek5, p)))
    return aus


def _objective_name(e) -> str:
    d = e.daten
    if e.art == "DragonKill":
        return DRACHE_DE.get(d.get("DragonType", ""), "?") + "-Drache"
    if e.art in ("TurretKilled", "InhibKilled"):
        st = struktur(d.get(e.art, ""))
        return ("Turm " if e.art == "TurretKilled" else "Inhibitor ") + (f"{st.lane} {st.stufe}" if st else "?")
    return {"BaronKill": "Baron", "HeraldKill": "Herold", "HordeKill": "Larve"}.get(e.art, e.art)


def _kaempfe(partien: list[Partie], sekunden: list[Sekunde]) -> list[Moment]:
    ende = partien[-1]
    kills = [e for e in ende.ereignisse if e.art == "ChampionKill"]
    gruppen, aktuell = [], []
    for e in kills:
        if aktuell and e.zeit - aktuell[-1].zeit > KAMPF_LUECKE:
            gruppen.append(aktuell)
            aktuell = []
        aktuell.append(e)
    if aktuell:
        gruppen.append(aktuell)
    aus = []
    for gr in gruppen:
        if len(gr) < 2:
            continue  # Einzelkills stecken in den Toden bzw. sind klein
        von, bis = gr[0].zeit, gr[-1].zeit
        p = next((q for q in partien if q.zeit >= von - 2), ende)
        wir, die = p.mein_team, gegenteam(p.mein_team)
        k_wir = sum(1 for e in gr if e.team == wir)
        k_die = len(gr) - k_wir
        beteiligt_ich = any(e.taeter is not None and e.taeter.name == p.ich.name or
                            (e.opfer is not None and e.opfer.name == p.ich.name) or
                            p.ich.name in [n for n in e.daten.get("Assisters", [])] or
                            any(n in p.ich.namen for n in e.daten.get("Assisters", [])) for e in gr)
        sek = _sekunde(sekunden, von - 3)
        lebend = (5 - sum(1 for n in (sek.tot if sek else []) if any(s.name == n and s.team == wir for s in p.spieler)),
                  5 - sum(1 for n in (sek.tot if sek else []) if any(s.name == n and s.team == die for s in p.spieler)))
        fakten = [f"Kills: ihr {k_wir}, Gegner {k_die}",
                  f"Vor dem Kampf lebten: ihr {lebend[0]}, Gegner {lebend[1]}",
                  "Ablauf: " + "; ".join(f"{uhr(e.zeit)} {_wer(e)}"
                                          f" -> {(e.opfer.champion if e.opfer else e.daten.get('VictimName', '?'))}" for e in gr)]
        ort_opfer = None
        opfer_pos = [sek.positionen.get(e.opfer.name) for e in gr if e.opfer and sek and sek.positionen.get(e.opfer.name)]
        if opfer_pos:
            ort_opfer = (sum(q[0] for q in opfer_pos) / len(opfer_pos), sum(q[1] for q in opfer_pos) / len(opfer_pos))
            fakten.append("Ort: " + minimap.ort(*ort_opfer, wir))
        ich_pos = _eigene_position(sek, p)
        if not beteiligt_ich:
            fakten.append("Du warst nicht beteiligt" + (f" - du warst {minimap.ort(*ich_pos, wir)}" if ich_pos else ""))
        danach = [e for e in ende.ereignisse if bis < e.zeit <= bis + 60 and e.art in
                  ("TurretKilled", "DragonKill", "BaronKill", "HeraldKill", "HordeKill", "InhibKilled")]
        if danach:
            fakten.append("In der Minute danach: " + ", ".join(
                f"{'ihr' if e.team == wir else 'Gegner'} {_objective_name(e)}" for e in danach))
        titel = f"Kampf {k_wir}:{k_die}" + (" (ohne dich)" if not beteiligt_ich else "")
        aus.append(Moment("kampf", von - 10, bis + 5, titel, fakten,
                          gewicht=min(5, 2 + abs(k_wir - k_die) + (1 if not beteiligt_ich and k_die > k_wir else 0)),
                          ort=ort_opfer))
    return aus


def _wer(e) -> str:
    if e.taeter:
        return e.taeter.champion
    roh = e.daten.get("KillerName", "?")
    if st := struktur(roh):
        return f"Turm ({st.lane} {st.stufe})"
    return "Vasallen" if roh.startswith("Minion_") else roh


def _objectives(partien: list[Partie], sekunden: list[Sekunde]) -> list[Moment]:
    ende = partien[-1]
    aus = []
    for e in ende.ereignisse:
        if e.art not in ("DragonKill", "BaronKill", "HeraldKill", "InhibKilled") and \
                not (e.art == "TurretKilled"):
            continue
        p = next((q for q in partien if q.zeit >= e.zeit - 1), ende)
        wir = p.mein_team
        sek = _sekunde(sekunden, e.zeit - 2)
        ich_pos = _eigene_position(sek, p)
        fakten = [f"{'Ihr' if e.team == wir else 'Der Gegner'} holt {_objective_name(e)}"]
        helfer = [h.champion for h in (p.spieler_namens(n) for n in e.daten.get("Assisters", [])) if h]
        fakten.append("Letzter Treffer: " + _wer(e) + (f", beteiligt: {', '.join(helfer)}" if helfer else ", keine Helfer gemeldet"))
        if ich_pos:
            fakten.append(f"Du warst {minimap.ort(*ich_pos, wir)}")
        if sek:
            tot_wir = [s.champion for s in p.team(wir) if s.name in sek.tot]
            tot_die = [s.champion for s in p.gegner() if s.name in sek.tot]
            fakten.append(f"Tot in dem Moment: ihr {', '.join(tot_wir) or 'keiner'}; Gegner {', '.join(tot_die) or 'keiner'}")
        gross = e.art in ("DragonKill", "BaronKill", "HeraldKill", "InhibKilled")
        gewicht = (3 if e.art == "BaronKill" else 2 if gross else 1) + (1 if e.team != wir else 0)
        aus.append(Moment("objective", e.zeit - 20, e.zeit, fakten[0], fakten, gewicht=gewicht))
    return aus


def _schwuenge(sekunden: list[Sekunde]) -> list[Moment]:
    aus = []
    i = 0
    while i < len(sekunden):
        a = sekunden[i]
        j = next((k for k in range(i + 1, len(sekunden)) if sekunden[k].zeit - a.zeit >= SCHWUNG_FENSTER), None)
        if j is None:
            break
        b = sekunden[j]
        delta = b.itemgold_diff - a.itemgold_diff
        if abs(delta) >= SCHWUNG_AB:
            aus.append(Moment("schwung", a.zeit, b.zeit,
                              f"Gold-Schwung {delta:+d} fuer {'euch' if delta > 0 else 'den Gegner'}",
                              [f"Itemgold-Vorsprung von {a.itemgold_diff:+d} auf {b.itemgold_diff:+d} "
                               f"(Wert gekaufter Items - Gold zaehlt erst nach dem Kauf)",
                               f"Kills in der Zeit: {b.kills[0] - a.kills[0]} zu {b.kills[1] - a.kills[1]}"],
                              gewicht=min(5, 2 + abs(delta) // 1500)))
            i = j
        else:
            i += 10
    return aus


def _lane(partien: list[Partie]) -> list[Moment]:
    aus = []
    for minute in (5, 10, 14):
        p = next((q for q in partien if q.zeit >= minute * 60), None)
        if not p or not (g := p.gegenueber()):
            continue
        aus.append(Moment("lane", p.zeit, p.zeit, f"Lane bei {minute}:00", [
            f"CS: du {p.ich.cs}, {g.champion} {g.cs}",
            f"Level: du {p.ich.level}, {g.champion} {g.level}",
            f"Itemgold: du {p.ich.item_gold}, {g.champion} {g.item_gold}",
            f"KDA: du {p.ich.kills}/{p.ich.tode}/{p.ich.assists}, {g.champion} {g.kills}/{g.tode}/{g.assists}"],
            gewicht=1))
    return aus


def _verschenkt(partien: list[Partie]) -> list[Moment]:
    """Gold horten (lebendig, >= 1500, >= 60 s)."""
    aus, seit, hoch = [], None, 0.0
    for p in partien:
        if p.gold is not None and p.gold >= 1500 and not p.ich.tot:
            seit = seit or p.zeit
            hoch = max(hoch, p.gold)
        else:
            if seit and p.zeit - seit >= 60:
                aus.append(Moment("horten", seit, p.zeit, f"{int(hoch)} Gold mit dir herumgetragen",
                                  [f"{uhr(seit)} bis {uhr(p.zeit)} lebendig mit bis zu {int(hoch)} Gold, ohne zu kaufen"],
                                  gewicht=2 + (1 if hoch >= 3000 else 0)))
            seit, hoch = None, 0.0
    return aus


# --- fuer Analyse und Oberflaeche ------------------------------------------------

def als_text(v: Verlauf, hoechstens: int = 60) -> str:
    """Kompakte Zeitleiste fuer Claude: Kopf + die wichtigsten Momente mit Fakten."""
    kopf = (f"Partie: {v.champion} gegen {v.gegner or '?'}, Ergebnis {v.ergebnis}, Dauer {uhr(v.dauer)}. "
            + ("Bot-Partie. " if any(s['bot'] for s in v.spieler if not s['freund']) else "")
            + "Team: " + ", ".join(f"{s['champion']} ({s['rolle']}) {s['kda']}" for s in v.spieler if s['freund'])
            + ". Gegner: " + ", ".join(f"{s['champion']} ({s['rolle']}) {s['kda']}" for s in v.spieler if not s['freund']))
    auswahl = sorted(v.momente, key=lambda m: (-m.gewicht, m.von))[:hoechstens]
    auswahl.sort(key=lambda m: m.von)
    zeilen = [kopf, ""]
    for m in auswahl:
        zeilen.append(f"[{uhr(m.von)}-{uhr(m.bis)}] {m.art.upper()}: {m.titel}")
        zeilen += [f"   - {f}" for f in m.fakten]
    if v.notizen:
        zeilen += ["", "Notizen des Spielers waehrend der Partie:"] + v.notizen
    return "\n".join(zeilen)


def speichern(v: Verlauf, ziel: Path) -> None:
    daten = asdict(v)
    ziel.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
