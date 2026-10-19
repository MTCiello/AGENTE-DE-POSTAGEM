@echo off
rem Abre o Escritorio Ciello (pixel-agents original, layout da Ciello) na pasta do assistente.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if exist .venv\Scripts\python.exe (set PY=.venv\Scripts\python.exe) else (set PY=py -3)
%PY% central\escritorio\abrir.py %*
pause
