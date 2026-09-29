"""Faehigkeitsformeln aller Champions von CommunityDragon -> wissen/faehigkeiten/cdragon.json (einmal je Patch).

Je Champion die vier Faehigkeiten (Q W E R) mit Grundwerten je Rang, Effektwerten und den Rechnungen, die der
Tooltip als Schaden auszeichnet (<physicalDamage>{{ Name }}</physicalDamage>, magicDamage, trueDamage). Nicht
ausgezeichnete Rechnungen (Schilde, Heilung, Boni) fallen weg. Rechnen: lolcoach/faehigkeiten.py.

    python werkzeuge/faehigkeiten_holen.py            # alle Champions aus Data Dragon (~15 MB Download)
    python werkzeuge/faehigkeiten_holen.py Riven Zed  # nur diese (zum Pruefen)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))
from lolcoach import ddragon  # noqa: E402

CDRAGON = "https://raw.communitydragon.org/latest/game"
TEXTE = f"{CDRAGON}/en_us/data/menu/en_us/lol.stringtable.json"
ZIEL = HIER / "wissen" / "faehigkeiten" / "cdragon.json"
PUFFER = HIER / "daten" / "cdragon" / "bin"
TAG = re.compile(r"<(physicalDamage|magicDamage|trueDamage)>(.*?)</\1>", re.S | re.I)
VAR = re.compile(r"@([A-Za-z0-9_.]+)(\*[\d.]+)?@(%?)")
ART = {"physicaldamage": "physisch", "magicdamage": "magisch", "truedamage": "wahr"}
# "@BonusAD@ Attack Damage" (Rivens R) steht im Schadens-Tag, ist aber ein Bonus auf Werte, kein Schaden
KEIN_SCHADEN = re.compile(r"attack damage|ability power|armor|magic resist|attack speed", re.I)
# Nunus Q frisst Vasallen fuer 1200 wahren Schaden, Volibears R trifft Tuerme - gegen Champions gilt das nicht.
# Dazu alles, was am Ziel haengt (Prozent seines Lebens), je Sekunde/Tick zaehlt, nur unter Bedingung faellt
# (Wand, Mitte, verstaerkt, Krit) oder gar kein Schaden ist (Annies E wirft zurueck, "ManaRestore", "ADRatioBonus")
NICHT_SICHER = re.compile(r"monster|minion|tower|turret|structure|max|percent|health|hp|persecond|dps|pertick|dot|"
                          r"wallhit|sweetspot|empower|^emp|crit|return|restore|ratio", re.I)
# "bis zu @MaximumDamage@" (Nunus R, voll kanalisiert), "insgesamt @TotalDamage@ ueber 2,5 s" (Vel'Koz R): nur,
# wenn alles klappt - keine Untergrenze
OBERGRENZE = re.compile(r"up to|a total of|over the duration|per second", re.I)
UEBER_ZEIT = re.compile(r"^\s*(over|per second|each second)", re.I)   # "... magic damage over 5 seconds"


def _hole(url: str, datei: Path | None = None) -> bytes:
    if datei is not None and datei.exists():
        return datei.read_bytes()
    roh = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LoLCoach"}),
                                 timeout=30).read()
    if datei is not None:
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_bytes(roh)
    return roh


def texte() -> dict[str, str]:
    d = json.loads(_hole(TEXTE, PUFFER / "lol.stringtable.json"))
    eintraege = d.get("entries", d)
    return {k.lower(): v for k, v in eintraege.items() if isinstance(v, str)}


def _aufloesen(text: str, tt: dict[str, str], tiefe: int = 0) -> str:
    """Eingebettete Texte einsetzen: Syndras Q sagt 'dealing {{Spell_SyndraQ_Damage_0}}', Kha'Zix
    '{{Spell_KhazixQ_Tooltip_@IsEvolved@}}' (unentwickelt = 0)."""
    if tiefe > 3:
        return text

    def ersetze(m):
        schl = re.sub(r"@[^@]*@", "0", m.group(1)).strip().lower()
        return _aufloesen(tt.get(schl, ""), tt, tiefe + 1)

    return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", ersetze, text)


def _abhaengig(calcs: dict, name: str, gesehen: set) -> None:
    """Rechnungen, auf die eine Rechnung verweist (GameCalculationModified), mitnehmen."""
    if name in gesehen or name not in calcs:
        return
    gesehen.add(name)
    r = calcs[name]
    if isinstance(r, dict) and r.get("mModifiedGameCalculation"):
        _abhaengig(calcs, r["mModifiedGameCalculation"], gesehen)


GRUNDWERTE = HIER / "wissen" / "grundwerte.json"
# Data Dragon 16.19.1 hat attackdamageperlevel = 0 fuer ALLE Champions (Live-API: Rivens AD steigt von Level 1 auf 3
# um 2,16 und 2,27 - genau Riots Formel mit 3,0). Die Spieldaten haben die echten Werte.
FELDER = {"attackdamage": "baseDamageModifiable", "attackdamageperlevel": "damagePerLevelModifiable",
          "hp": "baseHPModifiable", "hpperlevel": "hpPerLevelModifiable", "armor": "baseArmorModifiable",
          "armorperlevel": "armorPerLevelModifiable", "spellblock": "baseMR", "spellblockperlevel": "mrPerLevel"}


def grundwerte(cid: str) -> dict | None:
    klein = cid.lower()
    bin_ = json.loads(_hole(f"{CDRAGON}/data/characters/{klein}/{klein}.bin.json", PUFFER / f"{klein}.bin.json"))
    wurzel = next((v for k, v in bin_.items() if k.lower() == f"characters/{klein}/characterrecords/root"), None)
    if not isinstance(wurzel, dict):
        return None
    aus = {}
    for dd, cd in FELDER.items():
        v = wurzel.get(cd)
        v = v.get("baseValue") if isinstance(v, dict) else v
        if isinstance(v, (int, float)):
            aus[dd] = round(float(v), 4)
    return aus


def champion(cid: str, tt: dict[str, str]) -> dict | None:
    klein = cid.lower()
    bin_ = json.loads(_hole(f"{CDRAGON}/data/characters/{klein}/{klein}.bin.json", PUFFER / f"{klein}.bin.json"))
    wurzel = next((v for k, v in bin_.items() if k.lower() == f"characters/{klein}/characterrecords/root"), None)
    if not isinstance(wurzel, dict):
        return None
    faehigkeiten = {k: v for k, v in bin_.items() if isinstance(v, dict) and v.get("mRootSpell")}
    aus = {}
    for slot, pfad in zip("QWER", wurzel.get("spells", [])):
        objekt = next((v for v in faehigkeiten.values() if v.get("mRootSpell") == pfad), None)
        pfade = [pfad] + [p for p in (objekt or {}).get("mChildSpells", []) if p != pfad]
        werte, effekte, calcs, schluessel = {}, [], {}, []
        for i, p in enumerate(pfade):
            s = (bin_.get(p) or {}).get("mSpell") or {}
            for dv in s.get("DataValues", []) or []:
                werte.setdefault(dv.get("name"), dv.get("values", []))
            if i == 0:
                effekte = [e.get("value", []) for e in s.get("mEffectAmount", []) or []]
            for name, r in (s.get("mSpellCalculations") or {}).items():
                calcs.setdefault(name, r)
            k = (((s.get("mClientData") or {}).get("mTooltipData") or {}).get("mLocKeys") or {}).get("keyTooltip")
            if k:
                schluessel.append(k.lower())
        # Nur der Tooltip der Hauptfaehigkeit, und darin nur der ERSTE echte Schadenswert: weitere sind oft
        # Alternativen ("@TotalDamage@ ... @PassThroughDamage@" bei Zeds Q = voller und verminderter Schaden,
        # "@MinDamage@ bis @MaxDamage@" bei Rivens R) - zusammengezaehlt waere es zu viel. Eine Untergrenze.
        schaden, gesehen = [], set()
        text = _aufloesen(next((tt[x] for k in schluessel[:1] for x in (f"generatedtip_{k}", k) if x in tt), ""), tt)
        for m in TAG.finditer(text):
            tag, inhalt = m.group(1), m.group(2)
            davor = re.sub(r"<[^>]+>", "", text[max(0, m.start() - 60):m.start()]) + inhalt
            danach = re.sub(r"<[^>]+>", "", text[m.end():m.end() + 40])
            if schaden or KEIN_SCHADEN.search(inhalt) or OBERGRENZE.search(davor) or UEBER_ZEIT.search(danach):
                continue
            for name, faktor, prozent in VAR.findall(inhalt):
                if faktor or prozent:            # "@ExecuteDamage*100@% fehlendes Leben": braucht das Ziel
                    continue
                name = name.split(":")[-1]       # "@spell.GnarQ:MiniTotalDamage@"
                if NICHT_SICHER.search(name):
                    continue
                if name in calcs:
                    _abhaengig(calcs, name, gesehen)
                elif name in werte:
                    calcs[name] = {"__type": "GameCalculation", "mFormulaParts": [
                        {"__type": "NamedDataValueCalculationPart", "mDataValue": name}]}
                    gesehen.add(name)
                elif (m := re.fullmatch(r"Effect(\d+)Amount", name)) and effekte:
                    calcs[name] = {"__type": "GameCalculation", "mFormulaParts": [
                        {"__type": "EffectValueCalculationPart", "mEffectIndex": int(m.group(1))}]}
                    gesehen.add(name)
                else:
                    continue
                schaden.append((name, ART[tag.lower()]))
                break
        aus[slot] = {"werte": werte, "effekte": effekte, "rechnungen": {n: calcs[n] for n in gesehen},
                     "schaden": schaden}
    return aus


def main(namen: list[str]) -> None:
    tt = texte()
    alle = json.loads(ZIEL.read_text(encoding="utf-8")) if ZIEL.exists() and namen else {}
    ids = namen or sorted(ddragon.champions())
    ohne = []
    for cid in ids:
        try:
            fa = champion(cid, tt)
        except Exception as e:     # ein fehlender Champion haelt die anderen nicht auf
            print(f"{cid}: {type(e).__name__}: {e}")
            fa = None
        if not fa:
            ohne.append(cid)
            continue
        alle[cid] = fa
        leer = [s for s, f in fa.items() if not f["schaden"]]
        if leer:
            ohne.append(f"{cid}({''.join(leer)})")
        time.sleep(0.05)
    ZIEL.write_text(json.dumps(alle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    werte = json.loads(GRUNDWERTE.read_text(encoding="utf-8")) if GRUNDWERTE.exists() and namen else {}
    for cid in ids:
        if g := grundwerte(cid):
            werte[cid] = g
    GRUNDWERTE.write_text(json.dumps(werte, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    print(f"{len(alle)} Champions -> {ZIEL} ({ZIEL.stat().st_size // 1024} KB); ohne Schadensteil: {', '.join(ohne)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
