import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from langchain_groq import ChatGroq
from sqlalchemy import create_engine, text
import re

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Travel Assistant Chatbot", page_icon="🌍")
st.title("🛅 Travel Assistant Chatbot")
st.write("Ask about hotels or flights using flexible filters like city, rating, stars, and facilities.")

if not groq_api_key:
    st.error("🛑 GROQ_API_KEY not found. Please set it in your `.env` file.")
    st.stop()

# SQL Config
st.sidebar.header("🔧 SQL Server Configuration")
server = st.sidebar.text_input("Server Name", value=r"M0HYDLAP050-SAT\SQLEXPRESS")
driver = st.sidebar.selectbox("ODBC Driver", ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"], index=0)
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

# Language
st.sidebar.markdown("---")
language = st.sidebar.selectbox("Language", ["English", "Tamil", "Hindi", "Kannada", "Telugu"], index=0)

# Load LLM
llm = ChatGroq(model_name="llama3-8b-8192", groq_api_key=groq_api_key)

# User Input
st.markdown("### 🗨️ Chat With the Travel Assistant")
user_input = st.text_input("Ask me about hotels or flights:")

# Extract filters from question
def extract_filters(text):
    filters = {}

    city_match = re.search(r"in\s+([A-Za-z\s]+)", text)
    if city_match:
        filters["city"] = city_match.group(1).strip()

    star_match = re.search(r"(\d(?:\.\d)?)\s*star", text, re.IGNORECASE)
    if star_match:
        filters["hotel_star_rating"] = star_match.group(1)

    rating_match = re.search(r"rating\s*(?:above|greater than|more than)\s*([\d.]+)", text, re.IGNORECASE)
    if rating_match:
        filters["site_review_rating"] = f"> {rating_match.group(1)}"

    facility_match = re.search(r"(?:has|with|including)\s+([A-Za-z0-9\s]+(?:,?\s*[A-Za-z0-9\s]+)*)\s*(?:facility|facilities)?", text, re.IGNORECASE)
    if facility_match:
        filters["hotel_facilities"] = facility_match.group(1).strip()

    return filters

if user_input:
    filters = extract_filters(user_input)
    where_clauses = []
    params = {}

    for col, val in filters.items():
        if col == "site_review_rating":
            where_clauses.append(f"{col} {val}")
        elif col == "hotel_facilities":
            where_clauses.append(f"{col} LIKE :{col}")
            params[col] = f"%{val}%"
        else:
            where_clauses.append(f"{col} = :{col}")
            params[col] = val

    where_clause = " AND ".join(where_clauses)

    # Hotel Query
    hotel_query = "SELECT TOP 3 * FROM HotelTable"
    if where_clause:
        hotel_query += f" WHERE {where_clause}"
    hotel_query += " ORDER BY site_review_rating DESC"

    # Flight Query (based on departure/arrival city)
    flight_query = "SELECT TOP 3 * FROM Flightsdata"
    flight_clauses = []
    if "city" in filters:
        flight_clauses.append("Departure_city = :dep OR Arrival_City = :arr")
        params["dep"] = filters["city"]
        params["arr"] = filters["city"]

    if flight_clauses:
        flight_query += " WHERE " + " AND ".join(flight_clauses)
    flight_query += " ORDER BY price ASC"

    try:
        hotel_df, flight_df = pd.DataFrame(), pd.DataFrame()
        hotel_engine = create_engine(hotel_conn_str)
        flight_engine = create_engine(flight_conn_str)

        with hotel_engine.connect() as conn:
            hotel_df = pd.read_sql(text(hotel_query), conn, params=params)

        with flight_engine.connect() as conn:
            flight_df = pd.read_sql(text(flight_query), conn, params=params)

        if hotel_df.empty and flight_df.empty:
            st.info("⚠️ No hotel or flight results found with the given filters.")
        else:
            if not hotel_df.empty:
                hotel_df = hotel_df.drop_duplicates()
                hotel_summary = "\n".join([
                    f"{row.property_name} ({row.hotel_star_rating}★) - Rating: {row.site_review_rating}, Facilities: {str(row.hotel_facilities)[:50]}..."
                    for _, row in hotel_df.iterrows()
                ])
            else:
                hotel_summary = "No hotel data found."

            if not flight_df.empty:
                flight_df = flight_df.drop_duplicates()
                flight_summary = "\n".join([
                    f"{row.airline} flight {row.flight_num} from {row.Departure_city} to {row.Arrival_City}, departs at {row.dep_time}, price: ₹{row.price}"
                    for _, row in flight_df.iterrows()
                ])
            else:
                flight_summary = "No flight data found."

            # Combine summary and get response
            combined_summary = f"Hotels:\n{hotel_summary}\n\nFlights:\n{flight_summary}"
            prompt = (
                f"You are a travel assistant. Summarize the hotel and flight options below in {language}. Help the user choose.\n\n"
                f"{combined_summary}"
            )

            response = llm.invoke(prompt).content

            st.markdown(f"**🤖 Assistant Summary:**\n\n{response}")

            if not hotel_df.empty:
                st.markdown("#### 🏨 Top 3 Hotel Details")
                st.dataframe(hotel_df)
            if not flight_df.empty:
                st.markdown("#### ✈️ Top 3 Flight Details")
                st.dataframe(flight_df)

    except Exception as e:
        st.error(f"❌ Error occurred: {e}")
