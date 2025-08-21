import streamlit as st

# Test if Streamlit can run basic functionality
st.set_page_config(
    page_title="Test AI Diagram Generator",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Test - Generator diagramów AI")
st.write("Aplikacja Streamlit działa poprawnie!")

# Test session state
if 'test_counter' not in st.session_state:
    st.session_state.test_counter = 0

if st.button("Test Button"):
    st.session_state.test_counter += 1
    st.success(f"Przycisk został kliknięty {st.session_state.test_counter} razy!")

st.write("To jest test podstawowej funkcjonalności Streamlit.")
