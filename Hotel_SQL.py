import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType, AgentExecutor
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.callbacks.base import BaseCallbackHandler
import pandas as pd

# === SQL Debug Handler ===
class SQLDebugHandler(BaseCallbackHandler):
    def __init__(self):
        self.intermediate_steps = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.intermediate_steps.append(input_str)

    def get_sql(self):
        return "\n\n".join(self.intermediate_steps)

    def clear(self):
        self.intermediate_steps = []

# === Load GROQ API Key ===
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="SQL Agent Assistant", page_icon="🧠")
st.title("🧠 Direct SQL Agent for Your Database")
st.write("Ask natural language questions. The app will convert them to SQL queries and fetch results from your database.")

if not groq_api_key:
    st.error("🚫 GROQ_API_KEY not found in `.env`. Please set it in your environment or a .env file.")
    st.stop()

# === Sidebar: SQL Server Config ===
st.sidebar.header("🔧 SQL Server Configuration")
server = st.sidebar.text_input("Server Name", value="M0HYDLAP050-SAT\SQLEXPRESS")
database = st.sidebar.text_input("Database Name", value="HotelDB")
driver = st.sidebar.selectbox("ODBC Driver", options=[
    "ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"
], index=0)
use_windows_auth = st.sidebar.checkbox("Use Windows Authentication", value=True)

# === Dynamic Connection String ===
if use_windows_auth:
    conn_str = f"mssql+pyodbc://@{server}/{database}?driver={driver}&trusted_connection=yes"
else:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"

# === Agent + SQL Connection ===
sql_debug = SQLDebugHandler()

if st.sidebar.button("🔄 Connect to Database"):
    try:
        db = SQLDatabase.from_uri(
            conn_str,
            include_tables=["HotelTable"],
            sample_rows_in_table_info=True,
            custom_table_info={
                "HotelTable": (
                    "This table contains hotel listings from across India, including details such as hotel name, city, state, star rating, number of reviews, average review rating, facilities, room types, latitude, longitude, and booking URLs. "
                    "Use it to answer questions about hotel attributes, reviews, availability, amenities, location, and ratings."
                )
            }
        )

        llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.3)

        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()

        tools[0].description = (
            "Query HotelTable to retrieve hotel names, reviews, locations, amenities, and more across India. Ideal for retrieving filtered hotel data or summary statistics."
        )

        agent_executor: AgentExecutor = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            callbacks=[sql_debug],
            verbose=True,
            return_intermediate_steps=True
        )

        st.session_state["agent_executor"] = agent_executor
        st.session_state["db_engine"] = db._engine
        st.session_state["connected"] = True
        st.success("✅ Connected to SQL Server successfully!")

    except Exception as e:
        st.session_state["connected"] = False
        st.error(f"❌ Failed to connect: {e}")

# === Main QA Section ===
if st.session_state.get("connected", False) and "agent_executor" in st.session_state:
    query = st.text_input("💬 Ask your question about the database:")

    if query:
        with st.spinner("🤖 Thinking..."):
            try:
                sql_debug.clear()
                output = st.session_state["agent_executor"].invoke({"input": query})
                result = output["output"]
                steps = output.get("intermediate_steps", [])

                st.markdown("### 🧠 Answer")
                st.write(result)

                sql_query = None
                for step in steps:
                    if isinstance(step[0], dict) and "tool_input" in step[0]:
                        sql_query = step[0]["tool_input"]
                        break

                if sql_query:
                    st.markdown("### 🔍 SQL Query Used")
                    st.code(sql_query, language="sql")

                    try:
                        df = pd.read_sql_query(sql_query, st.session_state["db_engine"])
                        if not df.empty:
                            st.markdown("### 📋 Table Result")
                            st.dataframe(df)
                    except Exception as df_err:
                        st.warning(f"⚠️ Could not display table result: {df_err}")

            except Exception as e:
                st.error(f"❌ Error during execution: {e}")
else:
    st.info("👈 Configure the database connection in the sidebar and click 'Connect'.")
