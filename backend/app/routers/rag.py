"""
RAG endpoints for ZoundZcope.

This module exposes two FastAPI endpoints that perform retrieval-augmented
generation (RAG) over two corpora:
- Documentation corpus (/rag_docs)
- Tutorial/implementation corpus (/rag_tut)

It builds prompts from retrieved chunks, optionally summarizes long chat
history, calls the LLM, and tracks token usage.

Endpoints:
    POST /rag_docs
        Uses the documentation corpus to explain implementation details, quote
        relevant code, and optionally return full functions on request.

    POST /rag_tut
        Uses the tutorial/implementation corpus to explain ZoundZcope’s
        concepts, usage, and code paths, with the same behavior for code
        extraction and full-function returns.

Dependencies:
    - FAISS utils: load_faiss_index, load_metadata, embed_query, search_index
    - Token counting/tracking: count_tokens, add_token_usage
    - OpenAI Chat Completions API (model: gpt-4o-mini)
    - FastAPI for routing and request models
"""

from rag.rag_utils import (
    load_faiss_index,
    load_metadata,
    embed_query,
    search_index,
)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils import count_tokens
from app.token_tracker import add_token_usage

import os, re, logging
from httpx import Timeout
from openai import OpenAI

# Logging
logger = logging.getLogger(__name__)

print("Current working directory:", os.getcwd())


router = APIRouter()

# ----- OpenAI client (with timeouts + optional base_url/model from env) -----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional (e.g. school proxy)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is not set! RAG endpoints will return an error.")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    timeout=Timeout(20.0, connect=5.0)  # 5s connect, 20s total
)


# 3x dirname, weil rag.py liegt in backend/app/routers/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAG_DOCS_INDEX_PATH = os.path.join(BASE_DIR, "rag", "rag_docs", "combined_faiss.index")
RAG_DOCS_METADATA_PATH = os.path.join(BASE_DIR, "rag", "rag_docs", "combined_metadata.json")

RAG_TUT_INDEX_PATH = os.path.join(BASE_DIR, "rag", "rag_tut", "rag_tut_faiss.index")
RAG_TUT_METADATA_PATH = os.path.join(BASE_DIR, "rag", "rag_tut", "rag_tut_metadata.json")


for p in (RAG_DOCS_INDEX_PATH, RAG_DOCS_METADATA_PATH, RAG_TUT_INDEX_PATH, RAG_TUT_METADATA_PATH):
    if not os.path.exists(p):
        logger.error("RAG asset missing: %s", p)

docs_index = load_faiss_index(RAG_DOCS_INDEX_PATH)
docs_metadata = load_metadata(RAG_DOCS_METADATA_PATH)

tut_index = load_faiss_index(RAG_TUT_INDEX_PATH)
tut_metadata = load_metadata(RAG_TUT_METADATA_PATH)

print(f"Loading FAISS docs index from: {RAG_DOCS_INDEX_PATH}")


print(f"Loading FAISS index from: {RAG_DOCS_INDEX_PATH}")



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
    history: list[dict] = []


def extract_code_blocks(text: str):
    """
        Extract code blocks from a string.

        Searches for code enclosed in triple backticks (```), optionally
        followed by a language tag, and returns the inner code content.

        Args:
            text (str): The input text that may contain code blocks.

        Returns:
            list[str]: The extracted code block contents without backticks.
        """
    return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)


def build_prompt_docs(query, retrieved_chunks, history):
    """
    Build an LLM prompt using documentation chunks.

    Assembles a prompt that includes prior chat history, relevant code
    snippets extracted from retrieved documentation chunks, and additional
    contextual excerpts from the docs.

    Args:
        query (str): The user's question.
        retrieved_chunks (list[dict]): Chunks retrieved from the docs corpus.
            Each chunk dict should contain 'text', 'filename', and 'chunk_index'.
        history (list[dict]): Previous Q&A pairs (and optional summary), each
            with 'question' and 'answer' keys.

    Returns:
        str: The fully constructed prompt string for the LLM.
    """
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
    """
        Build an LLM prompt using tutorial/implementation chunks.

        Assembles a prompt that includes prior chat history, relevant code
        snippets extracted from retrieved tutorial chunks, and additional
        contextual excerpts focused on ZoundZcope’s implementation details.

        Args:
            query (str): The user's question.
            retrieved_chunks (list[dict]): Chunks from the tutorial corpus with
                'text', 'filename', and 'chunk_index'.
            history (list[dict]): Previous Q&A pairs (and optional summary).

        Returns:
            str: The fully constructed prompt string for the LLM.
        """
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
    """
    Generate an answer from the LLM and track token usage, with robust error handling.
    Returns a string. On error, returns a user-facing "Error: ..." string.
    """
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY is not set on the server."

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You explain code and implementation clearly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3,
        )
    except Exception as e:
        # Anything from auth errors to timeouts ends up here
        logger.exception("OpenAI chat error (RAG generate_answer)")
        return f"Error: OPENAI_API_ERROR: {e}"

    try:
        response_text = resp.choices[0].message.content
    except Exception as e:
        logger.exception("Malformed OpenAI response structure")
        return f"Error: MALFORMED_OPENAI_RESPONSE: {e}"

    # token accounting (best-effort; don’t crash UI if missing)
    try:
        from app.utils import count_tokens
        prompt_tokens = count_tokens(prompt)
        response_tokens = count_tokens(response_text)
        total = prompt_tokens + response_tokens
        logger.info(f"RAG tokens — prompt:{prompt_tokens} resp:{response_tokens} total:{total}")

        # provider usage (if present)
        usage = getattr(resp, "usage", None)
        if usage and getattr(usage, "prompt_tokens", None) is not None:
            total_reported = usage.prompt_tokens + usage.completion_tokens
            from app.token_tracker import add_token_usage
            add_token_usage(total_reported, model_name=OPENAI_MODEL)
    except Exception:
        # Don’t let metrics kill the response
        logger.debug("Token accounting failed; continuing.")

    return response_text


'''
def generate_answer(prompt: str):
    """
        Generate an answer from the LLM and track token usage.

        Sends the prompt to the OpenAI Chat Completions API using a concise
        system instruction, logs token counts (prompt/response/total), and
        records usage via the token tracker.

        Args:
            prompt (str): The prompt string to send to the model.

        Returns:
            str: The generated answer text from the LLM.
        """
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
'''

def search_and_answer(index, metadata, question, history, build_prompt_fn, context_note=""):
    """
        Retrieve relevant chunks, build a prompt, and generate an answer.

        Applies rolling summarization when the history grows, embeds the
        query, searches the FAISS index, constructs a prompt from the
        retrieved chunks and history, and calls the LLM.

        Args:
            index: The FAISS index to search.
            metadata (list[dict]): Metadata aligned with the index entries.
            question (str): The user's question.
            history (list[dict]): Conversation history and optional summary.
            build_prompt_fn (Callable): Function that constructs the LLM prompt
                (e.g., `build_prompt_docs` or `build_prompt_tut`).
            context_note (str): Additional context passed to summarization.

        Returns:
            str: The generated answer text.
        """
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
    """
        RAG endpoint using the documentation corpus.

        Validates the input, retrieves relevant documentation chunks, builds
        a prompt from the docs and history, and returns the generated answer.

        Args:
            question (Question): Request body with 'question' text and optional
                'history' of previous Q&A pairs.

        Returns:
            dict: A JSON object with the generated 'answer'.

        Raises:
            HTTPException: If 'question' is empty or whitespace.
        """
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
    """
        RAG endpoint using the tutorial/implementation corpus.

        Validates the input, retrieves tutorial/implementation chunks, builds
        a prompt from the tutorial content and history, and returns the
        generated answer.

        Args:
            question (Question): Request body with 'question' text and optional
                'history' of previous Q&A pairs.

        Returns:
            dict: A JSON object with the generated 'answer'.

        Raises:
            HTTPException: If 'question' is empty or whitespace.
        """
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
    """
        Summarize recent conversation history to keep context compact.

        Produces a rolling summary with the LLM if at least four new Q&A
        pairs have been added since the last summary. The updated history
        starts with a summary item (where 'question' == "__summary__")
        followed by the remaining unsummarized Q&A items.

        Args:
            history (list[dict]): The full conversation history. Summary items
                are marked with 'question' == "__summary__".
            context_note (str): Optional note to guide the summarization style
                or focus (e.g., docs vs. tutorial context).

        Returns:
            list[dict]: The updated history with a new summary when triggered.
        """
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

        # Call LLM to generate summary (robust)
        if not OPENAI_API_KEY:
            # Skip summarization gracefully if key missing
            return history

        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are summarizing a technical Q&A exchange."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            summary = response.choices[0].message.content
        except Exception as e:
            logger.exception("OpenAI chat error (RAG summarize_history)")
            # Don’t break the chat if summarization fails
            return history

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
