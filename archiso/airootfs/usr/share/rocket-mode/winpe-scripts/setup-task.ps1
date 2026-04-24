# Scheduled Task XML for Windows
# Runs rocket-boot.ps1 at logon in Rocket Mode
# Import: schtasks /create /tn "RocketMode" /xml C:\RocketOS\rocket-task.xml

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\RocketOS\rocket-boot.ps1"

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable -Priority 4

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask -TaskName "RocketMode" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "Rocket Mode auto-launcher" -Force

Write-Host "✅ Tarea programada 'RocketMode' creada. Se ejecutará en cada inicio."
