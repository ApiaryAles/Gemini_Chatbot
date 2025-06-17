# chatbot_app.py - FINAL VERSION 8 (Manual Supabase Connection)

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client # NEW: Import the manual client

# --- SETUP AND CONSTANTS ---
load_dotenv()

# --- CONFIGURE THE GEMINI API & SUPABASE ---
try:
    # Configure Gemini (Unchanged)
    genai.configure(api_key=st.secrets["app_secrets"]["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # --- MANUAL SUPABASE CONNECTION (NEW) ---
    # This section replaces the failing st.connection() call.
    # It reads the secrets directly and creates the Supabase client manually.
    url: str = st.secrets["connections"]["supabase"]["url"]
    key: str = st.secrets["connections"]["supabase"]["key"]
    supabase: Client = create_client(url, key)
    # -----------------------------------------

except Exception as e:
    st.error(f"Error initializing services: {e}")
    st.stop()


# --- DATABASE FUNCTIONS (Unchanged) ---
# The rest of the code does not need to change, as it now has the 'supabase' client object.
def load_history():
    """Loads chat history from the Supabase database using the correct syntax."""
    # The modern syntax is .table("...").select("...").order("...").execute()
    query = supabase.table("chat_history").select("*").order("created_at").execute()
    return query.data

def save_history(role, content):
    """Saves a new chat message to the Supabase database."""
    supabase.table("chat_history").insert([{"role": role, "content": content}]).execute()


# --- PASSWORD FUNCTION (Unchanged) ---
def check_password():
    """Shows a password form and sets session state upon submission."""
    with st.form("password_form"):
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

        if submitted:
            correct_password = st.secrets["app_secrets"]["CHATBOT_PASSWORD"]
            if password_input == correct_password:
                st.session_state["password_correct"] = True
            else:
                st.session_state["password_correct"] = False
                st.error("The password you entered is incorrect.")


# --- CHATBOT APP (Unchanged) ---
def chatbot_app():
    """The main chatbot application."""
    st.title("My AI Chatbot Assistant")
    st.caption("Powered by Google Gemini & Supabase")

    if "chat" not in st.session_state:
        db_history = load_history()
        history_for_gemini = []
        for msg in db_history:
            history_for_gemini.append({"role": msg["role"], "parts": [msg["content"]]})
        
        st.session_state.chat = model.start_chat(history=history_for_gemini)

    for message in st.session_state.chat.history:
        role = "assistant" if message.role == "model" else message.role
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

    if prompt := st.chat_input("What would you like to ask?"):
        save_history("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            response = st.session_state.chat.send_message(prompt)
            save_history("model", response.text)
            with st.chat_message("assistant"):
                st.markdown(response.text)


# --- MAIN CONTROLLER (Unchanged) ---
if st.session_state.get("password_correct", False):
    chatbot_app()
else:
    check_password()