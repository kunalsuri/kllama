from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_streamlit() -> subprocess.Popen[bytes]:
    streamlit_file = Path(__file__).with_name("kllama.py")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(streamlit_file)],
        cwd=streamlit_file.parent,
    )


def main() -> int:
    process = run_streamlit()
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())