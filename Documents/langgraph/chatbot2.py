import os
from langgraph.graph import StateGraph
from typing import TypedDict, Union, List
from langgraph.graph import START, END
from dotenv import load_dotenv
from langchain_groq import ChatGroq          
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv(dotenv_path="/home/rudri/Documents/langgraph/.env")
MY_API_KEY = os.getenv("GROQ_API_KEY")      
print(f"Key loaded: {MY_API_KEY}")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=MY_API_KEY)  

class AgentState(TypedDict):
    message: List[Union[HumanMessage, AIMessage]]  

def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["message"])        
    state["message"].append(AIMessage(content=response.content))
    print(response.content)
    return state

graph = StateGraph(AgentState)                     

graph.add_node("conversation", process)
graph.add_edge(START, "conversation")
graph.add_edge("conversation", END)

my_bot2 = graph.compile()

conversation_history = []                          

user_input = input("Enter: ")
while user_input != "exit":
    conversation_history.append(HumanMessage(content=user_input))
    result = my_bot2.invoke({"message": conversation_history})
    conversation_history = result["message"]       
    user_input = input("Enter: ")




