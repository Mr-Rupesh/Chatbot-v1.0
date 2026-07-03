from langgraph.graph import StateGraph, START, END
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from typing import TypedDict, Literal, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = HuggingFaceEndpoint(
        repo_id="meta-llama/Llama-3.1-8B-Instruct",
        task="conversational",
        temperature=0.7,
    )
model = ChatHuggingFace(llm=llm)

model1 = ChatGoogleGenerativeAI(model='gemini-3-flash-preview', temperature=0.7)
        #########################
        #   Define the state    #
        #########################

        
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


        #########################
        #   Define the nodes    #
        #########################


def chat_node(state: ChatState) -> str:
    messages = state["messages"]
    response = model.invoke(messages)

    return {'messages': [response]}


        #########################
        #   Define the graph    #
        #########################

conn = sqlite3.connect(database="chatbot_memory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)

graph.add_node("chat", chat_node)
graph.add_edge(START, "chat")
graph.add_edge("chat", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint_tuple in checkpointer.list(None):
        all_threads.add(checkpoint_tuple.config['configurable']['thread_id'])
    return list(all_threads)

