from typing import TypedDict
from langgraph.graph import StateGraph 

class Message(TypedDict):
    message : str 

def say_hello(state:Message) -> Message :
    """This tools basicaly takes the input from users and returns them a greeting message"""
    state["message"] ="Hello "+state["message"] +",How are you doing ?"
    return state

graph=StateGraph(Message)
graph.add_node("greet" , say_hello)
graph.set_entry_point("greet")
graph.set_entry_point("greet")
app=graph.compile()
result=app.invoke({"message":"Rudri"})
print(result["message"])