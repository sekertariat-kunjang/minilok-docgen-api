# PowerShell Script to create a Desktop Shortcut for Minilok DocGen
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$CurrentDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($CurrentDir)) { $CurrentDir = Get-Location }

# Shortcut Settings
$ShortcutPath = Join-Path $DesktopPath "Minilok DocGen.lnk"
$IconPath = Join-Path $CurrentDir "app_icon.ico"

# Build the PowerShell command to run inside the shortcut
# Opens browser after 3 seconds, then starts the server
$PsCommand = "-ExecutionPolicy Bypass -NoProfile -Command `"Set-Location '$CurrentDir'; Start-Process powershell -WindowStyle Hidden -ArgumentList '-Command Start-Sleep 3; Start-Process http://localhost:8000/static/index.html'; & '$CurrentDir\venv\Scripts\python.exe' '$CurrentDir\main.py'; Read-Host 'Tekan Enter untuk keluar'`""

# Create the shortcut targeting powershell.exe
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = $PsCommand
$Shortcut.WorkingDirectory = $CurrentDir
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "Buka Dashboard Minilok DocGen"
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "-----------------------------------------------------------"
Write-Host "  SHORTCUT BERHASIL DIBUAT DI DESKTOP!"
Write-Host "-----------------------------------------------------------"
Write-Host "Nama Shortcut: Minilok DocGen"
Write-Host "Target Folder : $CurrentDir"
Write-Host "-----------------------------------------------------------"
Write-Host "Sekarang Anda bisa membuka aplikasi langsung dari Desktop."
pause
