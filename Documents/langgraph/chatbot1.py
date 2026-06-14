from langgraph.graph import StateGraph, END, START
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

load_dotenv("/home/rudri/Documents/langgraph/.env")
MY_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o" , api_key=MY_API_KEY)

class AgentState(TypedDict):
    messages: list

def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    state["messages"].append(response)
    return state

graph = StateGraph(AgentState)

graph.add_node("conversation", process)
graph.add_edge(START, "conversation")
graph.add_edge("conversation", END)

chatbot = graph.compile()

user_input = input("Enter: ")

while user_input != "exit":
    result = chatbot.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    print(result["messages"][-1].content)

    user_input = input("Enter: ")
