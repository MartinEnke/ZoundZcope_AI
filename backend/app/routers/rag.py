from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.rag.rag_utils import load_faiss_index, load_metadata, embed_query, search_index
from openai import OpenAI
import re
import os

print("Current working directory:", os.getcwd())


router = APIRouter()

client = OpenAI()


# 3x dirname, weil rag.py liegt in backend/app/routers/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAG_DOCS_INDEX_PATH = os.path.join(BASE_DIR, "rag", "rag_docs", "combined_faiss.index")
RAG_DOCS_METADATA_PATH = os.path.join(BASE_DIR, "rag", "rag_docs", "combined_metadata.json")

RAG_TUT_INDEX_PATH = os.path.join(BASE_DIR, "rag", "rag_tut", "rag_tut_faiss.index")
RAG_TUT_METADATA_PATH = os.path.join(BASE_DIR, "rag", "rag_tut", "rag_tut_metadata.json")

print(f"Loading FAISS docs index from: {RAG_DOCS_INDEX_PATH}")


print(f"Loading FAISS index from: {RAG_DOCS_INDEX_PATH}")
docs_index = load_faiss_index(RAG_DOCS_INDEX_PATH)
docs_metadata = load_metadata(RAG_DOCS_METADATA_PATH)

tut_index = load_faiss_index(RAG_TUT_INDEX_PATH)
tut_metadata = load_metadata(RAG_TUT_METADATA_PATH)

class Question(BaseModel):
    question: str

def extract_code_blocks(text: str):
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

def build_prompt_docs(query, retrieved_chunks):
    prompt = (
        "You are an expert explaining the implementation of a music AI project.\n"
        "If the user requests the full original function, return the entire function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant code.\n\n"
    )
    all_codes = []
    for chunk in retrieved_chunks:
        codes = extract_code_blocks(chunk['text'])
        all_codes.extend(codes)
    if all_codes:
        prompt += "Here are the relevant code snippets:\n\n"
        for code in all_codes:
            prompt += f"```python\n{code}\n```\n\n"
    prompt += "Additional context and explanations from the docs:\n\n"
    for chunk in retrieved_chunks:
        prompt += f"File: {chunk['filename']}, Section {chunk['chunk_index']}:\n{chunk['text']}\n\n"
    prompt += f"User question: {query}\n\nAnswer accordingly."
    return prompt

def build_prompt_tut(query, retrieved_chunks):
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

def generate_answer(prompt: str):
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

def search_and_answer(index, metadata, question, build_prompt_fn):
    query_emb = embed_query(question)
    indices, _ = search_index(index, query_emb, top_k=3)
    retrieved = [metadata[i] for i in indices]
    prompt = build_prompt_fn(question, retrieved)
    answer = generate_answer(prompt)
    return answer

@router.post("/rag_docs")
async def rag_docs(question: Question):
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = search_and_answer(docs_index, docs_metadata, question.question, build_prompt_docs)
    return {"answer": answer}

@router.post("/rag_tut")
async def rag_tut(question: Question):
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = search_and_answer(tut_index, tut_metadata, question.question, build_prompt_tut)
    return {"answer": answer}
