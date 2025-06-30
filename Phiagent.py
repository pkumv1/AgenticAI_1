import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from phi.assistant import Assistant
from phi.llm.groq import Groq
import time

# === Load Environment Variables ===
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Hotel & Flight Summary Generator", page_icon="✈️", layout="wide")
st.title("✈️ Hotel & Flight Summary Generator")
st.write("Easily generate personalized hotel and flight summaries using Groq-powered LLMs.")

if not groq_api_key:
    st.error("🔑 GROQ_API_KEY not found. Please set it in your .env file.")
    st.stop()

# === Sidebar Config ===
st.sidebar.header("🔧 SQL Server Configuration")
server = st.sidebar.text_input("Server Name", value="SATHISHROHINI\\SQLEXPRESS")
driver = st.sidebar.selectbox("ODBC Driver", options=["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"])
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

# === LLM Setup ===
model_options = ["llama3-8b-8192", "llama3-70b-8192"]
selected_model = st.sidebar.selectbox("Select Groq Model", model_options, index=0)

llm = Groq(api_key=groq_api_key, model=selected_model, temperature=0.5)

# === Load dropdown values ===
if "dropdowns_loaded" not in st.session_state:
    st.session_state.dropdowns_loaded = False

if st.button("🔄 Load Options") or not st.session_state.dropdowns_loaded:
    try:
        hotel_engine = create_engine(hotel_conn_str)
        flight_engine = create_engine(flight_conn_str)

        with hotel_engine.connect() as conn:
            hotel_df = pd.read_sql("SELECT * FROM HotelTable", conn)
            st.session_state.hotel_df = hotel_df
            st.session_state.states = sorted(hotel_df["state"].dropna().unique().tolist())

        with flight_engine.connect() as conn:
            flight_df = pd.read_sql("SELECT * FROM flightsdata", conn)
            st.session_state.flight_df = flight_df
            st.session_state.dep_cities = sorted(flight_df["Departure_city"].dropna().unique().tolist())

        st.session_state.dropdowns_loaded = True
        st.success("✅ Options loaded successfully!")

    except Exception as e:
        st.error(f"❌ Error loading options: {e}")

if st.session_state.dropdowns_loaded:
    st.header("🔍 Details")

    with st.expander("🌐 Visitor Details"):
        col1, col2, col3 = st.columns(3)
        visitor_name = col1.text_input("Name")
        visitor_email = col2.text_input("Email")
        visitor_count = col3.number_input("No. of People", min_value=1, value=2)

    with st.expander("🏨 Hotel Preferences"):
        state = st.selectbox("State", st.session_state.states)
        cities = sorted(st.session_state.hotel_df[st.session_state.hotel_df["state"] == state]["city"].dropna().unique().tolist())
        city = st.selectbox("City", cities)
        ratings = sorted(st.session_state.hotel_df[(st.session_state.hotel_df["state"] == state) & (st.session_state.hotel_df["city"] == city)]["hotel_star_rating"].dropna().astype(str).unique().tolist())
        rating = st.selectbox("Hotel Rating", ratings)
        num_hotels = st.number_input("How many hotels to include? (max 5)", min_value=1, max_value=5, value=3)

    with st.expander("✈️ Flight Preferences"):
        dep_city = st.selectbox("Departure City", st.session_state.dep_cities)
        arr_cities = sorted(st.session_state.flight_df[st.session_state.flight_df["Departure_city"] == dep_city]["Arrival_City"].dropna().unique().tolist())
        arr_city = st.selectbox("Arrival City", arr_cities)
        classes = sorted(st.session_state.flight_df[(st.session_state.flight_df["Departure_city"] == dep_city) & (st.session_state.flight_df["Arrival_City"] == arr_city)]["class"].dropna().unique().tolist())
        travel_class = st.selectbox("Class", classes)
        stops = sorted(st.session_state.flight_df[(st.session_state.flight_df["Departure_city"] == dep_city) & (st.session_state.flight_df["Arrival_City"] == arr_city) & (st.session_state.flight_df["class"] == travel_class)]["stops"].dropna().unique().tolist())
        stop = st.selectbox("Stops", stops)
        airlines = sorted(st.session_state.flight_df[(st.session_state.flight_df["Departure_city"] == dep_city) & (st.session_state.flight_df["Arrival_City"] == arr_city) & (st.session_state.flight_df["class"] == travel_class) & (st.session_state.flight_df["stops"] == stop)]["airline"].dropna().unique().tolist())
        selected_airlines = st.multiselect("Preferred Airlines", airlines, default=airlines)

    if st.button("🤖 Generate Summary"):
        try:
            st.info(f"🧠 Generating your personalized travel summary using {selected_model}...")
            progress_bar = st.progress(0)

            hotel_query = f"""
                SELECT TOP {num_hotels} property_name, hotel_star_rating, site_review_rating,
                       city, state, address, hotel_description, hotel_facilities, room_type, pageurl
                FROM HotelTable
                WHERE state = '{state}' AND city = '{city}' AND hotel_star_rating = '{rating}'
                ORDER BY site_review_rating DESC
            """

            airline_str = "','".join(selected_airlines)
            flight_query = f"""
                SELECT TOP 5 * FROM flightsdata
                WHERE Departure_city = '{dep_city}' AND Arrival_City = '{arr_city}'
                AND airline IN ('{airline_str}') AND class = '{travel_class}' AND stops = '{stop}'
                ORDER BY price ASC
            """

            hotel_engine = create_engine(hotel_conn_str)
            flight_engine = create_engine(flight_conn_str)

            hotel_df = pd.read_sql(hotel_query, hotel_engine)
            flight_df = pd.read_sql(flight_query, flight_engine)

            progress_bar.progress(50)

            hotel_text = hotel_df.to_string(index=False)
            flight_text = flight_df.to_string(index=False)

            hotel_assistant = Assistant(
                name="Hotel Summary Expert",
                llm=llm,
                description="Summarizes hotel options in detail",
                instructions=[
                    "You are a hotel assistant.",
                    f"Analyze hotel options in {city}, {state} for a {visitor_count}-person trip.",
                    "Provide a summary using bullet points. Include 5-6 bullet points with highlights, location, room type, amenities, and value."
                ]
            )

            flight_assistant = Assistant(
                name="Flight Summary Expert",
                llm=llm,
                description="Summarizes flight options",
                instructions=[
                    "You are a flight assistant.",
                    f"Summarize flight options from {dep_city} to {arr_city} for {visitor_count} people.",
                    "Use bullet points (3-5) highlighting price, airline, time, and best value picks."
                ]
            )

            hotel_summary = "".join(chunk for chunk in hotel_assistant._run(f"Hotel details:\n{hotel_text}"))
            flight_summary = "".join(chunk for chunk in flight_assistant._run(f"Flight details:\n{flight_text}"))

            progress_bar.progress(100)
            st.success("✅ Summary generated successfully!")

            st.markdown("### 🏨 Hotel Summary")
            st.markdown(hotel_summary)

            st.markdown("### ✈️ Flight Summary")
            st.markdown(flight_summary)

        except Exception as e:
            st.error(f"❌ Generation failed: {e}")
