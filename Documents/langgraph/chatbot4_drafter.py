import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode

load_dotenv()

GROQ_API = os.getenv("GROQ_API_KEY")
llm_model = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API)

document_content = ""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def document_editor(content: str) -> str:
    """This tool edits the existing document by following all the instructions provided by the user."""
    print("\nYour document is being edited...")
    global document_content
    document_content = content
    return f"Your document has been edited and the current document content is: {document_content}"

@tool
def document_saver(filename: str) -> str:
    """This tool saves the document_content into a txt file. Argument: filename provided by user."""
    if not filename.endswith('.txt'):
        filename = f"{filename}.txt"
    with open(f"documen_-content", "w") as file:
        file.write(document_content)
    return f"Your document has been saved. Content: \n {document_content}"

tool_list = [document_editor, document_saver]
llm_model = llm_model.bind_tools(tool_list)

def communicator(state: AgentState) -> AgentState:
    global document_content
    system_prompt = SystemMessage(content=f"""
       You are an AI drafting agent. Edit the document content based on user instructions.
       - Use document_editor tool to make changes to the document
       - Use document_saver tool after editing to save the file
       Current document: {document_content}""")

    if not state["messages"]:
     
        user_input = "I want to create a document. Please help me."
        user_message = HumanMessage(content=user_input)
        to_pass = [system_prompt] + [user_message]

    elif isinstance(state["messages"][-1], ToolMessage):
        to_pass = [system_prompt] + list(state["messages"])

    else:
     
        user_input = input("\nWhat would you like to do with the document? ")
        user_message = HumanMessage(content=user_input)
        to_pass = [system_prompt] + list(state["messages"]) + [user_message]

    result = llm_model.invoke(to_pass)
    return {"messages": [result]}

def shall_continue(state: AgentState) -> str:
    messages = state["messages"]
    if not messages:
        return "continue"
    for message in reversed(messages):
        if (isinstance(message, ToolMessage) and
            "saved" in message.content.lower() and
            "document" in message.content.lower()):
            return "end"
    return "continue"

graph = StateGraph(AgentState)
graph.add_node("communicator", communicator)
all_tools = ToolNode(tools=tool_list)
graph.add_node("tools", all_tools)
graph.add_edge(START, "communicator")
graph.add_edge("communicator" , "tools")
graph.add_conditional_edges(
    "tools",
    shall_continue,
    {
        "continue" : "communicator" ,
        "end" :END
    }
)

my_drafter_ai = graph.compile()

chat_history = []
user_input = input("Enter: ")

while user_input != "exit":
    chat_history.append(HumanMessage(content=user_input))
    response = my_drafter_ai.invoke({"messages": chat_history})
    chat_history = response["messages"]
    print(f"AI: {response['messages'][-1].content}")
    user_input = input("Enter: ")

with open("chatbot4_drafter.txt", "w") as file:
    file.write("\nConversation begin")
    for messages in chat_history:
        if isinstance(messages, HumanMessage):
            file.write(f'\nYou: {messages.content}')
        else :
            file.write(f'\nAI: {messages.content}')
    file.write("\nConversation end")
