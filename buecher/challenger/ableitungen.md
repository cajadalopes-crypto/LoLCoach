# Ableitungen und ihre Pruefung (Auftrag 029, Schritt 3)

2792 gueltige Partien. Je Ableitung 50 zufaellige Funde (Zufall 29), Gegenprobe aus Daten, die die Ableitung selbst nicht benutzt. **alle** = dieselbe Gegenprobe ueber alle Funde. Back: nur echte Backs (ohne Kauf nach Tod); Kampf: nur >= 2 Kills und <= 10 s neben einer vollen Minute (sonst an Positionen nicht pruefbar).

**Nullprobe** = dieselbe Gegenprobe mit falschem Ort bzw. falscher Zeit (Kampf an der Diagonale gespiegelt, Objective 3 min spaeter, Gank/Split andere Lane, Rotation alte Zone, Gruppe gespiegelt, Back am gegnerischen Laden, Todeszeit halb so lang). Liegt sie nah an **alle**, trennt die Gegenprobe nicht.

| Ableitung | Funde | je Partie | Stichprobe Treffer | Zweifel | alle Funde stimmig | Nullprobe |
|---|---:|---:|---:|---:|---:|---:|
| Back | 189545 | 67.9 | 50/50 | 0 | 100% | 86% |
| TP | 1258 | 0.5 | 29/50 | 21 | 54% | – |
| Kampf | 11019 | 3.9 | 50/50 | 0 | 98% | 12% |
| Objective | 23901 | 8.6 | 37/50 | 13 | 71% | 63% |
| Gank | 15677 | 5.6 | 44/50 | 6 | 86% | 3% |
| Rotation | 8813 | 3.2 | 50/50 | 0 | 98% | 33% |
| Gruppe | 41736 | 14.9 | 45/50 | 5 | 93% | 65% |
| Split | 1894 | 0.7 | 44/50 | 6 | 92% | 56% |
| Todeszeit | 155742 | 55.8 | 45/50 | 5 | 89% | 76% |

## Kennzahlen nebenbei

- **TP:** gefundene Spruenge bei TP-Spielern 686 von 21227 TP-Einsaetzen (`summonerXCasts`) = 3% gefunden; bei Spielern OHNE TP 572 Spruenge in 22232 Spieler-Partien (Fehlalarm-Quelle). Arten: {'aus der Basis': 1249, 'zum Kampf': 9}. Stufe *wahrscheinlich* (normales Tempo, Weg x 1,15): 11066 bei TP-Spielern, 22541 bei Spielern ohne TP. `teleportTakedowns` (Kills/Assists kurz nach TP) gesamt: 1886
- **Back je Spieler und Partie:** ADC 6.6, Jungle 6.0, Mid 7.3, Top 6.7, Support 7.4
- **Ladenbesuche:** {('Back', True): 186768, ('Tod', True): 128309, ('Back', False): 2777} (Tod = Kauf nach dem Tod, kein Back)
- **Kaempfe:** 34074 mit >= 2 Kills, 55755 Einzelkills
- **Objectives (Typ, umkaempft):** AIR_DRAGON frei 1028, AIR_DRAGON umk. 583, BARON_NASHOR frei 1569, BARON_NASHOR umk. 1371, CHEMTECH_DRAGON frei 1106, CHEMTECH_DRAGON umk. 638, EARTH_DRAGON frei 1044, EARTH_DRAGON umk. 562, ELDER_DRAGON frei 42, ELDER_DRAGON umk. 60, FIRE_DRAGON frei 1043, FIRE_DRAGON umk. 601, HEXTECH_DRAGON frei 995, HEXTECH_DRAGON umk. 658, HORDE frei 6101, HORDE umk. 2275, RIFTHERALD frei 1770, RIFTHERALD umk. 785, WATER_DRAGON frei 1079, WATER_DRAGON umk. 591

## Back

Beispiele:
- EUW1_7995635007 5:25 Zoe (Support): Back 1 Kaeufe
- EUW1_7977965327 2:21 Jhin (ADC): Back 1 Kaeufe
- EUW1_7990155751 11:40 Lulu (Support): Back 2 Kaeufe
- EUW1_7996803131 24:44 Samira (ADC): Back 1 Kaeufe
- EUW1_7997074879 10:04 Janna (Support): Back 1 Kaeufe

## TP

Beispiele:
- EUW1_7995784272 9:45->9:55 Zaahen (Top): basis_rot -> top (aus der Basis; 11230 zu weit in 10 s)
- EUW1_7993450467 12:31->13:00 Veigar (Mid): basis_blau -> mid (aus der Basis; 8038 zu weit in 29 s)
- EUW1_7979445509 10:29->11:00 Leblanc (Mid): basis_rot -> mid (aus der Basis; 8690 zu weit in 31 s)
- EUW1_7992646617 18:46->18:59 Tryndamere (Top): basis_blau -> top (aus der Basis; 11240 zu weit in 14 s)
- EUW1_7982059189 5:20->5:22 Karthus (ADC): basis_rot -> bot (aus der Basis; 10090 zu weit in 2 s)

Zweifel der Stichprobe:
- EUW1_7979445509 10:29->11:00 Leblanc (Mid): basis_rot -> mid (aus der Basis; 8690 zu weit in 31 s) – kein TP gespielt (Leblanc)
- EUW1_7992646617 18:46->18:59 Tryndamere (Top): basis_blau -> top (aus der Basis; 11240 zu weit in 14 s) – kein TP gespielt (Tryndamere)
- EUW1_7982059189 5:20->5:22 Karthus (ADC): basis_rot -> bot (aus der Basis; 10090 zu weit in 2 s) – kein TP gespielt (Karthus)
- EUW1_7988877582 13:39->14:00 Seraphine (Support): basis_blau -> bot (aus der Basis; 7709 zu weit in 21 s) – kein TP gespielt (Seraphine)
- EUW1_7983473075 17:48->18:00 Kled (Top): basis_blau -> mid (aus der Basis; 10916 zu weit in 12 s) – kein TP gespielt (Kled)
- EUW1_7991697175 25:38->25:59 Jayce (Jungle): basis_blau -> mid (aus der Basis; 6777 zu weit in 22 s) – kein TP gespielt (Jayce)
- EUW1_7994425421 15:44->16:00 Skarner (Support): basis_rot -> mid (aus der Basis; 5383 zu weit in 16 s) – kein TP gespielt (Skarner)
- EUW1_7991002765 22:42->22:51 Fiora (Top): basis_rot -> basis_blau (aus der Basis; 12900 zu weit in 9 s) – kein TP gespielt (Fiora)
- EUW1_7997641434 9:15->10:00 Bard (Support): basis_rot -> jungle_blau_oben (aus der Basis; 10901 zu weit in 45 s) – kein TP gespielt (Bard, globale Reise)
- EUW1_7981873286 3:39->3:39 Renekton (Mid): basis_rot -> mid (aus der Basis; 6469 zu weit in 1 s) – kein TP gespielt (Renekton)
- EUW1_7994814959 2:29->3:00 Olaf (Top): basis_rot -> fluss_oben (aus der Basis; 8981 zu weit in 31 s) – kein TP gespielt (Olaf)
- EUW1_7989753983 13:24->14:00 Braum (Support): basis_blau -> fluss_oben (aus der Basis; 8722 zu weit in 36 s) – kein TP gespielt (Braum)
- EUW1_7977128733 8:12->8:55 Renata (Support): basis_rot -> bot (aus der Basis; 10332 zu weit in 43 s) – kein TP gespielt (Renata)
- EUW1_7976116820 28:40->29:01 Olaf (Top): basis_rot -> jungle_blau_oben (aus der Basis; 10253 zu weit in 21 s) – kein TP gespielt (Olaf)
- EUW1_7980572920 15:25->16:00 Pyke (Support): basis_rot -> fluss_unten (aus der Basis; 7086 zu weit in 36 s) – kein TP gespielt (Pyke)
- EUW1_7996923965 1:03->1:04 Bard (Support): basis_rot -> bot (aus der Basis; 10068 zu weit in 1 s) – kein TP gespielt (Bard, globale Reise)
- EUW1_7971598302 12:13->12:14 Nautilus (Support): basis_rot -> jungle_blau_unten (aus der Basis; 8703 zu weit in 1 s) – kein TP gespielt (Nautilus)
- EUW1_7983498729 26:59->27:01 Elise (Jungle): basis_rot -> mid (aus der Basis; 8927 zu weit in 2 s) – kein TP gespielt (Elise)
- EUW1_7995280448 26:38->27:01 Jax (Top): basis_rot -> jungle_blau_oben (aus der Basis; 10445 zu weit in 22 s) – kein TP gespielt (Jax)
- EUW1_7992680279 9:57->10:00 Ornn (ADC): basis_rot -> fluss_unten (aus der Basis; 9012 zu weit in 4 s) – kein TP gespielt (Ornn)
- EUW1_7974792217 18:47->19:00 XinZhao (Jungle): basis_rot -> jungle_rot_oben (aus der Basis; 6175 zu weit in 13 s) – kein TP gespielt (XinZhao)

## Kampf

Beispiele:
- EUW1_7972754557 2:59 3 Kills bot, Tode {100: 2, 200: 1}
- EUW1_7980488195 22:55 2 Kills top, Tode {200: 2}
- EUW1_7984591652 23:00 3 Kills basis_blau, Tode {100: 2, 200: 1}
- EUW1_7980029282 6:01 4 Kills fluss_unten, Tode {200: 2, 100: 2}
- EUW1_7983415524 2:53 2 Kills jungle_blau_unten, Tode {200: 1, 100: 1}

## Objective

Beispiele:
- EUW1_7978247512 18:46 EARTH_DRAGON Team 200: frei
- EUW1_7989191269 8:17 HORDE Team 200: frei
- EUW1_7984341840 16:43 FIRE_DRAGON Team 200: frei
- EUW1_7993633249 23:17 BARON_NASHOR Team 100: umkaempft 5 Kills
- EUW1_7975477412 12:03 FIRE_DRAGON Team 200: frei

Zweifel der Stichprobe:
- EUW1_7978247512 18:46 EARTH_DRAGON Team 200: frei – frei genommen, aber 3 Gegner nah
- EUW1_7975477412 12:03 FIRE_DRAGON Team 200: frei – frei genommen, aber 3 Gegner nah
- EUW1_7996468761 15:31 RIFTHERALD Team 100: frei – frei genommen, aber 4 Gegner nah
- EUW1_7982812378 13:00 EARTH_DRAGON Team 200: frei – frei genommen, aber 4 Gegner nah
- EUW1_7994622564 29:14 BARON_NASHOR Team 200: umkaempft 1 Kills – Gegner nah: 1 (Kills eher Nebenschauplatz)
- EUW1_7989740482 21:29 BARON_NASHOR Team 200: frei – frei genommen, aber 4 Gegner nah
- EUW1_7993190235 16:46 RIFTHERALD Team 100: frei – frei genommen, aber 3 Gegner nah
- EUW1_7997487898 9:48 HORDE Team 100: frei – frei genommen, aber 3 Gegner nah
- EUW1_7989002135 19:45 RIFTHERALD Team 300: frei – frei genommen, aber 3 Gegner nah
- EUW1_7984970674 9:29 HORDE Team 100: frei – frei genommen, aber 4 Gegner nah
- EUW1_7979588351 6:36 WATER_DRAGON Team 200: frei – frei genommen, aber 3 Gegner nah
- EUW1_7998846886 9:07 HORDE Team 100: frei – frei genommen, aber 3 Gegner nah
- EUW1_7986403507 16:43 RIFTHERALD Team 100: umkaempft 1 Kills – Gegner nah: 0 (Kills eher Nebenschauplatz)

## Gank

Beispiele:
- EUW1_7982438860 11:51 bot: Elise ganked Tristana (ADC)
- EUW1_7998749054 10:19 bot: Viego ganked Leona (Support)
- EUW1_7994267752 11:13 top: Amumu ganked Gnar (Top)
- EUW1_7984182275 8:09 bot: JarvanIV ganked Thresh (Support)
- EUW1_7984321610 5:23 bot: Qiyana ganked Sivir (ADC)

Zweifel der Stichprobe:
- EUW1_7990251525 10:05 mid: Viego ganked Zoe (Support) – Opfer Support stirbt auf mid (Roam-Opfer)
- EUW1_7992560495 11:09 top: MonkeyKing ganked Leona (Support) – Opfer Support stirbt auf top (Roam-Opfer)
- EUW1_7978036305 11:16 bot: JarvanIV ganked Camille (Top) – Opfer Top stirbt auf bot (Roam-Opfer)
- EUW1_7998287050 10:25 mid: LeeSin ganked Janna (Support) – Opfer Support stirbt auf mid (Roam-Opfer)
- EUW1_7985130594 11:58 bot: Shaco ganked Lissandra (Mid) – Opfer Mid stirbt auf bot (Roam-Opfer)
- EUW1_7997221397 3:58 mid: Nidalee ganked Thresh (Support) – Opfer Support stirbt auf mid (Roam-Opfer)

## Rotation

Beispiele:
- EUW1_7993087445 3:00 Syndra (Mid): jungle_blau_oben -> mid
- EUW1_7995928462 14:00 Nautilus (Support): fluss_oben -> fluss_unten
- EUW1_7994283745 17:00 Katarina (Mid): mid -> top
- EUW1_7982387470 13:00 Shen (Top): jungle_blau_unten -> top
- EUW1_7994306541 20:00 Syndra (Mid): fluss_unten -> top

## Gruppe

Beispiele:
- EUW1_7971631106 14:00 Team 100: 3 beisammen mid
- EUW1_7988609820 17:00 Team 100: 4 beisammen jungle_rot_unten
- EUW1_7997904536 22:00 Team 200: 3 beisammen jungle_rot_oben
- EUW1_7998529993 17:00 Team 200: 4 beisammen mid
- EUW1_7991265995 28:01 Team 200: 3 beisammen fluss_unten

Zweifel der Stichprobe:
- EUW1_7997900204 40:01 Team 100: 5 beisammen bot – ohne Anlass (nichts passiert dort +-60 s)
- EUW1_7998792584 12:00 Team 200: 3 beisammen top – ohne Anlass (nichts passiert dort +-60 s)
- EUW1_7993324440 24:00 Team 100: 3 beisammen mid – ohne Anlass (nichts passiert dort +-60 s)
- EUW1_7979664867 27:01 Team 100: 3 beisammen mid – ohne Anlass (nichts passiert dort +-60 s)
- EUW1_7978888367 14:00 Team 200: 3 beisammen jungle_rot_unten – ohne Anlass (nichts passiert dort +-60 s)

## Split

Beispiele:
- EUW1_7986934477 18:00 Heimerdinger (Mid): allein top
- EUW1_7994782852 18:00 TwistedFate (Top): allein top
- EUW1_7984929249 15:00 Heimerdinger (Top): allein top
- EUW1_7977090245 15:00 Sion (Top): allein top
- EUW1_7996573386 23:00 Ezreal (ADC): allein bot

Zweifel der Stichprobe:
- EUW1_7997480500 18:00 Cassiopeia (Mid): allein top – nichts genommen, niemanden gezogen
- EUW1_7987565705 14:00 Ambessa (Top): allein bot – nichts genommen, niemanden gezogen
- EUW1_7995534499 19:00 Jax (Top): allein bot – nichts genommen, niemanden gezogen
- EUW1_7983747955 17:00 Fiora (Top): allein top – nichts genommen, niemanden gezogen
- EUW1_7978808048 15:00 Olaf (Top): allein top – nichts genommen, niemanden gezogen
- EUW1_7993378772 16:00 Ahri (Mid): allein bot – nichts genommen, niemanden gezogen

## Todeszeit

Beispiele:
- EUW1_7996591345 27:17 Lissandra (Mid): tot bis 28:09
- EUW1_7985095123 15:12 Yasuo (ADC): tot bis 15:37
- EUW1_7980557267 12:21 Nilah (ADC): tot bis 12:49
- EUW1_7992584583 23:47 Bard (Support): tot bis 24:25
- EUW1_7987381109 21:00 Elise (Support): tot bis 21:35

Zweifel der Stichprobe:
- EUW1_7998670493 35:17 Rell (Support): tot bis 36:04 – Formel 46 s, aber nach 43 s schon lebendig (Wiederbelebung/Zilean/GA?)
- EUW1_7983257071 21:56 Karthus (Jungle): tot bis 22:38 – Formel 42 s, aber nach 5 s schon lebendig (Wiederbelebung/Zilean/GA?)
- EUW1_7977969327 14:42 Kennen (Support): tot bis 15:07 – Formel 25 s, aber zur Minute noch tot
- EUW1_7981338623 28:43 MonkeyKing (Jungle): tot bis 29:36 – Formel 53 s, aber zur Minute noch tot
- EUW1_7988998289 23:37 Hecarim (Jungle): tot bis 24:23 – Formel 46 s, aber nach 23 s schon lebendig (Wiederbelebung/Zilean/GA?)
