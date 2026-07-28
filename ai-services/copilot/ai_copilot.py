import ollama
from rag.retriever import search

SYSTEM_PROMPT = """
You are an AI Security Copilot.

Answer only using the provided cybersecurity context.

If the answer is not present in the context, reply:
'I could not find relevant information in the knowledge base.'

Always explain:
1. Description
2. Severity
3. Indicators (if available)
4. Prevention
"""

while True:
    question = input("\nAsk a question (or 'exit'): ")

    if question.lower() == "exit":
        break

    docs = search(question)

    context = "\n\n".join([doc["content"] for doc in docs])

    prompt = f"""
Context:
{context}

Question:
{question}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    print("\n🤖 AI Security Copilot\n")
    print(response["message"]["content"])