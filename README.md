# AgenticAI_1

All Basic Agentic AI Stuff

## Description
This repository contains various agentic AI implementations using LangChain, including:
- PDF chatbot with RAG
- Multi-agent systems
- Hotel booking agents
- SQL and email agents

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running Locally

To run the main Streamlit app:
```bash
streamlit run app.py
```

## Deployment

This project is configured for deployment on Vercel. However, for better performance with Streamlit apps, consider using:
- [Streamlit Cloud](https://streamlit.io/cloud)
- [Railway](https://railway.app/)
- [Render](https://render.com/)

## Files
- `app.py` - Main Streamlit application for PDF Q&A
- `Chatbot.py` - Basic chatbot implementation
- `Hotel_RAG.py` - Hotel booking with RAG
- `Hotel_SQL.py` - Hotel booking with SQL database
- `Multiagent.py` - Multi-agent system example
- `langgraph.py` - LangGraph implementation
