@echo off
rem Abre o Escritorio Ciello (pixel-agents original) na pasta do assistente.
cd /d "%~dp0"
python central\escritorio\abrir.py %*
pause
