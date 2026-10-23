@echo off
chcp 65001 >nul
rem Agenda no Agendador de Tarefas do Windows:
rem   "Ciello Bom Dia"  todo dia as 7h, o briefing do gerente (sem Claude e sem internet) -> estado\briefing\
rem   "Ciello Piloto"   de hora em hora, o piloto automatico da rede social (Rede social no Ciello OS)
rem   agendar.cmd          cria ou atualiza a tarefa
rem   agendar.cmd remover  apaga a tarefa
cd /d "%~dp0"
if /i "%~1"=="remover" (
  schtasks /Delete /F /TN "Ciello Bom Dia"
  schtasks /Delete /F /TN "Ciello Piloto"
  pause
  exit /b
)
if not exist .venv\Scripts\python.exe (
  echo Rode antes o instalar.cmd
  pause
  exit /b 1
)
schtasks /Create /F /SC DAILY /ST 07:00 /TN "Ciello Bom Dia" /TR "\"%~dp0.venv\Scripts\python.exe\" \"%~dp0central\briefing.py\""
if errorlevel 1 (echo Nao consegui criar a tarefa. Tente clicar com o botao direito e "Executar como administrador".) else (echo Pronto: todo dia as 7h o briefing sai em estado\briefing\. Para testar agora: schtasks /Run /TN "Ciello Bom Dia")
schtasks /Create /F /SC HOURLY /MO 1 /ST 00:05 /TN "Ciello Piloto" /TR "\"%~dp0.venv\Scripts\python.exe\" \"%~dp0central\piloto.py\" rodar"
if errorlevel 1 (echo Nao consegui criar a tarefa do piloto.) else (echo Pronto: o piloto da rede social roda de hora em hora. Pausar: Rede social, Piloto, Pausado. Para testar agora: schtasks /Run /TN "Ciello Piloto")
pause
