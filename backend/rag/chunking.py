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
    parser.add_argument("--root", type=str, default="backend/rag/rag_tut",
                        help="Root directory containing markdown docs (recursively scanned).")
    args = parser.parse_args()

    chunks = process_files(args.root)

    # Compute output dir one level up, ensure it exists
    output_dir = os.path.abspath(os.path.join(args.root, ".."))
    os.makedirs(output_dir, exist_ok=True)  # create folder if missing

    output_file = os.path.join(output_dir, "rag_tut_chunks.json")

    print(f"Saving chunks to: {output_file}")

    save_chunks(chunks, output_file)
    print(f"Saved {len(chunks)} chunks from '{args.root}' to {output_file}")

