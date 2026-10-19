@echo off
chcp 65001 >nul
rem Agenda o briefing do chefe de gabinete todo dia as 7h (Agendador de Tarefas do Windows, sem Claude e sem internet).
rem O resultado fica em estado\briefing\AAAA-MM-DD.md e no painel (porta 3200).
rem   agendar.cmd          cria ou atualiza a tarefa
rem   agendar.cmd remover  apaga a tarefa
cd /d "%~dp0"
if /i "%~1"=="remover" (
  schtasks /Delete /F /TN "Ciello Bom Dia"
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
pause
