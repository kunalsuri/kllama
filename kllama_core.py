from __future__ import annotations

from typing import Any, Mapping, Sequence, TypedDict
import json
import datetime
from pathlib import Path


DEFAULT_ASSISTANT_GREETING = "How may I assist you?"

# Cap on how many prior conversation messages are replayed to the model each
# turn. The system prompt is added separately and is never counted here, so
# steering is preserved even when older turns are dropped. 20 keeps several
# exchanges of context without letting an unbounded transcript eventually
# overflow a small local model's context window.
DEFAULT_MAX_HISTORY_MESSAGES = 20


class ChatMessage(TypedDict):
    role: str
    content: str


def initial_chat_history() -> list[ChatMessage]:
    return [{"role": "assistant", "content": DEFAULT_ASSISTANT_GREETING}]


def trim_history(
    messages: Sequence[Mapping[str, str]],
    max_messages: int | None = DEFAULT_MAX_HISTORY_MESSAGES,
) -> list[ChatMessage]:
    """Return at most ``max_messages`` of the most recent conversation turns.

    A ``max_messages`` of ``None`` (or a value larger than the history) keeps
    everything. Trimming keeps the *tail* so the model always sees the latest
    context; older turns are dropped first.
    """
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in messages
    ]
    if max_messages is None or len(history) <= max_messages:
        return history
    return history[-max_messages:]


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
    max_history_messages: int | None = DEFAULT_MAX_HISTORY_MESSAGES,
) -> list[ChatMessage]:
    payload: list[ChatMessage] = []
    prompt = system_prompt.strip()
    if prompt:
        payload.append({"role": "system", "content": prompt})

    history = trim_history(messages, max_history_messages)

    # Most LLM Jinja prompt templates (e.g. Qwen, Gemma) require the first
    # non-system message to be a user turn.  The UI seeds the session with a
    # synthetic assistant greeting so the chat window isn't empty, but that
    # message must never be forwarded to the model or it will raise
    # "No user query found in messages."
    while history and history[0]["role"] == "assistant":
        history = history[1:]

    payload.extend(history)
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


def ensure_history_ignored(workspace_dir: str | Path) -> Path:
    """Ensures that the chat-history folder exists and is strictly git ignored.
    
    1. Creates 'chat-history' directory in the workspace root.
    2. Writes a '.gitignore' with '*' inside the 'chat-history' directory.
    3. Checks the workspace root '.gitignore' and appends rules if not present.
    """
    workspace = Path(workspace_dir).resolve()
    history_dir = workspace / "chat-history"
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Inner gitignore
    inner_gitignore = history_dir / ".gitignore"
    if not inner_gitignore.exists() or inner_gitignore.read_text(encoding="utf-8").strip() != "*":
        inner_gitignore.write_text("*\n", encoding="utf-8")
        
    # 2. Main gitignore update
    main_gitignore = workspace / ".gitignore"
    if main_gitignore.exists():
        content = main_gitignore.read_text(encoding="utf-8")
        lines = content.splitlines()
        has_rule = any("chat-history" in line.strip() and not line.strip().startswith("#") for line in lines)
        if not has_rule:
            # Append rules
            with main_gitignore.open("a", encoding="utf-8") as f:
                f.write("\n# Local chat history folder\nchat-history/\n/chat-history/\n")
    else:
        main_gitignore.write_text("# Local chat history folder\nchat-history/\n/chat-history/\n", encoding="utf-8")
        
    return history_dir


def save_chat_history(
    messages: list[dict[str, str]],
    username: str,
    model: str,
    system_prompt: str,
    chat_id: str,
    workspace_dir: str | Path,
) -> Path:
    """Saves the active conversation to a timestamped JSON file in 'chat-history'."""
    history_dir = ensure_history_ignored(workspace_dir)
    file_path = history_dir / f"chat_history_{chat_id}.json"
    
    payload = {
        "timestamp": datetime.datetime.now().isoformat(),
        "username": username,
        "model": model,
        "system_prompt": system_prompt,
        "messages": messages,
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    return file_path


def load_chat_history(file_path: Path) -> dict[str, Any]:
    """Loads and returns chat history from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_chat_histories(workspace_dir: str | Path) -> list[dict[str, Any]]:
    """Lists saved chat histories sorted by timestamp descending."""
    history_dir = Path(workspace_dir).resolve() / "chat-history"
    if not history_dir.exists():
        return []
        
    histories = []
    for file_path in history_dir.glob("chat_history_*.json"):
        try:
            data = load_chat_history(file_path)
            # Extrapolate basic metadata
            timestamp_str = data.get("timestamp", "")
            username = data.get("username", "Student")
            model = data.get("model", "Unknown Model")
            messages = data.get("messages", [])
            
            # Find a preview snippet
            snippet = ""
            for msg in messages:
                if msg.get("role") == "user":
                    snippet = msg.get("content", "")
                    break
            if not snippet and messages:
                snippet = messages[0].get("content", "")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
                
            histories.append({
                "file_path": str(file_path),
                "chat_id": file_path.stem.replace("chat_history_", ""),
                "timestamp": timestamp_str,
                "username": username,
                "model": model,
                "snippet": snippet,
                "messages_count": len(messages)
            })
        except Exception:
            # Ignore malformed files
            continue
            
    # Sort by timestamp descending. If timestamp is empty, fallback to file mtime.
    def sort_key(item: dict[str, Any]) -> str:
        t = item["timestamp"]
        if not t:
            try:
                t = datetime.datetime.fromtimestamp(Path(item["file_path"]).stat().st_mtime).isoformat()
            except Exception:
                t = ""
        return t
        
    histories.sort(key=sort_key, reverse=True)
    return histories


def delete_chat_history(file_path: Path | str) -> None:
    """Deletes a chat history file."""
    p = Path(file_path)
    if p.exists():
        p.unlink()


def build_translation_payload(
    text: str,
    src_lang: str,
    target_lang: str,
    tone: str,
) -> list[dict[str, str]]:
    """Builds a chat payload suitable for translation using Ollama."""
    system_content = (
        "You are a professional, high-fidelity translator. "
        "Translate the user's text accurately. "
        "Do not include any explanations, introduction, context, or extra text. "
        "Output ONLY the final translated text."
    )
    
    guidelines = []
    if src_lang == "Detect Language":
        guidelines.append("Detect the language of the source text.")
    else:
        guidelines.append(f"The source text is in {src_lang}.")
        
    guidelines.append(f"Translate the text into {target_lang}.")
    
    if tone == "Casual":
        guidelines.append(
            "Adopt a casual, informal, and conversational tone. "
            "For languages with formal/informal distinctions (e.g., French 'tu' vs 'vous', "
            "German 'du' vs 'Sie', Spanish 'tú' vs 'usted', Turkish 'sen' vs 'siz'), "
            "you MUST use the informal/casual pronouns and verb conjugations (e.g., 'tu' in French)."
        )
    elif tone == "Formal":
        guidelines.append(
            "Adopt a formal, polite, and professional tone. "
            "For languages with formal/informal distinctions (e.g., French 'tu' vs 'vous', "
            "German 'du' vs 'Sie', Spanish 'tú' vs 'usted', Turkish 'sen' vs 'siz'), "
            "you MUST use the formal/polite pronouns and verb conjugations (e.g., 'vous' in French)."
        )
    else:
        guidelines.append("Use a natural, neutral, and standard tone appropriate for general translation.")
        
    user_content = (
        f"Instructions:\n"
        f"{' '.join(guidelines)}\n\n"
        f"Text to translate:\n"
        f"\"\"\"\n{text}\n\"\"\""
    )
    
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]