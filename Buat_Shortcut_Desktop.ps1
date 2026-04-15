# PowerShell Script to create a Desktop Shortcut for Minilok DocGen
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$CurrentDir = Get-Location

# Shortcut Settings
$ShortcutPath = Join-Path $DesktopPath "Minilok DocGen.lnk"
$TargetPath = Join-Path $CurrentDir "Buka_Aplikasi.bat"
$IconPath = Join-Path $CurrentDir "app_icon.ico"
$WorkingDirectory = $CurrentDir

# Create the shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $WorkingDirectory
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "Buka Dashboard Minilok DocGen"
$Shortcut.Save()

Write-Host "-----------------------------------------------------------"
Write-Host "  SHORTCUT BERHASIL DIBUAT DI DESKTOP!"
Write-Host "-----------------------------------------------------------"
Write-Host "Nama Shortcut: Minilok DocGen"
Write-Host "Path Target  : $TargetPath"
Write-Host "Path Icon    : $IconPath"
Write-Host "-----------------------------------------------------------"
Write-Host "Sekarang Anda bisa membuka aplikasi langsung dari Desktop."
pause
