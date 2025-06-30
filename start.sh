#!/bin/bash
# Startup script for Streamlit on Render

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit/

# Create credentials file
echo "\
[general]\n\
email = \"\"\n\
" > ~/.streamlit/credentials.toml

# Create config file with proper settings
echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
port = $PORT\n\
\n\
[browser]\n\
serverAddress = \"0.0.0.0\"\n\
gatherUsageStats = false\n\
" > ~/.streamlit/config.toml

# Run streamlit
streamlit run app.py
