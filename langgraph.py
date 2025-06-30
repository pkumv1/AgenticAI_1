import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
from sqlalchemy import create_engine
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import StateGraph, END
# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Hotel & Flight Planner with LangGraph", page_icon="✈️", layout="wide")
st.title("✈️ Indian Hotel & Flight Planner with LangGraph")
st.write("Generate personalized hotel and flight plans, sightseeing spots, and daily itinerary using LangGraph and Groq.")

if not groq_api_key:
    st.error("💼 GROQ_API_KEY not found. Please set it in your .env file.")
    st.stop()

# SQL config
st.sidebar.header("🔧 SQL Server Configuration")
server = st.sidebar.text_input("Server Name", value="M0HYDLAP050-SAT\SQLEXPRESS")
driver = "ODBC Driver 17 for SQL Server"
use_windows_auth = st.sidebar.checkbox("Use Windows Authentication", value=True)

hotel_db = st.sidebar.text_input("Hotel Database Name", value="HotelDB")
flight_db = st.sidebar.text_input("Flight Database Name", value="Flightsdata")

if use_windows_auth:
    hotel_conn_str = f"mssql+pyodbc://@{server}/{hotel_db}?driver={driver}&trusted_connection=yes"
    flight_conn_str = f"mssql+pyodbc://@{server}/{flight_db}?driver={driver}&trusted_connection=yes"
else:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    hotel_conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{hotel_db}?driver={driver}"
    flight_conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{flight_db}?driver={driver}"

# Initialize LLM
llm = ChatGroq(model_name="llama3-8b-8192", groq_api_key=groq_api_key, temperature=0.3)

# Define node functions for the LangGraph
def process_hotel_data(state):
    hotel_info = state["hotel_info"]
    
    prompt = ChatPromptTemplate.from_template(
        """You are a Hotel Planner who summarizes hotel data in a readable format.
        Please summarize the following hotel data in bullet point format:
        
        {hotel_info}
        
        Highlight the most important amenities, ratings, and location information.
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    hotel_summary = chain.invoke({"hotel_info": hotel_info})
    
    state["hotel_summary"] = hotel_summary
    return state

def process_flight_data(state):
    flight_info = state["flight_info"]
    
    prompt = ChatPromptTemplate.from_template(
        """You are a Flight Planner who summarizes flight options.
        Please summarize the following flight data, identifying the best options based on price, duration, and airline:
        
        {flight_info}
        
        Provide a clear summary of the top flight options.
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    flight_summary = chain.invoke({"flight_info": flight_info})
    
    state["flight_summary"] = flight_summary
    return state

def process_sightseeing_data(state):
    attractions_text = state["attractions_text"]
    city = state["city"]
    
    prompt = ChatPromptTemplate.from_template(
        """You are a Sightseeing Curator specializing in Indian tourism.
        Please provide short descriptions for these attractions in {city}:
        
        {attractions_text}
        
        Include what makes each place special and worth visiting.
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    sightseeing_summary = chain.invoke({"attractions_text": attractions_text, "city": city})
    
    state["sightseeing_summary"] = sightseeing_summary
    return state

def generate_itinerary(state):
    hotel_summary = state["hotel_summary"]
    flight_summary = state["flight_summary"]
    sightseeing_summary = state["sightseeing_summary"]
    city = state["city"]
    stay_days = state["stay_days"]
    visitor_count = state["visitor_count"]
    language = state["language"]
    
    prompt_template = """You are an Itinerary Scheduler who creates detailed travel plans.
    Create a day-by-day itinerary for a {stay_days}-day trip to {city} for {visitor_count} people.
    
    Include:
    1. Hotel details: {hotel_summary}
    2. Flight information: {flight_summary}
    3. Daily activities incorporating these attractions: {sightseeing_summary}
    
    Format as a day-by-day plan with morning, afternoon, and evening activities.
    Include meal suggestions at local restaurants and practical travel tips.
    """
    
    if language != "English":
        prompt_template += f"\n\nTranslate the entire itinerary to {language}."
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    chain = prompt | llm | StrOutputParser()
    final_itinerary = chain.invoke({
        "hotel_summary": hotel_summary,
        "flight_summary": flight_summary,
        "sightseeing_summary": sightseeing_summary,
        "city": city,
        "stay_days": stay_days,
        "visitor_count": visitor_count
    })
    
    state["final_itinerary"] = final_itinerary
    return state

# Setup LangGraph
def create_travel_planner_graph():
    # Define the workflow
    workflow = StateGraph(state_type=dict)
    
    # Add nodes
    workflow.add_node("process_hotel_data", process_hotel_data)
    workflow.add_node("process_flight_data", process_flight_data)
    workflow.add_node("process_sightseeing_data", process_sightseeing_data)
    workflow.add_node("generate_itinerary", generate_itinerary)
    
    # Define edges - this is a linear workflow
    workflow.add_edge("process_hotel_data", "process_flight_data")
    workflow.add_edge("process_flight_data", "process_sightseeing_data")
    workflow.add_edge("process_sightseeing_data", "generate_itinerary")
    workflow.add_edge("generate_itinerary", END)
    
    # Set the entry point
    workflow.set_entry_point("process_hotel_data")
    
    return workflow.compile()

# Load dropdowns
if "dropdowns_loaded" not in st.session_state:
    st.session_state.dropdowns_loaded = False

if st.button("🔄 Load Options") or not st.session_state.dropdowns_loaded:
    try:
        hotel_df = pd.read_sql("SELECT * FROM HotelTable", create_engine(hotel_conn_str))
        flight_df = pd.read_sql("SELECT * FROM flightsdata", create_engine(flight_conn_str))

        st.session_state.hotel_df = hotel_df
        st.session_state.flight_df = flight_df
        st.session_state.states = sorted(hotel_df["state"].dropna().unique())
        st.session_state.ratings = sorted(hotel_df["hotel_star_rating"].dropna().astype(str).unique())
        st.session_state.dep_cities = sorted(flight_df["Departure_city"].dropna().unique())
        st.session_state.arr_cities = sorted(flight_df["Arrival_City"].dropna().unique())
        st.session_state.classes = sorted(flight_df["class"].dropna().unique())

        st.session_state.dropdowns_loaded = True
        st.success("✅ Options loaded.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

if st.session_state.dropdowns_loaded:
    st.subheader("🧑 Traveler Info")
    visitor_name = st.text_input("Name", value="Sathish")
    visitor_email = st.text_input("Email", value="sathish@example.com")
    visitor_count = st.number_input("No. of People", min_value=1, value=2)

    st.subheader("📅 Travel Dates")
    arrival_date = st.date_input("Arrival", value=date.today())
    departure_date = st.date_input("Departure", value=date.today())
    stay_days = max((departure_date - arrival_date).days, 1)
    st.markdown(f"🛏️ Nights of Stay: **{stay_days}**")

    st.subheader("🏨 Hotel Preferences")
    state = st.selectbox("State", st.session_state.states)
    city_options = sorted(st.session_state.hotel_df[st.session_state.hotel_df["state"] == state]["city"].dropna().unique())
    city = st.selectbox("City", city_options)
    rating_options = sorted(st.session_state.hotel_df[st.session_state.hotel_df["city"] == city]["hotel_star_rating"].dropna().astype(str).unique())
    rating = st.selectbox("Star Rating", rating_options)
    num_hotels_input = st.text_input("How many hotels to include? (1–10)", value="1")
    try:
        num_hotels = min(max(int(num_hotels_input), 1), 10)
    except:
        st.warning("⚠️ Invalid input, defaulting to 1 hotel.")
        num_hotels = 1

    st.subheader("✈️ Flight Preferences")
    dep_city = st.selectbox("Departure City", st.session_state.dep_cities)
    arr_city = st.selectbox("Arrival City", st.session_state.arr_cities)
    travel_class = st.selectbox("Class", st.session_state.classes)

    filtered_stops = st.session_state.flight_df[
        (st.session_state.flight_df["Departure_city"] == dep_city) &
        (st.session_state.flight_df["Arrival_City"] == arr_city) &
        (st.session_state.flight_df["class"] == travel_class)
    ]["stops"].dropna().unique().tolist()
    stop = st.selectbox("Stops", sorted(filtered_stops))

    airline_list = st.session_state.flight_df[
        (st.session_state.flight_df["Departure_city"] == dep_city) &
        (st.session_state.flight_df["Arrival_City"] == arr_city)
    ]["airline"].dropna().unique().tolist()
    selected_airlines = st.multiselect("Preferred Airlines", sorted(airline_list), default=airline_list)

    language = st.selectbox("🌐 Language", ["English", "Tamil", "Hindi", "Kannada", "Telugu"])

    if st.button("🧠 Generate Itinerary"):
        with st.spinner("Generating your travel plan..."):
            # Fetch hotel data
            hotel_query = f"SELECT TOP {num_hotels} * FROM HotelTable WHERE state = '{state}' AND city = '{city}' AND hotel_star_rating = '{rating}' ORDER BY site_review_rating DESC"
            hotel_df = pd.read_sql(hotel_query, create_engine(hotel_conn_str))
            hotel_info = "\n\n".join([
                f"Hotel: {row['property_name']}\nRating: {row['site_review_rating']}/5\nAddress: {row['address']}, {row['city']}\nFacilities: {row['hotel_facilities']}\nRoom: {row['room_type']}\nLink: {row['pageurl']}"
                for _, row in hotel_df.iterrows()
            ])

            # Fetch flight data
            flight_query = f"SELECT * FROM flightsdata WHERE Departure_city = '{dep_city}' AND Arrival_City = '{arr_city}' AND class = '{travel_class}' AND stops = '{stop}'"
            if selected_airlines:
                airline_list_str = ", ".join([f"'{airline}'" for airline in selected_airlines])
                flight_query += f" AND airline IN ({airline_list_str})"
            
            flight_df = pd.read_sql(flight_query, create_engine(flight_conn_str))
            top_flights = flight_df.sort_values("price").groupby("airline").head(2)
            flight_info = "\n\n".join([
                f"Airline: {row['airline']}\nFrom: {row['Departure_city']} {row['dep_time']} → To: {row['Arrival_City']} {row['arr_time']}\nStops: {row['stops']} | Duration: {row['duration']} | Price: ₹{row['price']}"
                for _, row in top_flights.iterrows()
            ])

            # Fetch sightseeing data
            def get_sightseeing(city):
                try:
                    search = f"top tourist attractions in {city} India site:tripadvisor.com"
                    r = requests.get(f"https://www.bing.com/search?q={search}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    soup = BeautifulSoup(r.text, "html.parser")
                    return [a.get_text() for a in soup.select("li.b_algo h2 a")][:10]
                except:
                    return [f"{city} Temple", f"{city} Museum", f"{city} Garden", f"{city} Market", f"{city} Palace"]

            attractions = get_sightseeing(city)
            attractions_text = "\n".join(f"- {a}" for a in attractions)

            # Initialize LangGraph state
            initial_state = {
                "hotel_info": hotel_info,
                "flight_info": flight_info,
                "attractions_text": attractions_text,
                "city": city,
                "stay_days": stay_days,
                "visitor_count": visitor_count,
                "language": language
            }

            # Create and run the graph
            travel_planner = create_travel_planner_graph()
            result = travel_planner.invoke(initial_state)

            st.success("✅ Your plan is ready!")
            st.subheader("📋 Travel Plan")
            st.markdown(result["final_itinerary"])

            # Show detailed summaries in expandable sections
            with st.expander("🏨 Hotel Details"):
                st.markdown(result["hotel_summary"])
            
            with st.expander("✈️ Flight Options"):
                st.markdown(result["flight_summary"])
            
            with st.expander("🏛️ Sightseeing Attractions"):
                st.markdown(result["sightseeing_summary"])