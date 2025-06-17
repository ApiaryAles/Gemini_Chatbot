import streamlit as st

st.set_page_config(layout="wide")
st.title("Secrets Debugger")
st.write("This app checks which secrets are accessible to the Streamlit app.")

st.header("All Secret Keys Found:")
st.info(f"The `st.secrets` object has the following keys: **{st.secrets.keys()}**")

st.header("Checking for specific keys...")

# Check for GEMINI_API_KEY
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        st.success("SUCCESS: Found the `GEMINI_API_KEY`.")
        st.write(f"The key starts with: `{gemini_key[:5]}...` and ends with: `{gemini_key[-4:]}`")
    else:
        st.error("FAILURE: `GEMINI_API_KEY` was found but it is empty.")
except Exception as e:
    st.error(f"FAILURE: Could not access `GEMINI_API_KEY`. Error: {e}")


# Check for Supabase Connection
try:
    supabase_url = st.secrets.get("connections", {}).get("supabase", {}).get("url")
    if supabase_url:
        st.success("SUCCESS: Found the Supabase URL in `[connections.supabase]`.")
    else:
        st.error("FAILURE: Could not find the Supabase URL.")
except Exception as e:
    st.error(f"FAILURE: Could not access Supabase secrets. Error: {e}")

# Check for Chatbot Password
try:
    password = st.secrets.get("CHATBOT_PASSWORD")
    if password:
        st.success("SUCCESS: Found the `CHATBOT_PASSWORD`.")
    else:
        st.error("FAILURE: `CHATBOT_PASSWORD` was found but it is empty.")
except Exception as e:
    st.error(f"FAILURE: Could not access `CHATBOT_PASSWORD`. Error: {e}")