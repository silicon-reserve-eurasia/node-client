# Silicon Reserve Eurasia - Zero-Friction Windows Installer
# Usage: Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/silicon-reserve-eurasia/node-client/main/install.ps1'))

$OrgName = "silicon-reserve-eurasia"
$RepoName = "node-client"
$Branch = "main"
$BaseDir = "C:\SiliconReserve"

# --- 1. SELF-ELEVATION (Force Admin) ---
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[*] Elevating to Administrator..." -ForegroundColor Cyan
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "[SILICON RESERVE] Initializing Sovereign Node..." -ForegroundColor Cyan

# --- 2. DEPENDENCY INJECTION (The Auto-Installer) ---
Write-Host "[*] Auditing System Dependencies..." -ForegroundColor Yellow

# A. Python Check
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "    [!] Python missing. Installing via Winget..." -ForegroundColor Magenta
    winget install -e --id Python.Python.3.10 --scope machine --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "    [+] Python Installed." -ForegroundColor Green
}

# B. Docker Check (The Heavy Lift)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "    [!] Docker missing. Installing via Winget..." -ForegroundColor Magenta
    winget install -e --id Docker.DockerDesktop --scope machine --accept-package-agreements --accept-source-agreements
    
    # Docker needs a reboot. Set persistence to resume after reboot.
    Write-Host "    [!] Docker requires a REBOOT to activate WSL2." -ForegroundColor Red
    Write-Host "    [*] Setting auto-resume trigger..."
    
    # Create a Resume Script
    $ResumeScript = "$BaseDir\resume_install.ps1"
    if (-not (Test-Path -Path $BaseDir)) { New-Item -ItemType Directory -Path $BaseDir -Force | Out-Null }
    
    # We simply download and run this script again after reboot
    $ResumeCmd = "Start-Sleep -Seconds 30; Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/$OrgName/$RepoName/$Branch/install.ps1'))"
    Set-Content -Path $ResumeScript -Value $ResumeCmd
    
    # Add to RunOnce Registry
    Set-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name "SiliconReserveSetup" -Value "powershell.exe -ExecutionPolicy Bypass -File $ResumeScript"
    
    Write-Host "    [!] SYSTEM WILL REBOOT IN 10 SECONDS TO FINISH INSTALLATION." -ForegroundColor Red
    Start-Sleep -Seconds 10
    Restart-Computer -Force
    exit
}

# --- 3. PAYLOAD DEPLOYMENT ---
if (-not (Test-Path -Path $BaseDir)) { New-Item -ItemType Directory -Path $BaseDir | Out-Null }
Set-Location -Path $BaseDir

Write-Host "[*] Fetching Protocols..." -ForegroundColor Yellow
$BaseUrl = "https://raw.githubusercontent.com/$OrgName/$RepoName/$Branch"

$Files = @("main.py", "container_manager.py", "process_controller.py", "requirements.txt", "hardware.py", "classifier.py", "reporter.py")

foreach ($File in $Files) {
    try {
        Invoke-WebRequest -Uri "$BaseUrl/$File" -OutFile $File
        Write-Host "    + $File" -ForegroundColor Green
    } catch {
        Write-Host "    [X] Failed to fetch $File" -ForegroundColor Red
    }
}

# --- 4. FINALIZATION ---
Write-Host "[*] Updating Python Libraries..." -ForegroundColor Yellow
pip install -r requirements.txt --disable-pip-version-check | Out-Null

Write-Host "[*] Registering Background Service..." -ForegroundColor Yellow
$TaskName = "SiliconReserveNode"
$Action = New-ScheduledTaskAction -Execute "python" -Argument "$BaseDir\main.py"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -TaskName $TaskName -Description "Silicon Reserve Node" | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "[SUCCESS] Node is ONLINE and PERSISTENT." -ForegroundColor Green
Write-Host "The owner can now close this window. The bank is open."
Start-Sleep -Seconds 5
