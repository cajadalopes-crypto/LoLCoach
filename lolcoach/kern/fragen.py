"""Fragen an den Kern (Schritt 6; Buch 0, Kapitel 10 mit Buch 11, Kapitel 5 und 6).

`beantworte(kern, frage, p, lagebild)` ordnet die Frage einer Absicht zu und antwortet aus DEMSELBEN Plan und derselben
Zeitleiste wie die ungefragten Ansagen - ohne Claude, in Millisekunden:

  JETZT     "was mache ich jetzt", "wo gehe ich hin", "welche Welle"   -> Plan + Grund + danach
  DANACH    "was mache ich, nachdem ...", "und danach?"                -> danach (Buch 11, 3) mit Grund
  WARUM     "warum soll ich ...", "warum hast du gesagt ..."           -> Grund des Plans + Vergleich mit der genannten
                                                                          oder naechstbesten Handlung
  ENTWEDER  "zum Drachen oder zum Turm?"                               -> beide gerechnet, Empfehlung zuerst
  SOLL_ICH  "soll ich meinem Team helfen?"                             -> "Ja, ..." / "Nein, ... bringt mehr: ..."
  LAGE      "wie macht sich mein Team?"                                -> Kills, Tuerme, Drachen, Gold, dann der Plan
  TIMER     Flashes, "wann kommt der Herold?"                          -> Flash-Tabelle bzw. Zeitleiste
  WO        "wo ist Xin?"                                              -> die vorhandene Sofort-Antwort
  KAUF      "was soll ich kaufen?", "kein Platz im Inventar"           -> Kaufplan (R3), bei vollem Inventar mit Verkauf
  NOTIZ     "notier ...", Rueckmeldungen                               -> "Notiert." und, steckt eine Frage darin, ihre
                                                                          Antwort
  OFFEN     alles andere                                               -> None: Claude mit `kern.kontext()`

Regeln (Buch 11, 5): Mindestform Handlung + Ziel + Grund; kein Widerspruch zur letzten Ansage ohne "Neu:"; die Antwort
gilt danach als gesagter Plan; dieselbe Absicht in antwort_wiederholung_s bekommt mehr Grund; Aussagen von Carlos
("ich war in der Base", "Drache ist tot", "kein Platz") sind Korrekturen (korrektur_gilt_s).
"""
from __future__ import annotations

import re

from . import fuehren
from .handlung import Handlung

# --- Absicht ------------------------------------------------------------------------------------------------------

NOTIER = re.compile(r"notier|notiz|merk dir|merke dir")
KEIN_PLATZ = re.compile(r"kein(en)? platz|inventar (ist )?voll|volles inventar")
KAUF = re.compile(r"(was|welches item|welche items).{0,20}(kauf|bauen)|kaufen\?|build")
DANACH = re.compile(r"nachdem|und danach|was danach|danach\?|und dann\?")
WARUM_WORT = re.compile(r"(^|[^a-zäöüß])(warum|wieso|weshalb)([^a-zäöüß]|$)")
WARUM_BEZUG = re.compile(r"soll|sollte|sagst|gesagt|meintest|nicht|(^|[^a-zäöüß])ich([^a-zäöüß]|$)")
ENTWEDER = re.compile(r"(^|[^a-zäöüß])oder([^a-zäöüß]|$)")
SOLL_ICH = re.compile(r"(^|[^a-zäöüß])(soll|sollte|kann|darf) ich")
LAGE = re.compile(r"wie macht sich|wie steht|wie läuft|wie laeuft|wie sieht es (bei uns|insgesamt)|sorgen machen")
FLASH = re.compile(r"flash|fläch|flaech")
TIMER = re.compile(r"wann (kommt|spawnt|ist)|timer|wie lange noch")
WO = re.compile(r"(^|[^a-zäöüß])wo (ist|sind|steht|war)")
JETZT = re.compile(r"was mache ich|was mach ich|was jetzt|und jetzt|wo gehe? ich hin|wohin|was soll ich (jetzt|machen|tun)|"
                   r"was tue ich|was nun|welche welle|welche lane|was ist (der )?plan")
KORREKTUR_BASIS = re.compile(r"(ich (bin|war) (in der|in die) (base|basis))|(bin|war) in der base")
KORREKTUR_TOT = re.compile(r"(drache|herold|baron|larven)( ist)? (tot|weg|gemacht|down)")
KORREKTUR_BEI_MIR = re.compile(r"(ist|sind) (jetzt )?bei mir")
# eindeutige Rueckmeldungen - vor allen Fragen (213624 20:32: "Also wie gesagt ... Du sagst nicht, was die naechsten
# Schritte sind")
RUECKMELDUNG_KLAR = re.compile(r"^(übrigens|uebrigens|also wie gesagt)|du bist (überhaupt|gar) nicht|du ignorierst")
# Rueckmeldungen ueber den Coach oder das eigene Spiel (Carlos' Notizen 213624)
RUECKMELDUNG = re.compile(r"^(übrigens|uebrigens|also wie gesagt|ich habe das gefühl|sag mal, können wir)|du sagst|"
                          r"du redest|du ignorierst|du bedenkst|du bist (überhaupt|gar) nicht|du antwortest|"
                          r"(habe|hab) ich .{0,30}(weggebummst|getötet|gekillt|getowerdived|besiegt)|"
                          r"ich habe .{0,20}getowerdived|einstellen|aussprich|schwer einschätzen")

OPTION = {
    "drache": re.compile(r"drach|drake|dragon"), "baron": re.compile(r"baron|nashor"),
    "herold": re.compile(r"herold|herald"), "larven": re.compile(r"larve|grubs"),
    "turm": re.compile(r"turm|tower|türm"), "top": re.compile(r"top|oben"), "mid": re.compile(r"mid|mitte"),
    "bot": re.compile(r"bot|unten"), "back": re.compile(r"(^|[^a-z])back|base|basis|recall"),
    "team": re.compile(r"team|gruppe|helfen"), "kampf": re.compile(r"kämpf|kaempf|kampf|rein gehen|all.?in"),
    "welle": re.compile(r"welle|farm"),
}
# welche genannte Option zaehlt, wenn mehrere in der Frage stehen ("... zur Top-Lane ... Team ... beim Drachen")
VORRANG = ("drache", "baron", "herold", "larven", "turm", "top", "mid", "bot", "back", "team", "kampf", "welle")
OPTION_WORT = {"drache": "Drache", "baron": "Baron", "herold": "Herold", "larven": "Larven", "turm": "Turm",
               "top": "Top", "mid": "Mid", "bot": "Bot", "back": "Back", "team": "zu deinem Team",
               "kampf": "Kampf", "welle": "Welle"}


def absicht(frage: str) -> str:
    f = frage.lower()
    if NOTIER.search(f) or RUECKMELDUNG_KLAR.search(f):
        return "NOTIZ"
    if KEIN_PLATZ.search(f):
        return "KAUF"
    if DANACH.search(f):
        return "DANACH"
    if WARUM_WORT.search(f) and WARUM_BEZUG.search(f):
        return "WARUM"
    if KAUF.search(f):
        return "KAUF"
    if FLASH.search(f):
        return "TIMER"
    if ENTWEDER.search(f) and len(optionen_in(f)) >= 2:
        return "ENTWEDER"
    if LAGE.search(f):
        return "LAGE"
    if JETZT.search(f) or KORREKTUR_BASIS.search(f) or KORREKTUR_TOT.search(f) or KORREKTUR_BEI_MIR.search(f):
        return "JETZT"
    if SOLL_ICH.search(f):
        return "SOLL_ICH"
    if TIMER.search(f):
        return "TIMER"
    if WO.search(f):
        return "WO"
    if RUECKMELDUNG.search(f):
        return "NOTIZ"
    return "OFFEN"


def optionen_in(f: str) -> list[str]:
    """Die genannten Optionen in der Reihenfolge der Frage."""
    treffer = []
    for name, muster in OPTION.items():
        if (m := muster.search(f)):
            treffer.append((m.start(), name))
    return [n for _, n in sorted(treffer)]


# --- Bausteine -----------------------------------------------------------------------------------------------------

def _sagbar(kern) -> list[Handlung]:
    """Kandidaten dieses Takts, die der Coach sagen wuerde (nicht stumm, nicht vom ungeeichten Modell), nach EV."""
    return [h for h in sorted(kern.kandidaten or [], key=lambda h: -h.ev)
            if not h.stumm and not fuehren.stumm(h) and (h.satz or h.ziel is not None)]


def _jetzt(kern) -> Handlung | None:
    """Der Plan - oder, wenn er nur Halten ist oder am ungeeichten Modell haengt, die beste sagbare Handlung."""
    p = kern.fuehrer.plan
    if p is not None and not fuehren.stumm(p.handlung) and (p.handlung.satz or fuehren.stumm_satz(p.handlung)):
        return p.handlung
    sagbar = _sagbar(kern)
    return sagbar[0] if sagbar else None


def _jetzt_satz(kern, h: Handlung | None) -> str:
    """Der Satz zum Plan - oder, gibt es keinen sagbaren, der Rueckfall: die eigene Welle."""
    s = satz(h)
    if s:
        return s
    lane = kern.m.meine_lane if kern.m is not None and kern.m.meine_lane else "Top"
    s = f"Farm deine {lane}-Welle, bis sich etwas öffnet."
    # gefragt nennt der Coach auch die beste Option, die am ungeeichten Kampfmodell haengt - ehrlich als unsicher
    # (Buch 11, 1.8; ungefragt bleibt sie stumm, Entscheidung 2)
    offen = next((x for x in sorted(kern.kandidaten or [], key=lambda x: -x.ev)
                  if fuehren.stumm(x) and not x.stumm and x.ziel is not None and x.art not in fuehren.NIE_DANACH), None)
    if offen is not None:
        s += f" Oder {fuehren.kurz(offen)}, aber mit Kampf - unsicher."
    return s


def satz(h: Handlung | None) -> str:
    """Handlung + Ziel + Grund als ein Satz."""
    if h is None:
        return ""
    if h.stumm:
        return fuehren.stumm_satz(h)
    s = (h.satz or "").strip()
    if s:
        return s if s.endswith((".", "!", "?")) else s + "."
    k = fuehren.kurz(h)
    return f"{k[:1].upper()}{k[1:]}: {h.grund}." if h.grund else f"{k[:1].upper()}{k[1:]}."


def _passt(h: Handlung, option: str, m) -> bool:
    k = fuehren.kurz(h).lower()
    o = h.daten.get("objective")
    if option in ("drache", "baron", "herold", "larven"):
        return o == option or option in k or (option == "drache" and "drachen" in k)
    if option == "turm":
        return h.art in ("DRUECKEN", "MIT_GRUPPE", "PLATTEN", "TP_SPIEL") or "turm" in k
    if option in ("top", "mid", "bot"):
        lane = (h.daten.get("lane") or "").lower()
        return lane == option or option in k
    if option == "back":
        return h.art in fuehren.BACK_ARTEN or h.art == "KAUFEN"
    if option == "team":
        return h.art in ("ZUR_GRUPPE", "MIT_GRUPPE")
    if option == "kampf":
        return h.art in ("ANNEHMEN", "REIN", "ALL_IN", "TRADE")
    if option == "welle":
        return h.art in ("SEITENWELLE", "WELLE_KLAEREN", "FARMEN", "WELLE_REIN_UND_BACK", "STAPELN") or "welle" in k
    return False


def _fuer_option(kern, option: str) -> Handlung | None:
    """Die beste Handlung zu einer genannten Option - auch eine, die ungefragt stumm bleibt (ungeeichtes Modell):
    gefragt nennt der Coach sie, mit "unsicher" (Buch 11, 1.8)."""
    alle = sorted(kern.kandidaten or [], key=lambda h: -h.ev)
    return next((h for h in alle if _passt(h, option, kern.m) and not h.stumm), None)


def _mit_vorbehalt(h: Handlung) -> str:
    return satz(h).rstrip(".") + (", aber mit Kampf - unsicher." if fuehren.stumm(h) else ".")


def _genannt(opts: list[str], h: Handlung | None, m) -> str | None:
    """Die genannte Option, die NICHT der Plan ist - Objectives vor Tuermen, Lanes, Back und Team."""
    rest = [o for o in opts if o != "kampf" and (h is None or not _passt(h, o, m))]
    return min(rest, key=VORRANG.index) if rest else None


def _warum_nicht(kern, option: str) -> str:
    """Warum eine genannte Option gerade keine ist - ein ganzer Satz mit dem Namen vorn, nur, was der Kern weiss."""
    m = kern.m
    wort = OPTION_WORT.get(option, option)
    wort = wort[:1].upper() + wort[1:]
    if option in ("drache", "baron", "herold", "larven") and m is not None:
        o = next((x for x in m.objectives or [] if x.schl == option), None)
        if o is not None and not o.lebt and o.spawn_in > 0:
            return f"{wort} spawnt erst in {int(o.spawn_in)} Sekunden"
        if o is not None and o.lebt:
            return f"{wort} lohnt gerade nicht: zu weit oder zu wenige von euch dort"
    if option == "kampf":
        return "Den Kampf rechnet der Coach noch nicht sicher"
    return f"{wort} ist gerade keine Option"


def _korrektur(kern, f: str, zeit: float) -> str | None:
    """Buch 11, 5.6 / Buch 0, 10.4: eine Aussage von Carlos ueberschreibt das Merkmal korrektur_gilt_s lang."""
    k = getattr(kern, "korrekturen", None)
    if k is None:
        kern.korrekturen = k = {}
    if KORREKTUR_BASIS.search(f):
        k["basis"] = zeit
        return "basis"
    if (m := KORREKTUR_TOT.search(f)):
        k[f"tot:{m.group(1)}"] = zeit
        return "tot"
    return None


def _lage(kern, p) -> str:
    from ..zustand import gegenteam
    wir, die = p.mein_team, gegenteam(p.mein_team)
    kw, kd = p.kills(wir), p.kills(die)
    tuerme_w = sum(1 for e in p.kills_von("TurretKilled") if e.team == wir)
    tuerme_d = sum(1 for e in p.kills_von("TurretKilled") if e.team == die)
    gold = p.item_gold(wir) - p.item_gold(die)
    fuehrt = "führt" if kw >= kd else "liegt hinten"
    s = (f"Ihr {fuehrt} {max(kw, kd)} zu {min(kw, kd)}, Türme {tuerme_w} zu {tuerme_d}, "
         f"Drachen {len(p.drachen(wir))} zu {len(p.drachen(die))}, {abs(gold)} Gold {'vorn' if gold >= 0 else 'hinten'}.")
    h = _jetzt(kern)
    return s + (f" Jetzt: {satz(h)}" if h is not None else "")


# --- Antworten ----------------------------------------------------------------------------------------------------

def _antwort(kern, a: str, frage: str, p, lagebild, zeit: float, wiederholt: bool) -> tuple[str | None, Handlung | None]:
    f = frage.lower()
    m = kern.m
    h = _jetzt(kern)
    danach = kern.danach_text
    if a == "JETZT":
        korr = _korrektur(kern, f, zeit)
        if korr == "basis" and m is not None:
            opts = [o for o in optionen_in(f) if o not in ("back",)]
            c = _fuer_option(kern, opts[0]) if opts else None
            from .modi import basis
            try:
                z = basis.wohin(m, kern.cfg, "BASIS", kern._wohin, kern._lage(m))
            except Exception:
                z = None
            if opts and (c is not None or z is not None):
                wort = OPTION_WORT.get(opts[0], opts[0])
                if z is not None and z.satz and _passt(z, opts[0], m):
                    return f"Stimmt, dann {wort}: {satz(z)}", z        # das Ziel aus der Basis IST die Option
                if c is not None:
                    return f"Stimmt, dann {wort}: {_mit_vorbehalt(c)}", c
                return f"{_warum_nicht(kern, opts[0])}. {_jetzt_satz(kern, z or h)}", z or h
            if z is not None and z.satz:
                return f"Aus der Basis: {satz(z)}", z
        if "welle" in f or "lane" in f or "leine" in f:
            w = next((x for x in _sagbar(kern) if _passt(x, "welle", m) and x.daten.get("lane")), None)
            lane = m.meine_lane if m is not None else None
            if w is not None:
                return satz(w) + (f" Danach {danach}." if danach else ""), w
            if lane:
                return f"Deine Welle ist {lane}. " + (f"Jetzt aber: {satz(h)}" if satz(h) else f"Farm die {lane}-Welle."), h
        if kern.modus.aktuell == "KAMPF":
            return f"Erst der Kampf, dann {fuehren.kurz(h)}." if h is not None else "Erst der Kampf.", h
        text = _jetzt_satz(kern, h) + (f" Danach {danach}." if danach else "")
        if wiederholt:
            alt = next((x for x in _sagbar(kern) if x is not h and fuehren.kurz(x) != fuehren.kurz(h)), None)
            if alt is not None:
                text += f" Die Alternative wäre {fuehren.kurz(alt)}: {alt.grund or 'weniger wert'}."
        return text, h
    if a == "DANACH":
        if kern.danach is not None:
            d = kern.danach
            return f"Nach {fuehren.kurz(h)}: {fuehren.kurz(d)}" + (f", {d.grund}." if d.grund else "."), h
        return (f"Erst {fuehren.kurz(h)}, danach rechne ich neu: {h.grund}." if h is not None and h.grund
                else f"{_jetzt_satz(kern, h)} Danach rechne ich neu."), h
    if a == "WARUM":
        k = getattr(m.b, "kauf", None) if m is not None and m.b is not None else None
        if re.search(r"kauf|item", f) and k is not None and getattr(k, "item", None):
            return f"Kauf {k.item}: der nächste Schritt aus deinem eigenen Build.", h
        genannt = _genannt(optionen_in(f), h, m)
        text = _jetzt_satz(kern, h)
        if genannt is not None:
            wort = OPTION_WORT.get(genannt, genannt)
            wort = wort[:1].upper() + wort[1:]
            c = _fuer_option(kern, genannt)
            if c is None:
                text += f" {_warum_nicht(kern, genannt)}."
            elif c.ev < h.ev:
                text += f" {wort} bringt weniger: {c.grund or fuehren.kurz(c)}" + (
                    ", und mit Kampf - unsicher." if fuehren.stumm(c) else ".")
            else:
                text += f" {wort} geht auch: {c.grund or fuehren.kurz(c)}" + (
                    ", aber mit Kampf - unsicher." if fuehren.stumm(c) else ".")
        else:
            alt = next((x for x in _sagbar(kern) if x is not h and h is not None
                        and fuehren.kurz(x) != fuehren.kurz(h)), None)
            if alt is not None:
                text += f" {fuehren.kurz(alt)[:1].upper()}{fuehren.kurz(alt)[1:]} bringt weniger."
        return text, h
    if a == "ENTWEDER":
        opts = sorted(optionen_in(f), key=VORRANG.index)[:2]
        paar = [(o, _fuer_option(kern, o)) for o in opts]
        gut = [(o, c) for o, c in paar if c is not None]
        if not gut:
            gruende = " ".join(f"{_warum_nicht(kern, o)}." for o in opts)
            return f"Keins von beiden. {gruende} Jetzt: {_jetzt_satz(kern, h)}", h
        o1, c1 = max(gut, key=lambda oc: oc[1].ev)
        andere = next(o for o, _ in paar if o != o1)
        c2 = dict(paar).get(andere)
        rest = (f"{OPTION_WORT.get(andere, andere)} bringt weniger." if c2 is not None
                else f"{_warum_nicht(kern, andere)}.")
        return f"{_mit_vorbehalt(c1)} {rest}", c1
    if a == "SOLL_ICH":
        opts = optionen_in(f)
        if "kampf" in opts:
            return _kampf_antwort(kern, lagebild, h), h
        o = min((x for x in opts if x != "kampf"), key=VORRANG.index, default=None)
        c = _fuer_option(kern, o) if o else None
        if c is None:
            return f"Nein. {_jetzt_satz(kern, h)}" + (f" {_warum_nicht(kern, o)}." if o else ""), h
        if h is None:
            return f"Ja, geht: {_mit_vorbehalt(c)}", c
        if c is h or fuehren.kurz(c) == fuehren.kurz(h):
            return f"Ja: {_mit_vorbehalt(c)}", c
        schwelle = kern.cfg["plan"]["hysterese_ge"]
        if c.ev >= h.ev - schwelle:
            return f"Ja, geht auch: {_mit_vorbehalt(c)}", c
        return f"Nein, {fuehren.kurz(h)} bringt mehr: {h.grund or satz(h)}", h
    if a == "LAGE":
        return _lage(kern, p), h
    if a == "TIMER":
        if FLASH.search(f) or wiederholt:
            from ..antworten import flash_satz
            return flash_satz(p, lagebild), None
        for o in ("drache", "baron", "herold", "larven"):
            if OPTION[o].search(f) and m is not None:
                x = next((y for y in m.objectives or [] if y.schl == o), None)
                if x is not None:
                    if x.lebt:
                        return f"{OPTION_WORT[o]} lebt. {satz(h)}", h
                    return f"{OPTION_WORT[o]} spawnt in {int(x.spawn_in)} Sekunden.", None
        from .zeitleiste import als_text
        return (f"Als Nächstes: {als_text(kern.zeitleiste, m.zeit, 3)}." if kern.zeitleiste and m is not None
                else None), None
    if a == "WO":
        from ..antworten import sofort
        return sofort(frage, p, lagebild), None
    if a == "KAUF":
        k = getattr(m.b, "kauf", None) if m is not None and m.b is not None else None
        if k is not None and getattr(k, "verkaufen", None) and k.kaufen:
            return f"Kein Platz: verkauf {k.verkaufen}, dann kauf {', '.join(k.kaufen)}.", h
        if k is not None and k.kaufen:
            return f"Kauf {', '.join(k.kaufen)}" + (f", dann {fuehren.kurz(h)}." if h is not None else "."), h
        if k is not None and getattr(k, "naechstes", None):
            item, fehlt = k.naechstes
            return f"Noch {fehlt} Gold bis {item}: erst farmen, dann back.", h
        return (f"Gerade nichts zu kaufen: {satz(h)}" if h is not None else None), h
    return None, None


def _kampf_antwort(kern, lagebild, h: Handlung | None) -> str:
    """Kampf-Fragen: das Modell ist nicht geeicht (Entscheidung 2) - ehrlich, und fehlender Flash ist eine Chance."""
    z = getattr(lagebild, "zauber", None)
    m = kern.m
    if z is not None and m is not None and m.b is not None:
        for g in m.b.gegner:
            if g.sichtbar and g.abstand is not None and g.abstand <= 2000 and z.fehlt(g.s, "SummonerFlash", m.zeit):
                return f"Ja: {g.champion} ohne Flash ist dein Ziel, geh rein, wenn er vorn steht."
    rest = f" Jetzt: {satz(h)}" if h is not None else ""
    return "Den Kampf rechnet der Coach noch nicht sicher, entscheide selbst." + rest


def _innere_frage(frage: str) -> str | None:
    """Eine Frage in einer Notiz ("Alle sind tot. Warum sagst du, ich soll zurueckgehen? ... Notieren.")."""
    teile = [t.strip() for t in re.split(r"(?<=[.!?])\s+", frage) if t.strip()]
    for t in teile:
        if NOTIER.search(t.lower()):
            continue
        a = absicht(t)
        if a in ("JETZT", "DANACH", "WARUM", "ENTWEDER", "SOLL_ICH", "LAGE", "TIMER", "WO", "KAUF") \
                and (t.endswith("?") or a in ("WARUM", "SOLL_ICH", "JETZT")):
            return t
    return None


def beantworte(kern, frage: str, p, lagebild=None) -> dict:
    """{"text": Antwort oder None (OFFEN - Claude), "absicht", "ziel" (vergleichbar, Buch 11, 7), "quelle": "kern"}."""
    m = kern.m
    zeit = m.zeit if m is not None else (p.zeit if p is not None else 0.0)
    a = absicht(frage)
    cfg = kern.cfg["fuehren"]
    letzte = getattr(kern, "_frage_letzte", None)
    # Anschlussfrage ("Und die anderen Gegner?") erbt die Absicht der vorigen
    if a == "OFFEN" and letzte is not None and zeit - letzte[0] <= cfg["antwort_wiederholung_s"] \
            and frage.strip().lower().startswith(("und ", "und?")):
        a = letzte[1]
    wiederholt = letzte is not None and letzte[1] == a and zeit - letzte[0] <= cfg["antwort_wiederholung_s"]
    kern._frage_letzte = (zeit, a)
    if a == "OFFEN" or m is None:
        return {"text": None, "absicht": a, "ziel": None, "quelle": "claude"}
    if a == "NOTIZ":
        innen = _innere_frage(frage)
        text, h = ("Notiert.", None)
        if innen is not None:
            t2, h = _antwort(kern, absicht(innen), innen, p, lagebild, zeit, False)
            if t2:
                text = f"Notiert. {t2}"
        return _abschluss(kern, text, "NOTIZ", h, zeit)
    text, h = _antwort(kern, a, frage, p, lagebild, zeit, wiederholt)
    if not text:
        return {"text": None, "absicht": a, "ziel": None, "quelle": "claude"}
    return _abschluss(kern, text, a, h, zeit)


def _abschluss(kern, text: str, a: str, h: Handlung | None, zeit: float) -> dict:
    """Buch 11, 5, Regeln 3 und 4: kein Widerspruch ohne "Neu:"; die Antwort gilt als gesagter Plan."""
    ziel = fuehren.ziel_label(h) if h is not None else None
    letztes = getattr(kern, "_letztes_ziel", None)
    if ziel and letztes is not None and letztes[1] and letztes[1] != ziel \
            and zeit - letztes[0] <= kern.cfg["fuehren"]["widerspruch_fenster_s"] \
            and a in ("JETZT", "DANACH", "WARUM") and not text.startswith(("Neu:", "Notiert")):
        text = f"Neu: {text}"
    p = kern.fuehrer.plan
    if h is not None and p is not None and h is p.handlung:
        p.gesagt = zeit
        kern._angesagt[(p.art, h.ziel.name if h.ziel else "")] = zeit
    if ziel:
        kern._letztes_ziel = (zeit, ziel)
    return {"text": text, "absicht": a, "ziel": ziel, "quelle": "kern"}
