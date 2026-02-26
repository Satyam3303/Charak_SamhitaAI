"""
RAG Query Engine for Charak Samhita AI
Uses Groq (completely free, no limits) for cloud deployment
"""

import os
import zipfile
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

COLLECTION_NAME = "charak_samhita"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# ── Step 1: Find & unzip DB ──────────────────────────────────────────
# Try multiple possible paths where charak_db might be
POSSIBLE_DB_PATHS = ["./charak_db", "./charak_db/charak_db", "../charak_db"]
DB_PATH = None

def find_or_extract_db():
    global DB_PATH

    # First check if charak_db already exists somewhere
    for path in POSSIBLE_DB_PATHS:
        if os.path.exists(path):
            # Check if it actually has ChromaDB files inside
            for root, dirs, files in os.walk(path):
                if any(f.endswith(".sqlite3") or f.endswith(".bin") for f in files):
                    DB_PATH = path
                    print(f"Found DB at: {path}")
                    return

    # Not found — try to unzip
    zip_paths = ["./charak_db.zip", "../charak_db.zip"]
    for zip_path in zip_paths:
        if os.path.exists(zip_path):
            print(f"Unzipping {zip_path}...")
            with zipfile.ZipFile(zip_path, "r") as z:
                # Show zip contents
                names = z.namelist()
                print(f"Zip contains: {names[:10]}")
                z.extractall(".")
            print("Unzipped!")
            # Try to find DB again after extraction
            for path in POSSIBLE_DB_PATHS:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        if any(f.endswith(".sqlite3") or f.endswith(".bin") for f in files):
                            DB_PATH = path
                            print(f"Found DB at: {path} after unzip")
                            return
            break

    # If still not found, use default path
    if DB_PATH is None:
        DB_PATH = "./charak_db"
        print(f"Using default DB path: {DB_PATH}")
        os.makedirs(DB_PATH, exist_ok=True)

find_or_extract_db()

# ── Step 2: Debug — show full directory structure ────────────────────
print(f"\nDirectory contents:")
for item in os.listdir("."):
    print(f"  {item}")

if os.path.exists("./charak_db"):
    print(f"\ncharak_db contents:")
    for root, dirs, files in os.walk("./charak_db"):
        level = root.replace("./charak_db", "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in files:
            print(f"{indent}  {f}")

# ── Step 3: Load models ──────────────────────────────────────────────
print("\nLoading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# ── Step 4: Connect to ChromaDB ──────────────────────────────────────
print(f"Connecting to ChromaDB at: {DB_PATH}")
_chroma_client = chromadb.PersistentClient(path=DB_PATH)

available = _chroma_client.list_collections()
print(f"Available collections: {[c.name for c in available]}")

if len(available) == 0:
    print("WARNING: No collections found — creating empty one")
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
else:
    # Use exact match or first available
    _collection = None
    for col in available:
        if col.name == COLLECTION_NAME:
            _collection = _chroma_client.get_collection(col.name)
            break
    if _collection is None:
        _collection = _chroma_client.get_collection(available[0].name)
        print(f"Using collection: {available[0].name}")

print(f"DB ready! Total items: {_collection.count()}")

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
    groq_api_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_api_key:
        return {
            "answer": "Groq API key is not set. Please add GROQ_API_KEY in Streamlit secrets. Get free key from https://console.groq.com",
            "sources": [],
            "chunks_used": 0
        }

    if _collection.count() == 0:
        return {
            "answer": "The database is empty! Please re-upload charak_db.zip to GitHub with the correct contents.",
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
        answer = f"Error from Groq: {str(e)}"

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(docs)
    }