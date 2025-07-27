import os
import argparse
from rag_utils import split_markdown_to_chunks, save_chunks

def process_files(root_dir):
    all_chunks = []
    chunk_id = 0
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(subdir, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                chunks = split_markdown_to_chunks(text)
                for idx, chunk_text in enumerate(chunks):
                    chunk_id += 1
                    all_chunks.append({
                        "id": f"chunk_{chunk_id}",
                        "filename": os.path.relpath(filepath, root_dir),
                        "chunk_index": idx,
                        "text": chunk_text
                    })
    return all_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunk markdown files for RAG.")
    parser.add_argument("--root", type=str, default="rag_docs",
                        help="Root directory containing markdown docs (recursively scanned).")
    args = parser.parse_args()

    chunks = process_files(args.root)
    save_chunks(chunks, "rag_chunks.json")
    print(f"Saved {len(chunks)} chunks from '{args.root}' to rag_chunks.json")


# python backend/rag/embedding.py --input backend/rag/rag_chunks.json --output backend/rag/rag_chunks_embedded.json