import streamlit as st
from datetime import datetime
import ollama

st.title("✅🦙 Kllama: Your Local & Private Chatbot💬💪")

# Format function for chat messages
def format_message(sender, message, timestamp):
    return f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {sender}: {message}"

# Initialize chat history if not already set
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How may I assist you?"}]

# Function to clear chat history
def clear_chat_history():
    st.session_state["messages"] = [{"role": "assistant", "content": "How may I assist you?"}]

# Sidebar Settings
with st.sidebar:
    st.title('✅🦙 Kllama Settings ⚙️')
    user_username = st.text_input("Username", "Your Name")
    st.markdown("---")
    
    st.subheader('Open LLM Models')
    if "model" not in st.session_state:
        st.session_state["model"] = ""

    try:
        # Retrieve the list of models from Ollama
        response = ollama.list()
        models = [model.model for model in response.models]
        st.session_state["model"] = st.selectbox("Choose a Model via Ollama Framework", models)
        model_chosen = st.session_state["model"]
    except Exception as e:
        st.write(f"An error occurred while retrieving models: {e}")

    st.markdown("---")
    st.subheader('Chat History')
    st.button('Click to Clear Chat History', on_click=clear_chat_history)
    
    st.markdown("---")
    st.write(f"Logged in as: {user_username}")
    st.markdown('📖 Opensource Code and ReadMe available via [Github Repo](https://github.com/kunalsuri/kllama/)!')

# Generator function for streaming model responses
def model_result_generator():
    full_response = ""
    stream = ollama.chat(
        model=st.session_state["model"],
        messages=st.session_state["messages"],
        stream=True,
    )
    for chunk in stream:
        text = chunk["message"]["content"]
        full_response += text
        yield text

# Display chat history on app rerun
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.write(f"NOTE: You have selected the following LLM model via the Ollama Framework: {model_chosen}")

# Handle user input
if prompt_input := st.chat_input("How may I assist you?"):
    # Add the user message to chat history
    st.session_state["messages"].append({"role": "user", "content": prompt_input})
    
    with st.chat_message("user"):
        st.markdown(prompt_input)
    
    # Generate and stream the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking ..."):
            # Stream the output with a typewriter effect and return the full text
            message = st.write_stream(model_result_generator())
            st.session_state["messages"].append({"role": "assistant", "content": message})
