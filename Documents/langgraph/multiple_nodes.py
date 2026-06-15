from typing import TypedDict
from langgraph.graph import StateGraph, END, START

class Operations(TypedDict):
    number1: int
    number2: int
    number3: int
    operation1: str
    operation2: str
    result: int

def addition(state: Operations) -> Operations:
    state["result"] = state["number1"] + state["number2"]
    return state

def subtraction(state: Operations) -> Operations:
    state["result"] = state["number1"] - state["number2"]
    return state

def multiplication(state: Operations) -> Operations:
    state["result"] = state["result"] * state["number3"]
    return state

def division(state: Operations) -> Operations:
    state["result"] = state["result"] / state["number3"]
    return state

def decide_next_node1(state: Operations):
    if state["operation1"] == "+":
        return "addition-operation"
    elif state["operation1"] == "-":
        return "subtraction-operation"

def decide_next_node2(state: Operations):
    if state["operation2"] == "*":
        return "multiplication-operation"
    elif state["operation2"] == "/":
        return "division-operation"

graph = StateGraph(Operations)

graph.add_node("router1", lambda state: state)
graph.add_node("router2", lambda state: state)

graph.add_node("add-node", addition)
graph.add_node("subtract-node", subtraction)
graph.add_node("multiply-node", multiplication)
graph.add_node("divide-node", division)

graph.add_edge(START, "router1")

graph.add_conditional_edges(
    "router1", 
    decide_next_node1,
    {
        "addition-operation": "add-node",
        "subtraction-operation": "subtract-node",
    }
)

graph.add_edge("add-node", "router2")
graph.add_edge("subtract-node", "router2")

graph.add_conditional_edges(
    "router2",
    decide_next_node2,
    {
        "multiplication-operation": "multiply-node",
        "division-operation": "divide-node",
    }
)

graph.add_edge("multiply-node", END)
graph.add_edge("divide-node", END)

app = graph.compile()

result = app.invoke({
    "number1": 10,
    "number2": 5,
    "number3": 3,
    "operation1": "+",
    "operation2": "*",
    "result": 0
})

print(result)

