# db_config.py

import os
from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "invoice_processing"

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.invoices = self.db.invoices
        
    def insert_invoice(self, invoice_data):
        """Insert a new invoice into MongoDB"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in invoice_data:
                invoice_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            result = self.invoices.insert_one(invoice_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting invoice: {e}")
            return None
    ## -----------------------Storing vector embeddings in MongoDB-----------------------
    def insert_vector_embedding(self, invoice_id, embedding, metadata):
        """Insert vector embedding into MongoDB"""
        try:
            vector_data = {
                "invoice_id": invoice_id,
                "embedding": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                "metadata": metadata,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Create vectors collection if it doesn't exist
            vectors_collection = self.db.vectors
            result = vectors_collection.insert_one(vector_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting vector: {e}")
            return None
    
    def get_all_invoices(self):
        """Get all invoices from MongoDB"""
        try:
            invoices = list(self.invoices.find({}, {'_id': 0}))  # Exclude MongoDB _id field
            return invoices
        except Exception as e:
            print(f"Error retrieving invoices: {e}")
            return []
    
    def search_invoices(self, query):
        """Search invoices using text search"""
        try:
            # Create text search index if not exists
            self.create_text_index()
            
            # Perform text search
            results = list(self.invoices.find(
                {"$text": {"$search": query}},
                {'_id': 0}
            ))
            return results
        except Exception as e:
            print(f"Error searching invoices: {e}")
            return []
    
    def create_text_index(self):
        """Create text index for search functionality"""
        try:
            # Create text index on multiple fields
            self.invoices.create_index([
                ("invoice_number", "text"),
                ("company_name", "text"),
                ("customer_name", "text"),
                ("po_number", "text"),
                ("grn_number", "text"),
                ("asn_number", "text"),
                ("email", "text"),
                ("total", "text"),
                ("date", "text")
            ])
        except Exception as e:
            # Index might already exist
            pass
    
    def close_connection(self):
        """Close MongoDB connection"""
        self.client.close()

# Global MongoDB instance
mongo_db = MongoDB()