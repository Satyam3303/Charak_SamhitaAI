"""
RAG Query Engine for Charak Samhita AI
Uses Google Gemini (free) for cloud deployment on Streamlit Cloud
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

DB_PATH = "./charak_db"
COLLECTION_NAME = "charak_samhita"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5  # number of chunks to retrieve

# Configure Gemini API
# On Streamlit Cloud: set GEMINI_API_KEY in app secrets
# On local: set GEMINI_API_KEY as environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Load once globally (so Streamlit doesn't reload on every query)
print("🔄 Loading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("🗄️ Connecting to ChromaDB...")
_chroma_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _chroma_client.get_collection(COLLECTION_NAME)

print("✅ RAG Engine ready!")

SYSTEM_PROMPT = """You are an expert Ayurvedic scholar specializing in Charak Samhita — one of the foundational texts of Ayurveda.

Your role:
- Answer questions based ONLY on the context from Charak Samhita provided to you
- Be accurate, detailed, and mention which part of Charak Samhita the information comes from
- If the answer is not found in the context, clearly say: "This specific topic is not covered in the provided sections of Charak Samhita."
- Never invent or hallucinate information
- Use proper Ayurvedic terminology (Sanskrit terms with explanation)
- Always remind users that Ayurvedic treatments should be supervised by a qualified Vaidya (Ayurvedic physician)"""


def ask_charak(question: str) -> dict:
    """
    Main RAG function:
    1. Embed the question
    2. Find relevant chunks from Charak Samhita
    3. Ask Gemini with context
    4. Return answer + sources
    """

    if not GEMINI_API_KEY:
        return {
            "answer": "⚠️ Gemini API key is not set. Please add GEMINI_API_KEY in your Streamlit secrets or environment variables. Get a free key from https://aistudio.google.com",
            "sources": [],
            "chunks_used": 0
        }

    # Step 1: Embed the question
    q_embedding = _embedding_model.encode(question).tolist()

    # Step 2: Retrieve relevant chunks from ChromaDB
    results = _collection.query(
        query_embeddings=[q_embedding],
        n_results=TOP_K
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(
        [f"[From: {m['title']}]\n{doc}" for doc, m in zip(docs, metadatas)]
    )

    sources = list({m["title"] for m in metadatas})

    # Step 3: Build prompt
    full_prompt = f"""{SYSTEM_PROMPT}

Here are relevant passages from Charak Samhita:

{context}

---

Question: {question}

Please answer based on the above context from Charak Samhita."""

    # Step 4: Ask Gemini
    try:
        response = gemini_model.generate_content(full_prompt)
        answer = response.text
    except Exception as e:
        answer = f"⚠️ Error getting response from Gemini: {str(e)}\n\nMake sure your GEMINI_API_KEY is correct."

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(docs)
    }


# Quick test from command line
if __name__ == "__main__":
    print("\n🌿 Charak Samhita AI - Test Mode")
    print("Make sure GEMINI_API_KEY is set as environment variable")
    print("Type 'exit' to quit\n")

    while True:
        question = input("Your question: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        result = ask_charak(question)
        print(f"\n📖 Answer:\n{result['answer']}")
        print(f"\n📚 Sources: {', '.join(result['sources'])}")
        print(f"\n🔍 Chunks used: {result['chunks_used']}")
        print("\n" + "="*60 + "\n")