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
# Auftrag 008, A4 (101426 26:45: "Ich weiss nie, wann wer wo ist ... keine Uebersicht"): das Lagebild auf Abruf
LAGE_KARTE = re.compile(r"überblick|ueberblick|übersicht|uebersicht|(^|[^a-zäöüß])lage\b|wo sind (alle|die|sie)|"
                        r"wer ist wo|wo steh(en|t) (alle|die gegner)|kartenlage")
FLASH = re.compile(r"flash|fläch|flaech")
TIMER = re.compile(r"wann (kommt|spawnt|ist)|timer|wie lange noch")
WO = re.compile(r"(^|[^a-zäöüß])(wo (ist|sind|steht|war)|wo's|wos )")
JETZT = re.compile(r"was mache ich|was mach ich|was jetzt|und jetzt|wo gehe? ich hin|wohin|was soll ich (jetzt|machen|tun)|"
                   r"was tue ich|was nun|welche welle|welche lane|was ist (der )?plan")
KORREKTUR_BASIS = re.compile(r"(ich (bin|war) (in der|in die) (base|basis))|(bin|war) in der base")
KORREKTUR_TOT = re.compile(r"(drache|herold|baron|larven)( ist)? (tot|weg|gemacht|down)")
KORREKTUR_BEI_MIR = re.compile(r"(ist|sind|war|waren) (jetzt |doch |direkt |nur )?(bei mir|neben mir|(ein paar|paar|"
                               r"wenige) meter (weg )?(von|neben|bei) mir)")
# Auftrag 008, A3.1 (101426 32:13/32:16: "ich bin schon tot seit 10 Sekunden", "ja, ich bin auch tot")
ICH_TOT = re.compile(r"(ich bin|bin) (schon |auch |doch |gerade )?tot")
KORREKTUR_ALLE_TOT = re.compile(r"alle (sind )?tot|sind (doch )?alle tot")
KORREKTUR_ORT = re.compile(r"(ich bin|bin) (jetzt )?(beim|am|an der|in der) (drache|drachen|baron|herold|larven|grube)")
# Auftrag 004, Teil C 4: eine Frage nach der Gewissheit ("Warum bist du dir so sicher, dass ...?")
GEWISSHEIT = re.compile(r"bist du (dir )?(so |ganz )?sicher|woher wei(ß|ss)t du|wie sicher|sicher, dass")
TURM_WORT = re.compile(r"turm|tower|türme|towers")
RAUS_WORT = re.compile(r"(^|[^a-zäöüß])(raus|zurück|zurueck|zurückgehen|zurueckgehen)([^a-zäöüß]|$)")
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
    if GEWISSHEIT.search(f):
        return "GEWISSHEIT"
    if WARUM_WORT.search(f) and WARUM_BEZUG.search(f):
        return "WARUM"
    if KAUF.search(f):
        return "KAUF"
    if FLASH.search(f):
        return "TIMER"
    if ENTWEDER.search(f) and len(optionen_in(f)) >= 2:
        return "ENTWEDER"
    if LAGE.search(f) or LAGE_KARTE.search(f):
        return "LAGE"
    if JETZT.search(f) or KORREKTUR_BASIS.search(f) or KORREKTUR_TOT.search(f) or KORREKTUR_BEI_MIR.search(f) \
            or KORREKTUR_ORT.search(f) or ICH_TOT.search(f):
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
    if p is not None and p.handlung.art == "KAUFEN" and kern.m is not None:
        # Auftrag 007, Teil D (213624 10:38: "Kauf Spitzhacke ..." nach dem Kauf): erledigt - dann das Ziel danach
        from .modi.basis import _gekauft
        if (p.schritt >= 1 or _gekauft(kern.m, p)) and p.handlung.daten.get("wohin") is not None:
            return p.handlung.daten["wohin"]
    if p is not None and not fuehren.stumm(p.handlung) and (p.handlung.satz or fuehren.stumm_satz(p.handlung)):
        return p.handlung
    sagbar = _sagbar(kern)
    return sagbar[0] if sagbar else None


def _respawn_plan(kern) -> str:
    """Auftrag 008, A3.1: tot bekommt den Respawn-Plan - Zeit, Kauf, Ziel -, nie "Farm deine Mid-Welle" (101426 32:07:
    "Soll ich zu meinem Turm?" 18 s nach dem Tod -> "Nein. Farm deine Mid-Welle"; 32:22: "Bist du behindert?")."""
    m = kern.m
    p = kern.fuehrer.plan
    h = p.handlung if p is not None else None
    zeit = f"Du lebst in {max(1, int(round(m.respawn)))} Sekunden wieder" if m is not None and m.respawn else \
        "Du lebst gleich wieder"
    s = satz(h) if h is not None and h.art in ("KAUFEN", "WOHIN", "WOHIN_TP_LANE") else ""
    if s:
        return f"{zeit}: {s[:1].lower()}{s[1:]}"
    k = getattr(m.b, "kauf", None) if m is not None and m.b is not None else None
    lane = (m.meine_lane if m is not None else None) or "deine Lane"
    if k is not None and getattr(k, "kaufen", None):
        return f"{zeit}: kauf {' und '.join(k.kaufen[:2])}, dann zurück auf {lane}."
    return f"{zeit}, dann zurück auf {lane}."


def _jetzt_satz(kern, h: Handlung | None) -> str:
    """Der Satz zum Plan - oder, gibt es keinen sagbaren, der Rueckfall: die eigene Welle."""
    if kern.m is not None and kern.m.tot:
        return _respawn_plan(kern)                    # Auftrag 008, A3.1
    s = satz(h)
    if s and not (h is not None and h.art in ("FARMEN", "HALTEN")):
        return s
    lane = kern.m.meine_lane if kern.m is not None and kern.m.meine_lane else "Top"
    # Auftrag 004, Teil C 3: keine Floskel - die Welle, dazu was als Naechstes kommt (Zeitleiste); Teil A 1: gefragt
    # auch bei einem Farm-Plan die beste Kampf-Option (213624 9:46: der innere Top-Turm stand schon zur Wahl)
    s = _mit_vorschau(kern, s or f"Farm deine {lane}-Welle.")
    # gefragt nennt der Coach auch die beste Option, die am ungeeichten Kampfmodell haengt - ehrlich als unsicher
    # (Buch 11, 1.8; ungefragt bleibt sie stumm, Entscheidung 2)
    # Auftrag 004: aus den ungefilterten Kandidaten (die modellstummen stehen nicht mehr in kern.kandidaten) - ohne
    # die, die eine Schranke dieses Takts nahm (Leben, p_tod, klar unterlegen)
    weg = {e.split(":", 1)[0] for e in getattr(kern, "_schranke_takt", None) or []}
    offen = next((x for x in sorted(getattr(kern, "kandidaten_roh", None) or kern.kandidaten or [], key=lambda x: -x.ev)
                  if fuehren.stumm(x) and not x.stumm and x.ziel is not None and x.art not in fuehren.NIE_DANACH
                  and x.art not in weg), None)
    if offen is not None:
        s += f" Oder {fuehren.kurz(offen)}, aber mit Kampf - unsicher."
    return s


def _mit_vorschau(kern, s: str) -> str:
    """Ein Farm-Satz bekommt das naechste Ereignis der Zeitleiste dazu ("Farm deine Top-Welle, Drache in 70 Sekunden.")."""
    m = kern.m
    if m is None:
        return s
    for e in kern.zeitleiste or []:
        n = e.in_s(m.zeit)
        if 5 <= n <= kern.cfg["fuehren"]["vorschau_horizont_s"] and e.art in ("objective", "respawn", "kauf", "tp", "buff"):
            return s.rstrip(".") + f", {e.text} in {n} Sekunden."
    return s


OBJ_KOPF = {"Drache": "Zum Drachen", "Baron": "Zum Baron", "Herold": "Zum Herold", "Larven": "Zu den Larven",
            "Ältester": "Zum Ältesten"}


def satz(h: Handlung | None) -> str:
    """Handlung + Ziel + Grund als ein Satz."""
    if h is None:
        return ""
    if h.stumm:
        return fuehren.stumm_satz(h)
    s = (h.satz or "").strip()
    if s:
        # Auftrag 005: als Antwort mit Richtung - "Zum Drachen mit Malzahar: ..." statt "Drache mit Malzahar: ..."
        kopf = re.match(r"^(Drache|Baron|Herold|Larven|Ältester) (mit|jetzt|allein)\b", s)
        if kopf:
            s = OBJ_KOPF[kopf.group(1)] + s[len(kopf.group(1)):]
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
    # Auftrag 005 (213624 12:56 "Keins von beiden ... Jetzt: Drache mit Malzahar"): der gehaltene Plan zaehlt zuerst -
    # er steht nicht in jedem Takt unter den Kandidaten (Objective-Plaene gelten ueber die Modi hinweg)
    p = kern.fuehrer.plan
    if p is not None and not p.handlung.stumm and _passt(p.handlung, option, kern.m):
        return p.handlung
    alle = sorted(getattr(kern, "kandidaten_roh", None) or kern.kandidaten or [], key=lambda h: -h.ev)
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
            # Auftrag 005 (213624 10:54, 11:38): kein geratener Grund - was der Kern weiss: Weg und wer von euch dort ist
            # Auftrag 007 (Klasse 6): dieselbe Zaehlung wie die Ansage (ueberlegen.koepfe)
            from .ueberlegen import koepfe, koepfe_satz
            weg = m.weg(o.pos) if o.pos is not None else None
            wer = koepfe_satz(*koepfe(m, o.pos, kern.cfg["ueberlegen"]["kampf_fenster_s"]))
            if m.bereich == "basis_eigen":
                return f"{wort}: du bist in der Basis, {wer}"
            return f"{wort}: du brauchst {int(weg)} Sekunden hin, {wer}" if weg is not None else f"{wort}: {wer}"
    if option == "kampf":
        return "Den Kampf rechnet der Coach noch nicht sicher"
    # Auftrag 004, Teil C 3: nie ohne Grund - aus den Schranken dieses Takts, sonst aus dem, was fehlt
    arten = {"turm": ("DRUECKEN", "MIT_GRUPPE", "PLATTEN"), "team": ("ZUR_GRUPPE", "MIT_GRUPPE")}.get(option, ())
    for eintrag in getattr(kern, "_schranke_takt", None) or []:
        art, _, warum = eintrag.partition(": ")
        if art in arten:
            if warum.startswith("Leben"):
                return f"Für {'einen ihrer Türme' if option == 'turm' else wort} fehlt dir Leben"
            if warum.startswith("p_tod"):
                return f"{'Ihr nächster Turm' if option == 'turm' else wort} ist gerade zu riskant"
            if warum.startswith("klar unterlegen"):
                return f"Dort sind sie klar stärker: {warum.split(', ', 1)[-1]}"
    if option == "turm":
        return "Keinen ihrer Türme nimmst du jetzt"
    if option == "team":
        return "Bei deinem Team ist gerade kein Kampf"
    if option == "back":
        return "Für Back fehlt der Grund: genug Leben, kein Kauf fällig"
    if option in ("top", "mid", "bot"):
        return f"Auf {wort} wartet gerade keine Welle, die sich lohnt"
    return f"Für {wort} sehe ich gerade kein Ziel"


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
    s = (f"Ihr {fuehrt} {max(kw, kd)} zu {min(kw, kd)}, ihr habt {tuerme_w} Türme, sie {tuerme_d}, "
         f"Drachen {len(p.drachen(wir))} zu {len(p.drachen(die))}, {abs(gold)} Gold {'vorn' if gold >= 0 else 'hinten'}.")
    h = _jetzt(kern)
    return s + (f" Jetzt: {satz(h)}" if h is not None else "")


# --- Antworten ----------------------------------------------------------------------------------------------------

def _antwort(kern, a: str, frage: str, p, lagebild, zeit: float, wiederholt: bool) -> tuple[str | None, Handlung | None]:
    f = frage.lower()
    m = kern.m
    h = _jetzt(kern)
    danach = kern.danach_text
    if m is not None and m.tot and a in ("JETZT", "SOLL_ICH", "ENTWEDER", "DANACH"):
        return _respawn_plan(kern), h                  # Auftrag 008, A3.1
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
        if (bei := _korrektur_bei_mir(kern, f, zeit, p)) is not None:
            return bei
        if (grube := _an_der_grube(kern, f, zeit)) is not None:
            return grube
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
        # Auftrag 004, Teil C 3: keine Floskel - nach einem Turm die naechste Struktur (Teil B, 16:42), sonst das
        # naechste Objective der Zeitleiste, sonst die Welle
        jetzt = fuehren.kurz(h) if h is not None else "der Welle"
        if TURM_WORT.search(f):
            weg = {e.split(":", 1)[0] for e in getattr(kern, "_schranke_takt", None) or []}
            c = next((x for x in sorted(getattr(kern, "kandidaten_roh", None) or [], key=lambda x: -x.ev)
                      if x.art in ("DRUECKEN", "MIT_GRUPPE", "PLATTEN") and x.art not in weg and x.ziel is not None
                      and (h is None or fuehren.ziel_label(x) != fuehren.ziel_label(h))), None)
            if c is not None:
                return f"Nach ihrem Turm: {_mit_vorbehalt(c)}", h
        for e in kern.zeitleiste or []:
            n = e.in_s(m.zeit)
            if 5 <= n <= 180 and e.art in ("objective", "buff", "inhib"):
                return f"Nach {jetzt}: {e.text} in {n} Sekunden, dann dorthin.", h
        lane = m.meine_lane or "Top"
        return f"Nach {jetzt}: zurück zu deiner {lane}-Welle.", h
    if a == "WARUM":
        k = getattr(m.b, "kauf", None) if m is not None and m.b is not None else None
        if re.search(r"kauf|item", f) and k is not None and getattr(k, "item", None):
            return f"Kauf {k.item}: der nächste Schritt aus deinem eigenen Build.", h
        if RAUS_WORT.search(f):
            return _warum_raus(kern, h, zeit), h
        genannt = _genannt(optionen_in(f), h, m)
        if genannt is None and (letzte := _letzte_ansage(kern, zeit)) is not None:
            # Auftrag 004, Teil C 1: "warum?" ohne Ziel meint die letzte gesprochene Ansage
            text = (f"Grund der letzten Ansage: {letzte['grund']}." if letzte["grund"]
                    else f"Die letzte Ansage kam aus dem Plan: {letzte['text']}")
            if h is not None and fuehren.ziel_label(h) not in letzte["text"].lower():
                text += f" Jetzt: {_jetzt_satz(kern, h)}"
            return text, h
        # Buch 4, 4 (Auftrag 008): zwei Saetze - die entscheidende Beobachtung, dann die Alternative (die genannte
        # oder die zweitbeste) mit ihrem konkreten Nachteil
        if h is None or m is None or m.tot:
            return _jetzt_satz(kern, h), h
        if genannt is not None:
            wort = OPTION_WORT.get(genannt, genannt)
            wort = wort[:1].upper() + wort[1:]
            c = _fuer_option(kern, genannt)
            if c is None:
                return f"{fuehren.warum_satz(h, None, m, kern.cfg)} {_warum_nicht(kern, genannt)}.", h
            if c.ev >= h.ev:
                return (f"{wort} geht auch: {c.grund or fuehren.kurz(c)}" + (
                    ", aber mit Kampf - unsicher." if fuehren.stumm(c) else ".")) + f" Jetzt: {_jetzt_satz(kern, h)}", h
            return fuehren.warum_satz(h, c, m, kern.cfg) + (" Und mit Kampf - unsicher." if fuehren.stumm(c) else ""), h
        alt = next((x for x in _sagbar(kern) if x is not h and fuehren.kurz(x) != fuehren.kurz(h)), None)
        return fuehren.warum_satz(h, alt, m, kern.cfg), h
    if a == "GEWISSHEIT":
        return _gewissheit(kern, f, p, h), h
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
            return (f"Nein. {_jetzt_satz(kern, h)} {_warum_nicht(kern, o)}." if o else _jetzt_satz(kern, h)), h
        if h is None:
            return f"Ja, geht: {_mit_vorbehalt(c)}", c
        if c is h or fuehren.kurz(c) == fuehren.kurz(h):
            return f"Ja: {_mit_vorbehalt(c)}", c
        schwelle = kern.cfg["plan"]["hysterese_ge"]
        if c.ev >= h.ev - schwelle:
            return f"Ja, geht auch: {_mit_vorbehalt(c)}", c
        return f"Nein, {fuehren.kurz(h)} bringt mehr: {h.grund or satz(h)}", h
    if a == "LAGE":
        k = getattr(kern, "kartenlage", None)
        if k is not None and m is not None and (LAGE_KARTE.search(f) or not LAGE.search(f)):
            from . import kartenlage
            vor = fuehren.kurz(h) if h is not None and h.art in ("NEHMEN", "BESTREITEN", "MIT_GRUPPE", "DRUECKEN",
                                                                 "ZUR_GRUPPE", "PLATTEN") else None
            return kartenlage.satz(k, m, plan_kurz=vor), h    # Auftrag 008, A4: wer wo, Flashs, Tote, Folgerung
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
        if (wo := _wo_gegner(kern, f)) is not None:
            return wo, None                               # Auftrag 008, A4: aus der Kartenlage, ohne Claude
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


def _wo_gegner(kern, f: str) -> str | None:
    """Auftrag 008, A4 (101426 19:24 "Wo's Twitch?" ging an Claude): wo er ist bzw. zuletzt war, wie alt, wie weit - und
    wann er bei dir sein kann."""
    m = kern.m
    if m is None or m.b is None:
        return None
    g = next((x for x in m.b.gegner if x.champion.lower().replace("'", "") in f.replace("'", "")
              or x.champion.lower().split()[0] in f.split()), None)
    if g is None:
        return None
    if g.s.tot:
        return f"{g.champion} ist tot, noch {int(g.s.respawn or 0)} Sekunden."
    if g.pos is None or g.seit is None:
        return f"{g.champion} habe ich noch nicht gesehen."
    weit = f", {int(round(g.abstand, -2))} von dir" if g.abstand is not None else ""
    bald = f", kann in {int(g.ankunft)} Sekunden bei dir sein" if g.ankunft is not None and g.ankunft <= 20 else ""
    if g.sichtbar:
        return f"{g.champion} ist zu sehen, {g.ort}{weit}{bald}."
    return f"{g.champion} war vor {int(g.seit)} Sekunden {g.ort}{weit}{bald}."


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
        # Auftrag 005 (213624 20:00, 21:03: "Dann kann ich als Riven ... entscheiden" -> "Nein."): nur echte Fragen -
        # mit Fragezeichen oder mit dem Fragewort vorn
        vorn = re.match(r"^(warum|wieso|weshalb|soll|sollte|kann|darf|was|wo|wohin|welche|wann|wie)\b", t.lower()) \
            or re.search(r"\b(soll|sollte) ich\b", t.lower())     # "Dann soll ich doch erst recht kaempfen" (23:45)
        if a in ("JETZT", "DANACH", "WARUM", "ENTWEDER", "SOLL_ICH", "LAGE", "TIMER", "WO", "KAUF") \
                and (t.endswith("?") or (vorn and a in ("WARUM", "SOLL_ICH", "JETZT"))):
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
    vorige = getattr(kern, "_frage_text_merken", None)
    kern._frage_text_letzte = vorige                       # die Frage davor (Auftrag 008, A3.4)
    kern._frage_text_merken = (zeit, frage.lower())
    if a == "OFFEN" or m is None:
        return {"text": None, "absicht": a, "ziel": None, "quelle": "claude"}
    if a == "NOTIZ":
        innen = _innere_frage(frage)
        text, h = ("Notiert.", None)
        if KORREKTUR_ALLE_TOT.search(frage.lower()):
            text = f"Notiert. {_alle_tot(kern)}"
        if innen is not None:
            t2, h = _antwort(kern, absicht(innen), innen, p, lagebild, zeit, False)
            if t2:
                text = f"{text} {t2}"
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
    kern._antwort_letzte = (zeit, text)
    return {"text": text, "absicht": a, "ziel": ziel, "quelle": "kern"}


# --- Auftrag 004, Teil C -----------------------------------------------------------------------------------------------

def _letzte_ansage(kern, zeit: float, arten: tuple = ()) -> dict | None:
    for e in reversed(getattr(kern, "_ansage_log", None) or []):
        if zeit - e["zeit"] > 60.0:
            break
        if e["kategorie"] in ("INFO_FLASH", "BESTAETIGUNG"):
            continue
        if not arten or e["art"] in arten:
            return e
    return None


def _warum_raus(kern, h: Handlung | None, zeit: float) -> str:
    """Auftrag 004, Teil C 1: "Warum soll ich raus?" - der Grund der letzten Rueckzugs-Ansage; sieht der Kern die Lage
    jetzt anders, sagt er es offen ("Das war zu vorsichtig: ...")."""
    from .ueberlegen import lage
    e = _letzte_ansage(kern, zeit, ("ZURUECK", "RAUS", "BACK_JETZT", "WELLE_UND_RAUS"))
    jetzt = _jetzt_satz(kern, h)
    if e is None:
        # nicht gesagt: warum nicht - der Lane-Gegner ist tot, du bist klar vorn, oder es kommt keiner
        m = kern.m
        warum = "es kommt keiner, der dich schlägt"
        if m is not None and m.b is not None:
            lane = m.b.lane
            if lane is not None and lane.s.tot:
                warum = f"{lane.champion} ist tot"
            elif m.pos is not None:
                u, grund = lage(m, kern.cfg, m.pos)
                if u == "ueberlegen":
                    warum = f"du bist klar vorn, {grund}"
        return f"Raus sage ich nicht: {warum}. {jetzt}"
    text = f"Raus hatte einen Grund: {e['grund']}." if e["grund"] else f"Raus kam: {e['text']}"
    m = kern.m
    u, grund = lage(m, kern.cfg, m.pos) if m is not None and m.pos is not None else (None, "")
    if u == "ueberlegen":
        text += f" Das war zu vorsichtig: {grund}. {jetzt}"
    elif h is not None and h.art in ("DRUECKEN", "MIT_GRUPPE", "NEHMEN", "PLATTEN", "ANNEHMEN", "TRADE", "ALL_IN"):
        text += f" Jetzt ist die Lage anders: {jetzt}"
    return text


def _gewissheit(kern, f: str, p, h: Handlung | None) -> str:
    """Auftrag 004, Teil C 4: was der Kern weiss und was nicht - "Sicher nicht: ich sehe die Grube nicht. Dein Team
    steht aber dort, also hin."."""
    m = kern.m
    jetzt = _jetzt_satz(kern, h)
    for o in ("drache", "baron", "herold", "larven"):
        if OPTION[o].search(f) and m is not None:
            x = next((y for y in m.objectives or [] if y.schl == o), None)
            wort = OPTION_WORT[o]
            if x is not None and x.lebt:
                team = _team_an(kern, x.pos)
                zusatz = (f" Dein Team steht aber dort, zu {team}, also hin." if team >= 2 else f" {jetzt}")
                return f"Sicher nicht: ob der {wort} bis dahin fällt, sehe ich erst, wenn er fällt.{zusatz}"
            if x is not None and not x.lebt:
                return f"Sicher: der {wort} spawnt erst in {int(x.spawn_in)} Sekunden, das steht im Spiel. {jetzt}"
    if m is not None and m.b is not None:
        for g in m.b.gegner:
            if g.champion.lower().split()[0] in f:
                if g.sichtbar:
                    return f"Sicher: {g.champion} ist gerade zu sehen. {jetzt}"
                if g.seit is not None:
                    return f"Sicher nicht: {g.champion} habe ich vor {int(g.seit)} Sekunden zuletzt gesehen. {jetzt}"
                return f"Sicher nicht: {g.champion} habe ich noch nicht gesehen. {jetzt}"
    return f"Sicher nicht: ich rechne mit dem, was die Minimap zeigt. {jetzt}"


def _team_an(kern, ort) -> int:
    """Wer von euch schon an `ort` steht - dieselbe Zaehlung wie ueberall (Auftrag 007, Klasse 6)."""
    from .ueberlegen import koepfe
    m = kern.m
    if m is None or m.b is None or ort is None:
        return 0
    return koepfe(m, ort, 0.0)[0]


def _an_der_grube(kern, f: str, zeit: float):
    """Auftrag 004, Teil C 5: an der Grube mit Team kommt nie "Farm Top" - das Objective, oder mit Grund, dass es ohne
    dich laeuft. "ich bin beim Drachen" setzt den Ort (Korrektur)."""
    from ..bewertung import abstand
    m = kern.m
    if m is None:
        return None
    ort_k = KORREKTUR_ORT.search(f)
    if ort_k:
        schl = next((o for o in ("drache", "baron", "herold", "larven") if OPTION[o].search(ort_k.group(0))), None)
        if schl:
            k = getattr(kern, "korrekturen", None)
            if k is None:
                kern.korrekturen = k = {}
            k["ort"] = (schl, zeit)
    for x in m.objectives or []:
        if not x.lebt or x.pos is None:
            continue
        dort = (ort_k and OPTION[x.schl].search(ort_k.group(0))) or (m.bereich or "").startswith("grube:") \
            and m.pos is not None and abstand(m.pos, x.pos) <= 2500
        if not dort:
            continue
        team = _team_an(kern, x.pos)
        if team < 2 and not ort_k:
            continue
        wort = OPTION_WORT[x.schl]
        c = _fuer_option(kern, x.schl)
        if c is not None:
            am = {"drache": "am Drachen", "baron": "am Baron", "herold": "am Herold", "larven": "an den Larven"}
            grund = c.grund or (c.satz.split(": ", 1)[1].rstrip(".") if c.satz and ": " in c.satz else "")
            vorbehalt = ", aber mit Kampf - unsicher." if fuehren.stumm(c) else "."
            return f"Bleib mit deinem Team {am.get(x.schl, wort)}" + (f": {grund}" if grund else "") + vorbehalt, c
        return (f"Der {wort} läuft ohne dich: dein Team ist zu {team} dort. {_jetzt_satz(kern, _jetzt(kern))}",
                _jetzt(kern))
    return None


def _korrektur_bei_mir(kern, f: str, zeit: float, p):
    """Auftrag 004, Teil C 2: "Der ist jetzt bei mir oben" setzt die Sichtung des zuletzt genannten Gegners auf deinen
    Ort (korrektur_gilt_s) - die Antwort kommt aus der korrigierten Lage."""
    from .kampf import gegner_werte
    if not KORREKTUR_BEI_MIR.search(f):
        return None
    m = kern.m
    if m is None or m.b is None or p is None or p.ich is None:
        return None
    namen = {g.champion: g for g in m.b.gegner}
    # Auftrag 008, A3.4 (101426 19:38: "Er war ein paar Meter weg von mir" nach "Wo's Twitch?"): wen "er" meint, steht
    # in dieser Frage, der vorigen Frage, der letzten Antwort oder den Ansagen der letzten 60 s - in dieser Reihenfolge
    texte = [f] + [x[1] for x in (getattr(kern, "_frage_text_letzte", None), getattr(kern, "_antwort_letzte", None))
                   if x is not None and zeit - x[0] <= 60.0] \
        + [e["text"] for e in reversed(getattr(kern, "_ansage_log", None) or [])]
    g = next((namen[n] for t in texte for n in namen if n.lower() in t.lower()), None)
    if g is None:
        return None
    k = getattr(kern, "korrekturen", None)
    if k is None:
        kern.korrekturen = k = {}
    k["bei_mir"] = (g.champion, zeit)
    level, gold, _ = gegner_werte(g, m, kern.cfg["kampf"])
    vor_l, vor_g = p.ich.level - level, p.ich.item_gold - gold
    leben = m.leben or 0.0
    if re.search(r"(^|[^a-zäöüß])(war|waren) ", f) and not re.search(r"(ist|sind) (jetzt )?bei mir", f):
        # Vergangenheit (101426 19:38: "Er war ein paar Meter weg von mir"): die Lage war falsch - offen sagen, dann jetzt
        return f"Stimmt, {g.champion} war bei dir, das hat die Karte zu spät gezeigt. Jetzt: {_jetzt_satz(kern, _jetzt(kern))}", None
    if leben >= 0.6 and (vor_l >= 3 or (vor_l >= 2 and vor_g >= 1500)):
        return f"Stimmt, {g.champion} ist bei dir: nimm den Kampf, Level {p.ich.level} gegen {level}.", None
    from .sprache import unter
    ort = m.b.sicherer_ort()[0] if m.b is not None else "deiner Basis"
    if vor_l <= -2 or leben < 0.4:
        return f"Dann zurück {unter(ort)}: {g.champion} ist bei dir.", None
    return f"Stimmt, {g.champion} ist bei dir: bleib nah an deinem Turm, dort hilft er dir.", None


def _alle_tot(kern) -> str:
    """Auftrag 004, Teil C 2: "Alle sind tot" ist ein Abgleich mit den Toten."""
    m = kern.m
    if m is None or m.b is None:
        return ""
    leben = [g.champion for g in m.b.gegner if not g.s.tot]
    if not leben:
        return "Stimmt, alle tot."
    return f"Nicht alle: {liste(leben)} {'lebt' if len(leben) == 1 else 'leben'}."


def liste(teile: list[str]) -> str:
    return teile[0] if len(teile) == 1 else ", ".join(teile[:-1]) + " und " + teile[-1]
