import random
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class AgentState(TypedDict):
    actual_number: int
    guesses: list[int]
    number_of_guesses: int
    lower_bound: int
    upper_bound: int

def make_guess(state: AgentState) -> AgentState:
  
    if state["guesses"]:
        last_guess = state["guesses"][-1]
        if last_guess > state["actual_number"]:
            state["upper_bound"] = last_guess - 1
        else:
            state["lower_bound"] = last_guess + 1

  
    guess = random.randint(state["lower_bound"], state["upper_bound"])
    state["guesses"].append(guess)
    state["number_of_guesses"] += 1
    return state

def decision_maker(state: AgentState) -> str:
 #never make updates in router
    latest_guess = state["guesses"][-1]
    actual_number = state["actual_number"]

    if latest_guess == actual_number:
        return "exit"
    if state["number_of_guesses"] >= 7:
        return "exit"
    return "loops"

graph = StateGraph(AgentState)
graph.add_node("guess", make_guess)
graph.add_edge(START, "guess")
graph.add_conditional_edges(
    "guess",
    decision_maker,
    {
        "loops": "guess",
        "exit": END
    }
)

app = graph.compile()
result = app.invoke({
    "actual_number": 6,
    "guesses": [],
    "number_of_guesses": 0,
    "lower_bound": 1,
    "upper_bound": 20
})
print(result)