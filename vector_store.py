# vector_store.py

import faiss # type: ignore
import os
import json
from sentence_transformers import SentenceTransformer # type: ignore
from datetime import datetime

import numpy as np
from db_config import mongo_db

VECTOR_FOLDER = "faiss_store"
os.makedirs(VECTOR_FOLDER, exist_ok=True)

MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX_FILE = os.path.join(VECTOR_FOLDER, "index.faiss")
METADATA_FILE = os.path.join(VECTOR_FOLDER, "metadata.json")

# Load or initialize FAISS index and metadata
if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(METADATA_FILE, "r") as f:
        vector_metadata = json.load(f)
else:
    index = faiss.IndexFlatL2(384)  # 384 is the dimension for all-MiniLM-L6-v2
    vector_metadata = []

def save_vector_db():
    """Save FAISS index and metadata to disk"""
    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(vector_metadata, f, indent=2)

def add_invoice_to_db(json_data, filename):
    """Add invoice to both MongoDB and vector database"""
    try:
        # Convert the entire invoice JSON to a single string for embedding
        search_text = f"""
        Invoice: {json_data.get('invoice_number', '')}
        PO: {json_data.get('po_number', '')}
        GRN: {json_data.get('grn_number', '')}
        ASN: {json_data.get('asn_number', '')}
        Company: {json_data.get('company_name', '')}
        Customer: {json_data.get('customer_name', '')}
        Date: {json_data.get('date', '')}
        Total: {json_data.get('total', '')}
        Email: {json_data.get('email', '')}
        """
        
        # Generate embedding
        embedding = MODEL.encode([search_text.strip()])[0]
        
        # Add to FAISS index
        index.add(np.array([embedding]))
        
        # Store metadata for vector search
        metadata_entry = {
            "filename": filename,
            "invoice_number": json_data.get('invoice_number', ''),
            "company_name": json_data.get('company_name', ''),
            "search_text": search_text.strip()
        }
        vector_metadata.append(metadata_entry)
        
        # Save vector database
        save_vector_db()
        
        # Store embedding in MongoDB
        mongo_db.insert_vector_embedding(
            invoice_id=json_data.get('invoice_number', filename),
            embedding=embedding,
            metadata=metadata_entry
        )
        
        print("✅ Added to vector database")
        
    except Exception as e:
        print(f"❌ Error adding to vector DB: {e}")

def search_invoices(query, top_k=5):
    """Search invoices using vector similarity (fallback to MongoDB search)"""
    try:
        if len(vector_metadata) == 0:
            # Fallback to MongoDB text search
            return mongo_db.search_invoices(query)
        
        # Generate query embedding
        query_vec = MODEL.encode([query])[0].reshape(1, -1)
        
        # Search in FAISS
        distances, indices = index.search(query_vec, min(top_k, len(vector_metadata)))
        
        results = []
        for i in indices[0]:
            if i < len(vector_metadata) and i >= 0:
                metadata_entry = vector_metadata[i]
                # Get full invoice data from MongoDB
                invoices = mongo_db.get_all_invoices()
                for invoice in invoices:
                    if invoice.get('invoice_number') == metadata_entry.get('invoice_number'):
                        results.append({"data": invoice})
                        break
        
        return results if results else mongo_db.search_invoices(query)
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        # Fallback to MongoDB search
        return mongo_db.search_invoices(query)
