# Ciello OS: instala tudo o que o assistente e os agentes precisam no Windows.
# O instalador (CielloOS-Setup.exe) roda este script no fim; também dá para rodar à mão:
#   powershell -ExecutionPolicy Bypass -File instalador\preparar.ps1 [-Voz] [-SemVideo] [-SemClaude]
# Instala o que faltar: Python 3.12, Git, Node.js, FFmpeg, Claude Code; cria o .venv com as bibliotecas,
# o gerador de vídeo (Remotion e HyperFrames), o buscador do SDR e, se pedido, o Estúdio de Voz (uns 3 GB).
# Tudo fica anotado em estado\instalacao.log.
param(
  [string]$Pasta = (Split-Path -Parent $PSScriptRoot),
  [switch]$Voz,
  [switch]$SemVideo,
  [switch]$SemClaude
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = 'Ciello OS: preparando o seu PC'
Set-Location $Pasta
New-Item -ItemType Directory -Force -Path "$Pasta\estado" | Out-Null
Start-Transcript -Path "$Pasta\estado\instalacao.log" -Append | Out-Null
$env:PYTHONUTF8 = '1'
$avisos = New-Object System.Collections.Generic.List[string]

function Titulo($t) { Write-Host ''; Write-Host "==== $t ====" -ForegroundColor Cyan }
function Aviso($t) { Write-Host "[aviso] $t" -ForegroundColor Yellow; $avisos.Add($t) }
function Ok($t) { Write-Host "[ok] $t" -ForegroundColor Green }

function Recarregar-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
  foreach ($extra in @("$env:LOCALAPPDATA\Programs\Python\Python312", "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
                       "$env:ProgramFiles\nodejs", "$env:ProgramFiles\Git\cmd", "$env:USERPROFILE\.local\bin", "$Pasta\ferramentas\ffmpeg\bin")) {
    if ((Test-Path $extra) -and ($env:Path -notlike "*$extra*")) { $env:Path += ";$extra" }
  }
}

function Tem($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Winget($id) {
  if (-not (Tem 'winget')) { return $false }
  winget install -e --id $id --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  Recarregar-Path
  return $LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335189  # já instalado
}

function Baixar($url, $destino) {
  Write-Host "Baixando $url"
  Invoke-WebRequest -Uri $url -OutFile $destino -UseBasicParsing
}

function Adicionar-PathUsuario($dir) {
  $atual = [Environment]::GetEnvironmentVariable('Path', 'User')
  if ($atual -notlike "*$dir*") { [Environment]::SetEnvironmentVariable('Path', ($atual.TrimEnd(';') + ";$dir"), 'User') }
  Recarregar-Path
}

function Python312 {
  # o Kokoro e o Chatterbox (voz) ainda não rodam no 3.13: o assistente usa o 3.12
  if (Tem 'py') { & py -3.12 --version *> $null; if ($LASTEXITCODE -eq 0) { return @{ Exe = 'py'; Args = @('-3.12') } } }
  $local = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
  if (Test-Path $local) { return @{ Exe = $local; Args = @() } }
  return $null
}

Recarregar-Path
Write-Host ''
Write-Host '   CIELLO OS  ·  instalando as dependências' -ForegroundColor White
Write-Host "   Pasta: $Pasta"
Write-Host '   Pode levar de 10 a 30 minutos na primeira vez. Não feche esta janela.'

# ---------------------------------------------------------------- programas
Titulo 'Python 3.12'
$py = Python312
if (-not $py) {
  if (-not (Winget 'Python.Python.3.12')) {
    $exe = "$env:TEMP\python-3.12-instalador.exe"
    Baixar 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' $exe
    Start-Process $exe -Wait -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1', 'Include_test=0'
  }
  Recarregar-Path
  $py = Python312
}
if (-not $py) {
  Write-Host 'Não consegui instalar o Python 3.12. Instale pelo site python.org e rode o instalador de novo.' -ForegroundColor Red
  Stop-Transcript | Out-Null
  exit 1
}
$pyArgs = $py.Args
Ok "Python: $(& $py.Exe @pyArgs --version)"

Titulo 'Git'
if (Tem 'git') { Ok 'Git já instalado' } elseif (Winget 'Git.Git') { Ok 'Git instalado' } else { Aviso 'Git não instalou (só o Claude Code e o modo de teste usam).' }

Titulo 'FFmpeg (áudio e vídeo)'
if (-not (Tem 'ffmpeg')) {
  if (-not (Winget 'Gyan.FFmpeg') -or -not (Tem 'ffmpeg')) {
    $zip = "$env:TEMP\ffmpeg.zip"
    try {
      Baixar 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' $zip
      $tmp = "$env:TEMP\ffmpeg-ciello"; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
      Expand-Archive $zip $tmp -Force
      $bin = Get-ChildItem $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1
      New-Item -ItemType Directory -Force "$Pasta\ferramentas\ffmpeg\bin" | Out-Null
      Copy-Item "$($bin.DirectoryName)\*" "$Pasta\ferramentas\ffmpeg\bin" -Force
      Adicionar-PathUsuario "$Pasta\ferramentas\ffmpeg\bin"
    } catch { Aviso "FFmpeg não instalou: $_" }
  }
}
if (Tem 'ffmpeg') { Ok 'FFmpeg pronto' }

if (-not $SemVideo) {
  Titulo 'Node.js (gerador de vídeo)'
  if (Tem 'node') { Ok "Node $(node --version)" } elseif (Winget 'OpenJS.NodeJS.LTS') { Ok 'Node instalado' } else {
    try {
      $msi = "$env:TEMP\node-lts.msi"
      Baixar 'https://nodejs.org/dist/v22.20.0/node-v22.20.0-x64.msi' $msi
      Start-Process msiexec.exe -Wait -ArgumentList '/i', $msi, '/qn'
      Recarregar-Path
    } catch { Aviso "Node não instalou: $_" }
  }
}

if (-not $SemClaude) {
  Titulo 'Claude Code (os agentes de IA)'
  if (Tem 'claude') { Ok 'Claude Code já instalado' } else {
    try { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression; Recarregar-Path } catch { Aviso "Claude Code não instalou: $_" }
    if (Tem 'claude') { Ok 'Claude Code instalado. Na primeira vez, abra o Ciello OS e faça login na janela Claude Code.' }
  }
}

# ---------------------------------------------------------------- ambiente do assistente
Titulo 'Ambiente Python do assistente (.venv)'
$venvPy = "$Pasta\.venv\Scripts\python.exe"
if (Test-Path $venvPy) {
  $ver = & $venvPy -c "import sys; print(sys.version_info[:2] < (3, 13))"
  if ($ver -ne 'True') { Write-Host 'O .venv está num Python novo demais para a voz: refazendo no 3.12...'; Remove-Item "$Pasta\.venv" -Recurse -Force }
}
if (-not (Test-Path $venvPy)) { & $py.Exe @pyArgs -m venv "$Pasta\.venv" }
& $venvPy -m pip install --upgrade pip --disable-pip-version-check -q
& $venvPy -m pip install -r central\requirements.txt --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Aviso 'Algumas bibliotecas do Python não instalaram (veja acima).' } else { Ok 'Bibliotecas do Python' }

Titulo 'Buscador do Google Maps (SDR)'
& $venvPy central\sdr.py instalar-scraper
if ($LASTEXITCODE -ne 0) { Aviso 'O buscador do SDR não baixou agora: o SDR funciona com CSV e o Verificar tenta de novo.' }

$componentes = @('base')
if (-not $SemVideo -and (Tem 'npm')) {
  Titulo 'Estúdio de Vídeo (Remotion e HyperFrames)'
  Push-Location reels
  npm install --no-audit --no-fund
  if ($LASTEXITCODE -eq 0) { $componentes += 'video'; Ok 'Gerador de vídeo' } else { Aviso 'O gerador de vídeo não instalou (veja acima).' }
  $env:HYPERFRAMES_SKIP_SKILLS = '1'
  npx --yes hyperframes browser ensure
  if ($LASTEXITCODE -ne 0) { Write-Host 'O navegador do HyperFrames baixa na primeira vez que gerar um vídeo.' }
  Pop-Location
}

if ($Voz) {
  Titulo 'Estúdio de Voz (Kokoro, Chatterbox e Whisper · uns 3 GB)'
  & $venvPy -m pip install -r central\requirements-voz.txt --disable-pip-version-check
  if ($LASTEXITCODE -eq 0) { $componentes += 'voz'; Ok 'Estúdio de Voz' } else { Aviso 'A voz não instalou. Dá para tentar de novo no Ciello OS: Estúdio de Voz, Instalar agora.' }
}

# ---------------------------------------------------------------- fim
& $venvPy instalador\atualizacao.py manifesto | Out-Null
$versao = (Get-Content VERSION -ErrorAction SilentlyContinue | Select-Object -First 1)
@{ versao = $versao; componentes = $componentes; data = (Get-Date -Format s); avisos = $avisos } |
  ConvertTo-Json | Set-Content -Encoding UTF8 "$Pasta\estado\instalacao.json"

Titulo 'Conferindo'
& $venvPy central\verificar.py --rapido

Write-Host ''
if ($avisos.Count) { Write-Host "Terminou com $($avisos.Count) aviso(s). O log completo está em estado\instalacao.log" -ForegroundColor Yellow }
else { Write-Host 'Tudo pronto! Abra o Ciello OS pelo ícone na área de trabalho.' -ForegroundColor Green }
Stop-Transcript | Out-Null
exit 0
