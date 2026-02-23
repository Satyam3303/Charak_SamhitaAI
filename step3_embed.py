"""
STEP 3: Generate embeddings and store in ChromaDB vector database
Run: python step3_embed.py
"""

import json
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

INPUT_FILE = "charak_chunks.json"
DB_PATH = "./charak_db"
COLLECTION_NAME = "charak_samhita"
BATCH_SIZE = 100

# Best free embedding model for multilingual/Sanskrit-adjacent text
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build_vector_db():
    print(f"📂 Loading chunks from {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks")

    print(f"\n🤖 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("  Model loaded!")

    print(f"\n🗄️ Setting up ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Deleted existing collection (rebuilding fresh)")
    except:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"\n⚡ Embedding and storing {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(total_batches):
        start = batch_num * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(chunks))
        batch = chunks[start:end]

        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = [{"title": c["title"], "chunk_index": c["chunk_index"]} for c in batch]

        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

        print(f"  Batch {batch_num + 1}/{total_batches} done ({end}/{len(chunks)} chunks)")

    print(f"\n✅ Vector DB built! {collection.count()} chunks stored at {DB_PATH}")


if __name__ == "__main__":
    build_vector_db()
