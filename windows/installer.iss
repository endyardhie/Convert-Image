#ifndef AppVersion
#define AppVersion "3.0.0"
#endif
#ifndef AppFileVersion
#define AppFileVersion "3.0.0.0"
#endif
#define AppId "{{2B414F21-4B8D-4DB6-9E69-7EE68D08C822}"

[Setup]
AppId={{2B414F21-4B8D-4DB6-9E69-7EE68D08C822}
AppName=Convert Image
AppVersion={#AppVersion}
VersionInfoCompany=Endy Ardhie
VersionInfoProductName=Convert Image
VersionInfoProductVersion={#AppFileVersion}
VersionInfoProductTextVersion={#AppVersion}
VersionInfoVersion={#AppFileVersion}
VersionInfoTextVersion={#AppFileVersion}
VersionInfoDescription=Convert Image Setup
VersionInfoCopyright=Copyright (c) 2026 Endy Ardhie
AppPublisher=Endy Ardhie
AppPublisherURL=https://github.com/endyardhie/Convert-Image
AppSupportURL=https://github.com/endyardhie/Convert-Image/issues
DefaultDirName={localappdata}\Programs\Convert Image
DefaultGroupName=Convert Image
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=Convert-Image-{#AppVersion}-Windows-x64-Setup
SetupIconFile=..\assets\branding\app.ico
UninstallDisplayIcon={app}\ConvertImage.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes
SetupLogging=yes

[Files]
Source: "..\dist\ConvertImage\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Convert Image"; Filename: "{app}\ConvertImage.exe"
Name: "{group}\Hapus Convert Image"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\Classes\CLSID\{#AppId}"; ValueType: string; ValueData: "Convert Image"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\CLSID\{#AppId}\InprocServer32"; ValueType: string; ValueData: "{app}\ConvertImageShell.dll"
Root: HKCU; Subkey: "Software\Classes\CLSID\{#AppId}\InprocServer32"; ValueType: string; ValueName: "ThreadingModel"; ValueData: "Apartment"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpg\shellex\ContextMenuHandlers\ConvertImage"; ValueType: string; ValueData: "{#AppId}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.jpeg\shellex\ContextMenuHandlers\ConvertImage"; ValueType: string; ValueData: "{#AppId}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.png\shellex\ContextMenuHandlers\ConvertImage"; ValueType: string; ValueData: "{#AppId}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.webp\shellex\ContextMenuHandlers\ConvertImage"; ValueType: string; ValueData: "{#AppId}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.avif\shellex\ContextMenuHandlers\ConvertImage"; ValueType: string; ValueData: "{#AppId}"; Flags: uninsdeletekey

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir, ConfigPath: String;
begin
  if CurStep = ssPostInstall then begin
    ConfigDir := ExpandConstant('{localappdata}\Convert Image\config');
    ConfigPath := ConfigDir + '\config.json';
    ForceDirectories(ConfigDir);
    if not FileExists(ConfigPath) then
      SaveStringToFile(ConfigPath, '{"speed":0,"threads":4}' + #13#10, False);
  end;
end;

[Messages]
FinishedLabel=Convert Image sudah terpasang.%n%nPilih gambar di File Explorer, lalu klik kanan > Convert Image. Pada Windows 11, pilih Show more options terlebih dahulu.%n%nAnda juga dapat membuka Convert Image dari menu Start.
