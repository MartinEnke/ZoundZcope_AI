from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.rag.rag_utils import load_faiss_index, load_metadata, embed_query, search_index
from backend.app.utils import count_tokens
from openai import OpenAI
import re
import os
from app.token_tracker import add_token_usage

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
    history: list[dict] = []

def extract_code_blocks(text: str):
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

def build_prompt_docs(query, retrieved_chunks, history):
    prompt = (
        "You are an expert explaining the implementation of a music AI project.\n"
        "Use the previous questions and answers as context.\n\n"
        "If the user requests the full original function, return the entire function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant code.\n\n"
    )
    # Include previous chat history
    if history:
        prompt += "Conversation so far:\n"
        for pair in history:
            prompt += f"User: {pair['question']}\nAI: {pair['answer']}\n\n"

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

def build_prompt_tut(query, retrieved_chunks, history):
    prompt = (
        "You are an expert audio engineer and developer specializing in AI-assisted mixing and mastering.\n"
        "Use the previous questions and answers as context.\n\n"
        "The user is asking about implementation details, usage, or concepts of a mixing/mastering AI assistant project called ZoundZcope.\n"
        "If the user requests full original code functions, return the entire function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant code and concepts.\n\n"
    )
    if history:
        prompt += "Conversation so far:\n"
        for pair in history:
            prompt += f"User: {pair['question']}\nAI: {pair['answer']}\n\n"

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



    # 🔢 Count tokens in the prompt
    prompt_tokens = count_tokens(prompt)
    print(f"🧮 Prompt token count: {prompt_tokens}")

    # 🔢 Count tokens in the response
    response_text = response.choices[0].message.content
    response_tokens = count_tokens(response_text)
    print(f"📦 Response token count: {response_tokens}")

    # 📊 Total token count
    total = prompt_tokens + response_tokens
    print(f"📊 Total tokens used: {total}")

    # Add this after response
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = prompt_tokens + completion_tokens
    add_token_usage(total_tokens, model_name="gpt-4o-mini")

    return response.choices[0].message.content

def search_and_answer(index, metadata, question, history, build_prompt_fn, context_note=""):
    # Auto-summarize if too many QA pairs
    if len(history) >= 4:
        history = summarize_history(history, context_note)

    query_emb = embed_query(question)
    indices, _ = search_index(index, query_emb, top_k=5)
    retrieved = [metadata[i] for i in indices]
    prompt = build_prompt_fn(question, retrieved, history)
    answer = generate_answer(prompt)
    return answer

@router.post("/rag_docs")
async def rag_docs(question: Question):
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = search_and_answer(
        docs_index,
        docs_metadata,
        question.question,
        question.history,
        build_prompt_docs,
        context_note="The assistant is helping the user understand code from documentation."
    )
    return {"answer": answer}

@router.post("/rag_tut")
async def rag_tut(question: Question):
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    answer = search_and_answer(
        tut_index,
        tut_metadata,
        question.question,
        question.history,
        build_prompt_tut,
        context_note="The assistant is helping the user understand the implementation and logic of an AI-based audio assistant project."
    )
    return {"answer": answer}




_last_summary_length = 0  # Tracks how many Q&A pairs existed at last summary

def summarize_history(history, context_note=""):
    global _last_summary_length

    # Count how many Q&A pairs since the last summary
    non_summary_history = [p for p in history if p["question"] != "__summary__"]

    if len(non_summary_history) - _last_summary_length < 4:
        print("⏩ Not enough new Q&As for summarization")
        return history

    print("🧠 Rolling summarization triggered...")

    # Build the prompt: include latest summary (if any) + next 4 Q&As
    summary_prompt = (
        f"You're an assistant summarizing a technical chat session.\n"
        f"{context_note}\n"
        "Summarize the following conversation concisely while preserving all relevant technical details:\n\n"
    )

    # Find last summary (if any)
    last_summary = next((p for p in history if p["question"] == "__summary__"), None)
    if last_summary:
        summary_prompt += f"Previous Summary:\n{last_summary['answer']}\n\n"

    # Get the next 4 Q&A pairs after the last summary
    new_pairs = non_summary_history[_last_summary_length:_last_summary_length + 4]
    for pair in new_pairs:
        summary_prompt += f"User: {pair['question']}\nAI: {pair['answer']}\n\n"

    # Call LLM to generate summary
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are summarizing a technical Q&A exchange."},
            {"role": "user", "content": summary_prompt}
        ],
        max_tokens=300,
        temperature=0.3,
    )

    # Add this after response
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = prompt_tokens + completion_tokens
    add_token_usage(total_tokens, model_name="gpt-4o-mini")

    summary = response.choices[0].message.content
    print("✅ Summary generated:\n", summary)

    # Update state: we’ve now summarized up to this point
    _last_summary_length += 4

    # New history starts with the new summary + rest of Q&As
    new_history = [{"question": "__summary__", "answer": summary}]
    new_history += non_summary_history[_last_summary_length:]

    return new_history
