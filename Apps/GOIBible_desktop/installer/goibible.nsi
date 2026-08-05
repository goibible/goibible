!define APP_NAME "GOI Bible"
!define APP_EXE "GOIBible.exe"
!define COMPANY "GOI Bible"
!define INSTALL_DIR "$LOCALAPPDATA\GOIBible"

Name "${APP_NAME}"
OutFile "..\dist\goibible_install.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel user
Unicode true

Icon "..\goibible\resources\goibible-icon.ico"
UninstallIcon "..\goibible\resources\goibible-icon.ico"

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "1.0.0.0"
VIAddVersionKey "ProductVersion" "1.0.0.0"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "..\dist\GOIBible-win\GOIBible\*"

  CreateDirectory "$SMPROGRAMS\GOI Bible"
  CreateShortcut "$SMPROGRAMS\GOI Bible\GOI Bible.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\goibible-icon.ico"
  CreateShortcut "$DESKTOP\GOI Bible.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\goibible-icon.ico"

  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GOIBible" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GOIBible" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GOIBible" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GOIBible" "Publisher" "${COMPANY}"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\GOI Bible.lnk"
  Delete "$SMPROGRAMS\GOI Bible\GOI Bible.lnk"
  RMDir "$SMPROGRAMS\GOI Bible"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GOIBible"
  RMDir /r "$INSTDIR"
SectionEnd
