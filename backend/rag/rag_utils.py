import os
import json
import re
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

# Load the model once globally to avoid reloading every call
_model = None



def split_markdown_to_chunks(text, max_chunk_size=1000):
    """
    Split markdown text into chunks by headers and paragraphs.

    Args:
        text (str): Full markdown text.
        max_chunk_size (int): Approximate max characters per chunk.

    Returns:
        List[str]: List of text chunks.
    """
    chunks = []
    sections = re.split(r'(?m)^#{1,6}\s+', text)
    headers = re.findall(r'(?m)^#{1,6}\s+(.+)', text)

    if not headers:
        # No headers found, split by paragraphs
        paragraphs = text.split('\n\n')
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_chunk_size:
                current_chunk += p + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    # With headers, pair each header with its section text
    for i, section_text in enumerate(sections[1:] if sections[0].strip() == "" else sections):
        header = headers[i] if i < len(headers) else ""
        section_text = section_text.strip()
        if len(section_text) > max_chunk_size:
            paragraphs = section_text.split('\n\n')
            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) < max_chunk_size:
                    current_chunk += p + "\n\n"
                else:
                    chunks.append(f"# {header}\n\n{current_chunk.strip()}")
                    current_chunk = p + "\n\n"
            if current_chunk:
                chunks.append(f"# {header}\n\n{current_chunk.strip()}")
        else:
            chunks.append(f"# {header}\n\n{section_text}")
    return chunks


def load_chunks(json_file):
    """Load chunk list from JSON file."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chunks(chunks, json_file):
    """Save chunk list to JSON file."""
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)



def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_text(text):
    """
    Generate embedding vector for a text using sentence-transformers.
    Returns a list of floats.
    """
    model = get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


# def embed_text(text):
#     """
#     Generate embedding vector for a text using OpenAI.
#
#     Returns:
#         List[float]: Embedding vector.
#     """
#     # Import OpenAI client only when needed
#
#     from openai import OpenAI
#     import os
#
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise ValueError("Set your OPENAI_API_KEY environment variable before calling embed_text()")
#
#     client = OpenAI(api_key=api_key)
#
#     response = client.embeddings.create(
#         input=text,
#         model="text-embedding-ada-002"
#     )
#     return response.data[0].embedding


def build_faiss_index(chunks, embedding_dim=384):
    """
    Build FAISS index from chunks with embeddings.

    Args:
        chunks (list): List of chunks with 'embedding' field.
        embedding_dim (int): Dimensionality of embeddings.

    Returns:
        faiss.Index: FAISS index.
    """

    # Import faiss only when needed
    import faiss
    import numpy as np

    index = faiss.IndexFlatL2(embedding_dim)
    embeddings = np.array([chunk["embedding"] for chunk in chunks], dtype='float32')
    index.add(embeddings)
    return index


def save_faiss(index, path):
    """Save FAISS index to file."""
    import faiss

    faiss.write_index(index, path)


def load_faiss_index(path):
    """Load FAISS index from file."""
    import faiss

    return faiss.read_index(path)


def save_metadata(chunks, path):
    """
    Save chunk metadata (without embeddings) for retrieval.

    Args:
        chunks (list): List of chunk dicts.
        path (str): File path.
    """
    metadata = [{"id": c["id"], "filename": c["filename"], "chunk_index": c["chunk_index"], "text": c["text"]} for c in
                chunks]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_metadata(path):
    """Load chunk metadata from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_query(query):
    model = get_embedding_model()
    embedding = model.encode(query)
    return np.array(embedding).astype('float32')
    return np.array(response.data[0].embedding).astype('float32')


def search_index(index, query_embedding, top_k=3):
    """
    Search FAISS index for top_k closest chunks.

    Returns:
        indices (list[int]), distances (list[float])
    """
    distances, indices = index.search(np.array([query_embedding]), top_k)
    return indices[0], distances[0]


