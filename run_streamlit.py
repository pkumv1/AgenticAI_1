#!/usr/bin/env python
"""Run Streamlit with proper configuration for Render"""
import os
import sys
import streamlit.web.cli as stcli

if __name__ == '__main__':
    # Get port from environment
    port = int(os.environ.get('PORT', 8501))
    
    # Set Streamlit configuration
    os.environ['STREAMLIT_SERVER_PORT'] = str(port)
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Run Streamlit
    sys.argv = [
        'streamlit',
        'run',
        'app_lite.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    sys.exit(stcli.main())
