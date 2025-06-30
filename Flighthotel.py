import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from langchain_groq import ChatGroq
from sqlalchemy import create_engine

# === Load GROQ API Key ===
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Hotel & Flight Promotion Generator", page_icon="📧", layout="wide")
st.title("📧 Hotel & Flight Promotion Generator")
st.write("Easily generate personalized hotel and flight promotions for your customers.")

if not groq_api_key:
    st.error("💼 GROQ_API_KEY not found. Please set it in your .env file.")
    st.stop()

# === Sidebar Config ===
st.sidebar.header("🔧 SQL Server Configuration")
server = st.sidebar.text_input("Server Name", value="M0HYDLAP050-SAT\SQLEXPRESS")
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
llm = ChatGroq(model_name="llama3-70b-8192", groq_api_key=groq_api_key, temperature=0.5)

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

        cities = sorted(
            st.session_state.hotel_df[
                st.session_state.hotel_df["state"] == state
            ]["city"].dropna().unique().tolist()
        )
        city = st.selectbox("City", cities)

        ratings = sorted(
            st.session_state.hotel_df[
                (st.session_state.hotel_df["state"] == state) &
                (st.session_state.hotel_df["city"] == city)
            ]["hotel_star_rating"].dropna().astype(str).unique().tolist()
        )
        rating = st.selectbox("Hotel Rating", ratings)

        num_hotels_input = st.text_input("How many hotels to include? (1-10)", value="1")
        try:
            num_hotels = int(num_hotels_input)
            if num_hotels < 1:
                st.warning("Minimum 1 hotel must be selected.")
                num_hotels = 1
            elif num_hotels > 10:
                st.warning("Maximum 10 hotels allowed. Using 10.")
                num_hotels = 10
        except:
            st.warning("Please enter a valid number between 1 and 10. Defaulting to 1.")
            num_hotels = 1

    with st.expander("✈️ Flight Preferences"):
        dep_city = st.selectbox("Departure City", st.session_state.dep_cities)

        arr_cities = sorted(
            st.session_state.flight_df[
                st.session_state.flight_df["Departure_city"] == dep_city
            ]["Arrival_City"].dropna().unique().tolist()
        )
        arr_city = st.selectbox("Arrival City", arr_cities)

        classes = sorted(
            st.session_state.flight_df[
                (st.session_state.flight_df["Departure_city"] == dep_city) &
                (st.session_state.flight_df["Arrival_City"] == arr_city)
            ]["class"].dropna().unique().tolist()
        )
        travel_class = st.selectbox("Class", classes)

        stops = sorted(
            st.session_state.flight_df[
                (st.session_state.flight_df["Departure_city"] == dep_city) &
                (st.session_state.flight_df["Arrival_City"] == arr_city) &
                (st.session_state.flight_df["class"] == travel_class)
            ]["stops"].dropna().unique().tolist()
        )
        stop = st.selectbox("Stops", stops)

        airlines = sorted(
            st.session_state.flight_df[
                (st.session_state.flight_df["Departure_city"] == dep_city) &
                (st.session_state.flight_df["Arrival_City"] == arr_city) &
                (st.session_state.flight_df["class"] == travel_class) &
                (st.session_state.flight_df["stops"] == stop)
            ]["airline"].dropna().unique().tolist()
        )
        selected_airlines = st.multiselect("Preferred Airlines", airlines, default=airlines)

    language = st.selectbox("🌐 Output Language", ["English", "Tamil", "Hindi", "Kannada", "Telugu"])

    if st.button("🤖 Generate Content"):
        try:
            hotel_query = f"""
                SELECT TOP {num_hotels} property_name, hotel_star_rating, site_review_rating,
                       city, state, address, hotel_description, hotel_facilities, room_type, pageurl
                FROM HotelTable
                WHERE state = '{state}' AND city = '{city}' AND hotel_star_rating = '{rating}'
                ORDER BY site_review_rating DESC
            """
            hotel_df = pd.read_sql(hotel_query, create_engine(hotel_conn_str))

            airline_str = "','".join(selected_airlines)
            flight_query = f"""
                SELECT * FROM flightsdata
                WHERE Departure_city = '{dep_city}' AND Arrival_City = '{arr_city}'
                AND airline IN ('{airline_str}') AND class = '{travel_class}' AND stops = '{stop}'
                ORDER BY price ASC
            """
            flight_df = pd.read_sql(flight_query, create_engine(flight_conn_str))

            # === Show Detailed Hotel Table ===
            if not hotel_df.empty:
                st.subheader("🏨 Selected Hotel Options")
                hotel_preview_df = hotel_df[[
                    "property_name", "hotel_star_rating", "site_review_rating", "room_type",
                    "hotel_description", "hotel_facilities", "address", "city", "state", "pageurl"
                ]].rename(columns={
                    "property_name": "Hotel Name",
                    "hotel_star_rating": "Star Rating",
                    "site_review_rating": "Site Rating",
                    "room_type": "Room Type",
                    "hotel_description": "Description",
                    "hotel_facilities": "Facilities",
                    "address": "Address",
                    "city": "City",
                    "state": "State",
                    "pageurl": "Booking Link"
                })
                st.dataframe(hotel_preview_df, use_container_width=True)
            else:
                st.warning("No hotels found for selected preferences.")

            # === Show Detailed Flight Table ===
            if not flight_df.empty:
                st.subheader("✈️ Selected Flight Options")
                flight_preview_df = flight_df[[
                    "airline", "flight_num", "class", "stops", "Departure_city", "dep_time",
                    "Arrival_City", "arr_time", "duration", "price"
                ]].rename(columns={
                    "airline": "Airline",
                    "flight_num": "Flight Number",
                    "class": "Class",
                    "stops": "Stops",
                    "Departure_city": "From",
                    "dep_time": "Departure Time",
                    "Arrival_City": "To",
                    "arr_time": "Arrival Time",
                    "duration": "Duration",
                    "price": "Price (INR)"
                })
                st.dataframe(flight_preview_df, use_container_width=True)
            else:
                st.warning("No flights found for selected preferences.")

            hotel_summaries = "\n\n".join([
                f"Hotel: {row['property_name']}\nRating: {row['site_review_rating']}/5\nRoom: {row['room_type']}\nDescription: {row['hotel_description']}\nFacilities: {row['hotel_facilities']}\nAddress: {row['address']}, {row['city']}\nLink: {row['pageurl']}"
                for _, row in hotel_df.iterrows()
            ])

            flight_summaries = "\n\n".join([
                f"Airline: {row['airline']} Flight: {row['flight_num']}\nClass: {row['class']} | Stops: {row['stops']}\nFrom: {row['Departure_city']} at {row['dep_time']} → To: {row['Arrival_City']} at {row['arr_time']}\nDuration: {row['duration']} | Price: ₹{row['price']}"
                for _, row in flight_df.iterrows()
            ]) if not flight_df.empty else "No matching flights found."

            def prep_prompt(template, lang):
                translate = f"Translate to {lang}:\n" if lang != "English" else ""
                return translate + template

            email_prompt = prep_prompt(f"""
Generate a professional promotional email for {visitor_name} planning a {visitor_count}-person trip to {city}, {state}.

🏨 Hotels:
{hotel_summaries}

✈️ Flights:
{flight_summaries}

End with: Regards, Ram Tours and Travels
            """, language)

            whatsapp_prompt = prep_prompt(f"""
Create a WhatsApp message for {visitor_name}'s {visitor_count}-person trip to {city}, {state}.

🏨 Hotels:
{hotel_summaries}

✈️ Flights:
{flight_summaries}

End with: Message us to assist further!
            """, language)

            sms_prompt = prep_prompt(f"""
Create an SMS about {visitor_name}'s trip to {city}, {state}. Include hotel and flight options.

🏨 Hotels:
{hotel_summaries}

✈️ Flights:
{flight_summaries}
            """, language)

            st.info("Generating content. Please wait...")

            email = llm.invoke(email_prompt).content
            whatsapp = llm.invoke(whatsapp_prompt).content
            sms = llm.invoke(sms_prompt).content

            with st.spinner("Displaying generated content..."):
                st.subheader("📧 Email")
                st.markdown(email)

                st.subheader("💬 WhatsApp")
                st.markdown(whatsapp)

                st.subheader("📱 SMS")
                st.markdown(sms)

        except Exception as e:
            st.error(f"❌ Generation failed: {e}")
