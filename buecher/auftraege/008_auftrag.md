# Auftrag 008 – Buch 4: Kartenlage und Makro, jeder Rat mit Warum (Claude, Chat, 28.09.2026 03:40)

**Neu gefasst.** Die frühere Fassung (Buch 2, Lane-Duell) ist auf Carlos' Wunsch zurückgestellt: zuerst Makro, Mikro
später. Buch 2 bleibt als Datei liegen und wird **nicht** umgesetzt.

Nur nach Auftrag 007.

## Teil 0 – Antworten auf 008_frage.md und 007_bericht.md (Claude, Chat, 28.09.2026 09:50)

- **008_frage.md: B.** Diese Datei ist schon die neue Fassung: Buch 4 (Makro), Buch 2 bleibt zurückgestellt. Die
  Rückfrage ist damit erledigt, `008_in_arbeit` kann weg.
- **Inhibitor quer über die Karte oder Drache daneben:**
  - Der EV entscheidet, mit Weg und Fenster. `karte.ORDNUNG` gilt nur noch bei Gleichstand.
  - Liegen beide im Fenster und der Drache ist ≤ 10 s entfernt, gilt: erst Drache, `danach` der Inhibitor, wenn das
    Fenster dann noch reicht.
  - Satz: „Drache zuerst, der liegt neben euch; danach Mid-Inhibitor, sie sind noch 30 Sekunden tot.“
- **„Raus“ kurz nach „Back jetzt“:**
  - Während des Recall-Kanals kommt eine Warnung nur, wenn der erste Gegner vor dem Ende des Kanals plus 1 s bei dir
    sein kann.
  - Reicht die Zeit für den Recall, bleibt es still.
  - Eine echte Gefahr wird nie abgeschwächt.
- **Baron-Buff allein ist keine Belagerung.** Es gilt die Regel aus 007 A4: ≥ 3 von ihnen auf einer Lane in eurer
  Hälfte.
- **Carlos' Testpartie:** Liegt eine neue Aufnahme von heute mit `_notizen.md` vor, lies Notizen und
  Sprechtasten-Log zuerst.
  - Was dort auftaucht und in dieses Buch gehört, bekommt ein Szenario aus der Partie.
  - Alles andere kommt nach `OFFEN.md`.
  - Die Partie kommt zu den Protokollen und in die Kritik-Runde.

## Teil A – ZUERST: Carlos' Testpartie 2026-09-28_101426 (Riven Mid gegen Aurora, echte Gegner)

**Carlos' Urteil:** „immer noch komplett scheußlich, absolut unerträglich“.

**Die Zahlen:** 80 ungefragte Ansagen in 34 min, davon **36 Warnungen** („Raus zum Mid-Tier-1-Turm: Aurora und Viego
kommen.“, oft alle 30–60 s). Dazu kommen dünne Pläne („Dann Mid-Welle.“) und 4 Tode, zweimal trotz „Raus“.

**Die Ursache:** Der Coach ist ein Warnsystem mit wenig Plan. Die Warnungen kommen so oft, dass Carlos sie überhört.
Die wichtigen gehen dann unter (20:16, 25:42).

**Seine Notizen und Fragen** (`_notizen.md`, `_sprechtaste.log`) sind Pflichtlektüre. Die Kernpunkte:

- „Null-Gameplan“, „was soll ich als Nächstes machen“
- „Ich weiß nie, wann wer wo ist, wann die Flashes sind … keine Übersicht“
- „Raus zum Turm ist schwammig: zu meinem Tier 1?“
- „Zu welchem Bot Tier 2, meinem oder dem des Gegners?“
- „Was soll ‚Mid-Welle‘ heißen, nichtssagend“
- Tot, und die Antwort ist „Farm deine Mid-Welle“
- „Kayn ist AFK“ war falsch
- „Kauf Tiamat und ein Kontroll-Auge“ bei vollem Inventar

Diese Punkte kommen **vor** Buch 4, jeder zuerst als rotes Szenario aus 101426.

### A1. Warnungen radikal seltener

Ändert Buch 0, 7.5 und Buch 11, Kapitel 4. GEFAHR wird **nur** gesprochen, wenn **alles** zutrifft:

1. **Sichtbar und nah:** Mindestens ein Gegner ist sichtbar, kommt näher und kann in ≤ `warn_ankunft_s` (5 s) bei
   dir sein.
2. **Robust unterlegen:** In 5 s wären sie ≥ 1 Kopf mehr als ihr, **oder** dein Leben liegt unter 40 % und ist
   niedriger als das des nächsten Gegners, **oder** „klar unterlegen“ nach der Überlegenheits-Regel.
3. **Du bist nicht schon auf dem Rückzug:** Du läufst nicht Richtung Sicherheit (≥ 300 in 2 s) und bist nicht ≤ 5 s
   von ihr.
4. **Nicht dieselbe Gegnermenge in 60 s,** außer das Todesrisiko steigt um ≥ 0,2.

**Ungesehene Gefahr** (Jungler, MIA) wird nicht mehr als „Raus“ gesagt. Stattdessen gibt es höchstens einen
Vorsicht-Satz je 90 s, und nur, wenn du jenseits des Flusses stehst **und** ≥ 2 Gegner seit ≥ 20 s fehlen: „Du stehst
tief: Viego und Twitch fehlen seit 30 Sekunden.“

**Ziel:** ≤ 10 Warnungen je 30 min, Warnungen ≤ 25 % der ungefragten Ansagen. Beides kommt als neue Kennzahl nach
`kennzahlen.py`.

### A2. Konkrete Sprache

Ändert alle Satzbausteine.

- **Türme** immer mit Besitzer und Lage, ohne „Tier“:
  - „dein äußerer Mid-Turm“, „euer innerer Bot-Turm“, „ihr Inhibitor-Turm unten“
  - Rückzug: „Zurück unter deinen Mid-Turm“
  - Im Kampf: „Raus, zu deinem Turm!“ bzw. „Raus, zu Kayn!“
- **Welle** nie allein. Es heißt Lane plus Tätigkeit oder Grund: „Dann auf Mid, deine Welle ist gleich an deinem
  Turm.“ Sätze wie „Dann Mid-Welle.“ gibt es nicht mehr.
- **Test** über alle Bausteine:
  - verboten: „Tier-“, „Raus, zum Turm“, ein Satz, der nur aus „Dann <Ort>.“ besteht
  - Pflicht: „dein/euer/ihr“ vor jedem Turm

### A3. Fehler aus 101426

1. **Tot:** Fragen wie „was jetzt“ bekommen den Respawn-Plan (Kauf, Ziel, Zeit), nie „Farm …“ (32:07–32:22).
2. **Alte AFK-Regel** (`_afk`): ganz aus. „Kayn ist AFK“ war falsch (23:24).
3. **Kaufplan bei vollem Inventar** (28:39: „Kauf Tiamat und ein Kontroll-Auge“): Prüf, warum R3 hier nicht griff, und
   behebe das. Ein Kontroll-Auge ohne freien Platz wird nicht genannt.
4. **Antworten auf Korrekturen:** „Bro, der war ein paar Meter weg von mir“ (19:38) gilt als Korrektur der Lage und
   bekommt eine Antwort aus der korrigierten Lage.

### A4. Lagebild auf Abruf und regelmäßig

Carlos will Übersicht („wann wer wo, wann die Flashes“). Das ergänzt Buch 4, Kapitel 5.

- **Frage** „Überblick?“, „Lage?“, „wo sind alle?“ (Absicht `LAGE`): in höchstens 2 Sätzen, wer wo ist (nach
  Kartenseite zusammengefasst), bekannte Flashs und Tote, dann die Folgerung.
  Beispiel: „Viego und Twitch unten, Aurora Mitte ohne Flash bis 24:10, Sett fehlt. Oben ist frei.“
- **Ungefragt ab 14:00:** höchstens einmal je `lagebild_abstand_s` (90 s), nur wenn in dieser Zeit nichts anderes
  gesagt wurde. Kurzform ≤ 16 Wörter, immer mit einer Folgerung.

### A5. Neue Abnahme: Nutzen statt nur „falsch“

Die Kritiker bekommen eine zweite Rolle. **Carlos-Kritiker:** Riven-Spieler, will Makro und Übersicht, hasst Floskeln
und Dauerwarnungen; seine Notizen aus 213624 und 101426 liegen bei. Er bewertet jede ungefragte Ansage mit
**hilft / neutral / nervt**.

**Soll** in 101426, 164326 und 173159:

- „nervt“ ≤ 10 %
- „hilft“ ≥ 60 %
- ≤ 10 Warnungen je 30 min
- 0 Sätze mit verbotener oder vager Form
- „falsch“ (Challenger-Kritiker wie bisher) ≤ 2 je 30 min


## Teil 1 – Buch 4 (nach Teil A)

Lies `buecher/04_kartenlage_makro.md` vollständig und setze es um, in dieser Reihenfolge:

1. **Kartenlage** (Kapitel 2) mit Dashboard-Anzeige: wie viele Gegner oben, in der Mitte, unten, unbekannt, tot, und
   Fenster je Seite.
2. **Teamplan** (Kapitel 3): Kurven, Stand, Plan-Satz um 14:00 und bei Umschwung.
3. **Warum-Regeln** (Kapitel 4):
   - der entscheidende Grund über die Gegenrechnung ohne diese Größe,
   - der Test gegen verbotene Gründe über alle Satzbausteine,
   - WARUM-Antworten mit Vergleich.
4. **Makro-Infos** (Kapitel 5) mit Budget, Wirkungsregel und Doppelungsverbot.
5. **Szenarien** (Kapitel 6), jedes zuerst rot.

Passt etwas im Buch nicht zum Code, entscheidest du nach Kapitel 1 und notierst es unter „Abweichungen“.

## Ende

1. Neue Protokolle für **101426 (mit `--fragen`)**, 164326, 173159, 144655 und 213624 (mit `--fragen`).
2. Eine Kritik-Runde wie in Auftrag 005, mit drei neuen Kritikern. Sie bekommen zusätzlich die Frage aus Buch 4,
   Kapitel 6: „Ist das Warum nachvollziehbar?“ (ja/nein je Satz) und die Klasse „Info ohne Folgen“. Das Ergebnis
   kommt nach `008_kritik.md`.
3. messungen.md, Abschnitt „Auftrag 008“, mit der Warum-Quote je Partie.
4. Committen und `008_bericht.md` schreiben. Starte den Coach nicht.
