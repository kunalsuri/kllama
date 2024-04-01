# Kllama Chatbot that will run the models from Replicate.com. You can deploy your code online via streamlit.app
import streamlit as st
from datetime import datetime
import replicate
import os

# App title
st.title("✅🦙 Kllama Chatbot 💬: Power of Open LLMs 💪")

# Clear Chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you?"}]

### App Sidebar Section Starts ###
with st.sidebar:
    st.title('✅🦙 Kllama Settings ⚙️')
    st.write('This chatbot is created using the open-source LLM model (Llama 2) from Meta.')

# Replicate Credentials
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api)==40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')

    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.sidebar.markdown("---")
    st.subheader('Select Model')
    selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-13B', 'Llama2-7B'], key='selected_model')
    if selected_model == 'Llama2-13B':
        llm_selected = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    elif selected_model == 'Llama2-7B':
        llm_selected = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'

    st.sidebar.markdown("---")
    st.subheader('Set Model Parameters')
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=32, max_value=128, value=120, step=8)


    st.sidebar.markdown("---")
    st.subheader('Chat History')
    st.sidebar.button('Click to Clear Chat History', on_click=clear_chat_history)

    st.sidebar.markdown("---")
    #st.sidebar.write(f"Logged in as: {user_username}")
    st.markdown('📖 Learn how to build this app in this [blog](https://kunalsuri.com/)!')
### App Sidebar Section Ends ###
    

# Show the selected Model
st.write("NOTE: You have selected the following LLM model via Replicate.com:  " + selected_model)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Function for generating LLaMA2 response. Refactored from https://github.com/a16z-infra/llama2-chatbot
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run(llm_selected, 
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
    return output

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
