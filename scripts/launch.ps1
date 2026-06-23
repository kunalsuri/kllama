#Requires -Version 5.1

# =============================================================================
#  launch.ps1 -- Kllama | Windows PowerShell launcher
#
#  Usage:
#    .\scripts\launch.ps1
#
#  What it does:
#    1. Verifies Python 3.10+ is on PATH
#    2. Creates / reuses a virtual environment at .venv/
#    3. Installs / updates packages from requirements.txt
#    4. Launches Streamlit at http://localhost:8501 and opens in browser
#
#  Environment variables (all optional):
#    $env:STREAMLIT_PORT  -- Port for the server (default: 8501)
#    $env:RECREATE_VENV   -- Set to 1 to delete and rebuild .venv
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve directories relative to this script
$ScriptDir    = $PSScriptRoot
$ProjectRoot  = Split-Path $ScriptDir -Parent
$VenvDir      = Join-Path $ProjectRoot ".venv"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

# == Validate required project files =========================================
if (-not (Test-Path (Join-Path $ProjectRoot "kllama.py"))) {
    Write-Error "[ERROR] kllama.py not found. Run launch.ps1 from inside the project folder."
    exit 1
}
if (-not (Test-Path $Requirements)) {
    Write-Error "[ERROR] requirements.txt not found."
    exit 1
}

# == Env defaults ============================================================
$StreamlitPort = if ($env:STREAMLIT_PORT) { $env:STREAMLIT_PORT } else { "8501" }
$RecreateVenv  = if ($env:RECREATE_VENV)  { $env:RECREATE_VENV } else { "0" }

$VenvWasNew = $false

# == Clean up incomplete venv on failure =====================================
trap {
    if ($VenvWasNew -and $VenvDir -and (Test-Path $VenvDir)) {
        Write-Host "[WARN]  Removing incomplete virtual environment due to launch failure..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
    }
    break
}

# == Helper: check if command is available ===================================
function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# == Logging helpers =========================================================
function Write-Banner {
    Write-Host ""
    Write-Host " +----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host " |  🦙  Kllama  |  Setup & Launcher                        |" -ForegroundColor Cyan
    Write-Host " +----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
}
function Write-Info  { param([string]$Msg) Write-Host "[INFO]  $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Cyan  }
function Write-Ok    { param([string]$Msg) Write-Host "[OK]    $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "[WARN]  $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "[ERROR] $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Red }

Write-Banner

# =============================================================================
#  STEP 1 -- Verify Python 3.10+
# =============================================================================
Write-Info "[1/4] Checking Python..."

$PythonBin = $null
foreach ($candidate in @("python", "python3", "py")) {
    if (Test-Command $candidate) {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python 3") {
            $PythonBin = $candidate
            break
        }
    }
}

if ($null -eq $PythonBin) {
    Write-Err "Python not found. Please install Python 3.10+ from https://python.org"
    exit 1
}

$PyVer = & $PythonBin -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$Major, $Minor = $PyVer.Split('.') | ForEach-Object { [int]$_ }

if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 10)) {
    Write-Err "Python 3.10+ required. Found: $PyVer"
    exit 1
}
Write-Ok "Python $PyVer found."

# =============================================================================
#  STEP 2 -- Create or reuse virtual environment
# =============================================================================
Write-Host ""
Write-Info "[2/4] Setting up virtual environment..."

if ($RecreateVenv -eq "1" -and (Test-Path $VenvDir)) {
    Write-Warn "RECREATE_VENV=1 -- removing existing .venv\ ..."
    Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
}

$FirstRun = $false
if (-not (Test-Path $VenvDir)) {
    Write-Info "Creating virtual environment at .venv\ ..."
    & $PythonBin -m venv --upgrade-deps $VenvDir
    $VenvWasNew = $true
    $FirstRun = $true
    Write-Ok "Virtual environment created."
} else {
    Write-Ok "Existing virtual environment found."
}

# Activate the venv
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    Write-Err "Virtual environment activation script not found: $ActivateScript"
    exit 1
}

& $ActivateScript
Write-Ok "Virtual environment activated."

# =============================================================================
#  STEP 3 -- Install / verify packages
# =============================================================================
Write-Host ""
Write-Info "[3/4] Installing / verifying packages..."

if ($FirstRun) {
    python -m pip install --quiet --upgrade pip
    Write-Info "Installing packages from requirements.txt ..."
    pip install --no-cache-dir -r $Requirements
    Write-Ok "All packages installed."
} else {
    pip install --quiet --no-cache-dir -r $Requirements
    Write-Ok "Packages verified."
}

# =============================================================================
#  STEP 4 -- Launch Streamlit
# =============================================================================
Write-Host ""
Write-Info "[4/4] Starting Kllama..."

Write-Host ""
Write-Host " +----------------------------------------------------------+" -ForegroundColor Green
Write-Host " |  App running at http://localhost:$StreamlitPort"              -ForegroundColor Green
Write-Host " |  Press Ctrl+C to stop the server."                          -ForegroundColor Green
Write-Host " +----------------------------------------------------------+" -ForegroundColor Green
Write-Host ""

# Change working directory to project root so Streamlit relative paths resolve correctly
Set-Location $ProjectRoot

# Launch browser job
$BrowserJob = Start-Job -ScriptBlock {
    param($port)
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:$port"
} -ArgumentList $StreamlitPort

try {
    streamlit run kllama.py `
        "--server.port=$StreamlitPort" `
        "--server.headless=false" `
        "--browser.gatherUsageStats=false"
} finally {
    $BrowserJob | Remove-Job -Force
}
