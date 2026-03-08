from __future__ import annotations

from typing import Any, Mapping, Sequence, TypedDict


DEFAULT_ASSISTANT_GREETING = "How may I assist you?"


class ChatMessage(TypedDict):
    role: str
    content: str


def initial_chat_history() -> list[ChatMessage]:
    return [{"role": "assistant", "content": DEFAULT_ASSISTANT_GREETING}]


def list_model_names(response: Any) -> list[str]:
    models = getattr(response, "models", response)
    names: list[str] = []
    for model in models:
        name = getattr(model, "model", None) or getattr(model, "name", None)
        if name:
            names.append(str(name))
    return sorted(dict.fromkeys(names))


def build_chat_payload(
    messages: Sequence[Mapping[str, str]],
    system_prompt: str,
) -> list[ChatMessage]:
    payload: list[ChatMessage] = []
    prompt = system_prompt.strip()
    if prompt:
        payload.append({"role": "system", "content": prompt})
    payload.extend(
        {"role": message["role"], "content": message["content"]}
        for message in messages
    )
    return payload


def extract_message_text(chunk: Any) -> str:
    if isinstance(chunk, dict):
        return str(chunk.get("message", {}).get("content", ""))

    message = getattr(chunk, "message", None)
    return str(getattr(message, "content", "") or "")


def model_options(temperature: float, top_p: float, max_tokens: int) -> dict[str, float | int]:
    return {
        "temperature": round(temperature, 2),
        "top_p": round(top_p, 2),
        "num_predict": max_tokens,
    }


def transcript_as_markdown(
    messages: list[ChatMessage],
    username: str,
    model_name: str,
) -> str:
    lines = [
        "# Kllama Transcript",
        "",
        f"- User: {username or 'User'}",
        f"- Model: {model_name}",
        "",
    ]

    role_labels = {
        "assistant": "Kllama",
        "user": username or "User",
    }

    for message in messages:
        label = role_labels.get(message["role"], message["role"].title())
        lines.append(f"## {label}")
        lines.append("")
        lines.append(message["content"].strip())
        lines.append("")

    return "\n".join(lines).strip() + "\n"