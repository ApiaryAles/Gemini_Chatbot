# chatbot.py - FINAL VERSION 3 (No st.rerun)

import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load environment variables (useful for local development)
load_dotenv()

# --- SETUP ---
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except:
    # This error handling is for when the app is first deployed
    # and secrets haven't been added yet.
    pass

# --- PASSWORD FUNCTION (MODIFIED) ---
# This function now ONLY displays the form and checks the password.
# It does NOT call st.rerun().

def check_password():
    """Shows a password form and sets session state upon submission."""
    with st.form("password_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

        if submitted:
            if password == st.secrets.get("CHATBOT_PASSWORD"):
                st.session_state["password_correct"] = True
            else:
                st.session_state["password_correct"] = False
                st.error("The password you entered is incorrect.")

# --- CHATBOT APP ---
# This function is unchanged. It contains the main logic for the chatbot.

def chatbot_app():
    """The main chatbot application."""
    def get_ai_response(prompt_text):
        response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt_text}])
        return response.choices[0].message.content

    st.title("My AI Chatbot Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to ask?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            ai_response = get_ai_response(prompt)
            with st.chat_message("assistant"):
                st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})


# --- MAIN CONTROLLER (MODIFIED) ---
# This is the new logic that decides what to show on the page.

if st.session_state.get("password_correct", False):
    # If the password is correct, run the chatbot app.
    chatbot_app()
else:
    # If the password is not correct, show the password form.
    check_password()