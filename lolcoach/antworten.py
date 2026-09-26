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
    # "Was soll ich jetzt machen?" - der Entscheider hat die Antwort schon gerechnet: sofort sagen statt 5 s
    # auf Claude zu warten (Carlos: "moeglichst Richtung Echtzeit, damit es wie ein Gespraech ist")
    if ("was" in menge and menge & {"mache", "machen", "tun", "jetzt", "soll", "plan"} and len(w) <= 7
            and not menge & (KAUF_WORTE | {"warum", "wieso"}) and _champion_im_text(w, p) is None
            and (e := getattr(lagebild, "entscheider", None)) is not None and e.aktuell is not None):
        return e.aktuell.satz
    if menge & ENTSCHEIDUNG:
        return None  # "soll ich ...", "lieber ...", "warum ...": das ist eine Abwaegung, keine Nachschau
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
            if (jt := getattr(lagebild, "jungle", None)) and (jtext := jt.text(p.zeit, p.ich.rolle)):
                zeilen.append(jtext)
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
               bilder: list[bytes] | None = None) -> str:
    """`gehirn`: wenn da, bekommt Claude Spielakte + passende Lexikon-Abschnitte dazu.
    `bilder`: der Spielbildschirm im Moment der Frage (JPEG)."""
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
        return absichern(llm.frage(f"{inhalt}\n\nFrage des Spielers: {frage}",
                                   system=SYSTEM, modell=modell, timeout=40, aufwand="low", bilder=bilder).strip())[0]
    except llm.LLMFehler as e:
        print(f"  Claude-Fehler: {e}", flush=True)
        if "login" in str(e).lower():
            return "Für diese Frage brauche ich Claude, und die Anmeldung fehlt noch."
        if "keine antwort" in str(e).lower():
            return "Claude braucht gerade zu lange, frag gleich noch mal."
        return "Claude hat gerade einen Fehler gemeldet."
