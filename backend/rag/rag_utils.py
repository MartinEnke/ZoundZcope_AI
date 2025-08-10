"""
RAG (Retrieval-Augmented Generation) utilities for ZoundZcope.

This module provides helper functions for:
    - Splitting markdown content into manageable chunks.
    - Creating and saving embeddings for text chunks.
    - Building, saving, and loading FAISS vector indexes.
    - Managing associated metadata for chunk retrieval.
    - Performing semantic search queries against FAISS indexes.

Dependencies:
    - sentence-transformers for local embedding generation.
    - FAISS for vector indexing and similarity search.
    - numpy for numerical operations.
    - json/os/re for file and text processing.
"""
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
    Split a markdown document into smaller chunks for embedding.

    - Splits by markdown headers if present.
    - Falls back to paragraph-based splitting if no headers.
    - Attempts to respect `max_chunk_size` for each chunk.

    Args:
        text (str): Markdown text to split.
        max_chunk_size (int): Approximate maximum characters per chunk.

    Returns:
        list[str]: List of text chunks.
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
    """
    Load a list of text chunks from a JSON file.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        list: List of chunk dictionaries.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chunks(chunks, json_file):
    """
    Save a list of text chunks to a JSON file.

    Args:
        chunks (list): List of chunk dictionaries.
        json_file (str): Output JSON file path.
    """
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def get_embedding_model():
    """
        Retrieve or lazily load the global sentence-transformers model.

        Returns:
            SentenceTransformer: Loaded embedding model instance.
        """
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def embed_text(text):
    """
    Generate an embedding vector for a given text.

    Uses the loaded sentence-transformers model.

    Args:
        text (str): Text to embed.

    Returns:
        list[float]: Embedding vector.
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
    Build a FAISS index from chunk embeddings.

    Args:
        chunks (list): List of chunk dicts containing an "embedding" key.
        embedding_dim (int): Dimensionality of embeddings.

    Returns:
        faiss.Index: In-memory FAISS index.
    """

    # Import faiss only when needed
    import faiss
    import numpy as np

    index = faiss.IndexFlatL2(embedding_dim)
    embeddings = np.array([chunk["embedding"] for chunk in chunks], dtype='float32')
    index.add(embeddings)
    return index


def save_faiss(index, path):
    """
    Save a FAISS index to disk.

    Args:
        index (faiss.Index): FAISS index to save.
        path (str): File path for saving the index.
    """
    import faiss

    faiss.write_index(index, path)


def load_faiss_index(path):
    """
    Load a FAISS index from disk.

    Args:
        path (str): Path to the FAISS index file.

    Returns:
        faiss.Index: Loaded FAISS index.
    """
    import faiss

    return faiss.read_index(path)


def save_metadata(chunks, out_path):
    """
    Save metadata for chunks without storing embeddings.

    Args:
        chunks (list): List of chunk dicts.
        out_path (str): Output JSON file path.

    Notes:
        - Ensures the directory exists.
        - Saves id, filename, chunk_index, and text.
    """
    metadata = []
    for c in chunks:
        metadata.append({
            "id": c["id"],
            "filename": c.get("filename", "unknown"),
            "chunk_index": c.get("chunk_index", -1),  # use -1 or None if missing
            "text": c.get("text", "")
        })
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Saved metadata for {len(metadata)} chunks to {out_path}")


def load_metadata(path):
    """
    Load chunk metadata from a JSON file.

    Args:
        path (str): Metadata file path.

    Returns:
        list: List of chunk metadata dicts.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_query(query):
    """
        Generate a query embedding for similarity search.

        Args:
            query (str): Search query.

        Returns:
            numpy.ndarray: Embedding vector as float32 array.
        """
    model = get_embedding_model()
    embedding = model.encode(query)
    return np.array(embedding).astype('float32')
    return np.array(response.data[0].embedding).astype('float32')


def search_index(index, query_embedding, top_k=3):
    """
    Search a FAISS index for the most similar chunks.

    Args:
        index (faiss.Index): FAISS index to search.
        query_embedding (numpy.ndarray): Embedding vector for the query.
        top_k (int): Number of closest matches to return.

    Returns:
        tuple:
            - indices (list[int]): Indices of matching chunks.
            - distances (list[float]): Corresponding L2 distances.
    """
    distances, indices = index.search(np.array([query_embedding]), top_k)
    return indices[0], distances[0]



