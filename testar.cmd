@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if exist .venv\Scripts\python.exe (set PY=.venv\Scripts\python.exe) else (set PY=py -3)
%PY% central\verificar.py %*
echo.
echo Se apareceu alguma FALHA, me mande o arquivo estado\verificacao.txt
pause
