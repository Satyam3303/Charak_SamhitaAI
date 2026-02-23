"""
STEP 4: Streamlit Web App for Charak Samhita AI
Run: streamlit run app.py
"""

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
    .answer-box {
        background: #fafafa;
        border-left: 4px solid #4caf50;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
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
        "What does Charak Samhita say about Vata dosha?",
        "What are the properties of Ashwagandha according to Charak?",
        "How does Charak Samhita describe the daily routine (Dinacharya)?",
        "What are the causes of disease according to Charak Samhita?",
        "Explain Panchakarma as described in Charak Samhita"
    ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, key=f"ex_{i}", use_container_width=True):
            st.session_state.prefill = example
            st.rerun()

# Handle prefilled question from example buttons
prefill = st.session_state.pop("prefill", "")

# --- Chat Input ---
question = st.chat_input("Ask a question about Charak Samhita...") or prefill

if question:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get AI answer
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

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}\n\nMake sure Ollama is running! Run: ollama serve"
                st.error(error_msg)

# --- Disclaimer ---
st.markdown("""
<div class="disclaimer">
    ⚕️ <strong>Disclaimer:</strong> This AI is for educational purposes only. 
    Information is sourced from Charak Samhita. Always consult a qualified 
    Ayurvedic physician (Vaidya) before following any treatments or remedies.
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.success("✅ Running FREE with Ollama\n\n(Local AI — no API key needed!)")

    st.markdown("---")
    st.markdown("## 📖 About")
    st.markdown("""
    This AI is trained on **Charak Samhita** — the foundational 
    Ayurvedic text written by Acharya Charak.
    
    Data source: [carakasamhitaonline.com](https://www.carakasamhitaonline.com)
    
    **Technology:**
    - 🔍 RAG (Retrieval-Augmented Generation)
    - 🗄️ ChromaDB vector database
    - 🤖 Ollama (free, local LLM)
    - 🧠 LLaMA 3.2 model
    """)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
