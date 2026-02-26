import os
import zipfile

# Unzip charak_db BEFORE importing rag_engine
if not os.path.exists("./charak_db"):
    if os.path.exists("charak_db.zip"):
        print("Unzipping charak_db.zip...")
        with zipfile.ZipFile("charak_db.zip", "r") as z:
            z.extractall(".")
        print("Done unzipping!")
    else:
        print("WARNING: charak_db.zip not found!")

import streamlit as st
from rag_engine import ask_charak

# --- Page Config ---
st.set_page_config(
    page_title="Charak Samhita AI",
    page_icon="🌿",
    layout="centered"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1a4a1a, #2d7a2d);
        color: white;
        border-radius: 12px;
        margin-bottom: 30px;
    }
    .source-tag {
        display: inline-block;
        background: #e8f5e9;
        color: #2e7d32;
        border: 1px solid #a5d6a7;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.85em;
    }
    .disclaimer {
        background: #fff8e1;
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.85em;
        color: #5d4037;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>🌿 Charak Samhita AI</h1>
    <p>Ask questions from the ancient Ayurvedic text — Charak Samhita</p>
</div>
""", unsafe_allow_html=True)

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            st.markdown("**📚 Sources:**")
            source_html = "".join([f'<span class="source-tag">{s}</span>' for s in msg["sources"]])
            st.markdown(source_html, unsafe_allow_html=True)

# --- Example Questions ---
if not st.session_state.messages:
    st.markdown("### 💡 Try asking:")
    examples = [
        "What is the literal meaning of Deerghanjiviteeya Adhyaya?",
        "Who was Bharadwaja and why did he approach Indra?",
        "What is the divine lineage of Ayurveda?",
        "What are the causes of disease according to Charak Samhita?",
        "Explain Panchakarma as described in Charak Samhita"
    ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, key=f"ex_{i}", use_container_width=True):
            st.session_state.prefill = example
            st.rerun()

# Handle prefilled question
prefill = st.session_state.pop("prefill", "")

# --- Chat Input ---
question = st.chat_input("Ask a question about Charak Samhita...") or prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching Charak Samhita..."):
            try:
                result = ask_charak(question)
                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)
                st.markdown("**📚 Sources from Charak Samhita:**")
                source_html = "".join([f'<span class="source-tag">{s}</span>' for s in sources])
                st.markdown(source_html, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- Disclaimer ---
st.markdown("""
<div class="disclaimer">
    ⚕️ <strong>Disclaimer:</strong> This AI is for educational purposes only.
    Always consult a qualified Ayurvedic physician (Vaidya) before following any treatments.
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.success("✅ Powered by Groq (Free & Fast AI)")
    st.markdown("---")
    st.markdown("## 📖 About")
    st.markdown("""
    This AI is trained on **Charak Samhita** — the foundational
    Ayurvedic text written by Acharya Charak.

    Data source: [carakasamhitaonline.com](https://www.carakasamhitaonline.com)

    **Technology:**
    - 🔍 RAG (Retrieval-Augmented Generation)
    - 🗄️ ChromaDB vector database
    - 🤖 Groq LLaMA 3.3 70B (free)
    """)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()