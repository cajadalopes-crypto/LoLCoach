# Auftrag 011 – Warnungsrate nachziehen, Szenario 2522 richtigstellen (Claude, Chat, 28.09.2026 18:20)

Kleiner Nachtrag. In Auftrag 010 habe ich Carlos zwei Entscheidungen zu 009 mitgeteilt, aber die erste davon nicht in
den Auftragstext geschrieben – mein Fehler, nicht deiner. Sie fehlt noch. Danach ein zweiter, kleiner Punkt.

## 1. Warnungsrate (fehlte in 010)

Ungesehene Gegner zählen seit 009 als Kopf (≤ 20 s ungesehen, Ankunft ≤ 5 s). Das war richtig (20:16 muss warnen),
hat aber die Warnungsrate von 11,7/8,4/7,8 auf 15,0/11,9/11,0 je 30 min getrieben (Soll ≤ 10, angepasste
Szenario-Schranke 13). Zwei Stellschrauben, beide bauen, nicht nur eine:

1. **Ungesehen zählt nur gepaart:** Ein Ungesehener zählt nur als zusätzlicher Kopf, wenn zugleich mindestens ein
   Sichtbarer nah ist und näher kommt. Ein Ungesehener allein, ohne nahen Sichtbaren, löst keine Warnung aus. Prüfe an
   den Fällen aus 101426 (20:01, 20:10, 21:35, 23:35), ob das dort etwas ändert – wenn nicht, liegt der Rest an
   164326/173159, das bitte auch zeigen.
2. **Keine Wiederholung ohne neue Lage:** Dieselbe Warnung (gleicher Kopf, gleiches Ziel) wird nicht wiederholt, wenn
   sich seit dem letzten Mal nichts wesentlich geändert hat (kein neuer Kopf, kein Wechsel der Fluchtrichtung,
   `p_tod` nicht um mehr als eine Stufe gestiegen). Fall 20:10 in 101426 (9 s nach 20:01, nur `p_tod` leicht höher)
   soll danach wegfallen.

**Messung:** Warnungen je 30 min in allen neun Protokollen, vorher/nachher. `a1-warnungen-je-30min` soll grün werden
oder, falls nicht, mit Zahl und Grund erklärt sein, welcher der beiden Fälle (20:16-Art oder eine echte, neue
Mehrfachgefahr) den Rest ausmacht.

## 2. Szenario `2522-kein-baron-drache-lebt` richtigstellen

Der Split bei 102112 25:22 (Tryndamere allein zum Drachen, Riven zum Turm) ist seit 009 eine bewusste Entscheidung,
keine offene Frage mehr. Das Szenario prüft aber weiter den alten Ausgang („Drache“) und ist deshalb seit 009 ohne
Grund rot.

- Ändere die Erwartung im Szenario auf den akzeptierten Ausgang (Turm/Split), oder lege es wie die zwei offenen
  Leerlauf-Fälle nach `tests/szenarien/offen/` mit Begründung – wonach sich Buch 9, 12 dazu richten. Kein Verhalten
  ändern, nur das Szenario.

## Ende

1. Szenarien, dann Messung.
2. Bericht: neue Warnungsrate je Partie, ob `a1-warnungen-je-30min` jetzt grün ist.
3. Committen. Starte den Coach nicht.
