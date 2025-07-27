from dotenv import load_dotenv
load_dotenv()

from rag_utils import load_faiss_index, load_metadata, embed_query, search_index
from openai import OpenAI
import numpy as np

client = OpenAI()  # your key must be set in env


import re

def extract_code_blocks(text):
    """
        Extracts all markdown code blocks from chunk_text.
        Returns a list of code strings.
        """
    # Regex to match triple-backtick code blocks, optionally with language hint
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

def build_prompt(query, retrieved_chunks):
    prompt = "You are an expert explaining the implementation of a music AI project.\n"
    prompt += "If the user requests the full original function, return the entire function code exactly as it appears inside markdown code blocks.\n"
    prompt += "Otherwise, provide clear, concise explanations quoting relevant code.\n\n"

    all_codes = []
    for chunk in retrieved_chunks:
        codes = extract_code_blocks(chunk['text'])
        all_codes.extend(codes)

    # Add extracted code snippets first, if any
    if all_codes:
        prompt += "Here are the relevant code snippets:\n\n"
        for code in all_codes:
            prompt += f"```python\n{code}\n```\n\n"

    # Add explanations as well
    prompt += "Additional context and explanations from the docs:\n\n"
    for chunk in retrieved_chunks:
        prompt += f"File: {chunk['filename']}, Section {chunk['chunk_index']}:\n{chunk['text']}\n\n"

    # Finally, add the user question once
    prompt += f"User question: {query}\n\nAnswer accordingly."

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