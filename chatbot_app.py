# chatbot_app.py - FINAL VERSION 9 (Live Google Search)

import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests # NEW: Import for making API calls

# --- SETUP AND CONSTANTS ---
load_dotenv()

# --- CONFIGURE THE GEMINI API & SUPABASE ---
try:
    # Configure services
    genai.configure(api_key=st.secrets["app_secrets"]["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    url: str = st.secrets["connections"]["supabase"]["url"]
    key: str = st.secrets["connections"]["supabase"]["key"]
    supabase: Client = create_client(url, key)

    # NEW: Get Google Search credentials
    SEARCH_API_KEY = st.secrets["app_secrets"]["GEMINI_API_KEY"] # Re-using Gemini key
    SEARCH_ENGINE_ID = st.secrets["app_secrets"]["SEARCH_ENGINE_ID"]

except Exception as e:
    st.error(f"Error initializing services: {e}")
    st.stop()


# --- NEW: GOOGLE SEARCH FUNCTION ---
def perform_Google Search(query: str):
    """Performs a Google search and returns formatted results."""
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        search_results = response.json()
        
        snippets = [item.get('snippet', '') for item in search_results.get('items', [])]
        if not snippets:
            return "No relevant information found."
            
        return "\n".join(snippets)
    except Exception as e:
        st.warning(f"Could not perform search: {e}")
        return "Search failed."


# --- DATABASE FUNCTIONS (Unchanged) ---
def load_history():
    """Loads chat history from the Supabase database."""
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


# --- CHATBOT APP (MODIFIED FOR SEARCH) ---
def chatbot_app():
    """The main chatbot application."""
    st.title("My AI Chatbot Assistant")
    st.caption("Powered by Google Gemini, Supabase, and live search")

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
            # NEW: Perform search and create a contextual prompt
            with st.spinner("Performing live search..."):
                search_context = perform_Google Search(query=prompt)
            
            contextual_prompt = f"""
            Based on the following real-time search results, please answer the user's question.
            
            Search Results:
            ---
            {search_context}
            ---
            
            User's Question: "{prompt}"
            """
            
            response = st.session_state.chat.send_message(contextual_prompt)
            save_history("model", response.text)
            with st.chat_message("assistant"):
                st.markdown(response.text)


# --- MAIN CONTROLLER (Unchanged) ---
if st.session_state.get("password_correct", False):
    chatbot_app()
else:
    check_password()
