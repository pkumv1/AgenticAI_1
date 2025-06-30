#!/bin/bash
# Lightweight startup script for Streamlit on Render

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit/

# Create config file with minimal settings
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
address = 0.0.0.0\n\
maxUploadSize = 25\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
" > ~/.streamlit/config.toml

# Run the lite version
streamlit run app_lite.py
