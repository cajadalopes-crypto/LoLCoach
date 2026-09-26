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
ZAUBER_DE = {"SummonerFlash": "Flash", "SummonerTeleport": "Teleport", "SummonerDot": "Zünden",
             "SummonerHeal": "Heilen", "SummonerExhaust": "Erschöpfen", "SummonerBarrier": "Barriere",
             "SummonerSmite": "Zerschmettern", "SummonerHaste": "Geist", "SummonerBoost": "Reinigen"}


def _dauer(sek: float) -> str:
    s = int(round(sek))
    if s < 90:
        return f"{s} Sekunden"
    m, r = divmod(s, 60)
    return f"{m} Minuten" if r < 10 else f"{m} Minuten {r}"


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
    if not g:
        return f"{s.champion} habe ich noch nicht gesehen."
    ort = minimap.ort(g[1], g[2], p.mein_team)
    if lagebild.sichtbar(s):
        return f"{s.champion} ist {ort}, gerade zu sehen."
    return f"{s.champion} war vor {_dauer(p.zeit - g[0])} {ort}."


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


def sofort(frage: str, p: Partie, lagebild=None) -> str | None:
    """Antwort aus dem Zustand, oder None, wenn das Claude beantworten soll."""
    w = _woerter(frage)
    if not w or not p.ich:
        return None
    menge = set(w)
    if menge & ENTSCHEIDUNG:
        return None  # "soll ich ...", "lieber ...", "warum ...": das ist eine Abwaegung, keine Nachschau
    ziel = _ziel(w, p)

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
    zeilen = [f"Spielzeit {int(p.zeit // 60)}:{int(p.zeit % 60):02d}. Ich: {p.ich.champion} "
              f"({ROLLE_DE.get(p.ich.rolle, '?')}), Gold {int(p.gold or 0)}."
              + (" Bot-Partie (Gegner sind Bots)." if any(s.bot for s in p.gegner()) else "")]
    for team, wer in ((p.mein_team, "Mein Team"), (gegenteam(p.mein_team), "Gegner")):
        zeilen.append(f"{wer}:")
        for s in p.team(team):
            fertig = [it[i]["name"] for i in s.items if i in it and it[i]["gold"]["total"] >= 900]
            teile = [f"- {s.champion} {ROLLE_DE.get(s.rolle, '?')} L{s.level} {s.kills}/{s.tode}/{s.assists} "
                     f"CS {s.cs}, Items: {', '.join(fertig) or 'keine grossen'}"]
            if s.tot:
                teile.append(f"TOT noch {int(s.respawn)} s")
            elif lagebild is not None and (g := lagebild.gesehen(s)):
                teile.append(f"zuletzt vor {int(p.zeit - g[0])} s {minimap.ort(g[1], g[2], p.mein_team)}")
            zeilen.append(", ".join(teile))
    obj = [_timer(k, p) for k in ("drache", "larven", "herold", "baron")]
    zeilen.append("Objectives: " + " ".join(obj))
    zeilen.append(f"Drachen: wir {len(p.drachen(p.mein_team))}, Gegner {len(p.drachen(gegenteam(p.mein_team)))}.")
    if lagebild is not None and hasattr(lagebild, "zauber") and (aktiv := lagebild.zauber.aktiv(p.zeit)):
        zeilen.append("Beschwoererzauber weg (Gegner): " + ", ".join(
            f"{t.champion} {ZAUBER_DE.get(t.zauber, t.zauber)} noch {int(t.zurueck - p.zeit)} s ({t.quelle})" for t in aktiv))
    return "\n".join(zeilen)


SYSTEM = ("Du bist ein Challenger-Coach fuer League of Legends und sitzt neben dem Spieler, der gerade "
          "eine Partie spielt. Er fragt dich per Sprache. Antworte auf Deutsch in hoechstens zwei kurzen "
          "Saetzen, gesprochen, ohne Aufzaehlungen oder Markdown: erst was er tun soll, dann kurz warum. "
          "Nutze die Lage; erfinde nichts, was nicht darin steht. Items nur mit Namen aus der mitgegebenen "
          "Ladenliste nennen. Fragt er nach einer deiner letzten Ansagen ('was meinst du damit'), erklaere "
          "sie. Gibt er keine Frage, sondern Rueckmeldung ueber dich oder das Programm (Lob, Kritik, "
          "Wuensche), antworte nur mit dem einen Wort: Notiert.")


KAUF_WORTE = {"kaufen", "kauf", "item", "items", "build", "bauen", "baue", "shop", "laden", "gold"}


def laden_liste() -> str:
    """Alle fertigen Items des Patches, deutsch - damit Claude keine Namen erfindet."""
    it = ddragon.items()
    namen = sorted({v["name"] for v in it.values()
                    if v.get("gold", {}).get("purchasable") and v.get("maps", {}).get("11")
                    and not v.get("into") and v["gold"]["total"] >= 2200 and not v.get("requiredChampion")})
    return ", ".join(namen)


def mit_claude(frage: str, p: Partie, lagebild=None, modell: str = "sonnet", letzte=(), gehirn=None) -> str:
    """`gehirn`: wenn da, bekommt Claude Spielakte + passende Lexikon-Abschnitte dazu."""
    zusatz = ""
    if letzte:
        zusatz += "\n\nDeine letzten Ansagen: " + " | ".join(
            f"{int((a.gesprochen or a.zeit) // 60)}:{int((a.gesprochen or a.zeit) % 60):02d} {a.text}" for a in letzte)
    if set(_woerter(frage)) & KAUF_WORTE:
        zusatz += f"\n\nItems im Laden (Patch {ddragon.version()}, nur diese Namen verwenden): {laden_liste()}"
    lage = lage_text(p, lagebild) + zusatz
    inhalt = gehirn.kontext(frage, p, lage) if gehirn else f"Lage:\n{lage}"
    try:
        return llm.frage(f"{inhalt}\n\nFrage des Spielers: {frage}",
                         system=SYSTEM, modell=modell, timeout=40, aufwand="low").strip()
    except llm.LLMFehler as e:
        print(f"  Claude-Fehler: {e}", flush=True)
        if "login" in str(e).lower():
            return "Für diese Frage brauche ich Claude, und die Anmeldung fehlt noch."
        if "keine antwort" in str(e).lower():
            return "Claude braucht gerade zu lange, frag gleich noch mal."
        return "Claude hat gerade einen Fehler gemeldet."
