; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "SPS HC20 - Suite"
#define MyAppVersion "0.7.3"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{E5FB9DBF-2A0C-46E8-B5B3-3DFAE1D2E50B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} version {#MyAppVersion}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\installers
OutputBaseFilename=sps-hc20_suite-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\*.*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "doc\consolle.pdf"; DestDir: "{app}"
Source: "doc\report.pdf"; DestDir: "{app}"
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Consolle"; Filename: "{app}\consolle.exe"; WorkingDir: "{app}"
Name: "{group}\Manuale Consolle"; Filename: "{app}\consolle.pdf"
Name: "{group}\Referto Gara"; Filename: "{app}\report.exe"; WorkingDir: "{app}"
Name: "{group}\Manuale Referto Gara"; Filename: "{app}\report.pdf"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Consolle"; Filename: "{app}\consolle.exe"; WorkingDir: "{app}"; Tasks: desktopicon
