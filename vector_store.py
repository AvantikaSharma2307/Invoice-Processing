# vector_store.py
import faiss # type: ignore
import os
import json
from openai import OpenAI # type: ignore
from datetime import datetime
from dotenv import load_dotenv

import numpy as np
from db_config import mongo_db

# Load environment variables
load_dotenv()

VECTOR_FOLDER = "faiss_store"
os.makedirs(VECTOR_FOLDER, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
INDEX_FILE = os.path.join(VECTOR_FOLDER, "index.faiss")
METADATA_FILE = os.path.join(VECTOR_FOLDER, "metadata.json")

def save_vector_db():
    """Save FAISS index and metadata to disk"""
    faiss.write_index(index, INDEX_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(vector_metadata, f, indent=2)

# Load or initialize FAISS index and metadata
# Check if we need to recreate the index due to dimension mismatch
recreate_index = False

if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
    try:
        temp_index = faiss.read_index(INDEX_FILE)
        if temp_index.d != 1536:  # OpenAI embedding dimension
            print("⚠️  Dimension mismatch detected. Recreating FAISS index for OpenAI embeddings...")
            recreate_index = True
        else:
            index = temp_index
            with open(METADATA_FILE, "r") as f:
                vector_metadata = json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading existing index: {e}. Creating new index...")
        recreate_index = True

if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE) or recreate_index:
    print("🔄 Creating new FAISS index for OpenAI embeddings...")
    index = faiss.IndexFlatL2(1536)  # 1536 is the dimension for OpenAI text-embedding-3-small
    vector_metadata = []
    # Save the new empty index
    save_vector_db()

def add_invoice_to_db(json_data, filename,tenant_id,location):
    # Extract only relevant fields for embedding
    relevant_fields = {
        "company_name": json_data.get('company_name', ''),
        "invoice_number": json_data.get('invoice_number', ''),
        "po_number": json_data.get('po_number', ''),
        "asn_number": json_data.get('asn_number', ''),
        "grn_number": json_data.get('grn_number', ''),
        "email": json_data.get('email', ''),
        "total_amount": json_data.get('total_amount', ''),
        "gst_number": json_data.get('gst_number', ''),
        "filename": filename
    }
    
    # Convert only relevant fields to text for embedding
    embedding_text = " ".join([f"{k}: {v}" for k, v in relevant_fields.items() if v])
    
    # Generate embedding using OpenAI
    response = client.embeddings.create(
        input=embedding_text,
        model="text-embedding-3-small"
    )
    embedding = np.array(response.data[0].embedding, dtype=np.float32)
    
    index.add(embedding.reshape(1, -1))
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Store only filename in vector metadata
    metadata_entry = {
        "filename": filename
    }
    vector_metadata.append(metadata_entry)

    save_vector_db()
    
    # Store embedding in MongoDB
    mongo_db.insert_vector_embedding(
        invoice_id=json_data.get('invoice_number', filename),
        embedding=embedding,
        metadata=metadata_entry
    )

def search_invoices(query, top_k=5, similarity_threshold=1.2):
    """Search invoices using vector similarity (proper semantic search)"""
    try:
        if len(vector_metadata) == 0:
            print("No vector data available, falling back to MongoDB search")
            return mongo_db.search_invoices(query)
        
        print(f"🔍 Performing semantic search for: {query}")
        
        # Generate query embedding using OpenAI
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vec = np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)
        
        # Search in FAISS
        distances, indices = index.search(query_vec, min(top_k, len(vector_metadata)))
        
        results = []
        seen_invoices = set()  # To avoid duplicates
        
        for i, distance in zip(indices[0], distances[0]):
            # Only include results below the similarity threshold (lower distance = more similar)
            if distance > similarity_threshold:
                print(f"Skipping match with distance {distance}: {vector_metadata[i].get('filename', 'Unknown')} (above threshold {similarity_threshold})")
                continue
                
            if i < len(vector_metadata) and i >= 0:
                metadata_entry = vector_metadata[i]
                filename = metadata_entry.get('filename', '')
                print(f"Found match with distance {distance}: {filename}")
                
                if filename and filename not in seen_invoices:
                    # New approach: Get invoice data from MongoDB using filename
                    mongo_results = mongo_db.get_all_invoices()
                    for invoice_data in mongo_results:
                        if invoice_data.get('filename') == filename:
                            invoice_id = invoice_data.get('invoice_number', filename)
                            if invoice_id not in seen_invoices:
                                results.append(invoice_data)
                                seen_invoices.add(invoice_id)
                                print(f"✓ Added invoice {invoice_id} from MongoDB via semantic search")
                                break
        
        print(f"✅ Semantic search returned {len(results)} unique results")
        return results if results else mongo_db.search_invoices(query)
        
    except Exception as e:
        print(f"❌ Vector search error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        # Fallback to MongoDB search
        return mongo_db.search_invoices(query)
