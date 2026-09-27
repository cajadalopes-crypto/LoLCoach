"""Fragen beantworten - knapp, wie ein Coach im Voice-Chat.

Zwei Stufen:
  1. Sofort aus dem Zustand (unter 10 ms): wo ist X, wann kommt Drache, wer
     ist tot, wie steht's, CS, Gold, Items, Level, Beschwoererzauber.
  2. Alles andere: Claude mit einer kompakten Lage (ein paar Sekunden).

Champion-Namen kommen aus der Spracherkennung oft schief ("Schen" statt
"Shen"); sie werden unscharf gegen die zehn Champions der Partie abgeglichen.
"""
from __future__ import annotations

import difflib
import re

from . import ddragon, llm, minimap, wissen
from .zustand import ROLLE_DE, Partie, Spieler, gegenteam

OBJEKTIVE = {"drache": "drache", "drachen": "drache", "dragon": "drache", "baron": "baron", "nashor": "baron",
             "herold": "herold", "herald": "herold", "larven": "larven", "larve": "larven", "grubs": "larven",
             "voidgrubs": "larven", "ältester": "drache", "elder": "drache"}
ROLLEN_WORTE = {"jungler": "JUNGLE", "jungle": "JUNGLE", "dschungel": "JUNGLE", "top": "TOP", "toplaner": "TOP",
                "mid": "MIDDLE", "midlaner": "MIDDLE", "adc": "BOTTOM", "bot": "BOTTOM", "support": "UTILITY",
                "supporter": "UTILITY", "supp": "UTILITY"}
ENTSCHEIDUNG = {"soll", "sollte", "sollen", "sollten", "lieber", "besser", "warum", "wieso", "weshalb",
                "kaufen", "bauen", "kauf", "mache", "machen", "tun", "spielen", "gehen", "empfiehlst"}
# "Kann ich ihn killen?", "Soll ich reingehen?": die Denkkette hat das Urteil schon - sofort statt ~3 s Claude
KAMPF_WORTE = {"killen", "töten", "toeten", "umhauen", "reingehen", "reingehn", "kämpfen", "kaempfen", "fighten",
               "traden", "tradeen", "trade", "allin", "diven", "dive", "kill",
               # "Bin ich staerker als Gragas?", "Gewinne ich den 1 gegen 1?" - dasselbe Urteil
               "stärker", "staerker", "schwächer", "schwaecher", "gewinne", "gewinnen", "1v1", "duell"}
ZAUBER_DE = {"SummonerFlash": "Flash", "SummonerTeleport": "Teleport", "SummonerDot": "Zünden",
             "SummonerHeal": "Heilen", "SummonerExhaust": "Erschöpfen", "SummonerBarrier": "Barriere",
             "SummonerSmite": "Zerschmettern", "SummonerHaste": "Geist", "SummonerBoost": "Reinigen"}


def _dauer(sek: float) -> str:
    s = int(round(sek))
    if s < 90:
        return f"{s} Sekunden"
    m, r = divmod(s, 60)
    minuten = "1 Minute" if m == 1 else f"{m} Minuten"      # "vor 1 Minuten 30" (Probe 26.09. nachts)
    return minuten if r < 10 else f"{minuten} {r}"


def _woerter(text: str) -> list[str]:
    return re.findall(r"[a-zäöüß0-9']+", text.lower())


def _champion_im_text(woerter: list[str], p: Partie) -> Spieler | None:
    namen = {}
    for s in p.spieler:
        for n in {s.champion.lower(), s.champion_id.lower()}:
            namen[n.replace(" ", "").replace("'", "")] = s
    kandidaten = woerter + [a + b for a, b in zip(woerter, woerter[1:])]  # "lee sin" -> "leesin"
    for w in kandidaten:
        w = w.replace("'", "")
        treffer = difflib.get_close_matches(w, list(namen), n=1, cutoff=0.75)
        if not treffer and w.startswith("sch"):
            treffer = difflib.get_close_matches("sh" + w[3:], list(namen), n=1, cutoff=0.75)  # "Schen" -> Shen
        if treffer:
            return namen[treffer[0]]
    return None


def _ziel(woerter: list[str], p: Partie) -> Spieler | None:
    if s := _champion_im_text(woerter, p):
        return s
    eigen = any(w in ("unser", "unserem", "unseren", "mein", "meinem", "meinen") for w in woerter)
    team = p.mein_team if eigen else gegenteam(p.mein_team)
    for w in woerter:
        if rolle := ROLLEN_WORTE.get(w):
            return next((s for s in p.team(team) if s.rolle == rolle), None)
    if any(w in ("gegner", "lanegegner", "gegenüber") for w in woerter):
        return p.gegenueber()
    return None


def _wo(s: Spieler, p: Partie, lagebild) -> str:
    if s.tot:
        return f"{s.champion} ist tot, noch {_dauer(s.respawn)}."
    if lagebild is None or not lagebild.aktiv:
        return "Ich sehe die Minimap gerade nicht."
    g = lagebild.gesehen(s)
    if not g and s.rolle == "JUNGLE":
        return _jungler_ungesehen(s, p, lagebild)
    if not g:
        return f"{s.champion} habe ich noch nicht gesehen."
    ort = minimap.ort(g[1], g[2], p.mein_team)
    zusatz = ""
    try:   # dazu gerechnet: wie schnell er bei dir sein kann, und beim Jungler die wahrscheinliche Seite
        from . import bewertung
        b = bewertung.bewerte(p, lagebild)
        gl = next((x for x in b.gegner if x.s.name == s.name), None) if b else None
        if gl and gl.ankunft is not None and gl.ankunft >= 2 and not gl.unbekannt:
            zusatz = f" Frühestens in {_dauer(gl.ankunft)} bei dir."
        elif gl and gl.ankunft is not None and gl.ankunft < 2 and not lagebild.sichtbar(s):
            zusatz = f" {s.champion} könnte schon bei dir sein."
        jt = getattr(lagebild, "jungle", None)
        if s.rolle == "JUNGLE" and jt is not None and not lagebild.sichtbar(s):
            w = jt.wahrscheinlich(p.zeit)
            seite, anteil = max(w.items(), key=lambda x: x[1])
            if anteil >= 0.6:
                zusatz += f" Wahrscheinlich {seite}, {int(anteil * 100)} Prozent."
    except Exception:
        pass
    if lagebild.sichtbar(s):
        return f"{s.champion} ist {ort}, gerade zu sehen.{zusatz}"
    return f"{s.champion} war vor {_dauer(p.zeit - g[0])} {ort}.{zusatz}"


def _jungler_ungesehen(s: Spieler, p: Partie, lagebild) -> str:
    """Nie gesehen heisst nicht "keine Ahnung": aus Spielzeit, Clear-Zeiten 2026 und Startseite folgt, was er
    gerade tun kann (Live 26.09., 3:29: "Wo ist Tryndamere jetzt wohl?" - "habe ich noch nicht gesehen")."""
    from .jungle import DREI_CAMPS, FULL_CLEAR, anders
    jt = getattr(lagebild, "jungle", None)
    start = jt.start if jt is not None else None
    grund = f" Er hat {start} angefangen ({jt.start_grund})." if start else ""
    t = p.zeit
    if t < DREI_CAMPS[0]:
        return f"{s.champion} habe ich noch nicht gesehen - er räumt seine ersten Camps.{grund}"
    if t < FULL_CLEAR[0]:
        gank = f" {anders(start)}" if start else ""
        return (f"{s.champion} habe ich noch nicht gesehen. Nach drei Camps kann er jetzt schon ganken, mit Level 3"
                f"{gank} - oder er räumt weiter bis zum Full Clear gegen Minute drei.{grund}")
    if t < FULL_CLEAR[1] + 30:
        seite = f", wahrscheinlich {anders(start)}" if start else ""
        return (f"{s.champion} habe ich noch nicht gesehen. Sein Full Clear ist etwa jetzt fertig: als Nächstes "
                f"Scuttle oder der erste Gank{seite}. Lass deine Welle nicht über die Mitte laufen, bis er "
                f"auftaucht.{grund}")
    w = jt.wahrscheinlich(t) if jt is not None else {}
    lage = ""
    if w:
        seite, anteil = max(w.items(), key=lambda x: x[1])
        lage = f" Am ehesten {seite}, {int(anteil * 100)} Prozent."
    return (f"{s.champion} habe ich seit Spielbeginn nie gesehen - der Clear ist durch, er kann überall sein."
            f"{lage} Geh nicht tief, bis er sich zeigt.")


def _timer(schl: str, p: Partie) -> str:
    n = p.naechster_spawn(schl)
    name = "Der Älteste" if schl == "drache" and p.seele() else wissen.objektive()[schl]["name"]
    if n is None:
        return f"{name} kommt nicht mehr."
    if n <= p.zeit:
        return f"{name} lebt."
    return f"{name} in {_dauer(n - p.zeit)}."


def _items(s: Spieler) -> str:
    it = ddragon.items()
    fertig = [it[i]["name"] for i in s.items if i in it and not it[i].get("into") and it[i]["gold"]["total"] >= 2200]
    if not fertig:
        return f"{s.champion} hat noch kein fertiges Item."
    return f"{s.champion} hat {', '.join(fertig)}."


def _kampf(w: list[str], roh: str, p: Partie, lagebild) -> str | None:
    """'Kann ich ihn killen?' / 'Soll ich reingehen?' gegen den Lane-Gegner: das Kampf-Urteil der Denkkette mit
    seinen Gruenden (Leben, Combo-Rechnung, Flash, Jungler, Turm ...), in unter 10 ms. Ein anderer Champion als
    der Lane-Gegner und jedes "warum" gehen an Claude."""
    menge = set(w)
    if not (menge & KAMPF_WORTE or re.search(r"\ball[\s-]?in\b", roh)) or menge & {"warum", "wieso", "weshalb"}:
        return None
    # "Wo soll ich reingehen? Auf welcher Lane?" (Live 21:21) fragt nach dem Ort, nicht nach dem Lane-Gegner;
    # "Gewinnen wir das Spiel?" nach dem Team
    if menge & {"wo", "wohin", "welche", "welcher", "welchem", "lane", "wen", "wir", "uns", "spiel", "game", "team",
                "teamfight"}:
        return None
    if lagebild is None or not getattr(lagebild, "aktiv", False):
        return None
    ziel = _champion_im_text(w, p)
    from . import bewertung, denker
    b = bewertung.bewerte(p, lagebild)
    if b is None or b.lane is None or (ziel is not None and ziel.name != b.lane.s.name):
        return None
    if b.lane.s.tot:
        return f"{b.lane.champion} ist tot, noch {_dauer(b.lane.s.respawn)}."
    u = denker.urteil(b)
    return denker.fenster_satz(b, u) if u is not None else None


BACK_WORTE = {"back", "backen", "backe", "recall", "recallen", "recalle", "basis", "base", "heim"}
FRAGE_ENTSCHEIDUNG = {"soll", "sollte", "kann", "können", "koennen", "lohnt", "machen", "nehmen", "gehen", "sollen"}


def _back(w: list[str], roh: str, p: Partie, lagebild) -> str | None:
    """'Soll ich backen?' aus Leben, Gold (Kaufplan), Welle, Gefahr und Objective - sofort statt ~3 s Claude."""
    menge = set(w)
    if not menge & BACK_WORTE or not (menge & FRAGE_ENTSCHEIDUNG or "?" in roh) or menge & {"warum", "wieso"}:
        return None
    if lagebild is None or not getattr(lagebild, "aktiv", False):
        return None
    from . import bewertung, komponist
    b = bewertung.bewerte(p, lagebild)
    if b is None or p.ich.tot:
        return None
    kauf = b.kauf.satz() if b.kauf is not None else ""
    if kauf.startswith("noch "):          # "noch 700 bis ..." -> "dir fehlen 700 bis ..."
        gold = f"{b.gold // 100 * 100} Gold - dir fehlen {kauf.removeprefix('noch ')}"
    else:
        gold = f"{b.gold // 100 * 100} Gold" + (f", das {kauf}" if kauf else "")
    gefahr = komponist.gefahr(b)
    welle = b.welle
    schiebt = welle is not None and welle[0] >= welle[1] + 2
    ob = b.objective
    ob_satz = ""
    if ob and 0 < ob[1] <= 90:
        ob_satz = f" {komponist._gross(komponist.OBJ_NOM[ob[0]])} {komponist.kommt(ob[0])} in {komponist.sek(ob[1])}" \
                  + (" - bis dahin bist du zurück." if ob[1] >= 45 else " - bleib lieber dafür da.")
    if b.leben is not None and b.leben < 0.35:
        return f"Ja, geh jetzt back: du hast nur {int(b.leben * 100)} Prozent Leben und {gold}." + ob_satz
    if b.kauf is not None and b.kauf.kaufen and b.gold >= komponist.RECALL_GOLD:
        if gefahr:
            return (f"Ja, aber erst zu {b.turm_name}: {gefahr[0].champion} {komponist._wann(gefahr[0])}. "
                    f"Dort recall - du hast {gold}.")
        if schiebt:
            return f"Ja, jetzt: deine Welle läuft in seinen Turm, du verlierst nichts. Du hast {gold}." + ob_satz
        return f"Ja, aber schieb erst die Welle rein - du hast {gold}." + ob_satz
    leben = f", und du hast {int(b.leben * 100)} Prozent Leben" if b.leben is not None else ""
    return f"Noch nicht: du hast {gold}{leben}. Bleib und farm." + ob_satz


KAUF_FRAGE = {"kaufen", "kauf", "kaufe", "holen", "hole", "item", "items", "bauen", "baue", "shop"}


def _kauf(w: list[str], roh: str, p: Partie, lagebild) -> str | None:
    """'Was soll ich kaufen?' / 'Soll ich mir den Brutalisierer holen?' - sofort aus dem Kaufplan (denselben, den
    die Ansagen benutzen) statt ueber Claude. Live 235433, 4:07-4:34: Claude sagte erst "zuerst Kontroll-Auge
    kaufen" und dann "kauf jetzt kein Kontroll-Auge" - der Kaufplan widerspricht sich nicht."""
    from . import ddragon, kaufplan
    menge = set(w)
    if not menge & KAUF_FRAGE or menge & {"warum", "wieso", "weshalb"} or not p.ich:
        return None
    gold = int(p.gold or 0)
    try:
        k = kaufplan.plan(p.ich.champion_id, p.ich.items, gold)
    except Exception:
        return None
    if k is None:
        return None
    # ein genanntes Item: steht es im Plan?
    namen = {v.get("name", ""): i for i, v in ddragon.items().items() if isinstance(v, dict)}
    def kern(n: str) -> str:            # "Der Brutalisierer" steht in der Frage als "den Brutalisierer"
        return n.split(" ", 1)[1] if n.split(" ", 1)[0] in ("Der", "Die", "Das") and " " in n else n
    genannt = next((n for n in namen if len(kern(n)) >= 5 and kern(n).lower() in roh), None)
    ziel = f"Ziel ist {k.item}"
    kontroll = 2055 not in p.ich.items and gold - (k.kosten if k.kaufen else 0) >= 75
    ka = ", und ein Kontroll-Auge" if kontroll else ""
    if k.kaufen:
        teile = [kaufplan._akk(n) for n in k.kaufen]
        liste = teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " und " + teile[-1]
        if genannt and genannt not in k.kaufen:
            return f"Nicht {kaufplan._akk(genannt)}: mit {gold} Gold kauf {liste}{ka} - {ziel}."
        return (f"Ja, mit {gold} Gold kauf {liste}{ka} - {ziel}." if genannt
                else f"Mit {gold} Gold kauf {liste}{ka} - {ziel}.")
    if k.naechstes:
        return (f"Noch nichts Sinnvolles: dir fehlen {k.naechstes[1]} Gold bis {kaufplan._dat(k.naechstes[0])}{ka}. "
                f"{ziel}.")
    return None


def _objective(w: list[str], roh: str, p: Partie, lagebild) -> str | None:
    """'Sollen wir Drache machen?' - die Kampflage an der Grube (wer ist in 15 s dort, beide Seiten, Flash, Ults,
    Gold) und dein Weg dorthin, sofort."""
    menge = set(w)
    objs = [OBJEKTIVE[x] for x in w if x in OBJEKTIVE]
    if not objs or not (menge & FRAGE_ENTSCHEIDUNG) or menge & {"warum", "wieso", "wann"}:
        return None
    if lagebild is None or not getattr(lagebild, "aktiv", False):
        return None
    from . import bewertung, komponist
    schl = objs[0]
    n = p.naechster_spawn(schl)
    if n is not None and n - p.zeit > 60:
        return f"{komponist._gross(komponist.OBJ_NOM[schl])} {komponist.kommt(schl)} erst in {komponist.sek(n - p.zeit)}."
    kl = bewertung.kampf_um(p, lagebild, schl)
    if kl is None:
        return None
    _, satz = kl.urteil()
    mein = next((t for s, t, *_ in kl.wir if s is p.ich), None)
    weg = f" Du brauchst {komponist.sek(mein)} dorthin." if mein is not None and mein >= 5 else ""
    return satz + weg


def sofort(frage: str, p: Partie, lagebild=None) -> str | None:
    """Antwort aus dem Zustand, oder None, wenn das Claude beantworten soll."""
    w = _woerter(frage)
    if not w or not p.ich:
        return None
    menge = set(w)
    # "Was soll ich jetzt machen?" - der Entscheider hat die Antwort schon gerechnet: sofort sagen statt 5 s
    # auf Claude zu warten (Carlos: "moeglichst Richtung Echtzeit, damit es wie ein Gespraech ist")
    if ("was" in menge and menge & {"mache", "machen", "tun", "jetzt", "soll", "plan"} and len(w) <= 7
            and not menge & (KAUF_WORTE | {"warum", "wieso"}) and _champion_im_text(w, p) is None
            and (e := getattr(lagebild, "entscheider", None)) is not None and e.aktuell is not None):
        return e.aktuell.satz
    # Eine Aussage ("Ich bin tot.", "Du weisst schon, dass ich Level 12 bin ...") ist keine Nachschau-Frage:
    # Live 21:21 bekam sie "Gragas noch 10 Sekunden" und "Sona ist Level 8, du bist Level 12" - Claude antwortet
    # im Zusammenhang.
    roh = frage.strip().lower()
    aussage = roh.startswith(("ich bin", "ich habe", "ich hab ", "ich war", "nein", "doch", "du weißt", "du weisst",
                              "ja,", "ja ", "ich bringe", "ich hatte")) or len(w) > 12
    if not aussage:
        for weg in (_kampf, _back, _objective, _kauf):
            if antwort := weg(w, roh, p, lagebild):
                return antwort
    if menge & ENTSCHEIDUNG:
        return None  # "soll ich ...", "lieber ...", "warum ...": das ist eine Abwaegung, keine Nachschau
    if aussage:
        return None
    ziel = _ziel(w, p)

    if menge & {"ult", "ulti", "ultimate"}:
        s = ziel or p.gegenueber()
        timer = getattr(lagebild, "zauber", None)
        if s:
            if s.level < 6:
                return f"{s.champion} ist erst Level {s.level} - noch keine Ult."
            rest = timer.fehlt(s, "R", p.zeit) if timer else None
            if rest:
                return f"{s.champion}s Ult ist noch {_dauer(rest)} weg."
            return f"Einen Ult-Verbrauch von {s.champion} habe ich nicht mitbekommen - rechne damit, dass sie bereit ist."
    if menge & {"flash", "zauber", "summoner", "teleport", "tp", "zünden", "ignite", "heal", "cooldown", "cooldowns"}:
        s = ziel or p.gegenueber()
        if s:
            timer = getattr(lagebild, "zauber", None)
            weg = [(z, timer.fehlt(s, z, p.zeit)) for z in s.zauber] if timer else []
            weg = [(z, r) for z, r in weg if r]
            da = [ZAUBER_DE.get(z, z) for z in s.zauber if z not in dict(weg)]
            if weg:
                teile = [f"{ZAUBER_DE.get(z, z)} ist noch {_dauer(r)} weg" for z, r in weg]
                return f"{s.champion}: " + ", ".join(teile) + (f". {' und '.join(da)} vermutlich bereit." if da else ".")
            zauber = " und ".join(da)
            return (f"{s.champion} hat {zauber}. Einen Verbrauch habe ich nicht gesehen, weder im Chat "
                    f"noch auf der Minimap - also vermutlich bereit.")
    if menge & {"platten", "platte"}:
        from . import bewertung
        b = bewertung.bewerte(p, lagebild) if lagebild is not None and getattr(lagebild, "aktiv", False) else None
        if b is None or (b.platten_gegner is None and b.platten_eigen is None):
            return "Die Platten kann ich gerade nicht lesen."
        teile = []
        if b.platten_gegner is not None:
            teile.append(f"Sein vorderster Turm hat noch {b.platten_gegner} Platte{'n' if b.platten_gegner != 1 else ''}")
        if b.platten_eigen is not None:
            teile.append(f"deiner {b.platten_eigen}")
        return ", ".join(teile) + "."
    if "prio" in menge:
        from . import bewertung, komponist
        b = bewertung.bewerte(p, lagebild) if lagebild is not None and getattr(lagebild, "aktiv", False) else None
        satz = komponist._prio_satz(b, ("Top", "Mid", "Bot")) if b else ""
        return (satz[0].upper() + satz[1:] + ".") if satz else "Die Wellen stehen gerade offen, keiner hat klar Prio."
    if objs := [OBJEKTIVE[x] for x in w if x in OBJEKTIVE]:
        return _timer(objs[0], p)
    if menge & {"wo", "gesehen", "position", "steht"} and not menge & {"stehen", "steht's", "stehts"}:
        return _wo(ziel or p.jungler(gegenteam(p.mein_team)), p, lagebild)
    if menge & {"tot", "respawn", "lebt", "leben"}:
        if ziel:
            return f"{ziel.champion} ist tot, noch {_dauer(ziel.respawn)}." if ziel.tot else f"{ziel.champion} lebt."
        tote = [s for s in p.gegner() if s.tot]
        if not tote:
            return "Gerade ist kein Gegner tot."
        return " ".join(f"{s.champion} noch {_dauer(s.respawn)}." for s in tote)
    if menge & {"items", "item", "gebaut", "build"} and ziel:
        return _items(ziel)
    if menge & {"level", "lvl"}:
        s = ziel or p.gegenueber()
        return f"{s.champion} ist Level {s.level}, du bist Level {p.ich.level}." if s else None
    if menge & {"cs", "farm", "vasallen", "minions"}:
        s = ziel or p.gegenueber()
        text = f"Du hast {p.ich.cs} CS, {p.ich.cs / max(1, p.zeit / 60):.1f} pro Minute.".replace(".", ",", 1)
        return text + (f" {s.champion} hat {s.cs}." if s else "")
    if "gold" in menge and menge & {"ich", "mein", "habe", "hab"}:
        return f"Du hast {int(p.gold or 0)} Gold."
    if menge & {"vorne", "hinten", "stehen", "steht's", "stehts", "stand", "lage"}:
        wir, die = p.mein_team, gegenteam(p.mein_team)
        diff = p.item_gold(wir) - p.item_gold(die)
        richtung = "vorne" if diff >= 0 else "hinten"
        return (f"Kills {p.kills(wir)} zu {p.kills(die)}, ihr liegt {abs(diff)} Gold an Items {richtung}, "
                f"Drachen {len(p.drachen(wir))} zu {len(p.drachen(die))}.")
    return None


def lage_text(p: Partie, lagebild=None) -> str:
    """Kompakte Lage fuer Claude."""
    it = ddragon.items()
    zauber = [ZAUBER_DE.get(z, z) for z in p.ich.zauber]
    if p.ich.rolle == "TOP" and "SummonerTeleport" not in p.ich.zauber and p.zeit >= 815:
        zauber.append("Teleport (aus der Top-Quest)")
    m = p.werte.get("maxHealth")
    leben = (f"Leben {int(p.werte.get('currentHealth', 0))}/{int(m)} ({int(100 * p.werte.get('currentHealth', 0) / m)} %), "
             if m else "")
    zeilen = [f"Spielzeit {int(p.zeit // 60)}:{int(p.zeit % 60):02d}. Ich: {p.ich.champion} "
              f"({ROLLE_DE.get(p.ich.rolle, '?')}), {leben}Gold {int(p.gold or 0)}, Beschwoererzauber: {', '.join(zauber)}."
              + (" Bot-Partie (Gegner sind Bots)." if any(s.bot for s in p.gegner()) else "")]
    # ALLE eigenen Items, auch Bauteile - live 235433, 4:17: "Aber ich habe doch schon Spitzhacke" (875 Gold, unter der
    # 900er-Grenze der Uebersicht - Claude riet, sie zu kaufen); dazu der Kaufplan, den auch die Ansagen benutzen
    meine = [it[i]["name"] for i in p.ich.items if i in it]
    zeilen.append("Meine Items (alle, auch Bauteile): " + (", ".join(meine) or "keine"))
    try:
        from . import kaufplan
        if (k := kaufplan.plan(p.ich.champion_id, p.ich.items, float(p.gold or 0))) is not None:
            zeilen.append(f"Kaufplan des Coachs (Ziel {k.item}): " + (
                "jetzt " + ", ".join(k.kaufen) if k.kaufen else
                f"noch {k.naechstes[1]} Gold bis {k.naechstes[0]}" if k.naechstes else "nichts") + " - dem nicht widersprechen.")
    except Exception:
        pass
    # eigene Zauber und Faehigkeiten aus dem HUD - die Live-API kennt keine Abklingzeiten
    if lagebild is not None and hasattr(lagebild, "eigene_zauber"):
        if ez := lagebild.eigene_zauber(p, p.zeit):
            zeilen.append("Meine Beschwoererzauber jetzt (HUD): " + ", ".join(
                f"{ZAUBER_DE.get(z, z)} " + ("bereit" if r <= 0 else f"weg, noch ~{int(r)} s") for z, r in ez.items()))
        if ef := lagebild.eigene_faehigkeiten(p.zeit):
            zeilen.append("Meine Faehigkeiten jetzt (HUD): " + ", ".join(
                f"{t} {'bereit' if b else 'nicht bereit'}" for t, b in ef.items()))
    for team, wer in ((p.mein_team, "Mein Team"), (gegenteam(p.mein_team), "Gegner")):
        zeilen.append(f"{wer}:")
        for s in p.team(team):
            fertig = [it[i]["name"] for i in s.items if i in it and it[i]["gold"]["total"] >= 900]
            teile = [f"- {s.champion} {ROLLE_DE.get(s.rolle, '?')} L{s.level} {s.kills}/{s.tode}/{s.assists} "
                     f"CS {s.cs}, Items: {', '.join(fertig) or 'keine grossen'}"]
            if s.tot:
                teile.append(f"TOT noch {int(s.respawn)} s")
            elif lagebild is not None and hasattr(lagebild, "leben") and (lb := lagebild.leben(s, p.zeit)) is not None:
                ult = lagebild.ult_bereit(s, p.zeit)
                teile.append(f"Leben {int(lb * 100)} %" + ("" if ult is None else (", Ult bereit" if ult else ", Ult nicht bereit")))
            elif lagebild is not None and (g := lagebild.gesehen(s)):
                teile.append(f"zuletzt vor {int(p.zeit - g[0])} s {minimap.ort(g[1], g[2], p.mein_team)}")
            zeilen.append(", ".join(teile))
    if lagebild is not None and hasattr(lagebild, "welle"):
        teile = [f"{l}: {z.worte(p.mein_team)}" for l in ("Top", "Mid", "Bot") if (z := lagebild.welle(l, p.zeit))]
        if teile:
            zeilen.append("Wellen (Minimap): " + "; ".join(teile))
    obj = [_timer(k, p) for k in ("drache", "larven", "herold", "baron")]
    zeilen.append("Objectives: " + " ".join(obj))
    zeilen.append(f"Drachen: wir {len(p.drachen(p.mein_team))}, Gegner {len(p.drachen(gegenteam(p.mein_team)))}.")
    if lagebild is not None and hasattr(lagebild, "zauber") and (aktiv := lagebild.zauber.aktiv(p.zeit)):
        zeilen.append("Beschwoererzauber weg (Gegner): " + ", ".join(
            f"{t.champion} {ZAUBER_DE.get(t.zauber, t.zauber)} noch {int(t.zurueck - p.zeit)} s ({t.quelle})" for t in aktiv))
    # Die berechnete Lage (Laufzeiten, Fenster, Kraefte) - Claude soll rechnen lassen, nicht raten
    if lagebild is not None and getattr(lagebild, "aktiv", False):
        try:
            from . import bewertung
            if b := bewertung.bewerte(p, lagebild):
                zeilen.append(b.text())
                # das Kampf-Urteil mit allen Faktoren - live 235433, 6:46: "Wie hast du mein Damage kalkuliert?" ->
                # Claude: "grobe Schaetzung", obwohl der Coach es gerechnet hatte
                from . import denker
                if b.lane is not None and (u := denker.urteil(b)) is not None:
                    zeilen.append(
                        f"KAMPF-URTEIL DES COACHS gegen {b.lane.champion}: {u.art} (Summe {u.wert:+.1f}); Faktoren: "
                        + "; ".join(f"{x.satz} ({x.wert:+.1f})" for x in sorted(u.faktoren, key=lambda x: -abs(x.wert)))
                        + ". So rechnet der Combo: Faehigkeitsschaden aus den Spieldaten (CommunityDragon) mit den "
                          "Raengen nach Level und Skill-Reihenfolge, deiner AD/AP, seiner Ruestung/Magieresistenz, "
                          "je Faehigkeit ein Auto-Angriff, Zuenden wenn bereit - eine Untergrenze.")
            if (jt := getattr(lagebild, "jungle", None)) and (jtext := jt.text(p.zeit, p.ich.rolle)):
                zeilen.append(jtext)
            if (e := getattr(lagebild, "entscheider", None)) is not None and e.aktuell is not None:
                zeilen.append(f"GERECHNETER PLAN JETZT (so hat der Coach entschieden; nur mit klarem Grund aus Bild "
                              f"oder Frage davon abweichen): {e.aktuell.satz}")
        except Exception as e:
            print(f"  Bewertung fuer Claude fehlgeschlagen: {e}", flush=True)
    # "Warum bin ich gestorben?" - die Fakten der Todesanalyse, drei Minuten lang
    if (tod := getattr(lagebild, "letzter_tod", None)) and 0 <= p.zeit - tod[0] <= 180:
        zeilen.append(f"DEIN LETZTER TOD (vor {int(p.zeit - tod[0])} s; alle Angaben Stand beim Tod):\n{tod[1]}")
    return "\n".join(zeilen)


SYSTEM = ("Du bist ein Challenger-Coach fuer League of Legends und sitzt neben dem Spieler, der gerade "
          "eine Partie spielt. Er fragt dich per Sprache. Antworte auf Deutsch in hoechstens zwei kurzen "
          "Saetzen, gesprochen, ohne Aufzaehlungen oder Markdown: erst was er tun soll, dann kurz warum. "
          "Nutze die Lage; erfinde nichts, was nicht darin steht. Items nur mit Namen aus der mitgegebenen "
          "Ladenliste nennen. Fragt er nach einer deiner letzten Ansagen ('was meinst du damit'), erklaere "
          "sie. Gibt er keine Frage, sondern Rueckmeldung ueber dich oder das Programm (Lob, Kritik, "
          "Wuensche), antworte nur mit dem einen Wort: Notiert. " + "{BILD}")

BILD_HINWEIS = (
    "Liegt ein Bild bei, ist es sein Bildschirm in diesem Moment - AKTUELLER als die Lage (die kann ein paar "
    "Sekunden alt sein); widersprechen sie sich, gilt das Bild. Schau zuerst darauf und nutze es fuer die Antwort: "
    "unten Mitte sein Leben und Mana (Zahlen), seine Faehigkeiten und rechts daneben die zwei Beschwoererzauber "
    "(eine Zahl darauf = Abklingzeit, also weg), sein Gold unten rechts; ueber den Koepfen die Lebensbalken; ob "
    "er unter einem gegnerischen Turm steht; Vasallen beider Seiten. Sag nur, was wirklich zu sehen ist. "
    "Fehlt dir fuer eine gute Antwort etwas, das er mit der Kamera zeigen kann (z. B. den Kampf am Drachen, "
    "die Welle in seiner Lane), dann antworte NUR mit 'KAMERA: <wohin, hoechstens 8 Woerter>' - er schwenkt "
    "kurz dorthin, und du bekommst das neue Bild.")
KAMERA_NACHFRAGE = ("Er hat die Kamera wie gebeten geschwenkt - das Bild zeigt es jetzt. Beantworte seine Frage "
                    "damit; frag nicht noch einmal nach der Kamera.")
KAMERA_WARTEN = 4.0     # Sekunden zwischen "schwenk mal" und dem neuen Bild
SYSTEM = SYSTEM.replace("{BILD}", BILD_HINWEIS) + (
    " Die BEWERTUNG in der Lage ist gerechnet (Ankunftszeiten, Fenster, Kraefte, Prio, Platten, Kauf, "
    "Todeszeit): stuetz die Antwort darauf und nenne die entscheidende Zahl, statt zu schaetzen.")


AUFWAND = "low"   # gleich fuer Frage und vorgehaltenen Prozess (llm.vorhalten), sonst passt er nicht


KAUF_WORTE = {"kaufen", "kauf", "item", "items", "build", "bauen", "baue", "shop", "laden", "gold"}


def laden_liste() -> str:
    """Fertige Items und Bauteile des Patches, deutsch, MIT PREIS - damit Claude keine Namen erfindet und
    nicht behauptet, 1331 Gold reichten fuer Endlosen Hunger (Partie 7, 17:12)."""
    it = ddragon.items()
    kaufbar = {v["name"]: v for v in it.values() if v.get("gold", {}).get("purchasable") and v.get("maps", {}).get("11")
               and not v.get("requiredChampion")}
    fertig = sorted(f"{n} {v['gold']['total']}" for n, v in kaufbar.items()
                    if not v.get("into") and v["gold"]["total"] >= 2200)
    bauteile = sorted(f"{n} {v['gold']['total']}" for n, v in kaufbar.items()
                      if v.get("into") and 700 <= v["gold"]["total"] < 2200)
    return f"FERTIG: {', '.join(fertig)}\nBAUTEILE: {', '.join(bauteile)}"


def mit_claude(frage: str, p: Partie, lagebild=None, modell: str = "sonnet", letzte=(), gehirn=None,
               bilder: list[bytes] | None = None, bei_satz=None, vorhalten: bool = False) -> str:
    """`gehirn`: wenn da, bekommt Claude Spielakte + passende Lexikon-Abschnitte dazu.
    `bilder`: der Spielbildschirm im Moment der Frage (JPEG). `vorhalten`: danach gleich den naechsten
    Claude-Prozess vorstarten (live - die naechste Frage spart den Start)."""
    zusatz = ""
    if letzte:
        zusatz += "\n\nDeine letzten Ansagen: " + " | ".join(
            f"{int((a.gesprochen or a.zeit) // 60)}:{int((a.gesprochen or a.zeit) % 60):02d} {a.text}" for a in letzte)
    if set(_woerter(frage)) & KAUF_WORTE:
        zusatz += (f"\n\nItems im Laden (Patch {ddragon.version()}, Name Preis - nur diese Namen verwenden; "
                   f"reicht sein Gold nicht fuer das Item, nenn das passende Bauteil, das er JETZT kaufen kann, "
                   f"und was spaeter dazukommt):\n{laden_liste()}")
    lage = lage_text(p, lagebild) + zusatz
    inhalt = gehirn.kontext(frage, p, lage) if gehirn else f"Lage:\n{lage}"
    try:
        from .itemnamen import absichern
        if bei_satz is not None:   # Satz fuer Satz sprechen, sobald er fertig ist
            return absichern(llm.frage_strom(f"{inhalt}\n\nFrage des Spielers: {frage}",
                                             lambda s: bei_satz(absichern(s)[0]), system=SYSTEM, modell=modell,
                                             timeout=40, aufwand=AUFWAND, bilder=bilder,
                                             nachladen=vorhalten).strip())[0]
        return absichern(llm.frage(f"{inhalt}\n\nFrage des Spielers: {frage}",
                                   system=SYSTEM, modell=modell, timeout=40, aufwand="low", bilder=bilder).strip())[0]
    except llm.LLMFehler as e:
        print(f"  Claude-Fehler: {e}", flush=True)
        if "login" in str(e).lower():
            return "Für diese Frage brauche ich Claude, und die Anmeldung fehlt noch."
        if "keine antwort" in str(e).lower():
            return "Claude braucht gerade zu lange, frag gleich noch mal."
        return "Claude hat gerade einen Fehler gemeldet."
