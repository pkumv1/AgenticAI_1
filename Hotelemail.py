# Full Enhanced Streamlit App for Hotel Promotions

import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from langchain_groq import ChatGroq
from sqlalchemy import create_engine
import pyttsx3
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from io import BytesIO
from PIL import Image

# === Load API Key ===
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Hotel Promotion Generator", page_icon="🏨", layout="wide")
st.title("🏨 Hotel Promotion Generator")
st.write("Generate personalized promotional content based on real-time hotel data.")

if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found. Please check your .env file.")
    st.stop()

# === Sidebar Configuration ===
with st.sidebar:
    st.header("🔧 Database Configuration")
    server = st.text_input("SQL Server", value="M0HYDLAP050-SAT\SQLEXPRESS")
    database = st.text_input("Database Name", value="HotelDB")
    driver = st.selectbox("ODBC Driver", ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"])
    use_windows_auth = st.checkbox("Use Windows Authentication", value=True)

    if use_windows_auth:
        conn_str = f"mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes"
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"

    if st.button("🔄 Connect & Load Filters"):
        try:
            engine = create_engine(conn_str)
            with engine.connect() as conn:
                states = pd.read_sql("SELECT DISTINCT state FROM HotelTable WHERE state IS NOT NULL ORDER BY state", conn)
                st.session_state.states = states["state"].tolist()
                st.session_state.db_engine = engine
                st.success("✅ Connection successful!")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")

# === Main App Section ===
if "states" in st.session_state:
    engine = st.session_state.db_engine

    st.header("📝 Visitor & Hotel Preferences")
    with st.expander("📍 Select Your Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        state = col1.selectbox("State", st.session_state.states)

        cities = pd.read_sql(f"SELECT DISTINCT city FROM HotelTable WHERE state = '{state}' AND city IS NOT NULL ORDER BY city", engine)
        city = col2.selectbox("City", cities["city"].tolist())

        ratings_query = f"""
            SELECT DISTINCT hotel_star_rating FROM HotelTable
            WHERE state = '{state}' AND city = '{city}' AND hotel_star_rating IS NOT NULL
            ORDER BY hotel_star_rating
        """
        ratings = pd.read_sql(ratings_query, engine)
        rating = col3.selectbox("Hotel Rating", ratings["hotel_star_rating"].dropna().tolist())

        col4, col5, col6 = st.columns(3)
        num_hotels = col4.number_input("Number of Hotels to Include", min_value=1, max_value=10, value=3)
        visitor_name = col5.text_input("Visitor Name")
        visitor_count = col6.number_input("Number of People Visiting", min_value=1, value=2)

        visitor_email = st.text_input("Visitor Email")
        language = st.selectbox("🌐 Preferred Language", ["English", "Hindi", "Telugu", "Kannada", "Tamil", "Marathi"])

    def fetch_data():
        query = f"""
            SELECT TOP {num_hotels} property_name, hotel_star_rating, site_review_rating,
                   city, state, address, hotel_description, hotel_facilities, room_type, pageurl
            FROM HotelTable
            WHERE state = '{state}' AND city = '{city}' AND hotel_star_rating = '{rating}'
            ORDER BY site_review_rating DESC
        """
        return pd.read_sql(query, engine)

    def generate_hotel_summaries(df):
        return "\n".join([
            f"- *{row['property_name']}* ({row['hotel_star_rating']})\n"
            f"📍 {row['address']}, {row['city']}, {row['state']}\n"
            f"💬 Rating: {row['site_review_rating']}\n"
            f"🛎️ Room Type: {row['room_type']}\n"
            f"📝 {row['hotel_description'][:200]}...\n"
            f"📢 Facilities: {row['hotel_facilities'][:200]}...\n"
            f"🔗 {row['pageurl']}\n"
            for _, row in df.iterrows()
        ])

    def generate_qr(content):
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(content[:2950])
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    def get_email_prompt(summary_text):
        return f"""
Generate a professional promotional email from Ram Tours and Travels for {visitor_name} who is planning a {visitor_count}-person trip to {city}, {state}. Include the hotel summaries below.

{summary_text}

End with: Regards, Ram Tours and Travels
"""

    def translate_prompt(prompt_text):
        if language != "English":
            return f"Translate this into {language}:\n{prompt_text}"
        return prompt_text

    # === Action Buttons ===
    st.header("⚙️ Generate Promotional Content")
    col1, col2, col3 = st.columns(3)
    btn_email = col1.button("📨 Email")
    btn_whatsapp = col2.button("💬 WhatsApp")
    btn_sms = col3.button("📱 SMS")

    col4, col5, col6 = st.columns(3)
    btn_voice = col4.button("🔊 Voice")
    btn_qr = col5.button("📷 QR Code")
    btn_all = col6.button("✨ Generate All")

    if any([btn_email, btn_whatsapp, btn_sms, btn_voice, btn_qr, btn_all]):
        try:
            df = fetch_data()
            if df.empty:
                st.warning("No matching hotels found for your filters.")
            else:
                # Show hotel table
                st.subheader("🏨 Hotel Details")
                display_df = df.rename(columns={
                    "property_name": "Hotel Name",
                    "hotel_star_rating": "Stars",
                    "site_review_rating": "Site Rating",
                    "address": "Address",
                    "hotel_description": "Description",
                    "hotel_facilities": "Facilities",
                    "room_type": "Room Type",
                    "pageurl": "Booking Link"
                })
                st.dataframe(display_df[[
                    "Hotel Name", "Stars", "Site Rating", "Room Type", "Address", "Description", "Facilities", "Booking Link"
                ]], use_container_width=True)

                summaries = generate_hotel_summaries(df)
                full_prompt = get_email_prompt(summaries)
                prompt_translated = translate_prompt(full_prompt)

                if btn_email or btn_all or btn_voice:
                    llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.5)
                    response = llm.invoke(prompt_translated)
                    final_email = response.content
                    if btn_email or btn_all:
                        st.subheader("📨 Email Content")
                        st.markdown(final_email)

                if btn_whatsapp or btn_all:
                    whatsapp = f"""Hello {visitor_name} 👋,

We at *Ram Tours and Travels* curated the best hotels for your {visitor_count}-person trip to {city}, {state}:

{summaries}

Let us know if you'd like to book! 😊
-- Ram Tours and Travels"""
                    if language != "English":
                        llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.5)
                        whatsapp = llm.invoke(f"Translate to {language}:\n{whatsapp}").content
                    st.subheader("💬 WhatsApp Message")
                    st.text_area("WhatsApp", whatsapp, height=300)

                if btn_sms or btn_all:
                    sms = f"Hi {visitor_name}, Hotels for your {visitor_count}-person trip to {city}:\n\n"
                    for i, row in df.iterrows():
                        sms += f"{row['property_name']} - {row['address'][:30]}... ⭐ {row['site_review_rating']}\n"
                    sms += "Reply to book. – Ram Tours"
                    if language != "English":
                        llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.5)
                        sms = llm.invoke(f"Translate to {language}:\n{sms}").content
                    st.subheader("📱 SMS Message")
                    st.text_area("SMS", sms, height=300)

                if btn_qr or btn_all:
                    qr_data = "\n".join([f"{row['property_name']} - {row['pageurl']}" for _, row in df.iterrows()])
                    qr_img = generate_qr(qr_data)
                    st.image(qr_img, caption="📷 QR Code with Booking Links", use_container_width=True)

                if btn_voice or btn_all:
                    if 'final_email' not in locals():
                        llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.5)
                        final_email = llm.invoke(prompt_translated).content
                    engine_tts = pyttsx3.init()
                    engine_tts.save_to_file(final_email, "email_voice.mp3")
                    engine_tts.runAndWait()
                    audio_file = open("email_voice.mp3", "rb")
                    st.audio(audio_file.read(), format="audio/mp3")

        except Exception as e:
            st.error(f"❌ Error generating content: {e}")
else:
    st.info("👈 Please connect to your SQL Server and load filters.")
