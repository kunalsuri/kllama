from __future__ import annotations

import os
import uuid
import datetime
import json
from pathlib import Path
from typing import Iterator

import httpx
import streamlit as st
from ollama import Client, ResponseError

from kllama_core import (
    build_chat_payload,
    extract_message_text,
    initial_chat_history,
    list_model_names,
    model_options,
    transcript_as_markdown,
    ensure_history_ignored,
    save_chat_history,
    load_chat_history,
    list_chat_histories,
    delete_chat_history,
    build_translation_payload,
)

DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "http://localhost:1234")
DEFAULT_SYSTEM_PROMPT = (
    "You are Kllama, a helpful local AI assistant for students, builders, and "
    "researchers. Respond clearly, stay grounded in the user's request, and say "
    "when you are uncertain."
)
# Bound every request to Ollama/LM Studio so a hung or model-loading server surfaces an
# error instead of freezing the UI indefinitely. Overridable for slow first
# loads of large local models.
REQUEST_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT", "120"))
# ollama wraps a connection failure in a builtin ConnectionError rather than an
# httpx error, so it must be caught explicitly alongside the HTTP errors.
OLLAMA_ERRORS = (ResponseError, httpx.HTTPError, ConnectionError)


def make_client(ollama_host: str) -> Client:
    return Client(host=ollama_host, timeout=REQUEST_TIMEOUT_SECONDS)


@st.cache_data(ttl=15, show_spinner=False)
def fetch_models(ollama_host: str) -> list[str]:
    response = make_client(ollama_host).list()
    return list_model_names(response)


@st.cache_data(ttl=15, show_spinner=False)
def fetch_lmstudio_models(lmstudio_host: str) -> list[str]:
    host = lmstudio_host.strip() or DEFAULT_LMSTUDIO_HOST
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    
    base_url = host.rstrip("/")
    if not base_url.endswith("/v1") and "/v1/" not in base_url:
        models_url = f"{base_url}/v1/models"
    else:
        models_url = f"{base_url}/models"

    response = httpx.get(models_url, timeout=5.0)
    response.raise_for_status()
    data = response.json()
    
    names = []
    for item in data.get("data", []):
        model_id = item.get("id")
        if model_id:
            names.append(str(model_id))
    return sorted(names)


def stream_reply_lmstudio(
    lmstudio_host: str,
    model_name: str,
    messages: list[dict[str, str]],
    system_prompt: str,
    options: dict[str, float | int],
) -> Iterator[str]:
    payload = build_chat_payload(messages, system_prompt)
    
    max_tokens = options.get("num_predict")
    temperature = options.get("temperature")
    top_p = options.get("top_p")
    
    body = {
        "model": model_name,
        "messages": payload,
        "temperature": temperature,
        "top_p": top_p,
        "stream": True,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
        
    host = lmstudio_host.strip() or DEFAULT_LMSTUDIO_HOST
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
        
    base_url = host.rstrip("/")
    if not base_url.endswith("/v1") and "/v1/" not in base_url:
        chat_url = f"{base_url}/v1/chat/completions"
    else:
        chat_url = f"{base_url}/chat/completions"
        
    wrote_any = False
    try:
        with httpx.stream("POST", chat_url, json=body, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    content = line[6:].strip()
                    if content == "[DONE]":
                        break
                    try:
                        chunk = json.loads(content)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        text = delta.get("content", "")
                        if text:
                            wrote_any = True
                            yield text
                    except Exception:
                        continue
    except Exception as error:
        if not wrote_any:
            raise
        yield f"\n\n_Response interrupted: {error}_"



def reset_conversation() -> None:
    st.session_state["messages"] = initial_chat_history()
    st.session_state["current_chat_id"] = None


def stream_reply(
    ollama_client: Client,
    model_name: str,
    messages: list[dict[str, str]],
    system_prompt: str,
    options: dict[str, float | int],
) -> Iterator[str]:
    stream = ollama_client.chat(
        model=model_name,
        messages=build_chat_payload(messages, system_prompt),
        options=options,
        stream=True,
    )
    wrote_any = False
    try:
        for chunk in stream:
            text = extract_message_text(chunk)
            if text:
                wrote_any = True
                yield text
    except OLLAMA_ERRORS as error:
        # If we have already streamed visible text, keep it and append an
        # inline notice rather than discarding the partial answer. If nothing
        # was produced yet, re-raise so the caller shows the full error panel.
        if not wrote_any:
            raise
        yield f"\n\n_Response interrupted: {error}_"


def inject_custom_css(theme: str) -> None:
    if theme == "dark":
        css = """
        <style>
        :root {
            --theme-primary: #6366f1;
            --theme-bg: #0b0f19;
            --theme-secondary-bg: #111827;
            --theme-text: #f3f4f6;
            --border-color: rgba(255, 255, 255, 0.08);
            --card-bg: #1f2937;
            --shadow-color: rgba(0, 0, 0, 0.25);
            --status-connected-bg: rgba(16, 185, 129, 0.1);
            --status-connected-border: rgba(16, 185, 129, 0.25);
            --status-connected-text: #10b981;
            --status-disconnected-bg: rgba(239, 68, 68, 0.1);
            --border-status-disconnected: rgba(239, 68, 68, 0.25);
            --status-disconnected-text: #ef4444;
        }
        </style>
        """
    else:
        css = """
        <style>
        :root {
            --theme-primary: #4f46e5;
            --theme-bg: #f8fafc;
            --theme-secondary-bg: #f1f5f9;
            --theme-text: #0f172a;
            --border-color: rgba(0, 0, 0, 0.08);
            --card-bg: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.05);
            --status-connected-bg: rgba(16, 185, 129, 0.08);
            --status-connected-border: rgba(16, 185, 129, 0.2);
            --status-connected-text: #059669;
            --status-disconnected-bg: rgba(220, 38, 38, 0.08);
            --border-status-disconnected: rgba(220, 38, 38, 0.2);
            --status-disconnected-text: #dc2626;
        }
        </style>
        """
        
    common_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Override Streamlit core theme variables dynamically */
    :root, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        --primary-color: var(--theme-primary) !important;
        --background-color: var(--theme-bg) !important;
        --secondary-background-color: var(--theme-secondary-bg) !important;
        --text-color: var(--theme-text) !important;
    }
    
    /* Header Customization overrides */
    h1 {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        margin: 0.5rem 0 0 0 !important;
        background: linear-gradient(135deg, var(--theme-primary), #3b82f6) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    /* Header divider */
    .header-divider {
        height: 1px;
        background-color: var(--border-color);
        margin: 1rem 0 2rem 0;
    }
    
    /* Styled Header Hero Badge */
    .badge {
        background: linear-gradient(135deg, var(--theme-primary), #3b82f6);
        color: white !important;
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 1.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stCaptionContainer"] {
        color: var(--theme-text) !important;
        opacity: 0.7;
        font-size: 1.05rem !important;
        margin-bottom: 0 !important;
    }
    
    /* Styled Connection Status */
    div.status-bar {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.5rem !important;
        font-size: 0.9rem !important;
        border: 1px solid var(--border-color) !important;
        transition: all 0.3s ease !important;
    }
    div.status-connected {
        background-color: var(--status-connected-bg) !important;
        border-color: var(--status-connected-border) !important;
        color: var(--status-connected-text) !important;
    }
    div.status-disconnected {
        background-color: var(--status-disconnected-bg) !important;
        border-color: var(--border-status-disconnected) !important;
        color: var(--status-disconnected-text) !important;
    }
    div.status-bar code {
        background-color: rgba(0, 0, 0, 0.08) !important;
        color: inherit !important;
        padding: 0.1rem 0.3rem !important;
        border-radius: 4px !important;
        font-family: monospace !important;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-online {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
        animation: pulse-online 2s infinite;
    }
    .dot-offline {
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444;
    }
    @keyframes pulse-online {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* Styled Metric Cards */
    div[data-testid="metric-container"] {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        box-shadow: 0 2px 5px var(--shadow-color) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px var(--shadow-color) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--theme-text) !important;
        opacity: 0.85 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: var(--theme-text) !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Expanders styling - only style outer border and radius */
    .stExpander {
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        background-color: transparent !important;
    }
    
    /* Buttons Customization */
    div.stButton > button, div.stDownloadButton > button {
        background-color: var(--card-bg) !important;
        color: var(--theme-text) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        border-color: var(--theme-primary) !important;
        color: var(--theme-primary) !important;
        background-color: var(--theme-secondary-bg) !important;
    }

    /* Tighten sidebar spacing */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-bottom: 0.2rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(common_css, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Kllama", page_icon="🦙", layout="wide")
    
    workspace_dir = Path(__file__).resolve().parent
    ensure_history_ignored(workspace_dir)
    
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    if "current_chat_id" not in st.session_state:
        st.session_state["current_chat_id"] = None
    if "pending_chat_load" not in st.session_state:
        st.session_state["pending_chat_load"] = None
    if "messages" not in st.session_state:
        reset_conversation()
    if "ollama_host" not in st.session_state:
        st.session_state["ollama_host"] = DEFAULT_OLLAMA_HOST
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = ""
    if "system_prompt" not in st.session_state:
        st.session_state["system_prompt"] = DEFAULT_SYSTEM_PROMPT
    if "username" not in st.session_state:
        st.session_state["username"] = "Student"
    if "translator_src_lang" not in st.session_state:
        st.session_state["translator_src_lang"] = "French"
    if "translator_target_lang" not in st.session_state:
        st.session_state["translator_target_lang"] = "English"
    if "translator_tone" not in st.session_state:
        st.session_state["translator_tone"] = "Neutral"
    if "translator_result" not in st.session_state:
        st.session_state["translator_result"] = ""
    if "show_translator" not in st.session_state:
        st.session_state["show_translator"] = True
    if "provider_ollama" not in st.session_state:
        st.session_state["provider_ollama"] = True
    if "provider_lmstudio" not in st.session_state:
        st.session_state["provider_lmstudio"] = False
    if "lmstudio_host" not in st.session_state:
        st.session_state["lmstudio_host"] = DEFAULT_LMSTUDIO_HOST


    # Process pending chat load before rendering any widgets
    if st.session_state["pending_chat_load"] is not None:
        file_path_str = st.session_state["pending_chat_load"]
        try:
            loaded = load_chat_history(Path(file_path_str))
            st.session_state["messages"] = loaded.get("messages", [])
            st.session_state["username"] = loaded.get("username", "Student")
            st.session_state["selected_model"] = loaded.get("model", "")
            st.session_state["system_prompt"] = loaded.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
            st.session_state["current_chat_id"] = Path(file_path_str).stem.replace("chat_history_", "")
        except Exception as e:
            st.error(f"Failed to load chat history: {e}")
        finally:
            st.session_state["pending_chat_load"] = None
            st.rerun()

    # Inject the theme stylesheet
    inject_custom_css(st.session_state["theme"])

    # Modern header with a badge
    st.markdown('<span class="badge">Local AI Assistant</span>', unsafe_allow_html=True)
    st.title("Kllama")
    st.caption(
        "Local-first chat with Ollama. Started as a classroom project in 2024 and "
        "still maintained as a lightweight GenAI teaching app."
    )
    st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

    models: list[str] = []
    ollama_enabled = st.session_state.get("provider_ollama", True)
    lmstudio_enabled = st.session_state.get("provider_lmstudio", False)
    
    ollama_host = st.session_state.get("ollama_host", DEFAULT_OLLAMA_HOST).strip()
    lmstudio_host = st.session_state.get("lmstudio_host", DEFAULT_LMSTUDIO_HOST).strip()
    
    ollama_connected = False
    lmstudio_connected = False
    
    client = make_client(ollama_host)
    
    ollama_models = []
    if ollama_enabled:
        try:
            ollama_models = fetch_models(ollama_host)
            ollama_connected = True
        except OLLAMA_ERRORS:
            pass
            
    lmstudio_models = []
    if lmstudio_enabled:
        try:
            lmstudio_models = fetch_lmstudio_models(lmstudio_host)
            lmstudio_connected = True
        except Exception:
            pass

    for m in ollama_models:
        models.append(f"[Ollama] {m}")
    for m in lmstudio_models:
        models.append(f"[LM Studio] {m}")

    is_connected = (ollama_enabled and ollama_connected) or (lmstudio_enabled and lmstudio_connected)

    with st.sidebar:
        # Theme toggle at the top of the sidebar
        theme_emoji = "☀️" if st.session_state["theme"] == "dark" else "🌙"
        theme_label = "Light Mode" if st.session_state["theme"] == "dark" else "Dark Mode"
        if st.button(f"{theme_emoji} {theme_label}", use_container_width=True):
            st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
            st.rerun()

        st.markdown("---")

        with st.expander("👤 Session Settings", expanded=True):
            st.text_input("Username", key="username")
            st.checkbox("Show Translator Tab", key="show_translator")
            
            st.markdown("---")
            st.markdown("##### Local AI Providers")
            st.checkbox("Ollama", key="provider_ollama")
            if st.session_state.get("provider_ollama", True):
                st.text_input(
                    "Ollama host",
                    key="ollama_host",
                    help="Use the default local server or point to another Ollama-compatible endpoint.",
                )
                
            st.checkbox("LM Studio", key="provider_lmstudio")
            if st.session_state.get("provider_lmstudio", False):
                st.text_input(
                    "LM Studio host",
                    key="lmstudio_host",
                    help="Use the default local LM Studio API endpoint.",
                )
                
            if st.button("Refresh models", use_container_width=True):
                fetch_models.clear()
                fetch_lmstudio_models.clear()
                st.rerun()

            st.markdown("---")
             # Professional connection state warning cards
            if ollama_enabled and not ollama_connected:
                st.error(
                    "**Ollama is unreachable**\n\n"
                    "Please check that Ollama is running and accessible. "
                    "If you haven't installed it, [Download Ollama here](https://ollama.com)."
                )
                
            if lmstudio_enabled and not lmstudio_connected:
                st.error(
                    "**LM Studio is unreachable**\n\n"
                    "Please check that LM Studio is running and the Local Server is started. "
                    "If you haven't installed it, [Download LM Studio here](https://lmstudio.ai)."
                )

            if not ollama_enabled and not lmstudio_enabled:
                st.warning("Please enable at least one local AI provider.")
                st.selectbox("Model", ["No providers enabled"], disabled=True)
            elif (ollama_enabled and not ollama_connected) and (lmstudio_enabled and not lmstudio_connected):
                st.selectbox("Model", ["No models detected"], disabled=True)
            elif ollama_enabled and not ollama_connected and not lmstudio_enabled:
                st.selectbox("Model", ["No models detected"], disabled=True)
            elif lmstudio_enabled and not lmstudio_connected and not ollama_enabled:
                st.selectbox("Model", ["No models detected"], disabled=True)
            else:
                if models:
                    if st.session_state["selected_model"] not in models:
                        st.session_state["selected_model"] = models[0]
                    st.selectbox(
                        "Model",
                        models,
                        key="selected_model",
                        help="The selected model is used for every prompt in this session.",
                    )
                else:
                    st.selectbox("Model", ["No models found on server(s)"], disabled=True)


        with st.expander("⚙️ Advanced Parameters", expanded=False):
            temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
            top_p = st.slider("Top-p", min_value=0.1, max_value=1.0, value=0.9, step=0.05)
            max_tokens = st.slider("Max response tokens", min_value=64, max_value=4096, value=512, step=64)
            st.text_area("System prompt", key="system_prompt", height=170)

        with st.expander("📥 Conversation Actions", expanded=False):
            st.button("Clear chat", on_click=reset_conversation, use_container_width=True)
            st.download_button(
                "Download transcript",
                data=transcript_as_markdown(
                    st.session_state["messages"],
                    st.session_state["username"],
                    st.session_state.get("selected_model") or "Not selected",
                ),
                file_name="kllama-transcript.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with st.expander("⏳ Saved Chats", expanded=True):
            saved_chats = list_chat_histories(workspace_dir)
            if not saved_chats:
                st.info("No saved chats yet. Start chatting to save automatically.")
            else:
                for chat in saved_chats:
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        try:
                            dt = datetime.datetime.fromisoformat(chat["timestamp"])
                            time_str = dt.strftime("%b %d, %H:%M")
                        except Exception:
                            time_str = chat["timestamp"]
                        is_active = st.session_state.get("current_chat_id") == chat["chat_id"]
                        label = f"**{time_str}** ({chat['model']})"
                        if is_active:
                            label = f"👉 **{time_str}** ({chat['model']})"
                        st.markdown(label)
                        st.caption(chat["snippet"] or "_Empty chat_")
                    with col_actions:
                        if st.button("📂", key=f"load_{chat['chat_id']}", help="Load this chat", use_container_width=True):
                            st.session_state["pending_chat_load"] = chat["file_path"]
                            st.rerun()
                        if st.button("🗑️", key=f"del_{chat['chat_id']}", help="Delete this chat", use_container_width=True):
                            delete_chat_history(Path(chat["file_path"]))
                            if st.session_state.get("current_chat_id") == chat["chat_id"]:
                                st.session_state["current_chat_id"] = None
                            st.rerun()
                    st.markdown("<hr style='margin: 0.3rem 0; opacity: 0.3;' />", unsafe_allow_html=True)

        st.markdown("---")
        st.caption("Source: https://github.com/kunalsuri/kllama")

    selected_model = st.session_state.get("selected_model", "")
    generation_options = model_options(temperature, top_p, max_tokens)

    show_translator = st.session_state.get("show_translator", True)
    if show_translator:
        tab_chat, tab_translator = st.tabs(["💬 Chat", "🌐 Translator"])
    else:
        tab_chat = st.container()
        tab_translator = None

    with tab_chat:
        # Main dashboard metrics
        metrics = st.columns(3)
        metrics[0].metric("Messages", len(st.session_state["messages"]))
        metrics[1].metric("Streaming", "On")
        metrics[2].metric("Model", selected_model or "Unavailable")

        # Dynamic status bar with breathing animation dot
        current_model = st.session_state.get("selected_model", "")
        active_provider = ""
        active_host = ""
        is_active_connected = False
        
        if current_model.startswith("[Ollama] ") and ollama_connected:
            is_active_connected = True
            active_provider = "Ollama"
            active_host = ollama_host
        elif current_model.startswith("[LM Studio] ") and lmstudio_connected:
            is_active_connected = True
            active_provider = "LM Studio"
            active_host = lmstudio_host

        if is_active_connected:
            raw_model = current_model.split("] ", 1)[1]
            status_html = f"""
            <div class="status-bar status-connected">
                <span class="status-dot dot-online"></span>
                <span class="status-text">Connected: using {active_provider} model <code>{raw_model}</code> at <code>{active_host}</code>. Streaming responses.</span>
            </div>
            """
        else:
            if not ollama_enabled and not lmstudio_enabled:
                status_text = "No local AI providers enabled. Please enable Ollama or LM Studio in Session Settings."
            elif ollama_enabled and lmstudio_enabled:
                status_text = f"Disconnected: Both Ollama (at {ollama_host}) and LM Studio (at {lmstudio_host}) are offline. Please verify your local servers are running."
            elif ollama_enabled:
                status_text = f"Disconnected: Ollama (at {ollama_host}) is offline. Please check that Ollama is running."
            else:
                status_text = f"Disconnected: LM Studio (at {lmstudio_host}) is offline. Please check that LM Studio is running and its local server is started."
                
            status_html = f"""
            <div class="status-bar status-disconnected">
                <span class="status-dot dot-offline"></span>
                <span class="status-text"><strong>Offline:</strong> {status_text}</span>
            </div>
            """
        st.markdown(status_html, unsafe_allow_html=True)

        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input(
            "Ask Kllama something",
            disabled=not is_active_connected,
        ):
            if st.session_state.get("current_chat_id") is None:
                st.session_state["current_chat_id"] = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

            st.session_state["messages"].append({"role": "user", "content": prompt})
            save_chat_history(
                st.session_state["messages"],
                st.session_state["username"],
                selected_model,
                st.session_state["system_prompt"],
                st.session_state["current_chat_id"],
                workspace_dir
            )

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    if selected_model.startswith("[Ollama] "):
                        raw_model = selected_model[len("[Ollama] "):]
                        response_text = st.write_stream(
                            stream_reply(
                                client,
                                raw_model,
                                st.session_state["messages"],
                                st.session_state["system_prompt"],
                                generation_options,
                            )
                        )
                    elif selected_model.startswith("[LM Studio] "):
                        raw_model = selected_model[len("[LM Studio] "):]
                        response_text = st.write_stream(
                            stream_reply_lmstudio(
                                lmstudio_host,
                                raw_model,
                                st.session_state["messages"],
                                st.session_state["system_prompt"],
                                generation_options,
                            )
                        )
                    else:
                        response_text = "No valid model selected."
                        st.error(response_text)
                except Exception as error:
                    response_text = (
                        "Failed to communicate with the local AI server. Please verify that the "
                        f"server is running. (Error: {error})"
                    )
                    st.error(response_text)


            st.session_state["messages"].append({"role": "assistant", "content": response_text})
            save_chat_history(
                st.session_state["messages"],
                st.session_state["username"],
                selected_model,
                st.session_state["system_prompt"],
                st.session_state["current_chat_id"],
                workspace_dir
            )

    if show_translator and tab_translator is not None:
        with tab_translator:
            st.markdown("### 🌐 Instant Language Translator")
            
            # Tone options and active model indication
            col_tone, col_model_info = st.columns([2, 1])
            with col_tone:
                tone = st.radio(
                    "Tone Options",
                    options=["Neutral", "Casual", "Formal"],
                    key="translator_tone",
                    horizontal=True,
                    help="Select Casual to use informal address (like French 'tu') or Formal to use polite address (like French 'vous')."
                )
            with col_model_info:
                st.markdown(
                    f"<div style='border: 1px solid var(--border-color); padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; text-align: center; background-color: var(--card-bg);'>"
                    f"Active Model: <code style='color: var(--theme-primary);'>{selected_model or 'None Selected'}</code>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Language list config
            languages = ["English", "French", "Turkish", "German", "Spanish"]
            src_languages = ["Detect Language"] + languages
            
            # Form layout: Source Panel, Middle Swap Button, Target Panel
            col_src, col_swap, col_tgt = st.columns([10, 1, 10])
            
            with col_src:
                src_lang = st.selectbox(
                    "Translate from",
                    options=src_languages,
                    key="translator_src_lang"
                )
                src_text = st.text_area(
                    "Source Text",
                    placeholder="Enter text to translate...",
                    height=200,
                    key="translator_src_text_area"
                )
                # Show character count
                st.caption(f"Characters: {len(src_text or '')} / 5000")
                
            with col_swap:
                # Spacer to push swap button down to align with dropdowns
                st.markdown("<div style='height: 45px;'></div>", unsafe_allow_html=True)
                is_swap_disabled = st.session_state["translator_src_lang"] == "Detect Language"
                if st.button("↔️", key="translator_swap_btn", help="Swap languages", disabled=is_swap_disabled, use_container_width=True):
                    temp = st.session_state["translator_src_lang"]
                    st.session_state["translator_src_lang"] = st.session_state["translator_target_lang"]
                    st.session_state["translator_target_lang"] = temp
                    st.rerun()

            with col_tgt:
                # Filter out selected source language if it's in the target list
                current_src_lang = st.session_state["translator_src_lang"]
                tgt_options = [lang for lang in languages if lang != current_src_lang]
                if not tgt_options:
                    tgt_options = languages
                
                # Safeguard current selection index
                if st.session_state["translator_target_lang"] not in tgt_options:
                    st.session_state["translator_target_lang"] = tgt_options[0]
                    
                target_lang = st.selectbox(
                    "Translate to",
                    options=tgt_options,
                    key="translator_target_lang"
                )
                
                # Output text area placeholder
                target_placeholder = st.empty()
                target_placeholder.text_area(
                    "Translation Result",
                    value=st.session_state["translator_result"],
                    height=200,
                    disabled=True,
                )

            # Translation actions: Clear and Translate
            col_clr, col_trans = st.columns([1, 3])
            with col_clr:
                if st.button("🧹 Clear", key="translator_clear_btn", use_container_width=True):
                    st.session_state["translator_src_text_area"] = ""
                    st.session_state["translator_result"] = ""
                    st.rerun()
            with col_trans:
                is_trans_disabled = not is_active_connected or not src_text.strip()
                if st.button("Translate 🌐", key="translator_submit_btn", type="primary", use_container_width=True, disabled=is_trans_disabled):
                    try:
                        # Build the request messages using the core utility function
                        translation_payload = build_translation_payload(
                            src_text,
                            src_lang,
                            target_lang,
                            st.session_state["translator_tone"]
                        )
                        
                        # Show spinner and run translation with stream=True
                        with st.spinner("Translating..."):
                            translated_text = ""
                            if selected_model.startswith("[Ollama] "):
                                raw_model = selected_model[len("[Ollama] "):]
                                stream = client.chat(
                                    model=raw_model,
                                    messages=translation_payload,
                                    options={"temperature": 0.3},
                                    stream=True,
                                )
                                for chunk in stream:
                                    chunk_text = extract_message_text(chunk)
                                    if chunk_text:
                                        translated_text += chunk_text
                                        target_placeholder.text_area(
                                            "Translation Result",
                                            value=translated_text,
                                            height=200,
                                            disabled=True,
                                        )
                            elif selected_model.startswith("[LM Studio] "):
                                raw_model = selected_model[len("[LM Studio] "):]
                                stream = stream_reply_lmstudio(
                                    lmstudio_host,
                                    raw_model,
                                    translation_payload,
                                    "",  # no system prompt since payload is custom built
                                    {"temperature": 0.3}
                                )
                                for chunk_text in stream:
                                    if chunk_text:
                                        translated_text += chunk_text
                                        target_placeholder.text_area(
                                            "Translation Result",
                                            value=translated_text,
                                            height=200,
                                            disabled=True,
                                        )
                            else:
                                raise ValueError("No valid model selected.")
                                    
                            st.session_state["translator_result"] = translated_text
                            st.rerun()
                    except Exception as error:
                        st.error(f"Translation failed: {error}")


if __name__ == "__main__":
    main()
