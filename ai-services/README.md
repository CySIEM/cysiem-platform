# Knowledge Fabric - AI Security Copilot

## Overview
AI Security Copilot is a Retrieval-Augmented Generation (RAG) service that answers cybersecurity-related queries using a custom knowledge base, FAISS vector search, and the Ollama Llama 3.2 model.

## Features
- RAG-based question answering
- FAISS vector database
- Ollama (Llama 3.2) integration
- FastAPI REST API
- Cybersecurity knowledge base

## Tech Stack
- Python
- FastAPI
- FAISS
- Sentence Transformers
- Ollama (Llama 3.2)

## Project Structure
```
ai-services/
├── copilot/
├── embeddings/
└── rag/
```

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate embeddings:

```bash
python create_embeddings.py
```

Start the API:

```bash
uvicorn app:app --reload
```

## API Endpoint

**POST** `/ask`

Example Request:

```json
{
  "question": "Explain SQL Injection"
}
```

## Author

**Alokesh Ghosh**  
Team 5 – Knowledge Fabric & AI Security Copilot