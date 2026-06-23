from __future__ import annotations

import json
from pathlib import Path
import pytest

from kllama_core import (
    ensure_history_ignored,
    save_chat_history,
    load_chat_history,
    list_chat_histories,
    delete_chat_history,
)


def test_ensure_history_ignored_creates_folders_and_files(tmp_path: Path) -> None:
    workspace_dir = tmp_path
    main_gitignore = workspace_dir / ".gitignore"
    
    # Run the function
    history_dir = ensure_history_ignored(workspace_dir)
    
    # Check that directory is created
    assert history_dir.exists()
    assert history_dir.is_dir()
    
    # Check inner gitignore
    inner_gitignore = history_dir / ".gitignore"
    assert inner_gitignore.exists()
    assert inner_gitignore.read_text(encoding="utf-8").strip() == "*"
    
    # Check main gitignore
    assert main_gitignore.exists()
    gitignore_content = main_gitignore.read_text(encoding="utf-8")
    assert "chat-history/" in gitignore_content
    assert "/chat-history/" in gitignore_content


def test_ensure_history_ignored_appends_to_existing_gitignore(tmp_path: Path) -> None:
    workspace_dir = tmp_path
    main_gitignore = workspace_dir / ".gitignore"
    main_gitignore.write_text("# Existing rules\n__pycache__/\n", encoding="utf-8")
    
    ensure_history_ignored(workspace_dir)
    
    gitignore_content = main_gitignore.read_text(encoding="utf-8")
    assert "__pycache__/" in gitignore_content
    assert "chat-history/" in gitignore_content
    
    # Running it again should not duplicate rules
    ensure_history_ignored(workspace_dir)
    assert gitignore_content == main_gitignore.read_text(encoding="utf-8")


def test_save_load_delete_chat_history(tmp_path: Path) -> None:
    messages = [
        {"role": "user", "content": "How's the weather?"},
        {"role": "assistant", "content": "It is sunny!"}
    ]
    username = "Alice"
    model = "gemma3"
    system_prompt = "You are a weather bot."
    chat_id = "test_12345"
    
    # Save chat history
    file_path = save_chat_history(messages, username, model, system_prompt, chat_id, tmp_path)
    
    assert file_path.exists()
    assert file_path.name == f"chat_history_{chat_id}.json"
    
    # Load and verify
    data = load_chat_history(file_path)
    assert data["username"] == username
    assert data["model"] == model
    assert data["system_prompt"] == system_prompt
    assert data["messages"] == messages
    assert "timestamp" in data
    
    # Delete and verify
    delete_chat_history(file_path)
    assert not file_path.exists()


def test_list_chat_histories_sorting_and_snippet(tmp_path: Path) -> None:
    # Save multiple chats with different contents and timestamps
    chat_1_id = "chat1"
    messages_1 = [{"role": "user", "content": "Short query"}]
    save_chat_history(messages_1, "User1", "modelA", "Prompt1", chat_1_id, tmp_path)
    
    chat_2_id = "chat2"
    messages_2 = [{"role": "user", "content": "This is a very long user query that should be truncated by our snippet logic."}]
    save_chat_history(messages_2, "User2", "modelB", "Prompt2", chat_2_id, tmp_path)
    
    histories = list_chat_histories(tmp_path)
    
    assert len(histories) == 2
    
    # Check snippets
    chat_2_meta = next(h for h in histories if h["chat_id"] == "chat2")
    chat_1_meta = next(h for h in histories if h["chat_id"] == "chat1")
    
    assert chat_1_meta["snippet"] == "Short query"
    assert chat_2_meta["snippet"].endswith("...")
    assert len(chat_2_meta["snippet"]) == 60
    assert chat_2_meta["snippet"].startswith("This is a very long user query")
    
    # Verify the structure has required attributes
    assert chat_1_meta["model"] == "modelA"
    assert chat_2_meta["model"] == "modelB"
    assert chat_1_meta["username"] == "User1"
