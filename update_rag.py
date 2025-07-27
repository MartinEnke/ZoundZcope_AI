import subprocess

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        exit(1)

if __name__ == "__main__":
    # Step 1: Chunk markdown files
    run_command("python backend/rag/chunking.py --root backend/rag")

    # Step 2: Generate embeddings for chunks
    run_command("python backend/rag/embedding.py --input backend/rag/rag_chunks.json --output backend/rag/rag_chunks_embedded.json")

    # Step 3: Build and save FAISS index
    run_command("python backend/rag/indexing.py")

    print("RAG system updated successfully!")


# python update_rag.py