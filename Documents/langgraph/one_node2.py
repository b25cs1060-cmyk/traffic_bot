from itertools import product
from typing import TypedDict
from langgraph.graph import StateGraph
from math import prod

class Operation(TypedDict):
    values: list[int]
    name: str
    operation_to_be_performed: str
    result: str

def get_operation(state: Operation) -> Operation:
    if state["operation_to_be_performed"] == "sum":
        answer = sum(state["values"])
    elif(state["operation_to_be_performed"]=="multiply"):
        answer=prod(state["values"])
    state["result"] = "HELLO " + state["name"] + ", the result is " + str(answer)
    return state

graph = StateGraph(Operation)

graph.add_node("operations", get_operation)

graph.set_entry_point("operations")
graph.set_finish_point("operations")

app = graph.compile()

result = app.invoke({
    "values": [1, 2, 3, 4, 5],
    "name": "rudri",
    "operation_to_be_performed": "multiply"
})

print(result["result"])