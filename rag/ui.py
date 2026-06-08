import logging
import os

import streamlit as st

from rag.config import TEMPERATURE, TOP_K
from rag.llm import generate_answer
from rag.retriever import Retriever
from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)

st.set_page_config(page_title="MoSPI RAG Chatbot", layout="wide")

st.title("MoSPI RAG Chatbot")

with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Top-K", min_value=1, max_value=10, value=int(os.getenv("TOP_K", str(TOP_K))))
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(os.getenv("TEMPERATURE", str(TEMPERATURE))), step=0.05)

question = st.text_input("Question", placeholder="Ask a question from the MoSPI corpus")

if st.button("Ask") and question:
    try:
        vector_store = VectorStore()
        retriever = Retriever(vector_store)
        chunks = retriever.retrieve(question, top_k=top_k)

        if not chunks:
            st.info("I don't have that in my data.")
            st.subheader("Sources")
            st.write("No sources were found in the loaded corpus.")
            st.stop()

        context = "\n\n".join(chunk["text"] for chunk in chunks if chunk.get("text"))
        answer = generate_answer(question, context, temperature=temperature)

        st.subheader("Answer")
        st.markdown(answer)

        st.subheader("Citations")
        for item in chunks:
            st.markdown(f"- **{item.get('title', 'Untitled')}** — {item.get('url', '')}")

        with st.expander("Retrieved Chunks", expanded=True):
            for item in chunks:
                st.write(f"**{item.get('title', 'Untitled')}**")
                st.caption(item.get('url', ''))
                st.write(item.get('text', ''))
    except Exception as exc:
        logger.exception("Streamlit query failed")
        st.error(str(exc))
