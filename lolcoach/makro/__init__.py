"""Makro-Gehirn, Stufe 3a (Buch 17, Teil B; Auftrag 032).

Alle 111 Makro-Entscheidungen aus Buch 17, Teil B, als reine Funktionen einer `MakroLage`:

    lage.py            MakroLage - alles, was eine Entscheidung braucht (live gefuellt in Stufe 4 / Auftrag 033-034)
    wahrnehmung.py     welche Live-Eingabe es heute gibt und welche fehlt ("Wahrnehmung fehlt -> 033")
    rechner.py         Ankunft, Wellenkosten, Ueberzahl, Zeitfenster, TP, Roam-Wert, Rueckwaertsplanung, Schluss
    regeln.py          liest wissen/makro/*.toml (recherchierte Regeln mit Quelle und Datum)
    kommando.py        das Kommando "Tu X: weil Y. Danach Z."
    entscheidungen/    je Bereich ein Modul; Register aller 111
    vorrang.py         Gefahr zuerst, dann die Objective-Kette, dann der Rest nach Wert

Nichts hier spricht selbst: Die eine Stimme baut Stufe 4 (Auftrag 034). Das Paket aendert keine bestehende Datei in
lolcoach/ und importiert nur (bewertung, kern.uhren).
"""
