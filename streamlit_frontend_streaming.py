import streamlit as st
from langgraph_tool_backend import chatbot
from langchain_core.messages import HumanMessage

CONFIG = {'configurable': {'thread_id': 'thread- 1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input("Type your message here...") 

if user_input:
    st.session_state['message_history'].append({'role':'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    


    with st.chat_message('assistant'):
        
        def extract_content(chunk):
            content = chunk.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return "".join(item.get("text", "") for item in content if isinstance(item, dict))
            return ""

        ai_message = st.write_stream(
            extract_content(message_chunk)
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
            if extract_content(message_chunk)
        )
    
    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})