"""Generalprobe: der komplette Live-Weg ohne League of Legends.

Ein nachgebauter Spielclient liefert die Live-API aus einer Aufnahme (in Echtzeit),
ein randloses Fenster mit dem Titel des Spielfensters zeigt an der echten Stelle
die aufgezeichneten Bilder: das Spielbild (schirm_*.jpg, alle 5 s) in der 16:9-Mitte,
die Minimap (1/s, volle Aufloesung) genau dort, wo der Coach sie sucht. Ist das Fenster
breiter als 16:9 (Carlos' 7680 x 2160, randlos = ganzer Schirm), kommen Mitspieler-Leiste
und Chat an die Raender - so sitzt das HUD von League auf 32:9. Der Coach laeuft als
eigener Prozess dagegen - mit Bildschirmaufnahme, Verfolger, Mitspieler-Leiste, Regeln,
Dashboard, Speichern. Aufnahmen landen in
`aufnahmen_probe/`. Am Ende: Takt, Minimap gefunden, HUD gelesen, Fehler, CPU und Speicher
des Coach-Prozesses (und seiner fleissigsten Faeden), Flash-Clips.

Bildschirm aus (Energiesparen): die Desktop-Duplizierung liefert dann kein einziges Bild.
Die Probe merkt das und laesst den Coach per GDI sehen (`LOLCOACH_KAMERA=gdi`) - der Takt
ist dann eine Untergrenze, GDI kostet ein Vielfaches (Auftrag 007, C1).

    python werkzeuge/generalprobe.py [--aufnahme ...] [--ab 13] [--minuten 2.5] [--breite 7680]
                                     [--ohne-gehirn] [--gdi]
"""
import argparse
import bisect
import ctypes
import gzip
import json
import os
import subprocess
import sys
import threading
import time

os.environ.pop("LOLCOACH_API", None)             # Sparprotokoll (Buch 16, 2)
os.environ.pop("LOLCOACH_API_BUDGET", None)


def probe_umgebung(umgebung: dict) -> dict:
    """Die Umgebung des Probe-Coachs: ohne LOLCOACH_API und ohne Budget (entfernt, nicht nur nicht gesetzt)."""
    return {k: v for k, v in umgebung.items() if k not in ("LOLCOACH_API", "LOLCOACH_API_BUDGET")}
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from lolcoach import aufzeichnung, hud, lage, minimap  # noqa: E402

TITEL = "League of Legends (TM) Client"
HOEHE = 2160              # die Probebilder sind bei 4K-Hoehe aufgenommen (Minimap 764 px bei MinimapScale 2,91)


class Uhr:
    """Bildet die Wanduhr der Aufnahme auf jetzt ab."""

    def __init__(self, start_w: float):
        self.start_w, self.t0, self.ende = start_w, time.time(), False

    def jetzt_w(self) -> float:
        return self.start_w + (time.time() - self.t0)


def server(schnappschuesse, uhr: Uhr) -> ThreadingHTTPServer:
    ws = [w for w, _ in schnappschuesse]

    class Anfrage(BaseHTTPRequestHandler):
        def do_GET(self):
            i = bisect.bisect_right(ws, uhr.jetzt_w()) - 1
            if uhr.ende or i < 0 or self.path != "/liveclientdata/allgamedata":
                self.send_response(404)
                self.end_headers()
                return
            koerper = json.dumps(schnappschuesse[i][1]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(koerper)

        def log_message(self, *a):
            pass

    s = ThreadingHTTPServer(("127.0.0.1", 0), Anfrage)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# --- Messung am Coach-Prozess (nur Zaehler von Windows: Zeiten und Arbeitsspeicher, kein Speicherlesen) ---

class _Speicher(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
        (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                       "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                                       "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]


class _Faden(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ThreadID", wintypes.DWORD),
                ("th32OwnerProcessID", wintypes.DWORD), ("tpBasePri", ctypes.c_long),
                ("tpDeltaPri", ctypes.c_long), ("dwFlags", wintypes.DWORD)]


def _zeiten(griff, fn) -> float:
    a, b, k, u = (ctypes.c_ulonglong() for _ in range(4))
    if not fn(griff, ctypes.byref(a), ctypes.byref(b), ctypes.byref(k), ctypes.byref(u)):
        return 0.0
    return (k.value + u.value) / 1e7


def messpunkt(pid: int) -> dict:
    """CPU-Sekunden des Prozesses und je Faden, Arbeitsspeicher jetzt und Spitze."""
    k32 = ctypes.windll.kernel32
    aus = {"wand": time.time(), "cpu": 0.0, "faeden": {}, "ws": 0, "ws_spitze": 0}
    p = k32.OpenProcess(0x1000, False, pid)       # PROCESS_QUERY_LIMITED_INFORMATION
    if p:
        aus["cpu"] = _zeiten(p, k32.GetProcessTimes)
        m = _Speicher()
        m.cb = ctypes.sizeof(m)
        if k32.K32GetProcessMemoryInfo(p, ctypes.byref(m), m.cb):
            aus["ws"], aus["ws_spitze"] = m.WorkingSetSize, m.PeakWorkingSetSize
        k32.CloseHandle(p)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    schnapp = k32.CreateToolhelp32Snapshot(0x4, 0)   # TH32CS_SNAPTHREAD
    f = _Faden()
    f.dwSize = ctypes.sizeof(f)
    ok = k32.Thread32First(wintypes.HANDLE(schnapp), ctypes.byref(f))
    while ok:
        if f.th32OwnerProcessID == pid:
            t = k32.OpenThread(0x0800, False, f.th32ThreadID)   # THREAD_QUERY_LIMITED_INFORMATION
            if t:
                aus["faeden"][f.th32ThreadID] = _zeiten(t, k32.GetThreadTimes)
                k32.CloseHandle(t)
        ok = k32.Thread32Next(wintypes.HANDLE(schnapp), ctypes.byref(f))
    k32.CloseHandle(wintypes.HANDLE(schnapp))
    return aus


def duplizierung_liefert(fenster, kamera_box=(0, 0, 64, 64), dauer: float = 1.5) -> bool:
    """Kommt ueber die Desktop-Duplizierung ein neues Bild? Das Probefenster flackert dafuer kurz."""
    try:
        k = lage._Kamera()
    except Exception:
        return False
    if k._dx is None:
        return False
    ende, n = time.time() + dauer, 0
    try:
        while time.time() < ende:
            n += 1
            fenster.configure(bg="#101010" if n % 2 else "black")
            fenster.update()
            if k.hole(kamera_box) is not None:
                return True
            time.sleep(0.02)
        return False
    finally:
        fenster.configure(bg="black")
        try:
            k._dx.release()
        except Exception:
            pass


def _zeilen(pfad: Path):
    """Zeilen eines .jsonl.gz, auch wenn es abgeschnitten ist (Coach beendet, bevor er schloss)."""
    try:
        with gzip.open(pfad, "rt", encoding="utf-8") as f:
            for z in f:
                try:
                    yield json.loads(z)
                except ValueError:
                    continue
    except (OSError, EOFError):
        return


def auswerten(stamm: Path, log_text: str, messung: tuple[dict, dict] | None) -> None:
    """Die Kennzahlen der Probe aus dem, was der Coach geschrieben hat."""
    import numpy as np
    bilder = stamm.with_name(stamm.name + "_bilder")
    ws, mit = [], 0
    for d in _zeilen(bilder / "sichtungen.jsonl.gz"):
        ws.append(d["w"])
        mit += bool(d["s"])
    print("\n=== Generalprobe: Auswertung ===")
    if len(ws) > 10:
        ws_ = np.array(ws)
        _, je = np.unique(np.floor(ws_ - ws_[0]), return_counts=True)
        je = je[1:-1] if len(je) > 2 else je
        print(f"Takt (Minimap-Bilder/s): Mittel {len(ws) / (ws[-1] - ws[0]):.1f}, Median {np.median(je):.0f}, "
              f"5-%-Quantil {np.percentile(je, 5):.0f}, schlechteste Sekunde {je.min()}")
        print(f"Minimap gefunden: {mit}/{len(ws)} Bilder mit Sichtungen ({100 * mit / len(ws):.0f} %)")
    else:
        print(f"Takt: nur {len(ws)} Minimap-Bilder - der Beobachter hat nichts gesehen")
    arten: dict[str, int] = {}
    hud_mit = 0
    for d in _zeilen(bilder / "ereignisse.jsonl.gz"):
        arten[d["art"]] = arten.get(d["art"], 0) + 1
        if d["art"] == "hud" and any((m[0] or 0) > 0.05 for m in d["m"]):
            hud_mit += 1
    print(f"HUD (Mitspieler-Leiste): {arten.get('hud', 0)} gelesen, davon {hud_mit} mit Leben > 0; "
          f"eigene Tasten {arten.get('eigene', 0)}, Balkenspur-Bilder {arten.get('balkenspur', 0)}, "
          f"Spruenge Minimap/Spielbild {arten.get('sprung', 0)}/{arten.get('schirm_sprung', 0)}")
    # 28.09.: 148 Minimap-Spruenge in 2,5 min - die Aufnahme hat 1 Bild/s, dazwischen steht die Karte (Puls) still:
    # jeder Sekundenschritt sieht aus wie ein Flash. Echte Partien: 11-16 je Partie.
    print("  (Minimap-Spruenge und ihre Clips sind hier Artefakt: 1 Aufnahmebild/s, dazwischen ruht die Karte)")
    clips = stamm.with_name(stamm.name + "_flashclips")
    if clips.exists():
        n = [c for c in clips.iterdir() if c.is_dir()]
        mb = sum(b.stat().st_size for c in n for b in c.iterdir()) / 1e6
        print(f"Flash-Clips: {len(n)} in {clips.name} ({mb:.1f} MB)")
    else:
        print("Flash-Clips: keiner (kein Sprung, kein Blitz-Ping)")
    fehler = [z for z in log_text.splitlines() if "letzter Fehler" in z or "Traceback" in z]
    print("Fehler: " + ("; ".join(fehler) if fehler else "keine"))
    if messung:
        a, b = messung
        dt = b["wand"] - a["wand"]
        faeden = sorted(((b["faeden"][t] - a["faeden"].get(t, 0.0)) / dt for t in b["faeden"]), reverse=True)
        print(f"Coach-Prozess ueber {dt:.0f} s: CPU {100 * (b['cpu'] - a['cpu']) / dt:.0f} % eines Kerns "
              f"({os.cpu_count()} Kerne), fleissigste Faeden " + ", ".join(f"{100 * x:.0f} %" for x in faeden[:4])
              + f"; Arbeitsspeicher {b['ws'] / 1e6:.0f} MB (Spitze {b['ws_spitze'] / 1e6:.0f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aufnahme", default=str(WURZEL / "aufnahmen" / "2026-09-27_164326.jsonl.gz"))
    ap.add_argument("--ab", type=float, default=13.0, help="Spielminute, ab der die Probe laeuft")
    ap.add_argument("--minuten", type=float, default=2.5)
    ap.add_argument("--ohne-gehirn", action="store_true")
    ap.add_argument("--gdi", action="store_true", help="Coach sieht per GDI (sonst nur bei ausgeschaltetem Schirm)")
    schirm_b = ctypes.windll.user32.GetSystemMetrics(0)
    ap.add_argument("--breite", type=int, default=schirm_b, help="Fensterbreite (randlos = ganzer Schirm)")
    ap.add_argument("--links", type=int, default=None, help="Fensterposition (Standard: mittig)")
    args = ap.parse_args()
    breite = args.breite
    links = max(0, (schirm_b - breite) // 2) if args.links is None else args.links

    alle = list(aufzeichnung.lies_mit_zeit(args.aufnahme))
    start_i = next(i for i, (_, d) in enumerate(alle) if d["gameData"]["gameTime"] >= args.ab * 60)
    karten = aufzeichnung.bilder(args.aufnahme)
    schirme = aufzeichnung.bildschirme(args.aufnahme)
    if not karten:
        sys.exit(f"{args.aufnahme}: keine Minimap-Bilder mehr (aufgeraeumt) - eine der letzten Partien nehmen")
    karten_ws, schirm_ws = [w for w, _ in karten], [w for w, _ in schirme]

    import tkinter as tk
    from PIL import Image, ImageTk
    fenster = tk.Tk()
    fenster.title(TITEL)
    fenster.overrideredirect(True)
    fenster.geometry(f"{breite}x{HOEHE}+{links}+0")
    fenster.configure(bg="black")
    fenster.attributes("-topmost", True)
    fenster.update()

    gdi = args.gdi or os.environ.get("LOLCOACH_KAMERA", "").lower() == "gdi"
    if not gdi and not duplizierung_liefert(fenster):
        gdi = True
        print("Bildschirm aus oder Duplizierung stumm: kein neues Bild in 1,5 s - der Coach sieht per GDI. "
              "Der Takt ist dann eine Untergrenze; fuer den echten Weg mit eingeschaltetem Schirm wiederholen.")

    ml, mb = lage.spielbild(breite, HOEHE)
    k = minimap.faktor()
    kl, ko, kr, ku = minimap.kartenrechteck(breite, HOEHE, k)
    hinter = tk.Label(fenster, bg="black", bd=0)
    hinter.place(x=ml, y=0, width=mb, height=HOEHE)
    ecke = chat = None
    if ml > 0:   # 32:9: League klebt Mitspieler-Leiste und Chat an die Raender
        ecke = tk.Label(fenster, bg="black", bd=0)
        ecke.place(x=breite - hud.ECKE, y=HOEHE - hud.ECKE, width=hud.ECKE, height=hud.ECKE)
        ca, cb, cc, cd = lage.CHAT
        chat_box = (int(ca * mb), int(cb * HOEHE), int(cc * mb), int(cd * HOEHE))
        chat = tk.Label(fenster, bg="black", bd=0)
        chat.place(x=chat_box[0], y=chat_box[1], width=chat_box[2] - chat_box[0], height=chat_box[3] - chat_box[1])
    karte = tk.Label(fenster, bg="black", bd=0)
    karte.place(x=kl, y=ko, width=kr - kl, height=ku - ko)
    # Im Spiel aendert sich die Minimap in jedem Bild; die Aufnahme hat eins je Sekunde, und der Verfolger
    # ueberspringt pixelgleiche Bilder - dann zaehlte die Probe als Takt nur 1/s. Ein Punkt in der Ecke oben links
    # (Rand, kein Icon dort) wechselt deshalb alle 15 ms die Farbe: jeder Takt sieht ein neues Bild.
    puls = tk.Label(fenster, bg="#000000", bd=0)
    puls.place(x=kl + 1, y=ko + 1, width=2, height=2)

    uhr = Uhr(alle[start_i][0])
    srv = server(alle, uhr)
    basis = f"http://127.0.0.1:{srv.server_port}"
    ordner = WURZEL / "aufnahmen_probe"
    ordner.mkdir(exist_ok=True)
    vorher = set(ordner.glob("*.jsonl.gz"))
    log = open(ordner / "generalprobe.log", "w", encoding="utf-8")
    befehl = [sys.executable, "-m", "lolcoach", "--basis", basis, "live", "--stumm", "--ohne-sprache"]
    if args.ohne_gehirn:
        befehl.append("--ohne-gehirn")
    umgebung = {**os.environ, "LOLCOACH_AUFNAHMEN": str(ordner), "PYTHONUNBUFFERED": "1"}
    umgebung = probe_umgebung(umgebung)          # Sparprotokoll: der Probe-Coach nie ueber die API
    if gdi:
        umgebung["LOLCOACH_KAMERA"] = "gdi"
    coach = subprocess.Popen(befehl, cwd=WURZEL, stdout=log, stderr=subprocess.STDOUT, env=umgebung)
    print(f"Probe: Fenster {breite}x{HOEHE}+{links}+0 (Spielbild {mb} breit ab {ml}, Minimap {kr - kl} px bei "
          f"{kl},{ko}), Kamera {'GDI' if gdi else 'Desktop-Duplizierung'}, API {basis}, Coach-PID {coach.pid}")

    zustand = {"k": -1, "s": -1, "fotos": {}, "mess": []}
    beginn = time.time()
    ende = beginn + args.minuten * 60

    def pulsieren(n=[0]):
        n[0] += 1
        try:
            puls.configure(bg="#%02x%02x%02x" % (n[0] % 7 * 9, n[0] % 5 * 9, n[0] % 3 * 9))
            fenster.after(15, pulsieren)
        except tk.TclError:
            pass     # Fenster zu

    fenster.after(15, pulsieren)

    def zeige(label, bild, schluessel):
        zustand["fotos"][schluessel] = ImageTk.PhotoImage(bild)
        label.configure(image=zustand["fotos"][schluessel])

    def takt():
        jetzt = time.time()
        if (not zustand["mess"] and jetzt - beginn >= 30) or (len(zustand["mess"]) == 1 and jetzt >= ende):
            zustand["mess"].append(messpunkt(coach.pid))      # nach dem Anlauf und am Ende
        if jetzt >= ende:
            uhr.ende = True
            fenster.destroy()
            return
        w = uhr.jetzt_w()
        i = bisect.bisect_right(schirm_ws, w) - 1
        if i >= 0 and i != zustand["s"]:
            zustand["s"] = i
            gross = Image.open(schirme[i][1]).convert("RGB").resize((mb, HOEHE), Image.BILINEAR)
            zeige(hinter, gross, "hinter")
            if ecke is not None:
                zeige(ecke, gross.crop((mb - hud.ECKE, HOEHE - hud.ECKE, mb, HOEHE)), "ecke")
                zeige(chat, gross.crop(chat_box), "chat")
        i = bisect.bisect_right(karten_ws, w) - 1
        if i >= 0 and i != zustand["k"]:
            zustand["k"] = i
            bild = Image.open(karten[i][1]).convert("RGB")
            if bild.size != (kr - kl, ku - ko):
                bild = bild.resize((kr - kl, ku - ko), Image.BILINEAR)
            zeige(karte, bild, "karte")
        fenster.after(100, takt)

    fenster.after(100, takt)
    try:
        fenster.mainloop()
        print("Probe-Partie vorbei - warte auf die Aufnahme ...")
        frist = time.time() + 120
        ab = len((ordner / "generalprobe.log").read_text(encoding="utf-8", errors="replace"))
        while time.time() < frist and coach.poll() is None:
            text = (ordner / "generalprobe.log").read_text(encoding="utf-8", errors="replace")[ab:]
            if "Partie vorbei" in text:          # (kein Review mehr danach, Auftrag 028)
                break
            time.sleep(2)
    finally:
        uhr.ende = True
        # ganzer Baum: ein Claude-Aufruf liefe sonst ohne Coach weiter
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(coach.pid)], capture_output=True)
        if coach.poll() is None:
            coach.terminate()
        srv.shutdown()
        log.close()
    text = (ordner / "generalprobe.log").read_text(encoding="utf-8", errors="replace")
    print(text[-3000:])
    neu = sorted(set(ordner.glob("*.jsonl.gz")) - vorher)
    if neu:
        auswerten(neu[-1].with_name(neu[-1].name.removesuffix(".jsonl.gz")), text,
                  tuple(zustand["mess"]) if len(zustand["mess"]) == 2 else None)
    else:
        print("Keine neue Aufnahme - der Coach hat die Partie nicht erkannt.")
    # Auftrag 022: die Generalprobe raeumt ihre Ausgabe selbst auf - nur das letzte Log bleibt
    from lolcoach import aufraeumen
    print(f"Generalprobe aufgeraeumt: {aufraeumen.probe_aufraeumen():.0f} MB frei")


if __name__ == "__main__":
    main()
