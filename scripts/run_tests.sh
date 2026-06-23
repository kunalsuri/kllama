#!/usr/bin/env bash
# =============================================================================
#  run_tests.sh — One-click test runner for Kllama (macOS / Linux)
#
#  Usage:
#    chmod +x run_tests.sh && ./run_tests.sh        # run all tests
#    ./run_tests.sh --network                        # kept for compatibility
#    ./run_tests.sh --cov                            # + coverage report
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo
echo "========================================"
echo " Kllama | Test Suite"
echo "========================================"
echo

# ── Activate virtual environment if present ──────────────────────────────────
if [ -f ".venv/bin/activate" ]; then
    echo "[*] Activating virtual environment (.venv) ..."
    # shellcheck source=/dev/null
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "[*] Activating virtual environment (venv) ..."
    # shellcheck source=/dev/null
    source venv/bin/activate
else
    echo "[!] No .venv found — running with system Python."
    echo "    For isolation: python -m venv .venv && source .venv/bin/activate"
    echo
fi

# ── Install dev dependencies ─────────────────────────────────────────────────
echo "[*] Installing developer dependencies (editable mode with dev extras) ..."
pip install -e .[dev] -q
echo

# ── Parse arguments ──────────────────────────────────────────────────────────
NETWORK=false
COV=false

for arg in "$@"; do
    case "$arg" in
        --network) NETWORK=true ;;
        --cov)     COV=true ;;
    esac
done

# ── Build pytest command ─────────────────────────────────────────────────────
PYTEST_ARGS=("--tb=short" "-v")

# Note: Kllama tests are offline-only, but we accept the parameter for compatibility.
if [ "$NETWORK" = true ]; then
    echo "[*] Network flag detected (Kllama tests are offline-only, running normal suite)."
fi

if [ "$COV" = true ]; then
    echo "[*] Installing pytest-cov for coverage reporting ..."
    pip install pytest-cov -q
    PYTEST_ARGS+=("--cov=kllama" "--cov=kllama_core" "--cov-report=term-missing")
    echo "[*] Coverage mode: terminal report enabled for kllama modules."
fi

echo

# ── Run pytest ────────────────────────────────────────────────────────────────
echo "[*] Running tests ..."
echo

set +e
pytest "${PYTEST_ARGS[@]}"
EXIT_CODE=$?
set -e

# ── Summary ───────────────────────────────────────────────────────────────────
echo
echo "========================================"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo " RESULT: ALL TESTS PASSED  ✓"
else
    echo " RESULT: SOME TESTS FAILED  ✗"
    echo " Review the output above for details."
fi
echo "========================================"
echo

exit "$EXIT_CODE"
