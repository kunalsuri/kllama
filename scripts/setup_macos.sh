#!/usr/bin/env bash
# =============================================================================
#  setup_macos.sh — macOS Setup & Launcher for Kllama
# =============================================================================
#
#  USAGE
#    chmod +x setup_macos.sh   # (first time only)
#    ./setup_macos.sh
#
#  WHAT IT DOES
#    1. Detects macOS architecture (Apple Silicon arm64 vs Intel x86_64)
#    2. Checks for required system tools: Python 3, pip, Homebrew, git, ollama
#    3. Installs any missing system tools (Homebrew → git → ollama)
#    4. Creates / re-uses a Python virtual environment at .venv/
#    5. Upgrades pip, wheel, and setuptools inside the venv
#    6. Installs / upgrades all Python packages from requirements.txt
#    7. Verifies the installed packages are importable
#    8. Checks the status of the local Ollama service
#    9. Launches the Streamlit app, which opens automatically in the browser
#
#  REQUIREMENTS
#    • macOS 12 Monterey or later (Apple Silicon or Intel)
#    • An internet connection for first-time dependency installation
#    • No sudo password is required — Homebrew installs user-space tools
#
#  ENVIRONMENT VARIABLES (all optional)
#    STREAMLIT_PORT  — Port for the Streamlit server             (default: 8501)
#    SKIP_BREW       — Set to "1" to skip Homebrew checks       (default: 0)
#    RECREATE_VENV   — Set to "1" to delete and rebuild .venv    (default: 0)
#    OLLAMA_HOST     — Host for the Ollama server (default: http://localhost:11434)
#
# =============================================================================

set -euo pipefail   # Exit immediately on error, unset variable, or pipe failure

# ─── Terminal colour helpers ──────────────────────────────────────────────────
if [ -t 1 ]; then
    C_RESET="\033[0m"
    C_BOLD="\033[1m"
    C_RED="\033[31m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_BLUE="\033[34m"
    C_CYAN="\033[36m"
else
    C_RESET="" C_BOLD="" C_RED="" C_GREEN="" C_YELLOW="" C_BLUE="" C_CYAN=""
fi

# ─── Logging functions ────────────────────────────────────────────────────────
log_info()   { echo -e "${C_BLUE}[INFO]${C_RESET}  $(date '+%H:%M:%S')  $*"; }
log_ok()     { echo -e "${C_GREEN}[OK]${C_RESET}    $(date '+%H:%M:%S')  $*"; }
log_warn()   { echo -e "${C_YELLOW}[WARN]${C_RESET}  $(date '+%H:%M:%S')  $*"; }
log_error()  { echo -e "${C_RED}[ERROR]${C_RESET} $(date '+%H:%M:%S')  $*" >&2; }
log_step()   { echo -e "\n${C_BOLD}${C_CYAN}▶ $*${C_RESET}"; }
log_banner() {
    echo -e "\n${C_BOLD}${C_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║             🦙  Kllama — macOS Setup & Launcher             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${C_RESET}"
}

# ─── Error handler ───────────────────────────────────────────────────────────
trap 'log_error "Script failed at line ${LINENO}. Exiting."; exit 1' ERR

# ─── Cleanup on unexpected exit ──────────────────────────────────────────────
_VENV_WAS_NEW=0
cleanup() {
    local exit_code=$?
    if [[ "$_VENV_WAS_NEW" == "1" && -d "${VENV_DIR:-}" && "$exit_code" -ne 0 ]]; then
        log_warn "Removing incomplete virtual environment due to setup failure…"
        rm -rf "$VENV_DIR"
    fi
}
trap cleanup EXIT

# ─── Helper: retry a command up to N times with a short pause ────────────────
retry() {
    local attempts="$1"
    local delay="$2"
    shift 2
    local count=0
    until "$@"; do
        count=$(( count + 1 ))
        if [ "$count" -ge "$attempts" ]; then
            log_error "Command failed after ${attempts} attempt(s): $*"
            return 1
        fi
        log_warn "Attempt ${count}/${attempts} failed — retrying in ${delay}s…"
        sleep "$delay"
    done
}

# ─── Helper: check if a command is on PATH ───────────────────────────────────
have() { command -v "$1" &>/dev/null; }

# =============================================================================
#  SECTION 0 — Banner & OS validation
# =============================================================================
log_banner

# Confirm we are actually running on macOS.
if [[ "$(uname -s)" != "Darwin" ]]; then
    log_error "This script is designed for macOS only. Detected OS: $(uname -s)"
    log_info  "For Linux, run:   ./scripts/setup_linux.sh"
    log_info  "For Windows, run: .\\scripts\\setup_windows.ps1  (in PowerShell)"
    exit 1
fi

# Detect CPU architecture.
ARCH="$(uname -m)"
if [[ "$ARCH" == "arm64" ]]; then
    log_info "Architecture: Apple Silicon (${ARCH})"
    BREW_PREFIX="/opt/homebrew"
else
    log_info "Architecture: Intel (${ARCH})"
    BREW_PREFIX="/usr/local"
fi

# Read optional environment variable overrides (safe defaults).
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
SKIP_BREW="${SKIP_BREW:-0}"
RECREATE_VENV="${RECREATE_VENV:-0}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS="${PROJECT_ROOT}/requirements.txt"

log_info "Project root  : ${PROJECT_ROOT}"
log_info "Virtual env   : ${VENV_DIR}"
log_info "Streamlit port: ${STREAMLIT_PORT}"
log_info "macOS version : $(sw_vers -productVersion)"

# =============================================================================
#  SECTION 1 — Validate project files
# =============================================================================
log_step "Validating project files"

if [[ ! -f "${PROJECT_ROOT}/kllama.py" ]]; then
    log_error "kllama.py not found in ${PROJECT_ROOT}."
    log_info  "Are you running this script from inside the project folder?"
    exit 1
fi

if [[ ! -f "$REQUIREMENTS" ]]; then
    log_error "requirements.txt not found at ${REQUIREMENTS}."
    exit 1
fi

log_ok "kllama.py and requirements.txt found."

# =============================================================================
#  SECTION 2 — Check / install Homebrew and system utilities
# =============================================================================
log_step "Checking Homebrew"

if [[ "$SKIP_BREW" == "1" ]]; then
    log_warn "SKIP_BREW=1 — skipping Homebrew checks."
else
    if have brew; then
        log_ok "Homebrew found at $(brew --prefix)"
    else
        log_warn "Homebrew not found. Installing…"
        log_info "This will download and run the official Homebrew installer."
        log_info "See https://brew.sh for details."
        retry 3 5 /bin/bash -c \
            "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for the remainder of this session.
        if [[ -x "${BREW_PREFIX}/bin/brew" ]]; then
            eval "$("${BREW_PREFIX}/bin/brew" shellenv)"
            log_ok "Homebrew installed and added to PATH for this session."
        else
            log_error "Homebrew installed but binary not found at ${BREW_PREFIX}/bin/brew"
            exit 1
        fi
    fi

    # ── Check / install git ───────────────────────────────────────────────────
    log_step "Checking git"
    if have git; then
        log_ok "git found: $(git --version)"
    else
        log_warn "git not found. Installing via Homebrew…"
        retry 3 5 brew install git
        log_ok "git installed: $(git --version)"
    fi

    # ── Check / install Ollama ────────────────────────────────────────────────
    log_step "Checking Ollama CLI"
    if have ollama; then
        log_ok "Ollama CLI found: $(ollama --version 2>&1 | head -1)"
    else
        log_warn "Ollama CLI not found. Installing via Homebrew cask…"
        retry 3 10 brew install --cask ollama
        if have ollama; then
            log_ok "Ollama installed."
        else
            log_error "Ollama installation failed."
            log_warn "Please install Ollama manually from https://ollama.com"
        fi
    fi
fi

# =============================================================================
#  SECTION 3 — Check Python 3 (≥ 3.10)
# =============================================================================
log_step "Checking Python 3"

PYTHON_BIN=""
for candidate in python3 python; do
    if have "$candidate"; then
        version_output="$("$candidate" --version 2>&1)"
        major="$(echo "$version_output" | grep -oE '[0-9]+' | head -1)"
        if [[ "$major" == "3" ]]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    log_error "Python 3 not found on PATH."
    log_info  "Install it from https://www.python.org/downloads/ or via:"
    log_info  "  brew install python"
    exit 1
fi

PYTHON_VERSION="$("$PYTHON_BIN" --version 2>&1)"
log_ok "Python found: ${PYTHON_VERSION} (${PYTHON_BIN})"

# Enforce minimum version 3.10.
PYTHON_MINOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)')"
PYTHON_MAJOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.major)')"
if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 10 ]]; }; then
    log_error "Python 3.10 or newer is required. Found: ${PYTHON_VERSION}"
    log_info  "Install a newer Python: brew install python  or  https://www.python.org/downloads/"
    exit 1
fi
log_ok "Python version OK (≥ 3.10)"

# =============================================================================
#  SECTION 4 — Create / re-use Python virtual environment
# =============================================================================
log_step "Setting up Python virtual environment"

if [[ "$RECREATE_VENV" == "1" && -d "$VENV_DIR" ]]; then
    log_warn "RECREATE_VENV=1 — removing existing virtual environment…"
    rm -rf "$VENV_DIR"
    log_ok "Old virtual environment removed."
fi

if [[ -d "$VENV_DIR" ]]; then
    log_info "Existing virtual environment found at ${VENV_DIR}."
else
    log_info "Creating virtual environment at ${VENV_DIR}…"
    "$PYTHON_BIN" -m venv --upgrade-deps "$VENV_DIR"
    _VENV_WAS_NEW=1
    log_ok "Virtual environment created."
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
log_ok "Virtual environment activated. Python: $(python --version), pip: $(pip --version | awk '{print $2}')"

# =============================================================================
#  SECTION 5 — Upgrade pip, wheel, and setuptools
# =============================================================================
log_step "Upgrading pip and build tools"

retry 3 5 pip install --quiet --upgrade pip
retry 3 5 pip install --quiet --upgrade wheel setuptools
log_ok "pip, wheel, and setuptools are up to date."

# =============================================================================
#  SECTION 6 — Install Python packages from requirements.txt
# =============================================================================
log_step "Installing Python packages from requirements.txt"

log_info "Running: pip install -r ${REQUIREMENTS}"
retry 3 10 pip install --no-cache-dir --upgrade -r "$REQUIREMENTS"
log_ok "All Python packages installed."

# =============================================================================
#  SECTION 7 — Verify critical package imports
# =============================================================================
log_step "Verifying package imports"

check_import() {
    local module="$1"
    if python -c "import ${module}" &>/dev/null; then
        log_ok "  ✔  ${module}"
    else
        log_error "Failed to import '${module}'."
        log_info  "Try: RECREATE_VENV=1 ./scripts/setup_macos.sh"
        exit 1
    fi
}

check_import streamlit
check_import ollama
check_import httpx

log_ok "All critical imports verified."

# =============================================================================
#  SECTION 8 — Verify Ollama Service Status
# =============================================================================
log_step "Verifying Ollama service status"

if curl -s -m 5 "${OLLAMA_HOST}/api/tags" &>/dev/null; then
    log_ok "Ollama service is running locally at ${OLLAMA_HOST}."
else
    log_warn "Ollama service is NOT running or not responding on ${OLLAMA_HOST}."
    log_warn "Please make sure to start the Ollama service before sending prompts to Kllama."
fi

# =============================================================================
#  SECTION 9 — Launch Streamlit
# =============================================================================
log_step "Launching Streamlit application"

echo
echo -e "${C_BOLD}${C_GREEN}✅  Setup complete!${C_RESET}"
echo -e "   Opening ${C_CYAN}http://localhost:${STREAMLIT_PORT}${C_RESET} in your browser…"
echo -e "   Press ${C_BOLD}Ctrl + C${C_RESET} to stop the server.\n"

cd "$PROJECT_ROOT"

exec streamlit run kllama.py \
    "--server.port=${STREAMLIT_PORT}" \
    "--server.headless=false" \
    "--browser.gatherUsageStats=false"
