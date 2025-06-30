import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine
import pandas as pd
from langchain.schema import Document

# Load API Key
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="SQL Table RAG", page_icon="🧠")
st.title("🧠 RAG over SQL Table (HotelDB)")
st.write("Ask natural language questions about your HotelDB > HotelTable.")

# === Check API Key ===
if not groq_api_key:
    st.error("🚫 GROQ_API_KEY not found in `.env`.")
    st.stop()

# === LLM Init ===
llm = ChatGroq(
    model_name="llama3-70b-8192",
    temperature=0.7,
    max_tokens=1024
)

# === Connect to SQL Server & Fetch Data ===
try:
    engine = create_engine(
        "mssql+pyodbc://@M0HYDLAP050-SAT\\SQLEXPRESS/HotelDB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )

    df = pd.read_sql("SELECT * FROM HotelTable", engine)
    st.success("✅ Loaded HotelTable from SQL Server.")
    st.dataframe(df.head())
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# === Convert DataFrame to Text ===
text_data = df.astype(str).apply(lambda row: " | ".join(row), axis=1).tolist()
docs = [Document(page_content=chunk) for chunk in text_data]

# === Split text into chunks (if long) ===
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# === Embed using HuggingFace ===
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever()

# === RAG Chain (QA over SQL data) ===
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# === Ask the question ===
query = st.text_input("💬 Ask a question about HotelTable:")
if query:
    with st.spinner("🤖 Thinking..."):
        try:
            result = qa_chain.run(query)
            st.markdown("**🧠 Answer:**")
            st.write(result)
        except Exception as e:
            st.error(f"❌ Failed to answer: {e}")
