# 📚 RAG Architecture Documentation

This document provides a detailed overview of how the Retrieval-Augmented Generation (RAG) system is implemented in your project — from chunking and embedding to indexing, querying, and summarization.

---

## 📁 1. RAG Index Creation Pipeline

### 🔄 From Markdown to FAISS

```
📁 Markdown Files (Tutorials / Docs)
        │
        ▼
1️⃣ split_markdown_to_chunks(text)
    - Splits by headers and paragraphs
    - Returns: [{ id, filename, chunk_index, text }]
        │
        ▼
2️⃣ Save as: rag_tut_chunks.json
        │
        ▼
3️⃣ embedding.py
    - Loads chunks
    - Uses SentenceTransformer('all-MiniLM-L6-v2')
    - Calls embed_text(chunk["text"])
    - Appends .embedding to each chunk
    - Saves: rag_tut_chunks_embedded.json
        │
        ▼
4️⃣ build_faiss_index(chunks)
    - Converts embeddings to np.array
    - Creates FAISS IndexFlatL2
    - Saves: rag_tut_faiss.index
        │
        └──▶ save_metadata(chunks, rag_tut_metadata.json)
```

### ✅ Final RAG Artifacts

- `rag_tut_faiss.index` → Used for vector similarity search  
- `rag_tut_metadata.json` → Used for chunk reference & prompt building

---

## 🔁 2. RAG Runtime Retrieval & Prompt Generation

```
User asks question
      │
      ▼
embed_query(question)
  ⮕ Same SentenceTransformer used
      │
      ▼
search_index(index, query_embedding)
  ⮕ Finds similar chunks in FAISS
      │
      ▼
load_metadata() → retrieves chunk details
      │
      ▼
build_prompt_docs() or build_prompt_tut()
  ⮕ Formats:
     - System role
     - Conversation history
     - Code blocks + metadata text
     - New user query
      │
      ▼
OpenAI Chat Completion (e.g. GPT-4o)
      │
      ▼
AI Response
```

---

## 🧠 3. Auto-Summarization Logic (History Trimming)

To avoid token overflow, chat history is auto-summarized after 4 Q&A pairs.

```
If len(history) >= 4:
    summarize_history(history)
        - Builds summarization prompt
        - Sends to GPT-4o
        - Replaces first 4 pairs with:
            { "question": "Summary so far", "answer": "..." }
        - Returns new trimmed history
```

🔄 This keeps chat context fresh without losing core info.

---

## 💬 4. Frontend Separation of RAG Assistants

The two assistants (`rag_docs` and `rag_tut`) are isolated in both UI and logic:

```
Docs Assistant           Tutorial Assistant
───────────────         ─────────────────────
DOM: #docs-chat         DOM: #tut-chat
Form: docsForm          Form: tutForm
Input: docsInput        Input: tutInput
API: /chat/rag_docs     API: /chat/rag_tut
```

Each assistant:

- Maintains its own history (via `getChatHistory()`)
- Sends separate POST requests
- Receives isolated responses

➡️ This ensures clean separation with no shared memory.

---

## ✅ Summary

Your RAG system is:

- ✅ Lightweight (SentenceTransformer-based)  
- ✅ Modular (chunk → embed → index → prompt)  
- ✅ Efficient (summarization keeps context clean)  
- ✅ Scalable (FAISS for fast similarity search)  

Let me know if you want a diagram image or API documentation next!
