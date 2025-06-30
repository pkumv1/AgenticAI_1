import streamlit as st
import os
import tempfile
from groq import Groq
from pypdf import PdfReader

# === Streamlit App Config ===
st.set_page_config(page_title="PDF Q&A Assistant", page_icon="🤖")
st.title("🤖 PDF Q&A Assistant (Lite Version)")
st.write("Upload a PDF and ask questions about its content.")

# === Session state initialization ===
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "client" not in st.session_state:
    st.session_state.client = None

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
    try:
        st.session_state.client = Groq(api_key=api_key_input)
        # Test the API key
        st.session_state.client.chat.completions.create(
            messages=[{"role": "user", "content": "test"}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        st.sidebar.success("✅ API Key validated!")
    except Exception as e:
        st.sidebar.error(f"❌ Invalid API Key: {str(e)}")
        st.session_state.groq_api_key = None
        st.session_state.client = None

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

# === Process PDF ===
if uploaded_file:
    if st.button("📖 Read PDF", type="primary"):
        with st.spinner("Reading PDF..."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Read PDF
                reader = PdfReader(tmp_path)
                text = ""
                for i, page in enumerate(reader.pages):
                    text += f"\n\n--- Page {i+1} ---\n\n"
                    text += page.extract_text()
                
                # Store in session state
                st.session_state.pdf_text = text[:50000]  # Limit to first 50k chars
                
                # Clean up
                os.unlink(tmp_path)
                
                st.success(f"✅ PDF loaded! ({len(reader.pages)} pages, {len(text)} characters)")
                
            except Exception as e:
                st.error(f"❌ Error reading PDF: {str(e)}")

# === Chat Interface ===
if st.session_state.pdf_text and st.session_state.client:
    st.markdown("---")
    st.markdown("### 💬 Ask questions about your PDF")
    
    # Display a sample of the PDF content
    with st.expander("📄 View PDF Preview (first 500 characters)"):
        st.text(st.session_state.pdf_text[:500] + "...")
    
    # Question input
    question = st.text_input(
        "Your question:",
        placeholder="What is the main topic of this document?"
    )
    
    if question:
        with st.spinner("🤔 Thinking..."):
            try:
                # Create prompt
                prompt = f"""Based on the following PDF content, please answer the question.

PDF Content:
{st.session_state.pdf_text[:10000]}  # Limit context to 10k chars

Question: {question}

Please provide a clear and concise answer based only on the information in the PDF."""
                
                # Get response from GROQ
                response = st.session_state.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on PDF content."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",  # Using smaller model
                    max_tokens=500,
                    temperature=0.7
                )
                
                # Display answer
                answer = response.choices[0].message.content
                st.success("🧠 **Answer:**")
                st.write(answer)
                
            except Exception as e:
                st.error(f"❌ Error generating answer: {str(e)}")

# === Reset button ===
if st.sidebar.button("🔄 Reset Everything"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# === Status Display ===
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Status")
st.sidebar.write(f"API Key: {'✅' if st.session_state.groq_api_key else '❌'}")
st.sidebar.write(f"PDF: {'✅' if st.session_state.pdf_text else '❌'}")

# === Footer ===
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    ### About (Lite Version)
    This simplified version:
    - Uses direct GROQ API
    - No vector database
    - Lower memory usage
    - Works on free tier
    """
)
