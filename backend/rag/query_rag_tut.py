from dotenv import load_dotenv
load_dotenv()

from rag_utils import load_faiss_index, load_metadata, embed_query, search_index
from openai import OpenAI
import re

client = OpenAI()  # ensure your OPENAI_API_KEY is set in the environment


def extract_code_blocks(text):
    """
    Extracts all markdown code blocks from chunk text.
    Returns a list of code strings.
    """
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)


def build_prompt(query, retrieved_chunks):
    prompt = (
        "You are an expert audio engineer and developer specializing in AI-assisted mixing and mastering.\n"
        "The user is asking about implementation details, usage, or concepts of a mixing/mastering AI assistant project called ZoundZcope.\n"
        "If the user requests full original code functions, return the entire function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant code and concepts.\n\n"
    )

    all_codes = []
    for chunk in retrieved_chunks:
        codes = extract_code_blocks(chunk['text'])
        all_codes.extend(codes)

    if all_codes:
        prompt += "Here are the relevant code snippets from the implementation:\n\n"
        for code in all_codes:
            prompt += f"```python\n{code}\n```\n\n"

    prompt += "Additional context and explanations from the documentation:\n\n"
    for chunk in retrieved_chunks:
        prompt += f"File: {chunk['filename']}, Section {chunk['chunk_index']}:\n{chunk['text']}\n\n"

    prompt += f"User question: {query}\n\nPlease provide a detailed and accurate answer."

    return prompt


def generate_answer(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You explain audio AI software engineering concepts and code clearly and helpfully."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.3,
    )
    return response.choices[0].message.content


def main():
    index = load_faiss_index("backend/rag/rag_tut/rag_tut_faiss.index")
    metadata = load_metadata("backend/rag/rag_tut/rag_tut_metadata.json")

    print("Welcome to the ZoundZcope AI assistant tutorial query system.")
    print("Type your questions about the project, code, or functionality.")
    print("Type 'exit' or 'quit' to end.\n")

    while True:
        query = input("Ask your question: ").strip()
        if query.lower() in ('exit', 'quit'):
            break
        if not query:
            continue

        query_emb = embed_query(query)
        indices, _ = search_index(index, query_emb, top_k=3)
        retrieved = [metadata[i] for i in indices]

        prompt = build_prompt(query, retrieved)
        answer = generate_answer(prompt)

        print("\n--- AI Explanation ---\n")
        print(answer)
        print("\n----------------------\n")


if __name__ == "__main__":
    main()


# python backend/rag/query_rag_tut.py