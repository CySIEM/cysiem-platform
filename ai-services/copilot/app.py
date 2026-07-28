from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from rag.retriever import search

# Create FastAPI app FIRST
app = FastAPI(title="AI Security Copilot API")


# Request Model
class Question(BaseModel):
    question: str


SYSTEM_PROMPT = """
You are an AI Security Copilot.

Answer only using the provided cybersecurity context.

If the answer is not available in the context,
reply that you couldn't find relevant information.
"""


@app.get("/")
def home():
    return {
        "project": "AI Security Copilot",
        "status": "Running",
        "version": "1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ask")
def ask_ai(data: Question):

    docs = search(data.question)

    context = "\n\n".join([doc["content"] for doc in docs])

    sources = [doc["filename"] for doc in docs]

    prompt = f"""
Context:
{context}

Question:
{data.question}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    return {
        "question": data.question,
        "answer": response["message"]["content"],
        "sources": sources
    }