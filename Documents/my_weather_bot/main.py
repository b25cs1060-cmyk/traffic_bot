import code
import os
import requests
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from langchain_core.messages import SystemMessage,ToolMessage,BaseMessage
from langchain_groq import ChatGroq
from typing import Annotated,TypedDict,Dict,Sequence
from typing import Optional
from langgraph.graph import StateGraph , START , END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

load_dotenv()

API_KEY=os.getenv("GROQ_API_KEY")

weather_endpoint_url="https://api.openweathermap.org/data/2.5/weather"
geocoding_endpoint_url= "http://api.openweathermap.org/geo/1.0/direct"
weather_agent_api=os.getenv("WEATHER_API_KEY")

traffic_flow_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
traffic_api_key = os.getenv("TRAFFIC_API_KEY")

event_url= "https://app.ticketmaster.com/discovery/v2/events.json"
event_api_key=os.getenv("EVENT_API_KEY")

#tools 

#AGENT1

#Weather Agent
#fifteen minutes timeline

@tool
def get_weather_conditions(city_name :str , state_code: str , country_code : str) :

    """You are supposed to decode the geocode of the name of the city provided to you 
      using geocoding endpoint and then fetch the details of the weather data using the 
      weather endpoint provided to you
      
      Arguments : city_name , state_code , country_code"""
    
    params1={
        "q" : f'{city_name},{state_code},{country_code}',
        "limit" : 5 ,
        "appid": weather_agent_api
    }

    geocode_data=requests.get(geocoding_endpoint_url , params=params1)
    geocode_data.raise_for_status()
    geocode_data_json=geocode_data.json()

    if not geocode_data_json :
        return "Location not found"
    
    latitude=geocode_data_json[0]["lat"]
    longitude=geocode_data_json[0]["lon"]

    params2 ={
        "lat" : latitude,
        "lon" : longitude,
        "appid" : weather_agent_api
    }

    weather_data=requests.get(weather_endpoint_url , params=params2)
    weather_data.raise_for_status()
    weather_data_json=weather_data.json()
    stats=[weather_data_json["weather"],
           weather_data_json["main"],
           weather_data_json["wind"] ,
               weather_data_json.get("rain", {}),
           weather_data_json["clouds"]]
    #this will include all the alerts too
    return stats

#AGENT2

#traffic agent
@tool
def get_traffic_data(city_name: str, state_code: str, country_code: str):

    """You are supposed to decode the geocode of a city using the geocode endpoint (determint the latitude and the longitude )
       and then generate the necessary information related to traffic data and return the necessary parameters as they have
       been specified below at the end of the function
       
       Arguments : city_name , state_code , country_code
       """
    
    params1 = {
        "q": f"{city_name},{state_code},{country_code}",
        "limit": 1,
        "appid": weather_agent_api
    }

    geocode_data = requests.get(geocoding_endpoint_url, params=params1)
    geocode_data.raise_for_status()
    geocode_data_json = geocode_data.json()

    if not geocode_data_json:
        return "Location not found"

    latitude = geocode_data_json[0]["lat"]
    longitude = geocode_data_json[0]["lon"]

    params2 = {
        "key": traffic_api_key,
        "point": f"{latitude},{longitude}"
    }

    traffic_data = requests.get(traffic_flow_url, params=params2)
    traffic_data.raise_for_status()
    traffic_data_json = traffic_data.json()

    return {
        "frc": traffic_data_json["flowSegmentData"]["frc"],
        "currentSpeed": traffic_data_json["flowSegmentData"]["currentSpeed"],
        "freeFlowSpeed": traffic_data_json["flowSegmentData"]["freeFlowSpeed"],
        "currentTravelTime": traffic_data_json["flowSegmentData"]["currentTravelTime"],
        "freeFlowTravelTime": traffic_data_json["flowSegmentData"]["freeFlowTravelTime"],
        "confidence": traffic_data_json["flowSegmentData"]["confidence"],
        "roadClosure": traffic_data_json["flowSegmentData"]["roadClosure"]
    }
#AGENT3 

#event agent
@tool
def get_event_details(city: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """You are supposed to find all the information related to the ongoing events in the city which has been passed as a parameter . 
       The user might additionally also enter the start date and the end date
       
       Arguments = city , start_date (optional, format YYYY-MM-DD) , end_date (optional, format YYYY-MM-DD)"""

    params = {
        "apikey": event_api_key,
        "city": city,
        "size" :1
    }

    if start_date:
        params["startDateTime"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["endDateTime"] = f"{end_date}T00:00:00Z"

    event_data = requests.get(event_url, params=params)
    event_data.raise_for_status()
    event_data_json = event_data.json()

    if "_embedded" not in event_data_json:
        return "No events found"

    return event_data_json["_embedded"]["events"]

tool_list=[get_traffic_data,get_weather_conditions ,get_event_details]

class AgentState(TypedDict):
    messages :Annotated[Sequence[BaseMessage] , add_messages]

#model
llm_model=ChatGroq(model="llama-3.3-70b-versatile" , api_key=API_KEY ,  max_tokens=400).bind_tools(tool_list)

#NODE
def main_agent(state:AgentState) ->AgentState :
    system_prompt=SystemMessage(content="""
You are a traffic prediction assistant.
Use available traffic, weather, and event tools to gather data, predict traffic conditions, and explain the prediction.
""")
    
    if not state["messages"] :
        user_input = "I am here to assist you determine the traffic conditions of the city you wish to"
        user_message =HumanMessage(content=user_input)
    else :
        user_input ="How would you like to get the traffic data"
        user_message=HumanMessage(content=user_input)
    
    to_pass= [system_prompt] +list(state["messages"][-10:])
    response = llm_model.invoke(to_pass)
    return {"messages" : [response]}

#ROUTER
def shall_continue(state:AgentState)->AgentState:
    #the decider code
    last_message=state["messages"][-1]
    if not last_message.tool_calls :
       return "end"
      #terminate
    else : 
       return "continue"
    #go on with the loop
     
graph=StateGraph(AgentState)
graph.add_node("main_agent" , main_agent)
tools=ToolNode(tools=tool_list)
graph.add_node("tools" , tools)
graph.add_edge(START , "main_agent")
graph.add_conditional_edges(
    "main_agent" , #the source code
    shall_continue , #the decider
    {
        "continue" : "tools" , 
        "end" :END
    }
)
graph.add_edge("tools" , "main_agent")
my_traffic_bot =graph.compile()


chat_history=[]
user_input=input("Enter:  " )

#in order to maintain all the history
MAX_HISTORY = 2   # last 2 messages only

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    chat_history.append(HumanMessage(content=user_input))

    recent_history = chat_history[-MAX_HISTORY:]

    response = my_traffic_bot.invoke({"messages": recent_history})

    ai_msg =response["messages"][-1]
    print("\nBot:", ai_msg.content)

    chat_history.append(ai_msg)