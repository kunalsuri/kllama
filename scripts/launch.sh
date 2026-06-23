#!/usr/bin/env bash
# =============================================================================
#  launch.sh — Kllama | macOS / Linux launcher
#
#  Usage:
#    chmod +x launch.sh && ./launch.sh
#
#  What it does:
#    1. Verifies Python 3.10+ is on PATH
#    2. Creates / reuses a virtual environment at .venv/
#    3. Installs packages from requirements.txt
#    3.5 Checks if Ollama service is running
#    4. Launches Streamlit at http://localhost:8501
#
#  Environment variables (all optional):
#    STREAMLIT_PORT  — Port for the server (default: 8501)
#    RECREATE_VENV   — Set to 1 to delete and rebuild .venv
#    OLLAMA_HOST     — Host for the Ollama server (default: http://localhost:11434)
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# ── Suppress pip "new version" notices and force UTF-8 Python I/O ─────────────
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# ── Validate required project files ─────────────────────────────────────────
if [ ! -f "kllama.py" ]; then
    echo " [ERROR] kllama.py not found. Run launch.sh from inside the project folder."
    exit 1
fi
if [ ! -f "requirements.txt" ]; then
    echo " [ERROR] requirements.txt not found."
    exit 1
fi

STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo
echo " +----------------------------------------------------------+"
echo " |  🦙  Kllama  |  Setup & Launcher                         |"
echo " +----------------------------------------------------------+"
echo

# =============================================================================
#  STEP 1 — Verify Python 3.10+
# =============================================================================
echo " [1/4] Checking Python..."

if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found. Install Python 3.10+ from https://python.org"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo " [ERROR] Python 3.10+ required. Found: ${PY_VER}"
    exit 1
fi
echo " [OK]   Python ${PY_VER} found."

# =============================================================================
#  STEP 2 — Create or reuse virtual environment
# =============================================================================
echo
echo " [2/4] Setting up virtual environment..."

if [ "${RECREATE_VENV:-0}" = "1" ] && [ -d ".venv" ]; then
    echo " [WARN]  RECREATE_VENV=1 — removing existing .venv/ ..."
    rm -rf .venv
fi

FIRST_RUN=0
if [ ! -f ".venv/bin/activate" ]; then
    echo " [SETUP] Creating virtual environment at .venv/ ..."
    python3 -m venv --upgrade-deps .venv
    echo " [OK]   Virtual environment created."
    FIRST_RUN=1
else
    echo " [OK]   Existing virtual environment found."
fi

# shellcheck source=/dev/null
source .venv/bin/activate
echo " [OK]   Virtual environment activated."

# =============================================================================
#  STEP 3 — Install / verify packages
# =============================================================================
echo
echo " [3/4] Installing / verifying packages..."

if [ "$FIRST_RUN" -eq 1 ]; then
    python3 -m pip install --quiet --upgrade pip --disable-pip-version-check
    echo " [SETUP] Installing packages from requirements.txt ..."
    pip install --no-cache-dir -r requirements.txt --disable-pip-version-check
    echo " [OK]   All packages installed."
else
    python3 -m pip install --quiet --upgrade pip --disable-pip-version-check
    pip install --quiet --no-cache-dir -r requirements.txt --disable-pip-version-check
    echo " [OK]   Packages verified."
fi

# =============================================================================
#  STEP 3.5 — Check Ollama service status
# =============================================================================
echo
echo " [3.5/4] Checking Ollama service status..."

if curl -s -m 5 "${OLLAMA_HOST}/api/tags" &>/dev/null; then
    echo " [OK]   Ollama service is running at ${OLLAMA_HOST}."
else
    echo " [WARN]  Ollama service is NOT running or not responding on ${OLLAMA_HOST}."
    echo "         Please start the Ollama application before running Kllama prompts."
fi

# =============================================================================
#  STEP 4 — Launch Streamlit
# =============================================================================
echo
echo " [4/4] Starting Kllama..."

echo
echo " +----------------------------------------------------------+"
echo " |  App running at http://localhost:${STREAMLIT_PORT}"
echo " |  Press Ctrl+C to stop the server."
echo " +----------------------------------------------------------+"
echo

# Temporarily turn off exit-on-error so we can handle Streamlit stop behavior gracefully
set +e
streamlit run kllama.py \
    "--server.port=${STREAMLIT_PORT}" \
    "--server.headless=false" \
    "--browser.gatherUsageStats=false"
STREAMLIT_EXIT=$?
set -e

echo
if [ "$STREAMLIT_EXIT" -ne 0 ] && [ "$STREAMLIT_EXIT" -ne 130 ]; then
    echo " [WARN]  Streamlit stopped with an error (exit code ${STREAMLIT_EXIT})."
    echo "         Scroll up to see the error details."
    echo
fi

echo " Server stopped. Press Enter to close."
read -r
