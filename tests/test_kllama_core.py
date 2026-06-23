from __future__ import annotations

from types import SimpleNamespace

from kllama_core import (
    DEFAULT_MAX_HISTORY_MESSAGES,
    build_chat_payload,
    extract_message_text,
    initial_chat_history,
    list_model_names,
    model_options,
    transcript_as_markdown,
    trim_history,
    build_translation_payload,
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


def test_trim_history_keeps_recent_tail() -> None:
    messages = [{"role": "user", "content": str(i)} for i in range(5)]

    assert trim_history(messages, max_messages=2) == [
        {"role": "user", "content": "3"},
        {"role": "user", "content": "4"},
    ]


def test_trim_history_keeps_everything_when_under_cap() -> None:
    messages = [{"role": "user", "content": "only"}]

    assert trim_history(messages, max_messages=10) == messages
    assert trim_history(messages, max_messages=None) == messages


def test_build_chat_payload_caps_history_but_keeps_system_prompt() -> None:
    history = [{"role": "user", "content": str(i)} for i in range(50)]

    payload = build_chat_payload(history, "Stay grounded")

    assert payload[0] == {"role": "system", "content": "Stay grounded"}
    # System prompt is not counted against the history cap.
    assert len(payload) == DEFAULT_MAX_HISTORY_MESSAGES + 1
    assert payload[-1] == {"role": "user", "content": "49"}


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


def test_build_translation_payload_detect_language() -> None:
    payload = build_translation_payload("Bonjour", "Detect Language", "English", "Neutral")
    assert len(payload) == 2
    assert payload[0]["role"] == "system"
    assert "professional, high-fidelity translator" in payload[0]["content"]
    assert "Detect the language of the source text." in payload[1]["content"]
    assert "Translate the text into English." in payload[1]["content"]
    assert "Use a natural, neutral, and standard tone" in payload[1]["content"]
    assert "Bonjour" in payload[1]["content"]


def test_build_translation_payload_specific_languages() -> None:
    payload = build_translation_payload("Hello", "English", "French", "Neutral")
    assert "The source text is in English." in payload[1]["content"]
    assert "Translate the text into French." in payload[1]["content"]


def test_build_translation_payload_casual_tone() -> None:
    payload = build_translation_payload("Please sit down", "English", "French", "Casual")
    assert "Adopt a casual, informal, and conversational tone." in payload[1]["content"]
    assert "informal/casual pronouns" in payload[1]["content"]


def test_build_translation_payload_formal_tone() -> None:
    payload = build_translation_payload("Please sit down", "English", "French", "Formal")
    assert "Adopt a formal, polite, and professional tone." in payload[1]["content"]
    assert "formal/polite pronouns" in payload[1]["content"]