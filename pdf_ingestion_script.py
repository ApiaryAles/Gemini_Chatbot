# pdf_ingestion_script.py - FINAL CORRECTED VERSION

import os
from dotenv import load_dotenv, find_dotenv # find_dotenv kept for optional initial debug print
from supabase import create_client, Client
from io import BytesIO
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
import asyncio
import tempfile # For creating temporary PDF files

# --- SETUP AND CONFIGURATION ---
load_dotenv() # Load environment variables from .env once at the very start

# Optional: Initial debug prints to confirm .env loading location
# print(f"DEBUG: .env file loaded from: {find_dotenv()}")
# print(f"DEBUG: Current working directory: {os.getcwd()}")

# Get credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ensure all critical credentials are present
if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    raise ValueError("Missing Supabase or Gemini API credentials in environment variables. Please check your .env file.")

# Debug print of the key actually being used (remove after successful run)
print(f"DEBUG_INGESTION_RAW: Key as seen by script: '{GEMINI_API_KEY}' (Length: {len(GEMINI_API_KEY) if GEMINI_API_KEY else 'N/A'})")

# Configure Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit() # Exit if Supabase client fails to initialize

# Configure Gemini API and Embedding Model
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Initialize Embedding Model for PDF retrieval
    # Use 'google_api_key' parameter as per LangChain documentation for direct API key passing
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GEMINI_API_KEY # Pass the API key directly here
    )
except Exception as e:
    print(f"Error configuring Gemini API or Embedding Model: {e}")
    exit() # Exit if Gemini fails to initialize


# --- Constants ---
# IMPORTANT: Ensure BUCKET_NAME matches the exact name of your bucket in Supabase Storage.
# Your previous output showed 'pdfstorage' but the script default is 'pdfs'.
# Change "pdfs" to "pdfstorage" below if that's your bucket's name.
BUCKET_NAME = "pdfstorage"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


async def ingest_pdfs():
    print(f"Starting PDF ingestion from Supabase Storage bucket: {BUCKET_NAME}")

    # 1. List files in the Supabase Storage bucket
    try:
        response = supabase.storage.from_(BUCKET_NAME).list()
        pdf_files = [f for f in response if f['name'].lower().endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files in the bucket.")
    except Exception as e:
        print(f"Error listing files from Supabase Storage: {e}")
        return

    if not pdf_files:
        print("No PDF files found in the specified bucket. Exiting.")
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )

    for pdf_file in pdf_files:
        file_name = pdf_file['name']
        print(f"\nProcessing: {file_name}")

        temp_file_path = None # Initialize to None

        try:
            # 2. Download PDF content as bytes
            res = supabase.storage.from_(BUCKET_NAME).download(file_name)
            pdf_bytes_content = BytesIO(res).getvalue() # Get the raw bytes content

            # 3. Save to a temporary file, as PyPDFLoader expects a file path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(pdf_bytes_content)
                temp_file_path = temp_file.name # Get the path to the temporary file

            # 4. Load and split PDF using the temporary file path
            loader = PyPDFLoader(temp_file_path) # Pass the file path to the loader
            pages = loader.load_and_split(text_splitter)

            print(f"Extracted {len(pages)} chunks from {file_name}.")

            # 5. Generate embeddings and store in Supabase DB
            for i, doc in enumerate(pages):
                content = doc.page_content
                metadata = doc.metadata
                metadata["source_file"] = file_name
                metadata["chunk_index"] = i # Add chunk index for easier debugging/tracking

                # Ensure page number is stored as an integer, if present
                if 'page' in metadata:
                    metadata['page'] = int(metadata['page']) # Convert to int for consistency

                # Generate embedding for the content chunk
                embedding = embeddings_model.embed_query(content)

                # Store the chunk, its embedding, and metadata in Supabase 'documents' table
                data, count = supabase.table("documents").insert({
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata
                }).execute()

                if data:
                    print(f"  - Chunk {i+1} stored successfully.")
                else:
                    print(f"  - Failed to store chunk {i+1}: {count}")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")
        finally:
            # 6. Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"  - Cleaned up temporary file: {temp_file_path}")

    print("\nPDF Ingestion process completed.")

if __name__ == "__main__":
    asyncio.run(ingest_pdfs())