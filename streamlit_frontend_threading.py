import streamlit as st
from langgraph_tool_backend import chatbot
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import uuid

# ******************************** utility functions ********************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

    
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']

def extract_content(chunk):
    content = chunk.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict))
    return ""



# ******************************** Session setup ********************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
    

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if 'chat_thread_names' not in st.session_state:
    st.session_state['chat_thread_names'] = {}

add_thread(st.session_state['thread_id'])

# ******************************** Sidebar for thread management ********************************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    name = st.session_state['chat_thread_names'].get(thread_id, "unknown conversation")
    if st.sidebar.button(name, key=str(thread_id)):
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
        st.text(message['content'])

if user_input:

    if st.session_state['thread_id'] not in st.session_state['chat_thread_names']:
        st.session_state['chat_thread_names'][st.session_state['thread_id']] = user_input[:30]
    
    st.session_state['message_history'].append({'role':'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        
        def ai_only_stream():
            status_holder = {"box": None}
            
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                # Show status when AI decides to call a tool
                if isinstance(message_chunk, AIMessage) and message_chunk.tool_calls:
                    tool_name = message_chunk.tool_calls[0].get("name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Mark status complete when tool result comes back
                if isinstance(message_chunk, ToolMessage):
                    if status_holder["box"] is not None:
                        status_holder["box"].update(
                            label=f"✅ Done",
                            state="complete",
                            expanded=False,
                        )

                # Stream ONLY assistant text tokens
                if isinstance(message_chunk, AIMessage):
                    if (
                        message_chunk.content
                        and isinstance(message_chunk.content, list)
                        and message_chunk.content[0].get("type") == "text"
                    ):
                        yield message_chunk.content[0]["text"]
                    elif isinstance(message_chunk.content, str) and message_chunk.content:
                        yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())
    
    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})