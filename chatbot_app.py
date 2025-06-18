import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests # For making API calls (Google Search)
from langchain_google_genai import GoogleGenerativeAIEmbeddings # For embeddings


# --- SETUP AND CONSTANTS ---
load_dotenv() # Load .env for local testing (Streamlit Cloud uses st.secrets)

# --- CONFIGURE THE GEMINI API & SUPABASE ---
try:
    # Configure services
    genai.configure(api_key=st.secrets["app_secrets"]["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Initialize Embedding Model for PDF retrieval
    # It's crucial this matches the model used during ingestion (text-embedding-004)
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=st.secrets["app_secrets"]["GEMINI_API_KEY"] # Pass the API key explicitly
    )

    # Supabase connection
    url: str = st.secrets["connections"]["supabase"]["url"]
    # IMPORTANT: Ensure this matches your secrets.toml structure: [connections.supabase]
    key: str = st.secrets["connections"]["supabase"]["key"] 
    supabase: Client = create_client(url, key)

    # Google Search credentials (re-using Gemini key for simplicity as per your setup)
    SEARCH_API_KEY = st.secrets["app_secrets"]["GEMINI_API_KEY"] 
    SEARCH_ENGINE_ID = st.secrets["app_secrets"]["SEARCH_ENGINE_ID"]

except Exception as e:
    st.error(f"Error initializing services: {e}")
    st.stop()


# --- GOOGLE SEARCH FUNCTION ---
def perform_Google_Search(query: str):
    """Performs a Google search and returns formatted results."""
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={SEARCH_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        search_results = response.json()
        
        snippets = [item.get('snippet', '') for item in search_results.get('items', [])]
        if not snippets:
            return "No relevant information found from Google Search."
            
        return "\n".join(snippets)
    except Exception as e:
        st.warning(f"Could not perform Google Search: {e}")
        return "Google Search failed."

# --- PDF RETRIEVAL FUNCTION ---
def retrieve_pdf_chunks(query: str, top_k: int = 3, match_threshold: float = 0.7):
    """
    Performs a similarity search in the Supabase 'documents' table
    and retrieves relevant PDF content chunks using the 'match_documents' RPC.
    """
    try:
        # 1. Generate embedding for the user's query
        query_embedding = embeddings_model.embed_query(query)

        # 2. Call the Supabase RPC function for similarity search
        results = supabase.rpc('match_documents', {
            'query_embedding': query_embedding,
            'match_threshold': match_threshold, # Adjust similarity threshold as needed
            'match_count': top_k, # Number of chunks to retrieve
        }).execute()
        
        retrieved_chunks = []
        if results and results.data:
            for item in results.data:
                source_info = f"Source: {item['metadata'].get('source_file', 'Unknown File')}"
                if 'page' in item['metadata'] and item['metadata']['page'] is not None:
                    # Pages are often 0-indexed from PDF loaders, so add 1 for human readability
                    source_info += f", Page: {int(item['metadata']['page']) + 1}" 
                
                # Format the retrieved chunk for context
                retrieved_chunks.append(f"Content: {item['content']}\n({source_info}, Similarity: {item['similarity']:.2f})")
            
            return "\n\n".join(retrieved_chunks)
        else:
            return "No relevant internal documentation found."
            
    except Exception as e:
        st.warning(f"Could not retrieve PDF chunks: {e}")
        return "Internal documentation retrieval failed."


# --- DATABASE FUNCTIONS ---
def load_history():
    """Loads chat history from the Supabase database."""
    query = supabase.table("chat_history").select("*").order("created_at").execute()
    return query.data

def save_history(role, content):
    """Saves a new chat message to the Supabase database."""
    supabase.table("chat_history").insert([{"role": role, "content": content}]).execute()


# --- PASSWORD FUNCTION ---
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


# --- CHATBOT APP ---
def chatbot_app():
    """The main chatbot application."""
    st.title("My AI Chatbot Assistant")
    st.caption("Powered by Google Gemini, Supabase, live search, and internal documents")

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
            # Perform PDF Retrieval
            with st.spinner("Retrieving from internal documents..."):
                pdf_context = retrieve_pdf_chunks(query=prompt, top_k=5, match_threshold=0.75) 

            # Perform Google Search
            with st.spinner("Performing live Google search..."):
                search_context = perform_Google Search(query=prompt) 
            
            # Combine all contexts into a single prompt for Gemini
            contextual_prompt = f"""
            You are a helpful AI assistant. Answer the user's question by combining information from the provided internal documentation and real-time Google search results. Prioritize internal documentation if directly relevant and comprehensive. If information is contradictory, mention the discrepancy. If neither source provides sufficient information, state that.

            Internal Documentation Context:
            ---
            {pdf_context}
            ---
            
            Google Search Results:
            ---
            {search_context}
            ---
            
            User's Question: "{prompt}"
            """
            
            response = st.session_state.chat.send_message(contextual_prompt)
            save_history("model", response.text)
            with st.chat_message("assistant"):
                st.markdown(response.text)


# --- MAIN CONTROLLER ---
if st.session_state.get("password_correct", False):
    chatbot_app()
else:
    check_password()