from dotenv import load_dotenv
load_dotenv()

from rag_utils import load_faiss_index, load_metadata, embed_query, search_index
from openai import OpenAI
import numpy as np

client = OpenAI()  # your key must be set in env


def build_prompt(query, retrieved_chunks):
    prompt = "You are an expert explaining the implementation of a music AI project.\n"
    prompt += "Answer the user's question based on these code snippets and explanations:\n\n"
    for chunk in retrieved_chunks:
        prompt += f"File: {chunk['filename']}, Section {chunk['chunk_index']}:\n{chunk['text']}\n\n"
    prompt += f"User question: {query}\n\nAnswer clearly and concisely, quoting relevant code."
    return prompt


def generate_answer(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You explain code and implementation clearly."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


def main():
    index = load_faiss_index("backend/rag/rag_faiss.index")
    metadata = load_metadata("backend/rag/rag_metadata.json")

    while True:
        query = input("\nAsk your question (or type 'exit' to quit): ")
        if query.lower() in ('exit', 'quit'):
            break

        query_emb = embed_query(query)
        indices, _ = search_index(index, query_emb, top_k=3)
        retrieved = [metadata[i] for i in indices]

        prompt = build_prompt(query, retrieved)
        answer = generate_answer(prompt)
        print("\n--- AI Explanation ---\n")
        print(answer)


if __name__ == "__main__":
    main()


# python backend/rag/query.py