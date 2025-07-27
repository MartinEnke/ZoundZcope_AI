import ast
import asttokens
import os
import json

def extract_functions_with_decorators(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    atok = asttokens.ASTTokens(source, parse=True)
    tree = atok.tree

    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get full text span including decorators
            func_text = atok.get_text(node)
            func_name = node.name
            md_text = f"## Function: {func_name} ({os.path.basename(filepath)})\n\n```python\n{func_text}\n```\n"
            chunk = {
                "id": f"{os.path.basename(filepath)}_{func_name}",
                "filename": os.path.basename(filepath),
                "function_name": func_name,
                "text": md_text
            }
            chunks.append(chunk)
    return chunks


def chunk_all_python_files(root_dir = "../app"):
    all_chunks = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(subdir, file)
                # chunks = extract_functions_from_file(filepath)
                chunks = extract_functions_with_decorators(filepath)
                all_chunks.extend(chunks)
    return all_chunks

def save_chunks(chunks, out_json="backend/rag/function_chunks.json"):
    os.makedirs(os.path.dirname(out_json), exist_ok=True)  # create folder if needed
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chunks)} function chunks to {out_json}")

if __name__ == "__main__":
    chunks = chunk_all_python_files()
    save_chunks(chunks)
