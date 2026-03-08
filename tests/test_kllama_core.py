from __future__ import annotations

from types import SimpleNamespace

from kllama_core import (
    build_chat_payload,
    extract_message_text,
    initial_chat_history,
    list_model_names,
    model_options,
    transcript_as_markdown,
)


def test_initial_chat_history_contains_default_greeting() -> None:
    assert initial_chat_history() == [
        {"role": "assistant", "content": "How may I assist you?"}
    ]


def test_list_model_names_normalizes_and_deduplicates() -> None:
    response = SimpleNamespace(
        models=[
            SimpleNamespace(model="mistral"),
            SimpleNamespace(model="gemma3"),
            SimpleNamespace(model="mistral"),
        ]
    )

    assert list_model_names(response) == ["gemma3", "mistral"]


def test_build_chat_payload_prepends_system_prompt() -> None:
    messages = [{"role": "user", "content": "Hello"}]

    assert build_chat_payload(messages, "Be concise") == [
        {"role": "system", "content": "Be concise"},
        {"role": "user", "content": "Hello"},
    ]


def test_extract_message_text_supports_dict_and_object_chunks() -> None:
    dict_chunk = {"message": {"content": "hello"}}
    object_chunk = SimpleNamespace(message=SimpleNamespace(content="world"))

    assert extract_message_text(dict_chunk) == "hello"
    assert extract_message_text(object_chunk) == "world"


def test_model_options_matches_ollama_shape() -> None:
    assert model_options(0.73, 0.91, 512) == {
        "temperature": 0.73,
        "top_p": 0.91,
        "num_predict": 512,
    }


def test_transcript_as_markdown_includes_metadata_and_messages() -> None:
    transcript = transcript_as_markdown(
        [
            {"role": "assistant", "content": "How may I assist you?"},
            {"role": "user", "content": "Explain local LLMs"},
        ],
        username="Kunal",
        model_name="gemma3",
    )

    assert "# Kllama Transcript" in transcript
    assert "- User: Kunal" in transcript
    assert "- Model: gemma3" in transcript
    assert "## Kllama" in transcript
    assert "## Kunal" in transcript