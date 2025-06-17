# chatbot_app.py - FINAL VERSION 4 (Gemini AI Engine)

import streamlit as st
import google.generativeai as genai # NEW: Import Google's library
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- SETUP (MODIFIED FOR GEMINI) ---
try:
    # First, try to get the key from Streamlit's secrets
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        # If not found, fall back to the .env file for local development
        api_key = os.getenv("GEMINI_API_KEY")
    
    genai.configure(api_key=api_key)

except Exception as e:
    # This will show a helpful error if the API key is not set up correctly
    st.error(f"Error configuring the Gemini API: {e}")
    # We stop the app here because it can't run without the API key
    st.stop() 


# --- PASSWORD FUNCTION (Unchanged) ---
def check_password():
    """Shows a password form and sets session state upon submission."""
    with st.form("password_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

        if submitted:
            # Check against secrets first, then .env
            correct_password = st.secrets.get("CHATBOT_PASSWORD") or os.getenv("CHATBOT_PASSWORD")
            if password == correct_password:
                st.session_state["password_correct"] = True
            else:
                st.session_state["password_correct"] = False
                st.error("The password you entered is incorrect.")


# --- CHATBOT APP (MODIFIED FOR GEMINI) ---
def chatbot_app():
    """The main Gemini-powered chatbot application."""
    st.title("My AI Chatbot Assistant")
    st.caption("Powered by Google Gemini")

    # NEW: Initialize the Gemini model and chat history
    # We use gemini-1.5-flash for a good balance of speed and capability
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # NEW: The chat history is managed by Gemini's chat object
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

    # Display past messages from the chat's history
    for message in st.session_state.chat.history:
        # Gemini uses 'model' for the AI's role, so we map it to 'assistant' for display
        role = "assistant" if message.role == "model" else message.role
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

    # Get user input
    if prompt := st.chat_input("What would you like to ask?"):
        # Display user's message
        with st.chat_message("user"):
            st.markdown(prompt)

        # NEW: Send the message to Gemini and get the response
        with st.spinner("Thinking..."):
            response = st.session_state.chat.send_message(prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)

# --- MAIN CONTROLLER (Unchanged) ---
# This logic remains the same. It shows the password form or the app.
if st.session_state.get("password_correct", False):
    chatbot_app()
else:
    check_password()