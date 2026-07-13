"""
RAG endpoints for ZoundZcope.

This module exposes two FastAPI endpoints that perform retrieval-augmented
generation (RAG) over two corpora:
- Documentation corpus (/rag_docs)
- Tutorial/implementation corpus (/rag_tut)

It builds prompts from retrieved chunks, optionally summarizes long chat
history, calls Groq, and tracks token usage.

Endpoints:
    POST /rag_docs
        Uses the documentation corpus to explain implementation details, quote
        relevant code, and optionally return full functions on request.

    POST /rag_tut
        Uses the tutorial/implementation corpus to explain ZoundZcope's
        concepts, usage, and code paths, with the same behavior for code
        extraction and full-function returns.

Dependencies:
    - FAISS utils: load_faiss_index, load_metadata, embed_query, search_index
    - Token usage tracking: add_token_usage
    - Groq Chat Completions API
    - FastAPI for routing and request models
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.rag_utils import (
    load_faiss_index,
    load_metadata,
    embed_query,
    search_index,
)
from app.token_tracker import add_token_usage

from groq import Groq
from dotenv import load_dotenv

import logging
import os
import re


load_dotenv()

logger = logging.getLogger(__name__)

print("Current working directory:", os.getcwd())

router = APIRouter()


# ---------------------------------------------------------------------------
# Groq configuration
# ---------------------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    logger.error(
        "GROQ_API_KEY is not set. RAG requests will return an error."
    )
    client = None
else:
    client = Groq(api_key=GROQ_API_KEY)


# 3x dirname because rag.py is located in backend/app/routers/
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

RAG_DOCS_INDEX_PATH = os.path.join(
    BASE_DIR,
    "rag",
    "rag_docs",
    "combined_faiss.index",
)
RAG_DOCS_METADATA_PATH = os.path.join(
    BASE_DIR,
    "rag",
    "rag_docs",
    "combined_metadata.json",
)

RAG_TUT_INDEX_PATH = os.path.join(
    BASE_DIR,
    "rag",
    "rag_tut",
    "rag_tut_faiss.index",
)
RAG_TUT_METADATA_PATH = os.path.join(
    BASE_DIR,
    "rag",
    "rag_tut",
    "rag_tut_metadata.json",
)

print(f"Loading FAISS docs index from: {RAG_DOCS_INDEX_PATH}")
docs_index = load_faiss_index(RAG_DOCS_INDEX_PATH)
docs_metadata = load_metadata(RAG_DOCS_METADATA_PATH)

print(f"Loading FAISS tutorial index from: {RAG_TUT_INDEX_PATH}")
tut_index = load_faiss_index(RAG_TUT_INDEX_PATH)
tut_metadata = load_metadata(RAG_TUT_METADATA_PATH)


class Question(BaseModel):
    """
    Request body model for RAG queries.

    Attributes:
        question (str): The user's natural-language question.
        history (list[dict]): Optional list of previous Q&A items where each
            item has 'question' and 'answer' keys. May also include a rolling
            summary with 'question' == "__summary__".
    """

    question: str
    history: list[dict] = Field(default_factory=list)


def extract_code_blocks(text: str):
    """
    Extract code blocks from a string.

    Searches for code enclosed in triple backticks, optionally followed by
    a language tag, and returns the inner code content.

    Args:
        text (str): Input text that may contain code blocks.

    Returns:
        list[str]: Extracted code block contents without backticks.
    """
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)


def build_prompt_docs(query, retrieved_chunks, history):
    """
    Build an LLM prompt using documentation chunks.
    """
    prompt = (
        "You are an expert explaining the implementation of a music AI project.\n"
        "Use the previous questions and answers as context.\n\n"
        "If the user requests the full original function, return the entire "
        "function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant code.\n\n"
    )

    if history:
        prompt += "Conversation so far:\n"
        for pair in history:
            prompt += (
                f"User: {pair['question']}\n"
                f"AI: {pair['answer']}\n\n"
            )

    all_codes = []
    for chunk in retrieved_chunks:
        codes = extract_code_blocks(chunk["text"])
        all_codes.extend(codes)

    if all_codes:
        prompt += "Here are the relevant code snippets:\n\n"
        for code in all_codes:
            prompt += f"```python\n{code}\n```\n\n"

    prompt += "Additional context and explanations from the docs:\n\n"

    for chunk in retrieved_chunks:
        prompt += (
            f"File: {chunk['filename']}, "
            f"Section {chunk['chunk_index']}:\n"
            f"{chunk['text']}\n\n"
        )

    prompt += f"User question: {query}\n\nAnswer accordingly."
    return prompt


def build_prompt_tut(query, retrieved_chunks, history):
    """
    Build an LLM prompt using tutorial/implementation chunks.
    """
    prompt = (
        "You are an expert audio engineer and developer specializing in "
        "AI-assisted mixing and mastering.\n"
        "Use the previous questions and answers as context.\n\n"
        "The user is asking about implementation details, usage, or concepts "
        "of a mixing/mastering AI assistant project called ZoundZcope.\n"
        "If the user requests full original code functions, return the entire "
        "function code exactly as it appears inside markdown code blocks.\n"
        "Otherwise, provide clear, concise explanations quoting relevant "
        "code and concepts.\n\n"
    )

    if history:
        prompt += "Conversation so far:\n"
        for pair in history:
            prompt += (
                f"User: {pair['question']}\n"
                f"AI: {pair['answer']}\n\n"
            )

    all_codes = []
    for chunk in retrieved_chunks:
        codes = extract_code_blocks(chunk["text"])
        all_codes.extend(codes)

    if all_codes:
        prompt += (
            "Here are the relevant code snippets from the implementation:\n\n"
        )
        for code in all_codes:
            prompt += f"```python\n{code}\n```\n\n"

    prompt += (
        "Additional context and explanations from the documentation:\n\n"
    )

    for chunk in retrieved_chunks:
        prompt += (
            f"File: {chunk['filename']}, "
            f"Section {chunk['chunk_index']}:\n"
            f"{chunk['text']}\n\n"
        )

    prompt += (
        f"User question: {query}\n\n"
        "Please provide a detailed and accurate answer."
    )

    return prompt


def _extract_usage_metadata(response) -> tuple[int, int, int]:
    """
    Extract token usage reported by Groq.

    Returns:
        tuple[int, int, int]: Prompt, completion, and total token counts.
    """
    usage = getattr(response, "usage", None)
    if not usage:
        return 0, 0, 0

    prompt_tokens = int(
        getattr(usage, "prompt_tokens", 0) or 0
    )
    completion_tokens = int(
        getattr(usage, "completion_tokens", 0) or 0
    )
    total_tokens = int(
        getattr(
            usage,
            "total_tokens",
            prompt_tokens + completion_tokens,
        )
        or 0
    )

    return prompt_tokens, completion_tokens, total_tokens


def generate_answer(prompt: str) -> str:
    """
    Generate an answer with Groq and track token usage.

    Args:
        prompt (str): Prompt string to send to the model.

    Returns:
        str: Generated answer text, or a readable error string.
    """
    if not prompt or not prompt.strip():
        return "Error: Empty prompt."

    if not GROQ_API_KEY or client is None:
        return "Error: GROQ_API_KEY is not set on the server."

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain code and implementation clearly. "
                        "Use the supplied retrieved context for "
                        "project-specific claims."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=500,
            temperature=0.3,
        )

        response_text = (
            response.choices[0].message.content or ""
        ).strip()

        if not response_text:
            return "Error: Model returned an empty response."

        try:
            prompt_tokens, completion_tokens, total_tokens = (
                _extract_usage_metadata(response)
            )

            print(
                f"🧾 Groq RAG usage | prompt={prompt_tokens} | "
                f"completion={completion_tokens} | total={total_tokens}"
            )

            if total_tokens > 0:
                add_token_usage(
                    total_tokens,
                    model_name=GROQ_MODEL,
                )
        except Exception as usage_error:
            logger.warning(
                "RAG token accounting failed: %s",
                usage_error,
            )

        return response_text

    except Exception as error:
        error_type = error.__class__.__name__
        error_message = str(error).strip() or repr(error)

        logger.exception("Groq RAG request failed")

        return (
            f"Error: RAG request failed "
            f"({error_type}). {error_message}"
        )


def search_and_answer(
    index,
    metadata,
    question,
    history,
    build_prompt_fn,
    context_note="",
):
    """
    Retrieve relevant chunks, build a prompt, and generate an answer.
    """
    if len(history) >= 4:
        history = summarize_history(history, context_note)

    query_emb = embed_query(question)
    indices, _ = search_index(index, query_emb, top_k=5)
    retrieved = [metadata[i] for i in indices]

    prompt = build_prompt_fn(
        question,
        retrieved,
        history,
    )

    return generate_answer(prompt)


@router.post("/rag_docs")
async def rag_docs(question: Question):
    """
    RAG endpoint using the documentation corpus.
    """
    if not question.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    answer = search_and_answer(
        docs_index,
        docs_metadata,
        question.question,
        question.history,
        build_prompt_docs,
        context_note=(
            "The assistant is helping the user understand "
            "code from documentation."
        ),
    )

    return {"answer": answer}


@router.post("/rag_tut")
async def rag_tut(question: Question):
    """
    RAG endpoint using the tutorial/implementation corpus.
    """
    if not question.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    answer = search_and_answer(
        tut_index,
        tut_metadata,
        question.question,
        question.history,
        build_prompt_tut,
        context_note=(
            "The assistant is helping the user understand the "
            "implementation and logic of an AI-based audio assistant project."
        ),
    )

    return {"answer": answer}


_last_summary_length = 0


def summarize_history(history, context_note=""):
    """
    Summarize recent conversation history to keep context compact.

    Produces a rolling summary with Groq if at least four new Q&A pairs
    have been added since the last summary.
    """
    global _last_summary_length

    non_summary_history = [
        pair
        for pair in history
        if pair.get("question") != "__summary__"
    ]

    if len(non_summary_history) - _last_summary_length < 4:
        print("⏩ Not enough new Q&As for summarization")
        return history

    print("🧠 Rolling summarization triggered...")

    summary_prompt = (
        "You're an assistant summarizing a technical chat session.\n"
    )

    if context_note:
        summary_prompt += f"{context_note}\n"

    summary_prompt += (
        "Summarize the following conversation concisely while preserving "
        "all relevant technical details:\n\n"
    )

    last_summary = next(
        (
            pair
            for pair in history
            if pair.get("question") == "__summary__"
        ),
        None,
    )

    if last_summary:
        summary_prompt += (
            "Previous Summary:\n"
            f"{last_summary.get('answer', '')}\n\n"
        )

    new_pairs = non_summary_history[
        _last_summary_length:_last_summary_length + 4
    ]

    for pair in new_pairs:
        summary_prompt += (
            f"User: {pair.get('question', '')}\n"
            f"AI: {pair.get('answer', '')}\n\n"
        )

    if not GROQ_API_KEY or client is None:
        logger.error(
            "Cannot summarize RAG history because "
            "GROQ_API_KEY is not configured."
        )
        return history

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are summarizing a technical Q&A exchange. "
                        "Preserve implementation details, filenames, "
                        "function names, decisions, and unresolved questions."
                    ),
                },
                {
                    "role": "user",
                    "content": summary_prompt,
                },
            ],
            max_tokens=300,
            temperature=0.3,
        )

        summary = (
            response.choices[0].message.content or ""
        ).strip()

        if not summary:
            logger.warning(
                "Groq returned an empty RAG history summary."
            )
            return history

    except Exception:
        logger.exception(
            "Groq error while summarizing RAG conversation history."
        )
        return history

    try:
        prompt_tokens, completion_tokens, total_tokens = (
            _extract_usage_metadata(response)
        )

        print(
            f"🧾 Groq summary usage | prompt={prompt_tokens} | "
            f"completion={completion_tokens} | total={total_tokens}"
        )

        if total_tokens > 0:
            add_token_usage(
                total_tokens,
                model_name=GROQ_MODEL,
            )

    except Exception as usage_error:
        logger.warning(
            "RAG summary token accounting failed: %s",
            usage_error,
        )

    print("✅ Summary generated:\n", summary)

    _last_summary_length += len(new_pairs)

    new_history = [
        {
            "question": "__summary__",
            "answer": summary,
        }
    ]
    new_history += non_summary_history[_last_summary_length:]

    return new_history