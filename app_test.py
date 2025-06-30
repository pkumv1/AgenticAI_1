import streamlit as st

# Minimal test app
st.set_page_config(page_title="Test App", page_icon="🔧")
st.title("🔧 Streamlit Test")
st.write("If you can see this, Streamlit is working!")

# Simple counter to test interactivity
if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("Click me"):
    st.session_state.counter += 1
    
st.write(f"Button clicked {st.session_state.counter} times")

# Display some debug info
st.sidebar.title("Debug Info")
st.sidebar.write("Python packages:")
st.sidebar.code("""
streamlit
groq
pypdf
""")
