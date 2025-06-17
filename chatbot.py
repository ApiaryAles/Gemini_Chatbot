# chatbot.py

import streamlit as st
import openai
import os
from dotenv import load_dotenv

# --- PASSWORD FUNCTION (CORRECTED) ---

def check_password():
    """Returns `True` if the user had the correct password."""
    
    with st.form("password_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Enter")

        if submitted:
            # The lines below this `if` MUST be indented
            if password == "your_secret_password": # Make sure to use your actual password here
                st.session_state["password_correct"] = True
                st.rerun() # This reloads the page after a correct password
            else:
                st.error("The password you entered is incorrect.")
                st.session_state["password_correct"] = False
    
    return st.session_state.get("password_correct", False)
# --- SETUP ---
# Load environment variables from your .env file
load_dotenv()

# Set up your OpenAI API client
# This will use the OPENAI_API_KEY from your .env file
try:
    # NEW WAY FOR DEPLOYMENT
	openai.api_key = st.secrets["OPENAI_API_KEY"]
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
def chatbot_app():
	st.title("Nathan's Assistant")
	
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

if check_password():
    chatbot_app()