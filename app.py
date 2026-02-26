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
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Jost:wght@300;400;500&display=swap');

:root {
    --saffron:     #C8690A;
    --saffron-lt:  #F0A830;
    --deep:        #1A1008;
    --bark:        #2E1B0E;
    --parchment:   #FAF3E8;
    --parchment2:  #F2E8D5;
    --ink:         #3D2B1F;
    --muted:       #8C7B6B;
    --leaf:        #3B6B3B;
    --leaf-lt:     #5A9E5A;
    --gold:        #B8963E;
}

html, body, [data-testid="stApp"] {
    background: var(--parchment);
    color: var(--ink);
    font-family: 'Jost', sans-serif;
}

/* Hide streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── HERO BANNER ── */
.hero {
    background: linear-gradient(135deg, var(--bark) 0%, #3D2208 50%, #1A0E05 100%);
    border-radius: 20px;
    padding: 48px 48px 40px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(26,16,8,0.25);
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse at 80% 20%, rgba(200,105,10,0.18) 0%, transparent 60%),
        radial-gradient(ellipse at 20% 80%, rgba(90,158,90,0.10) 0%, transparent 50%);
    pointer-events: none;
}
.hero-om {
    font-size: 56px;
    line-height: 1;
    margin-bottom: 12px;
    filter: drop-shadow(0 2px 8px rgba(200,105,10,0.5));
}
.hero h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3.2rem;
    font-weight: 300;
    color: var(--parchment);
    letter-spacing: 0.04em;
    margin: 0 0 8px 0;
    line-height: 1.1;
}
.hero h1 span { color: var(--saffron-lt); font-style: italic; }
.hero p {
    color: rgba(250,243,232,0.65);
    font-size: 1.05rem;
    font-weight: 300;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(200,105,10,0.2);
    border: 1px solid rgba(200,105,10,0.4);
    color: var(--saffron-lt);
    font-size: 0.72rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 16px;
}

/* ── EXAMPLE PILLS ── */
.examples-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 12px;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    margin-bottom: 16px !important;
    border: none !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: var(--parchment2) !important;
}

/* User bubble */
.user-bubble {
    background: var(--parchment2);
    border: 1px solid rgba(184,150,62,0.25);
    border-radius: 18px 18px 4px 18px;
    padding: 16px 20px;
    margin: 8px 0;
    font-size: 1rem;
    color: var(--ink);
    line-height: 1.6;
}

/* Answer card */
.answer-card {
    background: white;
    border: 1px solid rgba(184,150,62,0.2);
    border-left: 4px solid var(--saffron);
    border-radius: 4px 16px 16px 4px;
    padding: 24px 28px;
    margin: 8px 0;
    line-height: 1.8;
    font-size: 1rem;
    color: var(--ink);
    box-shadow: 0 4px 20px rgba(26,16,8,0.06);
}

/* Source tags */
.sources-row { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.sources-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-right: 4px;
}
.source-chip {
    display: inline-block;
    background: rgba(59,107,59,0.08);
    border: 1px solid rgba(59,107,59,0.25);
    color: var(--leaf);
    font-size: 0.78rem;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'Jost', sans-serif;
    letter-spacing: 0.03em;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    border-radius: 40px !important;
    border: 1.5px solid rgba(184,150,62,0.35) !important;
    background: white !important;
    box-shadow: 0 4px 24px rgba(26,16,8,0.08) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--saffron) !important;
    box-shadow: 0 4px 24px rgba(200,105,10,0.15) !important;
}

/* ── BUTTONS ── */
.stButton button {
    background: white !important;
    border: 1px solid rgba(184,150,62,0.3) !important;
    color: var(--ink) !important;
    border-radius: 40px !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
}
.stButton button:hover {
    background: var(--bark) !important;
    color: var(--parchment) !important;
    border-color: var(--bark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(26,16,8,0.15) !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bark) !important;
    border-right: 1px solid rgba(200,105,10,0.2) !important;
}
[data-testid="stSidebar"] * { color: var(--parchment) !important; }
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    font-size: 1.3rem !important;
    letter-spacing: 0.08em !important;
    color: var(--saffron-lt) !important;
    border-bottom: 1px solid rgba(200,105,10,0.2) !important;
    padding-bottom: 8px !important;
}
.sidebar-stat {
    background: rgba(200,105,10,0.12);
    border: 1px solid rgba(200,105,10,0.2);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.85rem;
}
.sidebar-stat strong { color: var(--saffron-lt) !important; }

/* ── SPINNER ── */
[data-testid="stSpinner"] { color: var(--saffron) !important; }

/* ── DISCLAIMER ── */
.disclaimer {
    background: rgba(184,150,62,0.08);
    border: 1px solid rgba(184,150,62,0.2);
    border-radius: 12px;
    padding: 14px 20px;
    font-size: 0.82rem;
    color: var(--muted);
    margin-top: 24px;
    line-height: 1.6;
}

/* ── DIVIDER ── */
.om-divider {
    text-align: center;
    color: var(--gold);
    font-size: 1.2rem;
    letter-spacing: 0.5em;
    margin: 8px 0 24px;
    opacity: 0.4;
}

/* scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--parchment2); }
::-webkit-scrollbar-thumb { background: rgba(184,150,62,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-om">🕉️</div>
    <div class="hero-badge">Ancient Wisdom · AI Powered</div>
    <h1>Charak <span>Samhita</span></h1>
    <p>Ask questions from the world's oldest Ayurvedic treatise</p>
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── EXAMPLE QUESTIONS ─────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown('<div class="examples-title">✦ Try asking</div>', unsafe_allow_html=True)
    examples = [
        "What is the literal meaning of Deerghanjiviteeya Adhyaya?",
        "Who was Bharadwaja and why did he approach Indra?",
        "What is the divine lineage of Ayurveda?",
        "What does Charak say about Vata dosha?",
        "Explain Panchakarma from Charak Samhita",
        "What are the causes of disease according to Charak?",
    ]
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        if cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.prefill = ex
            st.rerun()
    st.markdown('<div class="om-divider">· · ॐ · ·</div>', unsafe_allow_html=True)

# ── CHAT HISTORY ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble">🙏 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        answer_html = msg["content"].replace("\n", "<br>")
        sources_html = ""
        if "sources" in msg and msg["sources"]:
            chips = "".join([f'<span class="source-chip">{s}</span>' for s in msg["sources"]])
            sources_html = f'<div class="sources-row"><span class="sources-label">📚 Sources</span>{chips}</div>'
        st.markdown(f'<div class="answer-card">{answer_html}{sources_html}</div>', unsafe_allow_html=True)

# ── PREFILL HANDLER ───────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", "")

# ── CHAT INPUT ────────────────────────────────────────────────────────
question = st.chat_input("Ask anything from Charak Samhita...") or prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    st.markdown(f'<div class="user-bubble">🙏 {question}</div>', unsafe_allow_html=True)

    with st.spinner("🌿 Searching ancient wisdom..."):
        try:
            result = ask_charak(question)
            answer = result["answer"]
            sources = result["sources"]

            answer_html = answer.replace("\n", "<br>")
            chips = "".join([f'<span class="source-chip">{s}</span>' for s in sources])
            sources_html = f'<div class="sources-row"><span class="sources-label">📚 Sources</span>{chips}</div>' if sources else ""
            st.markdown(f'<div class="answer-card">{answer_html}{sources_html}</div>', unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })

        except Exception as e:
            st.error(f"⚠️ {str(e)}")

# ── DISCLAIMER ────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("""
    <div class="disclaimer">
        ⚕️ <strong>Disclaimer:</strong> This AI is for educational purposes only.
        Always consult a qualified Ayurvedic physician (Vaidya) before following any treatments or remedies.
    </div>
    """, unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 About")
    st.markdown("""
    <div class="sidebar-stat">
        <strong>Source</strong><br>
        carakasamhitaonline.com
    </div>
    <div class="sidebar-stat">
        <strong>AI Model</strong><br>
        Groq · LLaMA 3.3 70B
    </div>
    <div class="sidebar-stat">
        <strong>Method</strong><br>
        RAG · ChromaDB
    </div>
    <div class="sidebar-stat">
        <strong>Cost</strong><br>
        100% Free ✓
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## ⚙️ Controls")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; opacity:0.5; line-height:1.8;'>
    Charak Samhita · Sutra Sthana<br>
    Ancient Ayurvedic Wisdom<br>
    Built with ❤️ for Ayurveda
    </div>
    """, unsafe_allow_html=True)