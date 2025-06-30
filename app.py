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
import traceback

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
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

# === API Key Input ===
st.sidebar.title("🔑 Configuration")
api_key_input = st.sidebar.text_input(
    "Enter your GROQ API Key:",
    type="password",
    placeholder="gsk_...",
    help="Get your API key from https://console.groq.com/keys"
)

# Update API key in session state when changed
if api_key_input and api_key_input != st.session_state.groq_api_key:
    st.session_state.groq_api_key = api_key_input
    st.session_state.llm = None  # Reset LLM when key changes
    st.session_state.agent = None  # Reset agent when key changes
    
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

# === PDF Processing and Agent Setup ===
def setup_agent(file, llm):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.getvalue())  # Use getvalue() instead of read()
            tmp_path = tmp_file.name

        # Load PDF
        st.write("📖 Loading PDF...")
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        if not documents:
            st.error("❌ No content found in PDF")
            return None
            
        st.write(f"✅ Loaded {len(documents)} pages")

        # Split documents
        st.write("✂️ Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(documents)
        st.write(f"✅ Created {len(docs)} chunks")

        # Create embeddings
        st.write("🔤 Creating embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create vector store
        st.write("🗄️ Building vector store...")
        vectorstore = FAISS.from_documents(docs, embeddings)
        retriever = vectorstore.as_retriever()

        # Create retrieval chain
        st.write("🔗 Setting up retrieval chain...")
        retrieval_qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=False
        )

        # Create tool
        tool = Tool(
            name="PDF Retriever",
            func=retrieval_qa.run,
            description="Useful for answering questions from the uploaded PDF"
        )

        # Initialize agent
        st.write("🤖 Initializing agent...")
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
        st.error(f"❌ Failed to set up agent: {str(e)}")
        st.error(f"Debug info: {traceback.format_exc()}")
        return None

# === Process PDF button ===
if uploaded_file and st.session_state.llm:
    if st.button("🚀 Process PDF and Create Agent", type="primary"):
        with st.spinner("⚙️ Processing PDF and setting up the agent..."):
            agent = setup_agent(uploaded_file, st.session_state.llm)
            if agent:
                st.session_state.agent = agent
                st.session_state.pdf_processed = True
                st.success("🎯 Agent is ready! You can now ask questions below.")
                st.balloons()

# === Reset button ===
if st.sidebar.button("🔄 Reset Everything"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# === Display current status ===
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Current Status")
st.sidebar.write(f"API Key: {'✅ Set' if st.session_state.groq_api_key else '❌ Not set'}")
st.sidebar.write(f"LLM: {'✅ Ready' if st.session_state.llm else '❌ Not ready'}")
st.sidebar.write(f"PDF: {'✅ Uploaded' if uploaded_file else '❌ Not uploaded'}")
st.sidebar.write(f"Agent: {'✅ Active' if st.session_state.agent else '❌ Not active'}")

# === Ask a Question ===
if st.session_state.agent and st.session_state.pdf_processed:
    st.markdown("---")
    st.markdown("### 💬 Ask something about your PDF")
    
    # Create a form for better UX
    with st.form(key="question_form"):
        user_input = st.text_area(
            "Type your question:",
            placeholder="What is the main topic of this document?",
            height=100
        )
        submit_button = st.form_submit_button("🤔 Ask Question")
    
    if submit_button and user_input:
        with st.spinner("🤔 Thinking..."):
            try:
                answer = st.session_state.agent.run(user_input)
                st.success("**🧠 Answer:**")
                st.write(answer)
            except Exception as e:
                st.error(f"❌ Error generating answer: {str(e)}")
                st.error(f"Debug info: {traceback.format_exc()}")
    
    # Also show a simple text input as alternative
    st.markdown("**Or use quick input:**")
    quick_input = st.text_input("Quick question:", key="quick_input")
    if quick_input:
        with st.spinner("🤔 Thinking..."):
            try:
                answer = st.session_state.agent.run(quick_input)
                st.success("**🧠 Answer:**")
                st.write(answer)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
else:
    if uploaded_file and not st.session_state.agent:
        st.info("👆 Click 'Process PDF and Create Agent' button to start chatting!")
    elif not uploaded_file:
        st.info("📄 Please upload a PDF file to get started.")

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
