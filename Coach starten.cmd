@echo off
rem Doppelklick: startet den Coach (wartet auf die Partie, Dashboard http://127.0.0.1:8790)
rem LOLCOACH_API=1: nur hier darf der Coach die Claude-API (Guthaben) nutzen - Sparprotokoll, buecher/16_sparprotokoll.md
cd /d "%~dp0"
set LOLCOACH_API=1
python -m lolcoach
pause
