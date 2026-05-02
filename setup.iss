; ── Ata Studio — Inno Setup Kurulum Scripti ─────────────────────────────────
; Derlemek için: Inno Setup Compiler ile bu dosyayı aç ve Compile
; İndir: https://jrsoftware.org/isinfo.php

#define AppName      "Ata Studio"
#define AppVersion   "5.0"
#define AppPublisher "Ata Studio"
#define AppURL       "https://github.com/ataeyvaz/AtaStudio"
#define AppExeName   "AtaStudio.exe"

[Setup]
AppId={{B7A2C4E1-3F8D-4A9B-BC12-7E5D6F8A3C21}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=AtaStudio_v{#AppVersion}_Setup
SetupIconFile=eagle.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} v{#AppVersion}

[Languages]
Name: "turkish";  MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english";  MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Masaüstü kısayolu oluştur";  GroupDescription: "Ek görevler:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Hızlı başlatma kısayolu";    GroupDescription: "Ek görevler:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Ana exe
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; FFmpeg — projede mevcut
Source: "ffmpeg.exe";  DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ffplay.exe";  DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Lisans ve readme
Source: "LICENSE";   DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"
Name: "{group}\{#AppName} Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";   Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// FFmpeg PATH'e ekle
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppPath: string;
  CurrentPath: string;
begin
  if CurStep = ssPostInstall then
  begin
    AppPath := ExpandConstant('{app}');
    RegQueryStringValue(HKCU, 'Environment', 'Path', CurrentPath);
    if Pos(AppPath, CurrentPath) = 0 then
    begin
      RegWriteStringValue(HKCU, 'Environment', 'Path',
        CurrentPath + ';' + AppPath);
    end;
  end;
end;
