@echo off
rem Doppelklick: startet den Coach (wartet auf die Partie, Dashboard http://127.0.0.1:8790)
cd /d "%~dp0"
python -m lolcoach
pause
