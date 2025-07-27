# merge_and_index.py
import json
import os
from rag_utils import load_chunks, build_faiss_index, save_faiss, save_metadata

def load_chunks_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_chunks_file(chunks, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chunks)} chunks to {out_path}")

def merge_chunks(file1, file2, out_file):
    chunks1 = load_chunks_file(file1)
    chunks2 = load_chunks_file(file2)

    # Prefix IDs and add type to avoid collision and mark chunk origin
    for c in chunks1:
        c["id"] = "doc_" + c["id"]
        c["type"] = "doc"
    for c in chunks2:
        c["id"] = "func_" + c["id"]
        c["type"] = "function"

    merged = chunks1 + chunks2
    save_chunks_file(merged, out_file)

def create_combined_index(merged_json, index_path, metadata_path):
    chunks = load_chunks(merged_json)
    index = build_faiss_index(chunks)
    save_faiss(index, index_path)
    save_metadata(chunks, metadata_path)
    print(f"Combined FAISS index saved to {index_path}")
    print(f"Combined metadata saved to {metadata_path}")

if __name__ == "__main__":
    file1 = "backend/rag/rag_chunks_embedded.json"
    file2 = "backend/rag/function_chunks_embedded.json"
    merged_out = "backend/rag/combined_chunks_embedded.json"
    faiss_out = "backend/rag/combined_faiss.index"
    metadata_out = "backend/rag/combined_metadata.json"

    print("Merging chunks...")
    merge_chunks(file1, file2, merged_out)
    print("Building combined FAISS index...")
    create_combined_index(merged_out, faiss_out, metadata_out)


# python backend/rag/merge_and_index.py