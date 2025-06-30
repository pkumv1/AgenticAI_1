# AgenticAI_1 - PDF Assistant with LangChain

🤖 An intelligent PDF assistant that uses LangChain agents and GROQ's Llama 3 model to answer questions about uploaded PDF documents.

## 🚨 Important: Deployment Issues

Due to memory constraints on free hosting tiers, we've created two versions:

1. **Full Version (`app.py`)** - Uses LangChain, FAISS, and embeddings (requires more memory)
2. **Lite Version (`app_lite.py`)** - Direct GROQ API calls, no vector database (works on free tier)

## Features

### Full Version Features:
- 📄 PDF upload and processing
- 🤖 Agentic AI with LangChain
- 🧠 Powered by GROQ's Llama 3 70B model
- 🔍 RAG (Retrieval-Augmented Generation)
- 📚 FAISS vector store for efficient search
- 🔑 No .env file needed - API key input in UI

### Lite Version Features:
- 📄 PDF upload and text extraction
- 🧠 Direct GROQ API integration
- 💬 Simple Q&A interface
- 💡 Low memory footprint
- 🔑 No .env file needed - API key input in UI

## Live Demo

- **Streamlit Cloud**: [Deploy Full Version]
- **Render (Free Tier)**: Uses Lite Version due to memory constraints

## Local Setup

### For Full Version:
```bash
git clone https://github.com/pkumv1/AgenticAI_1.git
cd AgenticAI_1
pip install -r requirements.txt
streamlit run app.py
```

### For Lite Version (Recommended for free hosting):
```bash
git clone https://github.com/pkumv1/AgenticAI_1.git
cd AgenticAI_1
pip install streamlit groq pypdf
streamlit run app_lite.py
```

## Deployment

### Deploy to Streamlit Cloud (Recommended for Full Version)

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub account
5. Select `pkumv1/AgenticAI_1` repository
6. Set branch as `main` and main file as `app.py`
7. Click "Deploy!"

### Deploy to Render (Uses Lite Version)

1. Fork this repository
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select `pkumv1/AgenticAI_1` repository
6. The lite version will be automatically deployed

## Usage

1. Enter your GROQ API key in the sidebar
2. Upload a PDF file
3. Click "Read PDF" (Lite) or "Process PDF" (Full)
4. Ask questions about the PDF content
5. Get AI-powered answers

## Memory Requirements

- **Full Version**: ~2GB RAM (due to embeddings and FAISS)
- **Lite Version**: ~256MB RAM (works on free tiers)

## Get GROQ API Key

1. Visit [console.groq.com](https://console.groq.com/keys)
2. Sign up or log in
3. Create a new API key
4. Use it in the app

## Project Structure

```
AgenticAI_1/
├── app.py                 # Full version with LangChain
├── app_lite.py           # Lite version for free hosting
├── requirements.txt       # Full dependencies
├── requirements_minimal.txt # Minimal dependencies
├── render.yaml           # Render deployment config
├── start.sh             # Startup script (full)
├── start_lite.sh        # Startup script (lite)
├── .streamlit/
│   └── config.toml      # Streamlit configuration
└── README.md           # This file
```

## Other Files in Repository

- Various agent examples (Chatbot.py, Hotel_RAG.py, etc.)
- These are standalone examples not used in the main app

## Technologies Used

### Full Version:
- **Streamlit** - Web UI framework
- **LangChain** - Agent and chain orchestration
- **GROQ** - LLM API (Llama 3 70B)
- **FAISS** - Vector database
- **HuggingFace** - Embeddings
- **PyPDF** - PDF processing

### Lite Version:
- **Streamlit** - Web UI framework
- **GROQ** - LLM API (Llama 3 8B)
- **PyPDF** - PDF processing

## Contributing

Feel free to open issues or submit pull requests!

## License

This project is open source and available under the MIT License.
