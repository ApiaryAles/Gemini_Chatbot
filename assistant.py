# First, we import the necessary libraries.
# 'os' is for interacting with the operating system, like getting environment variables.
# 'openai' is the library that lets us talk to the AI model.
# 'dotenv' is what we use to load our secret API key from the .env file.
import os
import openai
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Get the API key you stored in the .env file
# and set it for the openai library to use.
openai.api_key = os.getenv("OPENAI_API_KEY")


# --- The Main Function ---
# This function takes a text prompt from the user, sends it to the AI,
# and returns the AI's response.
def get_assistant_response(user_prompt):
    """Sends a prompt to the OpenAI API and gets a response."""
    try:
        # This is the main API call.
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # You can use other models like "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_prompt}
            ]
        )
        # We extract the text content from the AI's response.
        return response.choices[0].message.content

    except Exception as e:
        # If anything goes wrong (e.g., API key is wrong, network issue),
        # we print the error message.
        return f"An error occurred: {e}"


# --- The Main Loop of the Program ---
# This part of the script will run continuously until you type 'quit'.
if __name__ == "__main__":
    print("AI Assistant is ready! Type 'quit' to exit.")

    while True:
        # Get input from the user via the command line.
        user_input = input("You: ")

        # Check if the user wants to exit the program.
        if user_input.lower() == 'quit':
            print("Assistant shutting down. Goodbye!")
            break

        # If the user typed something, get the AI's response.
        if user_input:
            ai_response = get_assistant_response(user_input)
            print(f"Assistant: {ai_response}")