from rag_utils import load_chunks, build_faiss_index, save_faiss, save_metadata

def create_index(json_embedded="backend/rag/rag_tut_chunks_embedded.json"):
    chunks = load_chunks(json_embedded)
    index = build_faiss_index(chunks)
    save_faiss(index, "backend/rag/rag_tut/rag_tut_faiss.index")
    save_metadata(chunks, "backend/rag/rag_tut/rag_tut_metadata.json")
    print("FAISS index and metadata saved.")

if __name__ == "__main__":
    create_index()


# python backend/rag/indexing_rag_tut.py