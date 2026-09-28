# Bericht zu Auftrag 008 – Testpartie 101426, dann Buch 4 (Kartenlage und Makro)

Fertig am 28.09.2026. Der Coach wurde nicht gestartet. Einzelheiten stehen in `buecher/messungen.md` („Auftrag 008“),
die Kritik in `008_kritik.md`.

## Commits

- `17ae43a`:
  - Teil A (A1–A4),
  - Teil 1 (Kartenlage mit Dashboard-Kasten, Teamplan, Warum-Regeln, Makro-Infos, Szenarien Kapitel 6),
  - Kritik-Runde und Fixes aus der Kritik,
  - Buch 4 selbst (jetzt umgesetzt; Buch 2 bleibt unversioniert, zurückgestellt).
- Dazu der Commit mit Auftrag und Bericht.

## Tests und Szenarien

- `tests/alle.py` **10 / 10**, konstruierte Lagen **40 / 40**.
- Szenarien **217 / 221**, 3 übersprungen. Rot sind nur die alten Fälle: die Wendepunkt-Probe (12 späte Sätze, vorher
  29) und 0944.
- **Neu:** 101426 (16 + 4 aus der Kritik), Buch 4 (5), Kritik 164326/173159 (2) und 7 Unit-Tests.
  - Auf `dac2581` waren alle rot, außer zwei Wächtern.
- **Nachgezogen:** 14 alte Szenario-Stellen auf die neuen Wörter und die Folgen von A1. Jedes Verbot bekam die neue Form
  dazu.

## Kennzahlen (Soll aus A5)

| | 101426 | 164326 | 173159 |
|---|---|---|---|
| Warnungen je 30 min (≤ 10) | **11,7** | 8,4 | 7,8 |
| vage oder verbotene Sätze (0) | 0 | 0 | 0 |
| „falsch“ je 30 min (≤ 2) | **2,5** | 0,7 | 0,8 |
| „nervt“ (≤ 10 %) / „hilft“ (≥ 60 %) | 10 % / 88 % | 4 % / 91 % | 2 % / 93 % |
| Warum nachvollziehbar (≥ 90 %) | 91 % | 95 % | 92 % |

- **Warnungen:** Live kamen in 101426 36 Warnungen in 34 min.
- **Kritik:** kein „gefährlich“. Die 5 Fälle „Du stehst tief“ auf der eigenen Lane sind nach der Zählung behoben (nur
  noch in ihrem Jungle), nicht nachgezählt.
- **Nicht erreicht:**
  - Info ohne Folgen 1–4 statt 0 (Flash-Meldungen, „Gut raus.“).
  - Leerlauf ab 14:00 52–59 % statt ≤ 10 %.
  - Ungefragt 67–72 je 30 min.

**Unterwegs gefunden:**
- Viego in Urgots Gestalt hieß „Urgot“ („Aurora und Urgot kommen“, Urgot war dein Mitspieler).
- Für das rote Team war ihr Jungle „euer Jungle“.
- Die Leben-Zahl im Satz war veraltet (29 % statt 13 %).

## Zu entscheiden

1. **20:16 in 101426:** Nach A1 kommt keine Warnung. Sichtbar standen zwei gegen zwei, Viego war 17 s ungesehen; 5 s
   später war Riven tot. Soll ein Gegner, der ≤ 20 s ungesehen ist und in 5 s da sein kann, als Kopf zählen? Das würde
   101426 um 14:00 wieder zur Warnung machen („nur Aurora sichtbar“).
2. **Lagebild:** 30 s Ruhe statt der 90 s aus A4. Nach 14:00 gab es in 101426 keine 90 s Stille, das Lagebild wäre also
   nie gekommen. So lassen?
3. **Aus Teil 0 nicht gebaut:**
   - Drache vor Inhibitor über den EV;
   - Warnung im Recall-Kanal nur, wenn der erste Gegner vor Kanal-Ende plus 1 s da sein kann.
   Beides gehört in einen eigenen Auftrag.
