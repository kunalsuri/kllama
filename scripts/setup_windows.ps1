# =============================================================================
#  setup_windows.ps1 — Windows Setup & Launcher for Kllama
# =============================================================================
#
#  USAGE (run in PowerShell — requires PowerShell 5.1 or later)
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#    .\scripts\setup_windows.ps1
#
#  WHAT IT DOES
#    1. Detects Windows version and CPU architecture (x86_64 / ARM64)
#    2. Identifies the best available package manager (winget → Chocolatey → Scoop)
#    3. Checks for required tools: Python 3, pip, git, ollama
#    4. Installs any missing tools via the detected package manager
#    5. Creates / re-uses a Python virtual environment at .venv\
#    6. Upgrades pip, wheel, and setuptools inside the venv
#    7. Installs / upgrades all Python packages from requirements.txt
#    8. Verifies the installed packages are importable (streamlit, ollama, httpx)
#    9. Launches the Streamlit app and opens it in the default browser
#
#  REQUIREMENTS
#    - Windows 10 (build 1809+) or Windows 11
#    - PowerShell 5.1 or PowerShell 7+ (both are supported)
#    - An internet connection for first-time dependency installation
#
#  ENVIRONMENT VARIABLES (all optional)
#    $env:STREAMLIT_PORT     — Port for the Streamlit server      (default: 8501)
#    $env:SKIP_PKG_MANAGER   — Set to "1" to skip pkg checks      (default: 0)
#    $env:RECREATE_VENV      — Set to "1" to rebuild .venv        (default: 0)
#
# =============================================================================

#Requires -Version 5.1

# Use strict mode to catch common scripting errors.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Initialised here so the cleanup trap below can reference them safely under
# Set-StrictMode regardless of where the script exits.
$VenvWasNew = $false
$VenvDir    = $null   # overwritten to the real path once $ScriptDir is resolved

# On any terminating error, remove a newly-created (and therefore incomplete)
# virtual environment so the next run starts from a clean slate.
trap {
    if ($VenvWasNew -and $VenvDir -and (Test-Path $VenvDir)) {
        Write-Warn "Removing incomplete virtual environment due to setup failure…"
        Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
    }
    break
}

# =============================================================================
#  Colour helpers & logging
# =============================================================================

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║             🦙  Kllama — Windows Setup & Launcher            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info  { param([string]$Msg) Write-Host "[INFO]  $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Cyan  }
function Write-Ok    { param([string]$Msg) Write-Host "[OK]    $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Green }
function Write-Warn  { param([string]$Msg) Write-Host "[WARN]  $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Yellow }
function Write-Err   { param([string]$Msg) Write-Host "[ERROR] $(Get-Date -Format 'HH:mm:ss')  $Msg" -ForegroundColor Red }
function Write-Step  { param([string]$Msg) Write-Host "`n▶ $Msg" -ForegroundColor White -BackgroundColor DarkCyan }

# =============================================================================
#  Helper: check if a command / executable is available
# =============================================================================

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# =============================================================================
#  Helper: invoke a command with retry on failure
# =============================================================================

function Invoke-WithRetry {
    param(
        [scriptblock]$Command,
        [int]$MaxAttempts = 3,
        [int]$DelaySeconds = 5,
        [string]$Description = "command"
    )
    $attempt = 0
    while ($attempt -lt $MaxAttempts) {
        try {
            & $Command
            return
        } catch {
            $attempt++
            if ($attempt -ge $MaxAttempts) {
                Write-Err "Failed after $MaxAttempts attempt(s): $Description"
                throw
            }
            Write-Warn "Attempt $attempt/$MaxAttempts failed — retrying in ${DelaySeconds}s…"
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

# =============================================================================
#  SECTION 0 — Banner & OS validation
# =============================================================================

Write-Banner

# Confirm we are running on Windows.
if ($PSVersionTable.PSVersion.Major -ge 6) {
    if (-not $IsWindows) {
        Write-Err "This script is designed for Windows only."
        exit 1
    }
}

# Detect architecture.
$OsArch = if ([System.Environment]::Is64BitOperatingSystem) {
    if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "ARM64" } else { "x86_64" }
} else { "x86 (32-bit)" }

Write-Info "Architecture  : $OsArch"
Write-Info "OS Version    : $([System.Environment]::OSVersion.VersionString)"
Write-Info "PowerShell    : $($PSVersionTable.PSVersion)"

# Read optional environment variables with safe defaults.
$StreamlitPort   = if ($env:STREAMLIT_PORT)   { $env:STREAMLIT_PORT   } else { "8501" }
$SkipPkgManager  = if ($env:SKIP_PKG_MANAGER) { $env:SKIP_PKG_MANAGER } else { "0" }
$RecreateVenv    = if ($env:RECREATE_VENV)    { $env:RECREATE_VENV    } else { "0" }

# Resolve the project directory (this script lives in scripts/; parent = project root).
$ScriptDir    = $PSScriptRoot
$ProjectRoot  = Split-Path $ScriptDir -Parent
$VenvDir      = Join-Path $ProjectRoot ".venv"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

Write-Info "Project root  : $ProjectRoot"
Write-Info "Virtual env   : $VenvDir"
Write-Info "Streamlit port: $StreamlitPort"

# =============================================================================
#  SECTION 1 — Validate project files
# =============================================================================

Write-Step "Validating project files"

if (-not (Test-Path (Join-Path $ProjectRoot "kllama.py"))) {
    Write-Err "kllama.py not found in $ProjectRoot"
    Write-Info "Please run this script from inside the project directory."
    exit 1
}

if (-not (Test-Path $Requirements)) {
    Write-Err "requirements.txt not found at $Requirements"
    exit 1
}

Write-Ok "kllama.py and requirements.txt found."

# =============================================================================
#  SECTION 2 — Detect package manager (winget → Chocolatey → Scoop)
# =============================================================================

Write-Step "Detecting package manager"

$PkgManager = $null

if ($SkipPkgManager -eq "1") {
    Write-Warn "SKIP_PKG_MANAGER=1 — skipping package manager checks."
} else {
    # Prefer winget (built into Windows 10 1809+ and Windows 11).
    if (Test-Command "winget") {
        $PkgManager = "winget"
        Write-Ok "Package manager: winget (Windows Package Manager)"
    }
    # Fall back to Chocolatey if available.
    elseif (Test-Command "choco") {
        $PkgManager = "choco"
        Write-Ok "Package manager: Chocolatey"
    }
    # Fall back to Scoop.
    elseif (Test-Command "scoop") {
        $PkgManager = "scoop"
        Write-Ok "Package manager: Scoop"
    }
    else {
        Write-Warn "No supported package manager found (winget / choco / scoop)."
        Write-Warn "System dependencies (Python, git, ollama) must be installed manually."
        Write-Info "winget is built into Windows 10 1809+ and Windows 11."
        Write-Info "Chocolatey: https://chocolatey.org/install"
        Write-Info "Scoop:      https://scoop.sh"
        $PkgManager = $null
    }
}

# =============================================================================
#  SECTION 3 — Install system dependencies
# =============================================================================

Write-Step "Checking and installing system dependencies"

if ($SkipPkgManager -eq "1" -or $null -eq $PkgManager) {
    Write-Warn "Skipping automatic package installation."
} else {
    # ── Python ────────────────────────────────────────────────────────────────
    if (-not (Test-Command "python") -and -not (Test-Command "python3")) {
        Write-Info "Python not found. Installing via $PkgManager…"
        switch ($PkgManager) {
            "winget" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Python" -Command {
                    winget install --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
                }
            }
            "choco" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Python" -Command {
                    choco install python --yes --no-progress
                }
            }
            "scoop" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Python" -Command {
                    scoop install python
                }
            }
        }
        # Refresh PATH so python is available immediately.
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        Write-Ok "Python installed."
    } else {
        Write-Ok "Python already present."
    }

    # ── git ───────────────────────────────────────────────────────────────────
    if (-not (Test-Command "git")) {
        Write-Info "git not found. Installing via $PkgManager…"
        switch ($PkgManager) {
            "winget" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install git" -Command {
                    winget install --id Git.Git --accept-source-agreements --accept-package-agreements --silent
                }
            }
            "choco" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install git" -Command {
                    choco install git --yes --no-progress
                }
            }
            "scoop" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install git" -Command {
                    scoop install git
                }
            }
        }
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        Write-Ok "git installed."
    } else {
        Write-Ok "git already present: $(git --version 2>&1)"
    }

    # ── ollama ────────────────────────────────────────────────────────────────
    if (-not (Test-Command "ollama")) {
        Write-Info "Ollama not found. Installing via $PkgManager…"
        switch ($PkgManager) {
            "winget" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Ollama" -Command {
                    winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements --silent
                }
            }
            "choco" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Ollama" -Command {
                    choco install ollama --yes --no-progress
                }
            }
            "scoop" {
                Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "Install Ollama" -Command {
                    scoop install ollama
                }
            }
        }
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        if (Test-Command "ollama") {
            Write-Ok "Ollama installed."
        } else {
            Write-Warn "Ollama installation complete, but a system reboot or new terminal session may be required."
        }
    } else {
        Write-Ok "Ollama already present."
    }
}

# =============================================================================
#  SECTION 4 — Check Python 3 (≥ 3.10)
# =============================================================================

Write-Step "Checking Python 3"

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
    Write-Err "Python 3 not found on PATH."
    Write-Info "Download from https://www.python.org/downloads/"
    Write-Info "Or install via winget: winget install Python.Python.3.12"
    exit 1
}

$PythonVersion = & $PythonBin --version 2>&1
Write-Ok "Python found: $PythonVersion ($PythonBin)"

# Enforce minimum version 3.10.
$VersionNumbers = & $PythonBin -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
$Major, $Minor = $VersionNumbers.Split('.') | ForEach-Object { [int]$_ }

if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 10)) {
    Write-Err "Python 3.10 or newer is required. Found: $PythonVersion"
    Write-Info "Download Python 3.12: https://www.python.org/downloads/"
    exit 1
}
Write-Ok "Python version OK (>= 3.10)"

# =============================================================================
#  SECTION 5 — Create / re-use Python virtual environment
# =============================================================================

Write-Step "Setting up Python virtual environment"

if ($RecreateVenv -eq "1" -and (Test-Path $VenvDir)) {
    Write-Warn "RECREATE_VENV=1 — removing existing virtual environment…"
    Remove-Item -Recurse -Force $VenvDir
    Write-Ok "Old virtual environment removed."
}

if (Test-Path $VenvDir) {
    Write-Info "Existing virtual environment found at $VenvDir"
} else {
    Write-Info "Creating virtual environment at $VenvDir…"
    Invoke-WithRetry -MaxAttempts 2 -DelaySeconds 3 -Description "Create venv" -Command {
        & $PythonBin -m venv --upgrade-deps $VenvDir
    }
    $VenvWasNew = $true
    Write-Ok "Virtual environment created."
}

# Activate the virtual environment for the remainder of this script.
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    Write-Err "Virtual environment activation script not found: $ActivateScript"
    exit 1
}

try {
    & $ActivateScript
    Write-Ok "Virtual environment activated."
} catch {
    Write-Err "Failed to activate virtual environment: $_"
    Write-Info "If you see an execution policy error, run:"
    Write-Info "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}

# Verify pip is available inside the venv.
if (-not (Test-Command "pip")) {
    Write-Err "pip not found inside the virtual environment."
    exit 1
}

$PipVersion  = (& pip --version 2>&1) -replace "pip ([^\s]+).*", '$1'
$PyVenvCheck = & python --version 2>&1
Write-Ok "Venv Python: $PyVenvCheck  |  pip: $PipVersion"

# =============================================================================
#  SECTION 6 — Upgrade pip, wheel, and setuptools
# =============================================================================

Write-Step "Upgrading pip and build tools"

Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 5 -Description "Upgrade pip" -Command {
    pip install --quiet --upgrade pip
}
Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 5 -Description "Upgrade wheel/setuptools" -Command {
    pip install --quiet --upgrade wheel setuptools
}
Write-Ok "pip, wheel, and setuptools are up to date."

# =============================================================================
#  SECTION 7 — Install Python packages from requirements.txt
# =============================================================================

Write-Step "Installing Python packages from requirements.txt"

Write-Info "Running: pip install -r $Requirements"
Invoke-WithRetry -MaxAttempts 3 -DelaySeconds 10 -Description "pip install -r requirements.txt" -Command {
    pip install --no-cache-dir --upgrade -r $Requirements
}
Write-Ok "All Python packages installed."

# =============================================================================
#  SECTION 8 — Verify critical package imports
# =============================================================================

Write-Step "Verifying package imports"

$CriticalModules = @("streamlit", "ollama", "httpx")
foreach ($module in $CriticalModules) {
    $result = & python -c "import $module" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to import '$module': $result"
        Write-Info "Try: `$env:RECREATE_VENV='1'; .\scripts\setup_windows.ps1"
        exit 1
    }
    Write-Ok "  ✔  $module"
}

Write-Ok "All critical imports verified."

# =============================================================================
#  SECTION 9 — Check Ollama Service
# =============================================================================

Write-Step "Verifying Ollama service status"

if (Test-Command "ollama") {
    # Check if the Ollama service is reachable on the default local port.
    try {
        $OllamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        Write-Ok "Ollama service is running locally."
    } catch {
        Write-Warn "Ollama service is NOT running or not responding on http://localhost:11434."
        Write-Warn "Please start the Ollama application before running Kllama prompts."
    }
} else {
    Write-Warn "Ollama CLI is not installed or not in PATH."
}

# =============================================================================
#  SECTION 10 — Launch Streamlit
# =============================================================================

Write-Step "Launching Streamlit application"

Write-Host ""
Write-Host "✅  Setup complete!" -ForegroundColor Green -NoNewline
Write-Host "  Opening http://localhost:$StreamlitPort in your browser…" -ForegroundColor Cyan
Write-Host "   Press Ctrl + C to stop the server." -ForegroundColor White
Write-Host ""

# Change to the project root so relative paths in kllama.py resolve correctly.
Set-Location $ProjectRoot

# Open the browser after a short delay to let Streamlit start up.
$BrowserJob = Start-Job -ScriptBlock {
    param($port)
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:$port"
} -ArgumentList $StreamlitPort

# Launch Streamlit — this blocks until the user presses Ctrl+C.
try {
    streamlit run kllama.py `
        "--server.port=$StreamlitPort" `
        "--server.headless=false" `
        "--browser.gatherUsageStats=false"
} finally {
    # Cleanup only the browser-launch background job.
    $BrowserJob | Remove-Job -Force
}
