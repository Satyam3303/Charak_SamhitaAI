"""
RAG Query Engine for Charak Samhita AI
Used by the Streamlit app and can also be tested directly.
"""

import chromadb
from sentence_transformers import SentenceTransformer
import ollama

DB_PATH = "./charak_db"
COLLECTION_NAME = "charak_samhita"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3.2"  # change to "mistral" or "llama3" if preferred
TOP_K = 5  # number of chunks to retrieve

# Load once globally (so Streamlit doesn't reload on every query)
print("🔄 Loading models...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)
_chroma_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _chroma_client.get_collection(COLLECTION_NAME)
print("✅ Models ready! (Using Ollama - free, local, no API key needed)")

SYSTEM_PROMPT = """You are an expert Ayurvedic scholar specializing in Charak Samhita — one of the foundational texts of Ayurveda.

Your role:
- Answer questions based ONLY on the context from Charak Samhita provided to you
- Be accurate, detailed, and cite which part of Charak Samhita the information comes from
- If the answer is not found in the context, clearly say: "This specific topic is not covered in the provided sections of Charak Samhita."
- Never invent or hallucinate information
- Use proper Ayurvedic terminology (Sanskrit terms with explanation)
- Always remind users that Ayurvedic treatments should be supervised by a qualified Vaidya (Ayurvedic physician)"""


def ask_charak(question: str) -> dict:
    """
    Main RAG function:
    1. Embed the question
    2. Find relevant chunks from Charak Samhita
    3. Ask Claude with context
    4. Return answer + sources
    """

    # Step 1: Embed question
    q_embedding = _embedding_model.encode(question).tolist()

    # Step 2: Retrieve relevant chunks
    results = _collection.query(
        query_embeddings=[q_embedding],
        n_results=TOP_K
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = "\n\n---\n\n".join(
        [f"[From: {m['title']}]\n{doc}" for doc, m in zip(docs, metadatas)]
    )

    sources = list({m["title"] for m in metadatas})

    # Step 3: Ask Claude
    user_prompt = f"""Here are relevant passages from Charak Samhita:

{context}

---

Question: {question}

Please answer based on the above context from Charak Samhita."""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    return {
        "answer": response["message"]["content"],
        "sources": sources,
        "chunks_used": len(docs)
    }


# Quick test from command line
if __name__ == "__main__":
    print("\n🌿 Charak Samhita AI - Test Mode")
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
        print("\n" + "="*60 + "\n")
