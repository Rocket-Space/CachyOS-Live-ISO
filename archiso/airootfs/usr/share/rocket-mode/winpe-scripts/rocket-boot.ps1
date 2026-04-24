# Rocket Mode — Windows Side PowerShell Script
# Ejecutado al arrancar Windows en modo Rocket
# Ubicacion: C:\RocketOS\rocket-boot.ps1

param(
    [switch]$InstallMode
)

$CONFIG_PATH = "X:\rocket-mode-next.json"   # Cargado desde EFI/boot
$LOG_PATH    = "C:\RocketOS\rocket.log"
$RETURN_FLAG = "C:\RocketOS\return-to-rocket.flag"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts | $msg" | Tee-Object -FilePath $LOG_PATH -Append | Out-Null
}

function Disable-UnnecessaryServices {
    Write-Log "Desactivando servicios no esenciales..."
    $KILL_SERVICES = @(
        "wuauserv","WaaSMedicSvc","DiagTrack","dmwappushservice",
        "SysMain","TabletInputService","Fax","WMPNetworkSvc",
        "XblAuthManager","XblGameSave","XboxGipSvc","XboxNetApiSvc",
        "MapsBroker","lfsvc","SharedAccess","WSearch"
    )
    foreach ($svc in $KILL_SERVICES) {
        try {
            Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
            Set-Service  -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
        } catch {}
    }
    Write-Log "Servicios desactivados."
}

function Apply-GamingTweaks {
    Write-Log "Aplicando tweaks de rendimiento..."

    # Prioridad CPU alta para juegos
    $regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    Set-ItemProperty -Path $regPath -Name "SystemResponsiveness" -Value 0 -Type DWord -EA SilentlyContinue

    $gamesPath = "$regPath\Tasks\Games"
    if (-not (Test-Path $gamesPath)) { New-Item -Path $gamesPath -Force | Out-Null }
    Set-ItemProperty -Path $gamesPath -Name "Affinity"           -Value 0
    Set-ItemProperty -Path $gamesPath -Name "Background Only"    -Value "False"
    Set-ItemProperty -Path $gamesPath -Name "Clock Rate"         -Value 10000
    Set-ItemProperty -Path $gamesPath -Name "GPU Priority"       -Value 8
    Set-ItemProperty -Path $gamesPath -Name "Priority"           -Value 6
    Set-ItemProperty -Path $gamesPath -Name "Scheduling Category"-Value "High"

    # Deshabilitar Nagle para red
    Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" | ForEach-Object {
        Set-ItemProperty -Path $_.PSPath -Name "TcpAckFrequency" -Value 1 -Type DWord -EA SilentlyContinue
        Set-ItemProperty -Path $_.PSPath -Name "TCPNoDelay"      -Value 1 -Type DWord -EA SilentlyContinue
    }

    # Hardware-accelerated GPU scheduling (si disponible)
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" `
        -Name "HwSchMode" -Value 2 -Type DWord -EA SilentlyContinue

    Write-Log "Tweaks aplicados."
}

function Get-GameConfig {
    # Intentar desde EFI vars primero, luego archivo
    if (Test-Path $CONFIG_PATH) {
        return Get-Content $CONFIG_PATH | ConvertFrom-Json
    }
    # Fallback: buscar en boot partition
    $alt = "B:\rocket-mode-next.json"
    if (Test-Path $alt) { return Get-Content $alt | ConvertFrom-Json }
    return $null
}

function Launch-Game($exePath) {
    Write-Log "Lanzando: $exePath"
    if (-not (Test-Path $exePath)) {
        Write-Log "ERROR: No se encontro el ejecutable: $exePath"
        Show-ErrorAndReturn "No se encontró el juego: $exePath"
        return
    }
    $proc = Start-Process -FilePath $exePath -PassThru -WindowStyle Normal
    Write-Log "PID del juego: $($proc.Id)"
    $proc.WaitForExit()
    Write-Log "Juego terminado con codigo: $($proc.ExitCode)"
    Return-To-RocketOS
}

function Launch-Installer($exePath, $gameName) {
    Write-Log "Modo instalador: $exePath"
    Show-InstallerOverlay -GameName $gameName -ExePath $exePath

    # Instalador se lanza via overlay WPF (ver rocket-overlay.ps1)
    $overlayProc = Start-Process powershell -ArgumentList `
        "-File C:\RocketOS\rocket-overlay.ps1 -GameName '$gameName' -ExePath '$exePath'" `
        -PassThru -WindowStyle Normal
    $overlayProc.WaitForExit()
    Return-To-RocketOS
}

function Return-To-RocketOS {
    Write-Log "Regresando a Rocket OS..."
    # Limpiar procesos huerfanos (no los que necesita el juego)
    $KEEP_PROCESSES = @("explorer","dwm","csrss","smss","lsass","services","svchost")
    Get-Process | Where-Object {
        $_.Name -notin $KEEP_PROCESSES -and
        $_.Name -notmatch "^(audiodg|fontdrvhost|winlogon|wininit)$"
    } | ForEach-Object {
        try { $_.Kill() } catch {}
    }
    Start-Sleep -Seconds 2
    shutdown /r /t 0
}

function Show-ErrorAndReturn($msg) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $msg,
        "Rocket Mode — Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    Return-To-RocketOS
}

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
Write-Log "=== Rocket Mode iniciado ==="

Disable-UnnecessaryServices
Apply-GamingTweaks

$cfg = Get-GameConfig
if (-not $cfg) {
    Write-Log "No hay configuracion de juego. Regresando a Rocket OS."
    Return-To-RocketOS
    exit
}

Write-Log "Juego: $($cfg.game_name) | EXE: $($cfg.exe_path)"

if ($InstallMode -or $cfg.install_mode) {
    Launch-Installer -exePath $cfg.exe_path -gameName $cfg.game_name
} else {
    Launch-Game -exePath $cfg.exe_path
}
