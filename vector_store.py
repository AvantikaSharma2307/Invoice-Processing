# vector_store.py

import faiss # type: ignore
import os
import json
from sentence_transformers import SentenceTransformer # type: ignore
from datetime import datetime


VECTOR_FOLDER = "faiss_store"
os.makedirs(VECTOR_FOLDER, exist_ok=True)

MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX_FILE = os.path.join(VECTOR_FOLDER, "index.faiss")
DATA_FILE = os.path.join(VECTOR_FOLDER, "invoices.json")

# Load or initialize
if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(DATA_FILE, "r") as f:
        metadata = json.load(f)
else:
    index = faiss.IndexFlatL2(384)
    metadata = []

def save_vector_db():
    faiss.write_index(index, INDEX_FILE)
    with open(DATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

def add_invoice_to_db(json_data, filename,tenant_id,location):
    # Convert the entire invoice JSON to a single string for embedding
    full_text = json.dumps(json_data, indent=2)

    embedding = MODEL.encode([full_text])[0]  # Generate vector
    index.add(embedding.reshape(1, -1))


    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store metadata
    metadata.append({
        "filename": filename,
        "tenant_id": tenant_id,
        "location": location,
        "timestamp": timestamp,
        "data": json_data,
        "text": full_text
    })

    save_vector_db()


def search_invoices(query, top_k=5):
    query_vec = MODEL.encode([query])[0].reshape(1, -1)
    distances, indices = index.search(query_vec, top_k)
    results = []
    for i in indices[0]:
        if i < len(metadata):
            results.append(metadata[i])
    return results
