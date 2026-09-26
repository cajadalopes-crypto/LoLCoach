"""Generalprobe: der komplette Live-Weg ohne League of Legends.

Ein nachgebauter Spielclient liefert die Live-API aus einer Aufnahme (in Echtzeit),
ein randloses Fenster mit dem Titel des Spielfensters zeigt an der echten Stelle
die aufgezeichneten Minimap-/HUD-Bilder (Aufnahmen vom 26.09.2026, 12:00: die
Ecke 907 x 907 bei 4K). Der Coach laeuft als eigener Prozess dagegen - mit
dxcam-Aufnahme, Verfolger, Mitspieler-Leiste, Regeln, Stratege, Dashboard,
Speichern und Review danach. Aufnahmen landen in `aufnahmen_probe/`.

    python werkzeuge/generalprobe.py [--aufnahme ...] [--ab 13] [--minuten 4] [--ohne-gehirn]
"""
import argparse
import bisect
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from lolcoach import aufzeichnung  # noqa: E402

TITEL = "League of Legends (TM) Client"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aufnahme", default=str(WURZEL / "aufnahmen" / "2026-09-26_120049.jsonl.gz"))
    ap.add_argument("--ab", type=float, default=13.0, help="Spielminute, ab der die Probe laeuft")
    ap.add_argument("--minuten", type=float, default=4.0)
    ap.add_argument("--ohne-gehirn", action="store_true")
    ap.add_argument("--links", type=int, default=1920)
    args = ap.parse_args()

    alle = list(aufzeichnung.lies_mit_zeit(args.aufnahme))
    start_i = next(i for i, (_, d) in enumerate(alle) if d["gameData"]["gameTime"] >= args.ab * 60)
    uhr = Uhr(alle[start_i][0])
    bilder = aufzeichnung.bilder(args.aufnahme)
    bild_ws = [w for w, _ in bilder]
    srv = server(alle, uhr)
    basis = f"http://127.0.0.1:{srv.server_port}"

    ordner = WURZEL / "aufnahmen_probe"
    ordner.mkdir(exist_ok=True)
    log = open(ordner / "generalprobe.log", "w", encoding="utf-8")
    befehl = [sys.executable, "-m", "lolcoach", "--basis", basis, "live", "--stumm", "--ohne-sprache"]
    if args.ohne_gehirn:
        befehl.append("--ohne-gehirn")
    coach = subprocess.Popen(befehl, cwd=WURZEL, stdout=log, stderr=subprocess.STDOUT,
                             env={**os.environ, "LOLCOACH_AUFNAHMEN": str(ordner), "PYTHONUNBUFFERED": "1"})
    print(f"Probe: API {basis}, Coach-PID {coach.pid}, Log {ordner / 'generalprobe.log'}")

    import tkinter as tk
    from PIL import Image, ImageTk
    fenster = tk.Tk()
    fenster.title(TITEL)
    fenster.overrideredirect(True)
    fenster.geometry(f"3840x2160+{args.links}+0")
    fenster.configure(bg="black")
    fenster.attributes("-topmost", True)
    anzeige = tk.Label(fenster, bg="black", bd=0)
    anzeige.place(x=3840 - 907, y=2160 - 907, width=907, height=907)
    zustand = {"i": -1, "foto": None}
    ende = time.time() + args.minuten * 60

    def takt():
        if time.time() >= ende:
            uhr.ende = True
            fenster.destroy()
            return
        i = bisect.bisect_right(bild_ws, uhr.jetzt_w()) - 1
        if i >= 0 and i != zustand["i"]:
            zustand["i"] = i
            zustand["foto"] = ImageTk.PhotoImage(Image.open(bilder[i][1]))
            anzeige.configure(image=zustand["foto"])
        fenster.after(100, takt)

    fenster.after(100, takt)
    try:
        fenster.mainloop()
        print("Probe-Partie vorbei - warte auf Aufnahme, Bericht und Review ...")
        frist = time.time() + 420
        while time.time() < frist and coach.poll() is None:
            text = (ordner / "generalprobe.log").read_text(encoding="utf-8", errors="replace")
            if "Review fertig" in text or "Review fehlgeschlagen" in text:
                break
            time.sleep(5)
    finally:
        uhr.ende = True
        coach.terminate()
        srv.shutdown()
    print((ordner / "generalprobe.log").read_text(encoding="utf-8", errors="replace")[-6000:])


if __name__ == "__main__":
    main()
