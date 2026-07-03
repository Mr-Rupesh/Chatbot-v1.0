from langgraph.graph import StateGraph, START, END
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from typing import TypedDict, Literal, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

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

checkpointer = MemorySaver()
graph = StateGraph(ChatState)

graph.add_node("chat", chat_node)
graph.set_entry_point("chat")
graph.set_finish_point("chat")

chatbot = graph.compile(checkpointer=checkpointer)
