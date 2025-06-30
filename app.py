import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chains import RetrievalQA
import tempfile
import os

# === Streamlit App Config ===
st.set_page_config(page_title="Agentic PDF Assistant", page_icon="🤖")
st.title("🤖 Agentic PDF Assistant")
st.write("Upload a PDF and ask your AI agent anything about its content.")

# === Session state initialization ===
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "llm" not in st.session_state:
    st.session_state.llm = None

# === API Key Input ===
st.sidebar.title("🔑 Configuration")
api_key_input = st.sidebar.text_input(
    "Enter your GROQ API Key:",
    type="password",
    placeholder="gsk_...",
    help="Get your API key from https://console.groq.com/keys"
)

# Update API key in session state when changed
if api_key_input:
    st.session_state.groq_api_key = api_key_input
    if st.session_state.llm is None:
        try:
            st.session_state.llm = ChatGroq(
                api_key=api_key_input,
                model_name="llama3-70b-8192",
                temperature=0.7,
                max_tokens=1024
            )
            st.sidebar.success("✅ API Key validated!")
        except Exception as e:
            st.sidebar.error(f"❌ Invalid API Key: {str(e)}")
            st.session_state.groq_api_key = None
            st.session_state.llm = None

# === Check if API key is provided ===
if not st.session_state.groq_api_key:
    st.info("👈 Please enter your GROQ API key in the sidebar to get started.")
    st.markdown(
        """
        ### How to get your GROQ API Key:
        1. Visit [GROQ Console](https://console.groq.com/keys)
        2. Sign up or log in
        3. Create a new API key
        4. Copy and paste it in the sidebar
        """
    )
    st.stop()

# === PDF Upload UI ===
uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")

# === PDF Processing and Agent Setup ===
def setup_agent(file, llm):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(docs, embeddings)

        retriever = vectorstore.as_retriever()

        retrieval_qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=False
        )

        tool = Tool(
            name="PDF Retriever",
            func=retrieval_qa.run,
            description="Useful for answering questions from the uploaded PDF"
        )

        agent = initialize_agent(
            tools=[tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True
        )

        # Clean up temp file
        os.unlink(tmp_path)
        
        return agent
    except Exception as e:
        st.error(f"❌ Failed to set up agent: {e}")
        return None

# === Create agent after upload ===
if uploaded_file and st.session_state.agent is None and st.session_state.llm:
    with st.spinner("⚙️ Processing PDF and setting up the agent..."):
        # Reset file pointer
        uploaded_file.seek(0)
        agent = setup_agent(uploaded_file, st.session_state.llm)
        if agent:
            st.session_state.agent = agent
            st.success("🎯 Agent is ready! Ask your first question below.")

# === Reset button ===
if st.sidebar.button("🔄 Reset Agent"):
    st.session_state.agent = None
    st.session_state.llm = None
    st.session_state.groq_api_key = None
    st.rerun()

# === Ask a Question ===
if st.session_state.agent:
    st.markdown("### 💬 Ask something about your PDF")
    user_input = st.text_input("Type your question and press Enter:")

    if user_input:
        with st.spinner("🤔 Thinking..."):
            try:
                answer = st.session_state.agent.run(user_input)
                st.markdown(f"**🧠 Answer:** {answer}")
            except Exception as e:
                st.error(f"❌ Error generating answer: {e}")

# === Footer ===
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    ### About
    This app uses:
    - 🤖 LangChain Agents
    - 🧠 GROQ LLM (Llama 3)
    - 📚 FAISS Vector Store
    - 🔍 RAG (Retrieval-Augmented Generation)
    """
)
