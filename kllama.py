from __future__ import annotations

import os
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
)

DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_SYSTEM_PROMPT = (
    "You are Kllama, a helpful local AI assistant for students, builders, and "
    "researchers. Respond clearly, stay grounded in the user's request, and say "
    "when you are uncertain."
)


@st.cache_data(ttl=15, show_spinner=False)
def fetch_models(ollama_host: str) -> list[str]:
    response = Client(host=ollama_host).list()
    return list_model_names(response)


def reset_conversation() -> None:
    st.session_state["messages"] = initial_chat_history()


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
    for chunk in stream:
        text = extract_message_text(chunk)
        if text:
            yield text


st.set_page_config(page_title="Kllama", page_icon="🦙", layout="wide")
st.title("Kllama")
st.caption(
    "Local-first chat with Ollama. Started as a classroom project in 2024 and "
    "still maintained as a lightweight GenAI teaching app."
)

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

models: list[str] = []
host = st.session_state["ollama_host"].strip() or DEFAULT_OLLAMA_HOST
client = Client(host=host)

with st.sidebar:
    st.header("Session")
    st.text_input("Username", key="username")
    st.text_input(
        "Ollama host",
        key="ollama_host",
        help="Use the default local server or point to another Ollama-compatible endpoint.",
    )
    if st.button("Refresh models", use_container_width=True):
        fetch_models.clear()

    try:
        host = st.session_state["ollama_host"].strip() or DEFAULT_OLLAMA_HOST
        client = Client(host=host)
        models = fetch_models(host)
    except (ResponseError, httpx.HTTPError) as error:
        st.error(f"Unable to load models from Ollama: {error}")

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
        st.selectbox("Model", ["No models detected"], disabled=True)
        st.info("Start Ollama and pull a model such as `ollama pull gemma3`.")

    st.markdown("---")
    st.header("Generation")
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
    top_p = st.slider("Top-p", min_value=0.1, max_value=1.0, value=0.9, step=0.05)
    max_tokens = st.slider("Max response tokens", min_value=64, max_value=4096, value=512, step=64)
    st.text_area("System prompt", key="system_prompt", height=170)

    st.markdown("---")
    st.header("Conversation")
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
    st.caption("Source: https://github.com/kunalsuri/kllama")

selected_model = st.session_state.get("selected_model", "")
generation_options = model_options(temperature, top_p, max_tokens)

metrics = st.columns(3)
metrics[0].metric("Messages", len(st.session_state["messages"]))
metrics[1].metric("Streaming", "On")
metrics[2].metric("Model", selected_model or "Unavailable")

st.write(
    f"Connected to `{host}` with model `{selected_model or 'not selected'}`. "
    "Responses are streamed directly from Ollama."
)

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(
    "Ask Kllama something",
    disabled=not bool(selected_model),
):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response_text = st.write_stream(
                stream_reply(
                    client,
                    selected_model,
                    st.session_state["messages"],
                    st.session_state["system_prompt"],
                    generation_options,
                )
            )
        except (ResponseError, httpx.HTTPError) as error:
            response_text = (
                "I could not get a response from Ollama. Please verify that the server "
                f"is running and the model is available. Details: {error}"
            )
            st.error(response_text)

    st.session_state["messages"].append({"role": "assistant", "content": response_text})
