from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_with_mocked_ollama_models() -> None:
    app_path = Path(__file__).resolve().parents[1] / "kllama.py"
    mocked_response = SimpleNamespace(models=[SimpleNamespace(model="gemma3")])

    with patch("ollama.Client.list", return_value=mocked_response):
        app = AppTest.from_file(str(app_path))
        app.run()

    assert not app.exception
    assert app.title[0].value == "Kllama"
    assert len(app.chat_input) == 1


def test_streamlit_app_shows_model_load_error_when_ollama_fails() -> None:
    app_path = Path(__file__).resolve().parents[1] / "kllama.py"

    with patch.dict(os.environ, {"OLLAMA_HOST": "http://offline-test-host:11434"}):
        with patch("ollama.Client.list", side_effect=httpx.ConnectError("Ollama offline")):
            app = AppTest.from_file(str(app_path))
            app.run()

    assert not app.exception
    assert len(app.error) >= 1


def test_stream_reply_preserves_partial_output_on_midstream_error() -> None:
    from kllama import stream_reply

    def failing_stream():
        yield {"message": {"content": "Partial "}}
        yield {"message": {"content": "answer"}}
        raise httpx.ReadError("connection dropped")

    fake_client = SimpleNamespace(chat=lambda **kwargs: failing_stream())

    produced = list(
        stream_reply(fake_client, "gemma3", [], "", {})
    )

    assert "".join(produced[:2]) == "Partial answer"
    assert "Response interrupted" in produced[-1]


def test_stream_reply_reraises_when_nothing_was_streamed() -> None:
    from kllama import stream_reply

    def immediately_failing_stream():
        raise httpx.ConnectError("offline")
        yield  # pragma: no cover - makes this a generator

    fake_client = SimpleNamespace(chat=lambda **kwargs: immediately_failing_stream())

    try:
        list(stream_reply(fake_client, "gemma3", [], "", {}))
    except httpx.HTTPError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected the error to propagate")


def test_streamlit_app_accepts_prompt_and_streams_mocked_response() -> None:
    app_path = Path(__file__).resolve().parents[1] / "kllama.py"
    mocked_response = SimpleNamespace(models=[SimpleNamespace(model="gemma3")])
    streamed_chunks = iter(
        [
            {"message": {"content": "Local models keep "}},
            {"message": {"content": "the workflow private."}},
        ]
    )

    with patch.dict(os.environ, {"OLLAMA_HOST": "http://chat-test-host:11434"}):
        with patch("ollama.Client.list", return_value=mocked_response):
            with patch("ollama.Client.chat", return_value=streamed_chunks) as mocked_chat:
                with patch(
                    "streamlit.write_stream",
                    side_effect=lambda stream: "".join(part for part in stream),
                ):
                    app = AppTest.from_file(str(app_path))
                    app.run()
                    app.chat_input[0].set_value("Explain local AI in one sentence").run()

    assert not app.exception
    mocked_chat.assert_called_once()
    messages = app.session_state["messages"]
    assert messages[-2]["content"] == "Explain local AI in one sentence"
    assert messages[-1]["content"] == "Local models keep the workflow private."