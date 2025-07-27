import subprocess
import sys
import argparse
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

def run_command(cmd, step_name):
    logging.info(f"Starting {step_name}...")
    start = time.time()
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        elapsed = time.time() - start
        logging.info(f"{step_name} completed in {elapsed:.1f}s")
        if result.stdout:
            logging.debug(f"Output:\n{result.stdout}")
        if result.stderr:
            logging.debug(f"Errors:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"{step_name} failed with exit code {e.returncode}")
        if e.stdout:
            logging.error(f"Output:\n{e.stdout}")
        if e.stderr:
            logging.error(f"Errors:\n{e.stderr}")
        return False

def main(skip_chunking, skip_embedding, skip_indexing, root_dir):
    if not skip_chunking:
        if not run_command(f"python backend/rag/chunking.py --root {root_dir}", "Chunking"):
            sys.exit(1)
    else:
        logging.info("Skipping chunking step.")

    if not skip_embedding:
        if not run_command(f"python backend/rag/embedding.py --input {root_dir}/rag_chunks.json --output {root_dir}/rag_chunks_embedded.json", "Embedding"):
            sys.exit(1)
    else:
        logging.info("Skipping embedding step.")

    if not skip_indexing:
        if not run_command(f"python backend/rag/indexing.py", "Indexing"):
            sys.exit(1)
    else:
        logging.info("Skipping indexing step.")

    logging.info("RAG update pipeline completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update RAG system pipeline")
    parser.add_argument("--root", default="backend/rag", help="Root folder for rag docs")
    parser.add_argument("--skip-chunking", action="store_true", help="Skip chunking step")
    parser.add_argument("--skip-embedding", action="store_true", help="Skip embedding step")
    parser.add_argument("--skip-indexing", action="store_true", help="Skip indexing step")

    args = parser.parse_args()
    main(args.skip_chunking, args.skip_embedding, args.skip_indexing, args.root)


# python update_rag_pro.py