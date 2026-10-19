@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo.
echo ==== Ciello: instalando o assistente ====
echo.
set FALTA=
where git >nul 2>nul || set FALTA=%FALTA% Git.Git
where node >nul 2>nul || set FALTA=%FALTA% OpenJS.NodeJS.LTS
where ffmpeg >nul 2>nul || set FALTA=%FALTA% Gyan.FFmpeg
where py >nul 2>nul || set FALTA=%FALTA% Python.Python.3.11
if not "%FALTA%"=="" (
  echo Faltam programas:%FALTA%
  echo Instalando pelo winget...
  for %%P in (%FALTA%) do winget install -e --id %%P --accept-package-agreements --accept-source-agreements
  echo.
  echo Feche esta janela e rode o instalar.cmd de novo: o Windows precisa recarregar os programas novos.
  pause
  exit /b
)
if not exist .venv (
  echo Criando o ambiente Python do assistente...
  py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r central\requirements.txt
echo.
echo Instalando o gerador de video (Remotion)...
pushd reels
call npm install --no-audit --no-fund
popd
echo.
choice /m "Instalar tambem a voz (Kokoro, Chatterbox, Whisper)? Baixa uns 3 GB"
if errorlevel 2 goto fim
python -m pip install -r central\requirements-voz.txt
:fim
echo.
echo Pronto. Agora rode o testar.cmd
pause
