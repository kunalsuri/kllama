from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import app_runner


def test_run_streamlit_uses_active_python_and_app_file() -> None:
    streamlit_file = Path(app_runner.__file__).with_name("kllama.py")

    with patch("app_runner.subprocess.Popen") as mocked_popen:
        app_runner.run_streamlit()

    mocked_popen.assert_called_once_with(
        [app_runner.sys.executable, "-m", "streamlit", "run", str(streamlit_file)],
        cwd=streamlit_file.parent,
    )


def test_main_waits_for_streamlit_process() -> None:
    mocked_process = Mock()
    mocked_process.wait.return_value = 0

    with patch("app_runner.run_streamlit", return_value=mocked_process):
        assert app_runner.main() == 0

    mocked_process.wait.assert_called_once_with()