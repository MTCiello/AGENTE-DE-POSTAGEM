@echo off
rem Ciello OS: o assistente inteiro numa area de trabalho (escritorio dos agentes, financeiro, comercial, conteudo...).
rem Abre numa janela propria do Edge/Chrome. Feche esta janela preta para desligar.
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if exist .venv\Scripts\python.exe (set PY=.venv\Scripts\python.exe) else (set PY=py -3)
%PY% central\escritorio\servidor.py %*
pause
