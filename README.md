# MoSPI RAG Project

This project is a complete end-to-end retrieval-augmented generation (RAG) solution built around MoSPI (Ministry of Statistics and Programme Implementation) public documents. The goal is to take raw source material, clean and structure it, generate searchable chunks, build a vector index, and then allow users to ask questions through both an API and a web interface.

## What this project does

The project combines four main pieces:

1. A document collection and parsing pipeline for MoSPI publications.
2. A data validation and chunking pipeline for preparing clean text for search.
3. A FAISS-based vector store with sentence-transformers embeddings.
4. An LLM-powered question answering interface using Ollama, FastAPI, and Streamlit.

In simple terms, the system takes public documents, turns them into searchable knowledge, and lets a user ask natural-language questions about the corpus.

---

## Overall architecture

The project is organized into three connected layers:

### 1. Scraper layer
The scraper package is responsible for discovering and collecting MoSPI publication content.

- `scraper/crawl.py` collects listing pages and publication links.
- `scraper/parse.py` processes discovered material and extracts metadata.
- `scraper/report.py` generates reporting output for the crawl results.

This layer acts as the input stage of the project. It gathers the raw documents and their references before the RAG pipeline can use them.

### 2. Pipeline layer
The `pipeline/` package prepares the raw corpus into a clean, structured, and usable dataset.

- `pipeline/validation.py` loads JSON, text, and table records, normalizes fields, removes duplicates, and builds a quality summary.
- `pipeline/chunking.py` splits long text into manageable chunks for retrieval.
- `pipeline/database.py` stores the processed records and chunk-level metadata into SQLite.
- `pipeline/catalog.py` writes catalog files, reports, and exports for downstream use.

This is the core data preparation step. It ensures the content is not only readable but also consistent and ready for semantic search.

### 3. RAG layer
The `rag/` package is the intelligence layer that turns the processed corpus into an interactive assistant.

- `rag/embeddings.py` uses Sentence Transformers to generate embeddings.
- `rag/vectorstore.py` stores those embeddings in a FAISS index and saves metadata for retrieval.
- `rag/ingest.py` rebuilds the vector index from processed records.
- `rag/retriever.py` retrieves the most relevant chunks for a given question.
- `rag/llm.py` talks to Ollama for answer generation.
- `rag/api.py` exposes the system through a FastAPI API.
- `rag/ui.py` provides a Streamlit chat interface.

Together, these components allow the application to answer questions by grounding the response in the retrieved document chunks rather than relying only on the model’s general knowledge.

---

## What has been implemented in this repository

### Data ingestion and preparation
A major part of this work is the ingestion pipeline:

- Raw files are expected under `data/raw/`.
- Processed outputs are stored in `pipeline_output/` and related folders.
- The pipeline validates records, removes duplicates, and creates catalog and quality report artifacts.
- Chunking is implemented using simple token-based splitting, which makes the corpus easier to retrieve and more efficient for the LLM.

### Search and retrieval
The system creates a semantic search index using embeddings from Sentence Transformers and FAISS.

This means a user’s query is not matched by simple keyword text alone. Instead, the system converts both the question and the document chunks into vectors and retrieves the most relevant passages based on similarity.

### LLM answer generation
The retrieval layer is connected to an Ollama language model.

This allows the assistant to provide responses based on the retrieved context. The answer is not generated blindly; it is grounded in the actual document chunks that were found to be relevant.

### Developer-facing interfaces
Two interfaces are included:

- A REST API using FastAPI for integration and automation.
- A web UI using Streamlit for quick manual interaction.

This makes the project useful both for experimentation and for real application use.

### Containerized setup
The project includes Docker support through `docker-compose.yml` and Dockerfiles for the API and UI.

This makes it easier to run the complete stack in a consistent way, especially when Ollama and the frontend/backend need to work together.

---

## Project flow

The typical workflow in this project is:

1. Collect source documents using the scraper.
2. Run the pipeline to validate, deduplicate, and chunk the data.
3. Build or refresh the FAISS vector index.
4. Ask questions via the API or the Streamlit interface.
5. Retrieve relevant chunks, generate an answer with Ollama, and display citations.

This makes the project a practical example of a modern RAG system, from raw content ingestion to answer generation.

---

## Directory overview

- `scraper/` – crawling, parsing, and reporting utilities
- `pipeline/` – validation, chunking, catalog creation, and storage
- `rag/` – embeddings, vector search, retrieval, LLM integration, API, and UI
- `data/` – raw and processed source data
- `pipeline_output/` – generated pipeline artifacts
- `requirements.txt` – project dependencies
- `docker-compose.yml` – multi-service deployment setup

---

## How to run the project

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama
Make sure Ollama is available and has the model configured in the environment.

### 3. Run the pipeline

```bash
python -m pipeline.run
```

### 4. Rebuild the vector index

```bash
python -c "from rag.ingest import rebuild_index; print(rebuild_index())"
```

### 5. Start the API

```bash
uvicorn rag.api:app --host 0.0.0.0 --port 8000
```

### 6. Start the Streamlit UI

```bash
streamlit run rag/ui.py
```

### 7. Or use Docker Compose

```bash
docker compose up --build
```

---

## Why this setup is useful

This repository is not just a demo. It is a functioning knowledge assistant pipeline that can be extended in several directions:

- Add more document sources and better crawling logic.
- Improve chunking and retrieval quality.
- Swap in different embeddings or LLMs.
- Add authentication, logging, and monitoring for production usage.

The main value of this project is that it provides a complete path from raw public documents to a working question-answering system grounded in real source material.

---

## Summary

What has been built here is a complete MoSPI document-to-answer RAG system:

- document collection,
- validation and cleaning,
- chunking,
- embeddings and FAISS indexing,
- retrieval,
- LLM reasoning,
- API and UI access.

This gives the repository a strong foundation for both learning and practical deployment of an AI assistant over public government documents.
