; Instalador do Ciello OS (Inno Setup 6). Gera CielloOS-Setup-<versão>.exe.
; Quem compila é o GitHub Actions (.github/workflows/instalador.yml). Para compilar no PC:
;   git archive --format=zip HEAD -o app.zip  e extraia em build\app  (só os arquivos do repositório)
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DVersao=1.0.0 /DFonte=..\build\app instalador\ciello.iss
; O instalador copia o programa para a pasta escolhida e roda instalador\preparar.ps1, que baixa as dependências.

#ifndef Versao
  #define Versao "0.0.0"
#endif
#ifndef Fonte
  #define Fonte "..\build\app"
#endif

[Setup]
AppId={{6B2C3F1E-7A3D-4C8B-9E21-C1E770C1E770}
AppName=Ciello OS
AppVersion={#Versao}
AppVerName=Ciello OS {#Versao}
AppPublisher=CIELLO
AppPublisherURL=https://github.com/MTCiello/AGENTE-DE-POSTAGEM
AppUpdatesURL=https://github.com/MTCiello/AGENTE-DE-POSTAGEM/releases
DefaultDirName={sd}\Ciello\CielloOS
DisableDirPage=no
UsePreviousAppDir=yes
DefaultGroupName=Ciello OS
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\build
OutputBaseFilename=CielloOS-Setup-{#Versao}
SetupIconFile=marca\ciello.ico
UninstallDisplayIcon={app}\instalador\marca\ciello.ico
UninstallDisplayName=Ciello OS
WizardStyle=modern
WizardImageFile=marca\assistente.bmp
WizardSmallImageFile=marca\assistente-pequeno.bmp
WizardImageStretch=no
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
pt.WelcomeLabel2=Este assistente vai instalar o Ciello OS {#Versao} no seu computador: a área de trabalho com o escritório de agentes, Financeiro, Comercial, Conteúdo, Anúncios e os estúdios de Vídeo e Voz.%n%nNo fim ele baixa o que o assistente precisa (Python, FFmpeg, Node.js, Claude Code e as bibliotecas). Deixe o computador ligado à internet.
pt.SelectDirDesc=Onde o Ciello OS vai ficar?
pt.SelectDirLabel3=O Ciello OS e os seus dados (leads, financeiro, rascunhos) ficam nesta pasta. Evite pastas sincronizadas como OneDrive.

[Types]
Name: "completa"; Description: "Completa (com o Estúdio de Voz, baixa uns 3 GB a mais)"
Name: "padrao"; Description: "Padrão"
Name: "personalizada"; Description: "Personalizada"; Flags: iscustom

[Components]
Name: "base"; Description: "Ciello OS (área de trabalho, escritório e agentes)"; Types: completa padrao personalizada; Flags: fixed
Name: "claude"; Description: "Claude Code (faz os agentes de IA trabalharem)"; Types: completa padrao
Name: "video"; Description: "Estúdio de Vídeo (Node.js, Remotion e HyperFrames)"; Types: completa padrao
Name: "voz"; Description: "Estúdio de Voz (Kokoro, Chatterbox e Whisper · uns 3 GB)"; Types: completa

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#Fonte}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\estado"

[Icons]
Name: "{autoprograms}\Ciello OS\Ciello OS"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\instalador\lancador.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\instalador\marca\ciello.ico"; Comment: "Abrir o Ciello OS"
Name: "{autoprograms}\Ciello OS\Atualizações do Ciello OS"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\instalador\atualizador.pyw"" --procurar"; WorkingDir: "{app}"; IconFilename: "{app}\instalador\marca\ciello.ico"; Comment: "Procurar e instalar versões novas"
Name: "{autoprograms}\Ciello OS\Reinstalar dependências"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\instalador\preparar.ps1"" -Pasta ""{app}"""; WorkingDir: "{app}"; IconFilename: "{app}\instalador\marca\ciello.ico"
Name: "{autoprograms}\Ciello OS\Desinstalar o Ciello OS"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Ciello OS"; Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\instalador\lancador.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\instalador\marca\ciello.ico"; Comment: "Abrir o Ciello OS"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\instalador\preparar.ps1"" -Pasta ""{app}"" {code:OpcoesPreparar}"; WorkingDir: "{app}"; StatusMsg: "Baixando e instalando as dependências (Python, FFmpeg, Node.js, bibliotecas)... pode levar uns minutos."; Flags: waituntilterminated
Filename: "{app}\.venv\Scripts\pythonw.exe"; Parameters: """{app}\instalador\lancador.pyw"""; WorkingDir: "{app}"; Description: "Abrir o Ciello OS agora"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; o que o instalador baixou depois; os seus dados (estado, comercial, financeiro, founder, audio) ficam na pasta
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\reels\node_modules"
Type: filesandordirs; Name: "{app}\ferramentas"
Type: filesandordirs; Name: "{app}\comercial\bin"

[Code]
function OpcoesPreparar(Param: String): String;
begin
  Result := '';
  if WizardIsComponentSelected('voz') then Result := Result + ' -Voz';
  if not WizardIsComponentSelected('video') then Result := Result + ' -SemVideo';
  if not WizardIsComponentSelected('claude') then Result := Result + ' -SemClaude';
end;
