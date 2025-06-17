# chatbot.py

import streamlit as st
import openai
import os
from dotenv import load_dotenv

# --- SETUP ---
# Load environment variables from your .env file
load_dotenv()

# Set up your OpenAI API client
# This will use the OPENAI_API_KEY from your .env file
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if openai.api_key is None:
        st.error("OpenAI API key not found. Please make sure it's in your .env file.")
        st.stop()
except Exception as e:
    st.error(f"Error setting up OpenAI client: {e}")
    st.stop()


# --- YOUR AI LOGIC ---
# This is where you'll integrate the core logic from your assistant.py.
# We'll create a function that takes the user's prompt and returns the AI's response.

def get_ai_response(prompt):
    """
    Sends a prompt to the OpenAI API and returns the response.
    
    Replace this with the logic from your assistant.py.
    You might be using a specific model or have other parameters set up.
    """
    try:
        # Example using the ChatCompletion endpoint (most common)
        # You may need to adjust this based on your original script's logic
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Or whatever model you were using
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: Could not get a response from the AI. {e}"


# --- STREAMLIT APP ---

# Set the title of the web app
st.title("My AI Chatbot Assistant")

# Initialize the chat history in Streamlit's session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages from the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input from the chat input box at the bottom
if prompt := st.chat_input("What would you like to ask?"):
    
    # 1. Add user's message to the chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get the AI's response
    # Show a thinking spinner while waiting for the response
    with st.spinner("Thinking..."):
        ai_response = get_ai_response(prompt)

    # 3. Add AI's response to the chat history and display it
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    with st.chat_message("assistant"):
        st.markdown(ai_response)