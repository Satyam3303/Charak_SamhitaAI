"""
RAG Query Engine for Charak Samhita AI
Uses Groq (completely free, no limits) for cloud deployment
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

DB_PATH = "./charak_db"
COLLECTION_NAME = "charak_samhita"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# Load once globally
print("🔄 Loading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("🗄️ Connecting to ChromaDB...")
_chroma_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _chroma_client.get_collection(COLLECTION_NAME)

print("✅ RAG Engine ready! (Powered by Groq - free & fast)")

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
    3. Ask Groq LLaMA with context
    4. Return answer + sources
    """

    # Get API key fresh every call (fixes Streamlit Cloud loading issue)
    groq_api_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_api_key:
        return {
            "answer": "⚠️ Groq API key is not set. Please add GROQ_API_KEY in your Streamlit secrets. Get a free key from https://console.groq.com",
            "sources": [],
            "chunks_used": 0
        }

    # Initialize Groq client inside function (avoids startup errors)
    groq_client = Groq(api_key=groq_api_key)

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

    # Step 3: Ask Groq
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""Here are relevant passages from Charak Samhita:

{context}

---

Question: {question}

Please answer based on the above context from Charak Samhita."""}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        answer = response.choices[0].message.content

    except Exception as e:
        answer = f"⚠️ Error getting response from Groq: {str(e)}\n\nMake sure your GROQ_API_KEY is correct."

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(docs)
    }


# Quick test from command line
if __name__ == "__main__":
    print("\n🌿 Charak Samhita AI - Test Mode (Groq)")
    print("Make sure GROQ_API_KEY is set as environment variable")
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