"""Makro-Gehirn, Stufe 3a (Buch 17, Teil B; Auftrag 032) und Stufe 4, der Einbau (Auftrag 034).

Alle 111 Makro-Entscheidungen aus Buch 17, Teil B, als reine Funktionen einer `MakroLage`:

    lage.py            MakroLage - alles, was eine Entscheidung braucht (live gefuellt in Stufe 4 / Auftrag 033-034)
    wahrnehmung.py     welche Live-Eingabe es heute gibt und welche fehlt ("Wahrnehmung fehlt -> 033")
    rechner.py         Ankunft, Wellenkosten, Ueberzahl, Zeitfenster, TP, Roam-Wert, Rueckwaertsplanung, Schluss
    regeln.py          liest wissen/makro/*.toml (recherchierte Regeln mit Quelle und Datum)
    kommando.py        das Kommando "Tu X: weil Y. Danach Z."
    entscheidungen/    je Bereich ein Modul; Register aller 111
    vorrang.py         Gefahr zuerst, dann die Objective-Kette, dann der Rest nach Wert
  Stufe 4 (Auftrag 034):
    live.py            LageBau: MakroLage + Merkmale fuers Gehirn aus API, Minimap, HUD, Chat, Lesern aus 033
    takt.py            Entscheider: Gehirn + 111 + Vorrang -> genau eine Anweisung; Planwechsel nur mit Grund
    stimme.py          Claude formt nur den Satz; weicht er ab, faellt er aus, ist er zu langsam: die Vorlage
    einbau.py          MakroCoach: der Takt im Coach (kern.Kern, Stellung "makro"), Budget, Erinnerung, Fragen,
                       Protokoll <stamm>_makro.jsonl

Der alte Kern (lolcoach/kern) entscheidet in der Stellung "makro" (--kern makro, Standard) nicht mehr, er ist nur noch
die Sicherheits-Sperre (kern.Kern.makro_sperre). --kern neu gibt den Stand vor 034.
"""
