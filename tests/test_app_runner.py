from __future__ import annotations

from pathlib import Path
from typing import Iterator
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


def test_main_terminates_process_on_keyboard_interrupt() -> None:
    mocked_process = Mock()
    wait_results: Iterator[int | KeyboardInterrupt] = iter([KeyboardInterrupt(), 130])

    def wait_side_effect() -> int:
        result = next(wait_results)
        if isinstance(result, int):
            return result
        raise result

    mocked_process.wait.side_effect = wait_side_effect

    with patch("app_runner.run_streamlit", return_value=mocked_process):
        assert app_runner.main() == 130

    mocked_process.terminate.assert_called_once_with()
    assert mocked_process.wait.call_count == 2