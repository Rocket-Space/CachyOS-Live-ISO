# Rocket Mode — Installer Overlay (Windows WPF/Forms)
# Muestra overlay durante instalación de juegos (FitGirl, etc.)
# Ubicacion: C:\RocketOS\rocket-overlay.ps1

param(
    [string]$GameName = "Juego",
    [string]$ExePath = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Rocket Mode — Instalando: $GameName"
$form.Size = New-Object System.Drawing.Size(520, 320)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(8, 8, 16)
$form.ForeColor = [System.Drawing.Color]::FromArgb(0, 240, 255)
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.TopMost = $true

# Title
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "🚀 ROCKET MODE"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(0, 240, 255)
$lblTitle.AutoSize = $true
$lblTitle.Location = New-Object System.Drawing.Point(20, 15)
$form.Controls.Add($lblTitle)

# Status
$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Instalando: $GameName`nEjecutable: $ExePath"
$lblStatus.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$lblStatus.ForeColor = [System.Drawing.Color]::FromArgb(180, 200, 230)
$lblStatus.Size = New-Object System.Drawing.Size(470, 50)
$lblStatus.Location = New-Object System.Drawing.Point(20, 60)
$form.Controls.Add($lblStatus)

# Progress
$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Style = "Marquee"
$progress.Size = New-Object System.Drawing.Size(460, 8)
$progress.Location = New-Object System.Drawing.Point(20, 120)
$form.Controls.Add($progress)

# ── Buttons ──
$btnRetry = New-Object System.Windows.Forms.Button
$btnRetry.Text = "🔄 Reintentar"
$btnRetry.Size = New-Object System.Drawing.Size(140, 40)
$btnRetry.Location = New-Object System.Drawing.Point(20, 220)
$btnRetry.BackColor = [System.Drawing.Color]::FromArgb(20, 20, 40)
$btnRetry.ForeColor = [System.Drawing.Color]::FromArgb(0, 240, 255)
$btnRetry.FlatStyle = "Flat"
$btnRetry.Add_Click({
    $lblStatus.Text = "Reiniciando instalador..."
    Start-Sleep -Seconds 1
    shutdown /r /t 3
})
$form.Controls.Add($btnRetry)

$btnTerminal = New-Object System.Windows.Forms.Button
$btnTerminal.Text = "💻 Terminal"
$btnTerminal.Size = New-Object System.Drawing.Size(140, 40)
$btnTerminal.Location = New-Object System.Drawing.Point(180, 220)
$btnTerminal.BackColor = [System.Drawing.Color]::FromArgb(20, 20, 40)
$btnTerminal.ForeColor = [System.Drawing.Color]::FromArgb(0, 240, 255)
$btnTerminal.FlatStyle = "Flat"
$btnTerminal.Add_Click({
    Start-Process "powershell.exe" -WindowStyle Normal
})
$form.Controls.Add($btnTerminal)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Text = "✕ Volver a Rocket OS"
$btnCancel.Size = New-Object System.Drawing.Size(160, 40)
$btnCancel.Location = New-Object System.Drawing.Point(340, 220)
$btnCancel.BackColor = [System.Drawing.Color]::FromArgb(60, 20, 20)
$btnCancel.ForeColor = [System.Drawing.Color]::FromArgb(255, 80, 80)
$btnCancel.FlatStyle = "Flat"
$btnCancel.Add_Click({
    $form.Close()
    shutdown /r /t 0
})
$form.Controls.Add($btnCancel)

# Launch installer in background
if ($ExePath -and (Test-Path $ExePath)) {
    $proc = Start-Process -FilePath $ExePath -PassThru -WindowStyle Normal
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 2000
    $timer.Add_Tick({
        if ($proc.HasExited) {
            $timer.Stop()
            $lblStatus.Text = "✅ Instalación completada. Reiniciando a Rocket OS..."
            $progress.Style = "Continuous"
            $progress.Value = 100
            Start-Sleep -Seconds 3
            $form.Close()
            shutdown /r /t 0
        }
    })
    $timer.Start()
}

[void]$form.ShowDialog()
