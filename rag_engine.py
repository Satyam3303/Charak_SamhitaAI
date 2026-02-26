"""
RAG Query Engine for Charak Samhita AI
Uses Groq (completely free, no limits) for cloud deployment
"""

import os
import zipfile
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

DB_PATH = "./charak_db"
COLLECTION_NAME = "charak_samhita"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# ── Unzip DB if needed ──────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    if os.path.exists("charak_db.zip"):
        print("Unzipping charak_db.zip...")
        with zipfile.ZipFile("charak_db.zip", "r") as z:
            z.extractall(".")
        print("Unzipped successfully!")
    else:
        print("ERROR: charak_db.zip not found!")

# ── Debug: show what's inside charak_db ─────────────────────────────
print(f"DB_PATH exists: {os.path.exists(DB_PATH)}")
if os.path.exists(DB_PATH):
    for root, dirs, files in os.walk(DB_PATH):
        level = root.replace(DB_PATH, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in files:
            print(f"{indent}  {f}")

# ── Load embedding model ─────────────────────────────────────────────
print("Loading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# ── Connect to ChromaDB ──────────────────────────────────────────────
print("Connecting to ChromaDB...")
_chroma_client = chromadb.PersistentClient(path=DB_PATH)

# List all collections and pick the right one
available = _chroma_client.list_collections()
print(f"Available collections: {[c.name for c in available]}")

if len(available) == 0:
    raise ValueError("No collections found in charak_db! Please re-upload charak_db.zip")

# Use exact match first, otherwise use first available collection
_collection = None
for col in available:
    if col.name == COLLECTION_NAME:
        _collection = _chroma_client.get_collection(COLLECTION_NAME)
        print(f"Found collection: {COLLECTION_NAME}")
        break

if _collection is None:
    # Use whatever collection exists
    _collection = _chroma_client.get_collection(available[0].name)
    print(f"Using collection: {available[0].name}")

print(f"DB loaded! Total items: {_collection.count()}")

# ── System Prompt ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Ayurvedic scholar specializing in Charak Samhita — one of the foundational texts of Ayurveda.

Your role:
- Answer questions based ONLY on the context from Charak Samhita provided to you
- Be accurate, detailed, and mention which part of Charak Samhita the information comes from
- If the answer is not found in the context, clearly say: "This specific topic is not covered in the provided sections of Charak Samhita."
- Never invent or hallucinate information
- Use proper Ayurvedic terminology (Sanskrit terms with explanation)
- Always remind users that Ayurvedic treatments should be supervised by a qualified Vaidya (Ayurvedic physician)"""


def ask_charak(question: str) -> dict:
    # Get API key fresh every call
    groq_api_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_api_key:
        return {
            "answer": "Groq API key is not set. Please add GROQ_API_KEY in your Streamlit secrets. Get a free key from https://console.groq.com",
            "sources": [],
            "chunks_used": 0
        }

    groq_client = Groq(api_key=groq_api_key)

    # Embed question
    q_embedding = _embedding_model.encode(question).tolist()

    # Search ChromaDB
    results = _collection.query(
        query_embeddings=[q_embedding],
        n_results=TOP_K
    )

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = "\n\n---\n\n".join(
        [f"[From: {m.get('title', 'Charak Samhita')}]\n{doc}"
         for doc, m in zip(docs, metadatas)]
    )

    sources = list({m.get("title", "Charak Samhita") for m in metadatas})

    # Ask Groq
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
        answer = f"Error getting response from Groq: {str(e)}"

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(docs)
    }