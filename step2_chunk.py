"""
STEP 2: Clean and chunk scraped data
Run: python step2_chunk.py
"""

import json
import re

INPUT_FILE = "charak_samhita_raw.json"
OUTPUT_FILE = "charak_chunks.json"

CHUNK_SIZE = 400   # words per chunk
OVERLAP = 50       # overlapping words for better context


def clean_text(text):
    """Clean raw wiki text"""
    text = re.sub(r'==+.*?==+', '', text)        # remove section headers
    text = re.sub(r'\[.*?\]', '', text)            # remove [edit] tags
    text = re.sub(r'\{\{.*?\}\}', '', text)        # remove wiki templates
    text = re.sub(r'http\S+', '', text)            # remove URLs
    text = re.sub(r'\n{3,}', '\n\n', text)         # max 2 newlines
    text = re.sub(r'[ \t]+', ' ', text)            # collapse spaces
    return text.strip()


def chunk_text(text, title, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk.split()) > 50:  # skip tiny chunks
            chunks.append({
                "id": f"{title}_chunk_{len(chunks)}",
                "title": title,
                "chunk_index": len(chunks),
                "text": chunk
            })

    return chunks


def process_all():
    print(f"📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"Found {len(raw_data)} pages. Processing...")

    all_chunks = []
    skipped = 0

    for page in raw_data:
        title = page["title"]
        content = page.get("content", "")

        if not content or len(content) < 200:
            skipped += 1
            continue

        cleaned = clean_text(content)
        chunks = chunk_text(cleaned, title)
        all_chunks.extend(chunks)

    print(f"\n📊 Summary:")
    print(f"  Pages processed : {len(raw_data) - skipped}")
    print(f"  Pages skipped   : {skipped} (too short)")
    print(f"  Total chunks    : {len(all_chunks)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Chunks saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    process_all()
