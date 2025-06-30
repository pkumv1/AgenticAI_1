# AgenticAI_1 - PDF Assistant with LangChain

🤖 An intelligent PDF assistant that uses LangChain agents and GROQ's Llama 3 model to answer questions about uploaded PDF documents.

## Features

- 📄 PDF upload and processing
- 🤖 Agentic AI with LangChain
- 🧠 Powered by GROQ's Llama 3 70B model
- 🔍 RAG (Retrieval-Augmented Generation)
- 📚 FAISS vector store for efficient search
- 🔑 No .env file needed - API key input in UI

## Live Demo

- **Streamlit Cloud**: [Coming soon]
- **Render**: [Coming soon]

## Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/pkumv1/AgenticAI_1.git
   cd AgenticAI_1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

4. Open your browser and go to `http://localhost:8501`

5. Enter your GROQ API key in the sidebar (get one from [console.groq.com](https://console.groq.com/keys))

## Deployment

### Deploy to Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub account
5. Select `pkumv1/AgenticAI_1` repository
6. Set branch as `main` and main file as `app.py`
7. Click "Deploy!"

### Deploy to Render

1. Fork this repository
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select `pkumv1/AgenticAI_1` repository
6. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
7. Click "Create Web Service"

### Deploy to Vercel (Not Recommended)

Vercel is not ideal for Streamlit apps. Use Streamlit Cloud or Render instead.

## Usage

1. Enter your GROQ API key in the sidebar
2. Upload a PDF file
3. Wait for the agent to process the document
4. Ask questions about the PDF content
5. Get AI-powered answers based on the document

## Project Structure

```
AgenticAI_1/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── .streamlit/
│   └── config.toml      # Streamlit configuration
├── packages.txt         # System dependencies for Streamlit Cloud
└── README.md           # This file
```

## Other Files in Repository

- `Chatbot.py` - Basic chatbot implementation
- `Flighthotel.py` - Flight and hotel booking agent
- `Hotel_RAG.py` - Hotel booking with RAG
- `Hotel_SQL.py` - Hotel booking with SQL database
- `Hotelemail.py` - Hotel email agent
- `Multiagent.py` - Multi-agent system example
- `Phiagent.py` - Phi model agent
- `langgraph.py` - LangGraph implementation

## Technologies Used

- **Streamlit** - Web UI framework
- **LangChain** - Agent and chain orchestration
- **GROQ** - LLM API (Llama 3 70B)
- **FAISS** - Vector database
- **HuggingFace** - Embeddings
- **PyPDF** - PDF processing

## Contributing

Feel free to open issues or submit pull requests!

## License

This project is open source and available under the MIT License.
