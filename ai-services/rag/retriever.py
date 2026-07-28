import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index
index = faiss.read_index("vector_db/security_index.faiss")

# Load documents
with open("vector_db/documents.pkl", "rb") as f:
    documents = pickle.load(f)


def search(query, k=2):
    # Convert query into embedding
    query_embedding = model.encode([query])

    # Search FAISS
    distances, indices = index.search(query_embedding, k)

    results = []

    for i in indices[0]:
        if i != -1:
            results.append(documents[i])

    return results


if __name__ == "__main__":
    while True:
        question = input("\nAsk a cybersecurity question (or type 'exit'): ")

        if question.lower() == "exit":
            break

        results = search(question)

        print("\nTop Results:")
        print("=" * 60)

        for doc in results:
            print(f"\n📄 File: {doc['filename']}")
            print(doc["content"])