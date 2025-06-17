# chatbot_app.py - FINAL VERSION 7 (Secrets Workaround)

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from st_supabase_connection import SupabaseConnection

# --- SETUP AND CONSTANTS ---
load_dotenv()

# --- CONFIGURE THE GEMINI API & SUPABASE ---
try:
    # MODIFIED: Look for the key inside the [app_secrets] table
    genai.configure(api_key=st.secrets["app_secrets"]["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    supabase = st.connection("supabase", type=SupabaseConnection)

except Exception as e:
    st.error(f"Error initializing services: {e}")
    st.stop()


# --- DATABASE FUNCTIONS (Unchanged) ---
def load_history():
    """Loads chat history from the Supabase database."""
    query = supabase.query("*", table="chat_history", order="created_at", count="exact").execute()
    return query.data

def save_history(role, content):
    """Saves a new chat message to the Supabase database."""
    supabase.table("chat_history").insert([{"role": role, "content": content}]).execute()


# --- PASSWORD FUNCTION (MODIFIED) ---
def check_password():
    """Shows a password form and sets session state upon submission."""
    with st.form("password_form"):
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

        if submitted:
            # MODIFIED: Look for the password inside the [app_secrets] table
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