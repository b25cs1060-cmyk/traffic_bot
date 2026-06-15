import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()
GROQ_API = os.getenv("GROQ_API_KEY")

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def add(a: int, b: int):
    """Adds two numbers together."""
    return a + b

@tool
def multiply(a: int, b: int):
    """Multiplies two numbers."""
    return a * b

@tool
def subtract(a: int, b: int):
    """Subtracts b from a."""
    return a - b

@tool
def divide(a: int, b: int):
    """Divides a by b."""
    return a / b

tool_list = [add, multiply, subtract, divide]
llm_model = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API).bind_tools(tool_list)

def response_generator(state: AgentState) -> AgentState:
    prompt = SystemMessage(content="You are my AI agent. Please respond to queries through necessary tool calling.")
    response = llm_model.invoke([prompt] + list(state["messages"]))
    return {"messages": [response]}

def decider(state: AgentState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

graph = StateGraph(AgentState)
graph.add_node("communicator", response_generator)

tool_node = ToolNode(tools=tool_list)

graph.add_node("all_tools", tool_node)

graph.add_edge(START, "communicator")
graph.add_conditional_edges(
    "communicator",
    decider,
    {
     
        "continue": "all_tools",
        "end": END
    }
)

graph.add_edge("all_tools", "communicator")

my_first_ReACT_chatbot = graph.compile()

#using chat history we can now store all the chats 

chat_history=[]
user_input = input("Enter: ")
while user_input != "exit":
    chat_history.append(HumanMessage(content=user_input))
    result = my_first_ReACT_chatbot.invoke({"messages": chat_history})
    chat_history=result["messages"]
    print(f"\nAI: {result['messages'][-1].content}")
    user_input = input("Enter: ")

with open ("chatbot3.txt" , "w") as file:
     file.write("\nconversation start :")
     for messages in chat_history:
         if isinstance(messages , HumanMessage):
             file.write(f"\nYou:{messages.content}")
         else :
             file.write(f"\nAI:{messages.content}")
     file.write("\nConversation end")