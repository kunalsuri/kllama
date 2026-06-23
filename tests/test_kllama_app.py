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


def test_streamlit_app_renders_translator_tab_and_translates() -> None:
    app_path = Path(__file__).resolve().parents[1] / "kllama.py"
    mocked_response = SimpleNamespace(models=[SimpleNamespace(model="gemma3")])
    
    # Mocking translation response stream
    streamed_chunks = iter(
        [
            {"message": {"content": "Hello"}},
            {"message": {"content": ", how are you?"}},
        ]
    )

    with patch.dict(os.environ, {"OLLAMA_HOST": "http://trans-test-host:11434"}):
        with patch("ollama.Client.list", return_value=mocked_response):
            with patch("ollama.Client.chat", return_value=streamed_chunks) as mocked_chat:
                app = AppTest.from_file(str(app_path))
                app.run()
                
                # Check default translator states
                assert app.session_state["translator_src_lang"] == "French"
                assert app.session_state["translator_target_lang"] == "English"
                assert app.session_state["translator_tone"] == "Neutral"
                
                # Set input text to translate
                app.text_area("translator_src_text_area").set_value("Bonjour, comment ça va ?").run()
                
                # Run translation
                app.button("translator_submit_btn").click().run()
                
    assert not app.exception
    assert app.session_state["translator_result"] == "Hello, how are you?"
    mocked_chat.assert_called_once()


def test_fetch_lmstudio_models_success() -> None:
    from kllama import fetch_lmstudio_models
    mock_response = SimpleNamespace(
        status_code=200,
        json=lambda: {"data": [{"id": "meta-llama-3-8b-instruct"}, {"id": "mistral-7b"}]},
        raise_for_status=lambda: None
    )
    with patch("httpx.get", return_value=mock_response) as mock_get:
        fetch_lmstudio_models.clear()
        models = fetch_lmstudio_models("http://localhost:1234")
        assert models == ["meta-llama-3-8b-instruct", "mistral-7b"]
        mock_get.assert_called_once_with("http://localhost:1234/v1/models", timeout=5.0)


def test_stream_reply_lmstudio() -> None:
    from kllama import stream_reply_lmstudio
    
    class FakeResponse:
        def __init__(self):
            pass
        def raise_for_status(self):
            pass
        def iter_lines(self):
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"Hello \"}}]}"
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"world!\"}}]}"
            yield "data: [DONE]"
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
            
    with patch("httpx.stream", return_value=FakeResponse()) as mock_stream:
        generator = stream_reply_lmstudio(
            lmstudio_host="http://localhost:1234",
            model_name="meta-llama-3-8b-instruct",
            messages=[{"role": "user", "content": "hi"}],
            system_prompt="be helpful",
            options={"num_predict": 100, "temperature": 0.7, "top_p": 0.9}
        )
        res = "".join(generator)
        assert res == "Hello world!"
        mock_stream.assert_called_once()


def test_streamlit_app_with_lmstudio_enabled() -> None:
    app_path = Path(__file__).resolve().parents[1] / "kllama.py"
    mocked_ollama_response = SimpleNamespace(models=[SimpleNamespace(model="gemma3")])
    mocked_lmstudio_response = SimpleNamespace(
        status_code=200,
        json=lambda: {"data": [{"id": "meta-llama-3-8b-instruct"}]},
        raise_for_status=lambda: None
    )

    with patch("ollama.Client.list", return_value=mocked_ollama_response):
        with patch("httpx.get", return_value=mocked_lmstudio_response):
            from kllama import fetch_lmstudio_models
            fetch_lmstudio_models.clear()
            app = AppTest.from_file(str(app_path))
            app.session_state["provider_lmstudio"] = True
            app.session_state["provider_ollama"] = True
            app.run()

    assert not app.exception
    assert app.session_state["selected_model"] != ""
