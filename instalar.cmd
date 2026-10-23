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
where py >nul 2>nul || set FALTA=%FALTA% Python.Python.3.12
if not "%FALTA%"=="" (
  echo Faltam programas:%FALTA%
  echo Instalando pelo winget...
  for %%P in (%FALTA%) do winget install -e --id %%P --accept-package-agreements --accept-source-agreements
  echo.
  echo Feche esta janela e rode o instalar.cmd de novo: o Windows precisa recarregar os programas novos.
  pause
  exit /b
)
rem Python 3.12 de preferencia: a voz (Kokoro, Chatterbox) ainda nao roda no 3.13
if not exist .venv (
  echo Criando o ambiente Python do assistente...
  py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r central\requirements.txt
echo.
echo Baixando o buscador do Google Maps do SDR (gosom/google-maps-scraper, MIT)...
python central\sdr.py instalar-scraper || echo Nao deu para baixar agora: o SDR funciona com CSV, e o instalar.cmd tenta de novo na proxima vez.
echo.
echo Instalando o gerador de video (Remotion e HyperFrames do Estudio de Video)...
pushd reels
call npm install --no-audit --no-fund
set HYPERFRAMES_SKIP_SKILLS=1
call npx hyperframes browser ensure || echo O navegador do HyperFrames baixa na primeira vez que gerar um video.
popd
echo.
choice /m "Instalar tambem a voz (Kokoro, Chatterbox, Whisper)? Baixa uns 3 GB"
if errorlevel 2 goto fim
python -c "import sys; sys.exit(0 if sys.version_info < (3, 13) else 1)"
if not errorlevel 1 goto voz
echo.
echo A voz precisa do Python 3.12 (o Kokoro ainda nao roda no 3.13). Preparando o ambiente com o 3.12...
py -3.12 --version >nul 2>nul || winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
py -3.12 --version >nul 2>nul
if errorlevel 1 (
  echo O Python 3.12 foi instalado. Feche esta janela e rode o instalar.cmd de novo para terminar a voz.
  pause
  exit /b
)
call .venv\Scripts\deactivate.bat
rmdir /s /q .venv
py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r central\requirements.txt
:voz
python -m pip install -r central\requirements-voz.txt
if errorlevel 1 echo A voz nao instalou: me mande o erro acima. O resto do assistente funciona sem ela.
:fim
echo.
echo Pronto. Agora rode o testar.cmd
pause
