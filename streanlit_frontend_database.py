import streamlit as st
from langgraph_backend_database import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# ******************************** Utility functions ********************************

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    if not state or not state.values:          # ← fix: guard empty state
        return []
    return state.values.get('messages', [])    # ← fix: don't hard-index

def extract_content(chunk):
    content = chunk.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict))
    return ""

def get_thread_label(thread_id):
    names = st.session_state.get('chat_thread_names', {})
    return names.get(str(thread_id), "New conversation")  # ← friendly fallback label

# ******************************** Session setup ********************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'chat_thread_names' not in st.session_state:
    st.session_state['chat_thread_names'] = {}

add_thread(st.session_state['thread_id'])

# ******************************** Sidebar ********************************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    label = get_thread_label(thread_id)
    if st.sidebar.button(label, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_message_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                temp_message_history.append({'role': 'user', 'content': msg.content})
            else:
                temp_message_history.append({'role': 'assistant', 'content': extract_content(msg)})

        st.session_state['message_history'] = temp_message_history

# ******************************** Main UI ********************************

user_input = st.chat_input("Type your message here...")

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])        # ← markdown renders formatting

if user_input:

    # Name the thread after first message
    thread_key = str(st.session_state['thread_id'])
    if thread_key not in st.session_state['chat_thread_names']:
        st.session_state['chat_thread_names'][thread_key] = user_input[:30]  # ← first 30 chars as name

    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            extract_content(message_chunk)
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
            if extract_content(message_chunk)
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})