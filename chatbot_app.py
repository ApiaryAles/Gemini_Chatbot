# chatbot_app.py - FINAL VERSION 6 (Gemini with Supabase Memory)

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from st_supabase_connection import SupabaseConnection

# --- SETUP AND CONSTANTS ---
load_dotenv()

# --- CONFIGURE THE GEMINI API & SUPABASE ---
try:
    # Configure Gemini
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Initialize Supabase connection
    # The st.connection factory function will be used to get the connection object.
    # The name of the connection is "supabase" as defined in secrets.toml.
    supabase = st.connection("supabase", type=SupabaseConnection)

except Exception as e:
    st.error(f"Error initializing services: {e}")
    st.stop()


# --- DATABASE FUNCTIONS (NEW) ---

def load_history():
    """Loads chat history from the Supabase database."""
    query = supabase.query("*", table="chat_history", order="created_at", count="exact").execute()
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
            correct_password = st.secrets["CHATBOT_PASSWORD"]
            if password_input == correct_password:
                st.session_state["password_correct"] = True
            else:
                st.session_state["password_correct"] = False
                st.error("The password you entered is incorrect.")


# --- CHATBOT APP (MODIFIED FOR DATABASE) ---
def chatbot_app():
    """The main chatbot application."""
    st.title("My AI Chatbot Assistant")
    st.caption("Powered by Google Gemini & Supabase")

    # MODIFIED: Initialize the chat object from the database history
    if "chat" not in st.session_state:
        # Load the history and format it for Gemini
        db_history = load_history()
        history_for_gemini = []
        for msg in db_history:
            history_for_gemini.append({"role": msg["role"], "parts": [msg["content"]]})
        
        st.session_state.chat = model.start_chat(history=history_for_gemini)

    # Display past messages from the chat's history
    for message in st.session_state.chat.history:
        role = "assistant" if message.role == "model" else message.role
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

    # Get user input
    if prompt := st.chat_input("What would you like to ask?"):
        # Save and display user's message
        save_history("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI's response
        with st.spinner("Thinking..."):
            response = st.session_state.chat.send_message(prompt)
            # Save and display AI's response
            save_history("model", response.text)
            with st.chat_message("assistant"):
                st.markdown(response.text)


# --- MAIN CONTROLLER (Unchanged) ---
if st.session_state.get("password_correct", False):
    chatbot_app()
else:
    check_password()
# Forcing a Git update