from dotenv import load_dotenv
load_dotenv()

import time
import argparse
from rag_utils import load_chunks, save_chunks, embed_text


def embed_all_chunks(json_in, json_out):
    chunks = load_chunks(json_in)
    for i, chunk in enumerate(chunks):
        print(f"Embedding chunk {i+1}/{len(chunks)}: {chunk['id']}")
        chunk["embedding"] = embed_text(chunk["text"])
        time.sleep(0.5)
    save_chunks(chunks, json_out)
    print(f"All chunks embedded and saved to {json_out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="backend/rag/rag_tut_chunks.json", help="Input chunks JSON file")
    parser.add_argument("--output", default="backend/rag/rag_tut_chunks_embedded.json", help="Output embedded chunks JSON file")
    args = parser.parse_args()

    embed_all_chunks(args.input, args.output)


# python backend/rag/embedding.py

# python backend/rag/embedding.py --input backend/rag/rag_tut_chunks.json --output backend/rag/rag_tut_chunks_embedded.json