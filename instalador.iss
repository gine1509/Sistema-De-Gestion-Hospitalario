#define MyAppName "Sistema de Gestión Hospitalario"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sistema de Gestión Hospitalario"
#define MyAppExeName "Sistema_Gestion_Hospitalario.exe"

[Setup]
AppId=SistemaGestionHospitalario
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\Sistema de Gestión Hospitalario
DefaultGroupName={#MyAppName}

OutputDir=instalador
OutputBaseFilename=Sistema_Gestion_Hospitalario_1.0.0

SetupIconFile=iconos\hospital.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes

[Files]
Source: "dist\Sistema_Gestion_Hospitalario\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Sistema de Gestión Hospitalario"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Sistema de Gestión Hospitalario"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Sistema de Gestión Hospitalario"; Flags: nowait postinstall skipifsilent