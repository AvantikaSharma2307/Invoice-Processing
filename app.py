# app.py
import os
import json
import re
from datetime import datetime
from flask import Flask, request, render_template, redirect, jsonify,url_for, send_from_directory ,abort# type: ignore
from werkzeug.utils import secure_filename # type: ignore
from gemini_extractor import extract_invoice_fields
# Add MongoDB import
from db_config import mongo_db
from vector_store import add_invoice_to_db, search_invoices
from flask_cors import CORS # type: ignore


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
VECTOR_FOLDER = "faiss_store"
DATA_FILE = os.path.join(VECTOR_FOLDER, "invoices.json")

# Add at the top of app.py
TABLE_DATA_FILE = "output/invoice_table_data.json"


@app.route("/scan")
def scanner_page():
    return render_template("scanner.html")

@app.route("/table")
def table_page():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Use semantic search from vector database
        invoices = search_invoices(search_query)
        print(f"🔍 Search query: '{search_query}' returned {len(invoices)} results")
    else:
        # Get all invoices from MongoDB
        invoices = mongo_db.get_all_invoices()
    
    # Flatten nested structure for table display
    rows = []
    for invoice in invoices:
        if 'data' in invoice:
            # New nested structure
            data = invoice['data']
            row = {
                "invoice_number": data.get("invoice_number", ""),
                "date": data.get("date", ""),
                "due_date": data.get("due_date", ""),
                "company_name": data.get("company_name", ""),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "customer_name": data.get("customer_name", ""),
                "total": data.get("total", ""),
                "image_url": f"/uploads/{invoice.get('filename', '')}",
                "timestamp": invoice.get("timestamp", "")
            }
        else:
            # Old flat structure (for backward compatibility)
            row = {
                "invoice_number": invoice.get("invoice_number", ""),
                "date": invoice.get("date", ""),
                "due_date": invoice.get("due_date", ""),
                "company_name": invoice.get("company_name", ""),
                "email": invoice.get("email", ""),
                "phone": invoice.get("phone", ""),
                "customer_name": invoice.get("customer_name", ""),
                "total": invoice.get("total", ""),
                "image_url": invoice.get("image_url", ""),
                "timestamp": invoice.get("timestamp", "")
            }
        rows.append(row)
    
    return render_template("table.html", rows=rows, search_query=search_query)



# @app.route('/upload', methods=['POST'])
# def upload():
#     file = request.files.get('invoice_file')
#     camera_data = request.form.get('camera_image')

#     # ✅ Support for camera capture (base64)
#     if not file and camera_data:
#         import base64
#         import uuid

#         image_data = camera_data.split(',')[1]
#         image_bytes = base64.b64decode(image_data)
#         filename = f"camera_{uuid.uuid4().hex}.png"
#         save_path = os.path.join(UPLOAD_FOLDER, filename)
#         with open(save_path, "wb") as f:
#             f.write(image_bytes)
#     elif file:
#         filename = secure_filename(file.filename)
#         save_path = os.path.join(UPLOAD_FOLDER, filename)
#         file.save(save_path)
#     else:
#         return redirect(url_for('scanner_page'))

#     # ✅ Extract using Gemini
#     result_data = extract_invoice_fields(save_path)

#     try:
#         # Handle different types of responses
#         if isinstance(result_data, dict):
#             json_data = result_data
#         elif isinstance(result_data, str):
#             json_data = json.loads(result_data)
#         else:
#             return f"""
#             <h3>❌ Unexpected response type:</h3>
#             <p>Expected dictionary or JSON string, got {type(result_data)}</p>
#             <p><strong>Raw Response:</strong></p>
#             <pre>{result_data}</pre>
#             """
#     except Exception as e:
#         return f"""
#         <h3>❌ Failed to parse response:</h3>
#         <pre>{str(e)}</pre>
#         <p><strong>Raw Response:</strong></p>
#         <pre>{result_data}</pre>
#         """

#     # ✅ Save raw JSON output (optional)
#     json_filename = filename.rsplit(".", 1)[0] + ".json"
#     json_path = os.path.join(OUTPUT_FOLDER, json_filename)
#     with open(json_path, "w") as f:
#         json.dump(json_data, f, indent=2)

#     # ✅ Add to vector DB for search (existing logic)
#     add_invoice_to_db(json_data, filename)

#     # ✅ Extract 5 key fields for display
#     row_data = {
#         "invoice_number": json_data.get("invoice_number", ""),
#         "date": json_data.get("date", ""),
#         "due_date": json_data.get("due_date", ""),
#         "company_name": json_data.get("company_name", ""),
#         "company_address": json_data.get("company_address", ""),
#         "email": json_data.get("email", ""),
#         "phone": json_data.get("phone", ""),
#         "customer_name": json_data.get("customer_name", ""),
#         "billing_address": json_data.get("billing_address", ""),
#         "shipping_address": json_data.get("shipping_address", ""),
#         "subtotal": json_data.get("subtotal", ""),
#         "discount": json_data.get("discount", ""),
#         "tax": json_data.get("tax", ""),
#         "total": json_data.get("total", ""),
#         "image_url": f"/uploads/{filename}",
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     }

#     # ✅ Append to table data file
#     table_data_file = "output/invoice_table_data.json"
#     if os.path.exists(table_data_file):
#         with open(table_data_file, "r") as f:
#             table_rows = json.load(f)
#     else:
#         table_rows = []

#     table_rows.insert(0, row_data)
#     with open(table_data_file, "w") as f:
#         json.dump(table_rows, f, indent=2)
    # ✅ Prepare data for MongoDB with all extracted fields
    row_data = {
        "invoice_number": json_data.get("invoice_number", ""),
        "po_number": json_data.get("po_number", ""),
        "grn_number": json_data.get("grn_number", ""),
        "asn_number": json_data.get("asn_number", ""),
        "date": json_data.get("date", ""),
        "due_date": json_data.get("due_date", ""),
        "company_name": json_data.get("company_name", ""),
        "company_address": json_data.get("company_address", ""),
        "email": json_data.get("email", ""),
        "phone": json_data.get("phone", ""),
        "customer_name": json_data.get("customer_name", ""),
        "billing_address": json_data.get("billing_address", ""),
        "shipping_address": json_data.get("shipping_address", ""),
        "subtotal": json_data.get("subtotal", ""),
        "discount": json_data.get("discount", ""),
        "tax": json_data.get("tax", ""),
        "total": json_data.get("total", ""),
        "bank_name": json_data.get("bank_name", ""),
        "bank_account": json_data.get("bank_account", ""),
        "items": json_data.get("items", []),
        "image_url": f"/uploads/{filename}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # ✅ Save to MongoDB instead of JSON file
    mongo_db.insert_invoice(row_data)

#     return redirect(url_for("table_page"))





def append_invoice_row(data):
    if not os.path.exists(TABLE_DATA_FILE):
        rows = []
    else:
        with open(TABLE_DATA_FILE, "r") as f:
            rows = json.load(f)

    rows.append(data)
    with open(TABLE_DATA_FILE, "w") as f:
        json.dump(rows, f, indent=2)



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
    else:
        query = request.args.get('query', '')

    if not query:
        return render_template('table.html', rows=[], search_error="Please enter a search query")

    try:
        # Use MongoDB text search
        results = mongo_db.search_invoices(query)
        if not results:
            return render_template('table.html', rows=[], search_error="No matching invoices found")

        return render_template('table.html', rows=results, search_query=query)

    except Exception as e:
        return render_template('table.html', rows=[], search_error=f"Search error: {str(e)}")



@app.route('/submit_selected', methods=['POST'])
def submit_selected():
    # Load invoice data from MongoDB
    table_data = mongo_db.get_all_invoices()
    if not table_data:
        return "<h3>❌ No invoice data found.</h3>"

    submitted_rows = []

    # Case 1: Submit by row button
    submit_index = request.form.get("submit_index")
    if submit_index is not None:
        try:
            index = int(submit_index)
            if 0 <= index < len(table_data):
                submitted_rows.append(table_data[index])
        except:
            return "<h3>❌ Invalid submission index.</h3>"

    # Case 2: Submit by multiple checkboxes
    selected_indices = request.form.getlist("selected_invoices")
    for idx in selected_indices:
        try:
            i = int(idx)
            if 0 <= i < len(table_data):
                submitted_rows.append(table_data[i])
        except:
            continue

    if not submitted_rows:
        return "<h3>⚠️ No valid invoices selected or submitted.</h3>"

    # ✅ Do something with the submitted data (print, store, email, etc.)
    # For now, just show confirmation
    html = "<h2>✅ Submitted Invoices:</h2><ul>"
    for row in submitted_rows:
        html += f"<li>{row.get('invoice_number', 'N/A')} - {row.get('company_name', 'N/A')} - Total: {row.get('total', 'N/A')}</li>"
    html += "</ul><a href='/'>⬅ Back</a>"

    return html


#----------------------------API CREATED BY ANKIT------------------------------------

# @app.route('/invoices')
# def view_all_invoices():
#     # Load all invoices from the table data file
#     table_data_file = os.path.join(OUTPUT_FOLDER, "invoice_table_data.json")
#     if not os.path.exists(table_data_file):
#         return """
#         <h3>❌ No invoices found</h3>
#         <a href="/scan" class="btn">Go to Scanner</a>
#         """
    
#     with open(table_data_file, "r") as f:
#         invoices = json.load(f)
    
#     # Generate HTML for all invoices with detailed view
#     html = """
#     <style>
#         .invoice-container { max-width: 1200px; margin: 20px auto; padding: 20px; }
#         .invoice-card { 
#             background: #f8f9fa; 
#             border-radius: 8px; 
#             padding: 20px; 
#             margin-bottom: 20px;
#             box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#         }
#         .invoice-header { 
#             display: flex; 
#             justify-content: space-between; 
#             border-bottom: 2px solid #dee2e6;
#             padding-bottom: 10px;
#             margin-bottom: 15px;
#         }
#         .invoice-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
#         .invoice-image { max-width: 200px; margin-top: 10px; }
#         .btn { 
#             display: inline-block; 
#             padding: 8px 16px; 
#             background: #007bff; 
#             color: white; 
#             text-decoration: none; 
#             border-radius: 4px; 
#             margin: 5px;
#         }
#         .btn:hover { background: #0056b3; }
#         .nav-buttons {
#             margin: 20px 0;
#             padding: 10px;
#             background: #f8f9fa;
#             border-radius: 4px;
#         }
#     </style>
#     <div class="invoice-container">
#         <div class="nav-buttons">
#             <a href="/scan" class="btn">Scanner</a>
#             <a href="/table" class="btn">Table View</a>
#         </div>
#         <h2>📄 All Invoices (Detailed View)</h2>
#     """
@app.route('/invoices')
def view_all_invoices():
    # Load all invoices from MongoDB
    invoices = mongo_db.get_all_invoices()
    if not invoices:
        return """
        <h3>❌ No invoices found</h3>
        <a href="/scan" class="btn">Go to Scanner</a>
        """
    
    # Generate HTML for all invoices with detailed view
    html = """
    <style>
        .invoice-container { max-width: 1200px; margin: 20px auto; padding: 20px; }
        .invoice-card { 
            background: #f8f9fa; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .invoice-header { 
            display: flex; 
            justify-content: space-between; 
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .invoice-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .invoice-image { max-width: 200px; margin-top: 10px; }
        .btn { 
            display: inline-block; 
            padding: 8px 16px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 5px;
        }
        .btn:hover { background: #0056b3; }
        .nav-buttons {
            margin: 20px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
    </style>
    <div class="invoice-container">
        <div class="nav-buttons">
            <a href="/scan" class="btn">Scanner</a>
            <a href="/table" class="btn">Table View</a>
        </div>
        <h2>📄 All Invoices (Detailed View)</h2>
    """
    
#     for idx, invoice in enumerate(invoices):
#         html += f"""
#         <div class="invoice-card">
#             <div class="invoice-header">
#                 <h3>Invoice #{invoice.get('invoice_number', 'N/A')}</h3>
#                 <div>Date: {invoice.get('date', 'N/A')}</div>
#             </div>
#             <div class="invoice-details">
#                 <div>
#                     <h4>Company Details</h4>
#                     <p><strong>Name:</strong> {invoice.get('company_name', 'N/A')}</p>
#                     <p><strong>Address:</strong> {invoice.get('company_address', 'N/A')}</p>
#                     <p><strong>Email:</strong> {invoice.get('email', 'N/A')}</p>
#                     <p><strong>Phone:</strong> {invoice.get('phone', 'N/A')}</p>
#                 </div>
#                 <div>
#                     <h4>Customer Details</h4>
#                     <p><strong>Name:</strong> {invoice.get('customer_name', 'N/A')}</p>
#                     <p><strong>Billing Address:</strong> {invoice.get('billing_address', 'N/A')}</p>
#                     <p><strong>Shipping Address:</strong> {invoice.get('shipping_address', 'N/A')}</p>
#                 </div>
#                 <div>
#                     <h4>Financial Details</h4>
#                     <p><strong>Subtotal:</strong> {invoice.get('subtotal', 'N/A')}</p>
#                     <p><strong>Tax:</strong> {invoice.get('tax', 'N/A')}</p>
#                     <p><strong>Discount:</strong> {invoice.get('discount', 'N/A')}</p>
#                     <p><strong>Total:</strong> {invoice.get('total', 'N/A')}</p>
#                 </div>
#                 <div>
#                     <h4>Document</h4>
#                     <p><strong>Uploaded:</strong> {invoice.get('timestamp', 'N/A')}</p>
#                     <a href="{invoice.get('image_url', '#')}" target="_blank">
#                         <img src="{invoice.get('image_url', '#')}" alt="Invoice" class="invoice-image">
#                     </a>
#                 </div>
#             </div>
#         </div>
#         """
    
#     html += "</div>"
#     return html


#---------------------------------------------------------------------------------------API CREATED BY AVANTIKA----------------------------

### for mobile upload and camera capture and send data in response
@app.route('/mobile-upload', methods=['POST'])
def upload():
    file = request.files.get('invoice_file')
    camera_data = request.form.get('camera_image')

    if not file and camera_data:
        import base64
        import uuid

        image_data = camera_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        filename = f"camera_{uuid.uuid4().hex}.png"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(save_path, "wb") as f:
            f.write(image_bytes)
    elif file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
    else:
        return jsonify({"error": "No file or camera image provided"}), 400

    # Extract using Gemini
    result_data = extract_invoice_fields(save_path)

    try:
        if isinstance(result_data, dict):
            json_data = result_data
        elif isinstance(result_data, str):
            json_data = json.loads(result_data)
        else:
            return jsonify({
                "error": "Unexpected response type expected dictionary or JSON string",
                "type": str(type(result_data)),
                "raw_response": str(result_data)
            }), 500
    except Exception as e:
        return jsonify({
            "error": "Failed to parse response",
            "exception": str(e),
            "raw_response": str(result_data)
        }), 500

    # Extract key fields
    row_data = {
        "invoice_number": json_data.get("invoice_number", ""),
        "date": json_data.get("date", ""),
        "due_date": json_data.get("due_date", ""),
        "company_name": json_data.get("company_name", ""),
        "company_address": json_data.get("company_address", ""),
        "email": json_data.get("email", ""),
        "phone": json_data.get("phone", ""),
        "customer_name": json_data.get("customer_name", ""),
        "billing_address": json_data.get("billing_address", ""),
        "shipping_address": json_data.get("shipping_address", ""),
        "subtotal": json_data.get("subtotal", ""),
        "discount": json_data.get("discount", ""),
        "tax": json_data.get("tax", ""),
        "total": json_data.get("total", ""),
        "image_url": f"/uploads/{filename}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save raw JSON output (optional)
    json_filename = filename.rsplit(".", 1)[0] + ".json"
    json_path = os.path.join(OUTPUT_FOLDER, json_filename)
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    # Save to DB or file if needed
    add_invoice_to_db(json_data, filename)

    # Return response using jsonify
    return jsonify({
        "status": "success",
        "message": "Invoice processed successfully",
        "data": row_data
    }), 200

### for getting uploaded files image

@app.route('/uploads/<filename>',methods=['GET'])
def uploaded_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    # Security check: prevent directory traversal
    if not os.path.isfile(file_path):
        abort(404, description="File not found")
    return send_from_directory(UPLOAD_FOLDER, filename)

### for sending the whole invoice data
@app.route("/all-invoices", methods=["GET"])
def get_all_invoices():
    tenant_id = request.args.get("tenant_id")  # Get tenant_id from query params

    if not os.path.exists(DATA_FILE):
        return jsonify({"status": "error", "message": "No invoices found"}), 404

    try:
        with open(DATA_FILE, "r") as f:
            invoices = json.load(f)

        # If tenant_id is provided, filter invoices
        if tenant_id:
            filtered_invoices = [
                inv for inv in invoices
                if inv.get("tenant_id") == tenant_id
            ]
        else:
            filtered_invoices = invoices

        return jsonify({
            "status": "success",
            "total_invoices": len(filtered_invoices),
            "data": filtered_invoices
        }), 200

    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Invalid JSON format"}), 500






########### for web upload
def process_invoice_background(save_path, filename, tenant_id, location):
    try:
        result_data = extract_invoice_fields(save_path)

        if isinstance(result_data, dict):
            json_data = result_data
        elif isinstance(result_data, str):
            json_data = json.loads(result_data)
        else:
            print(f"[ERROR] Unexpected response type for {filename}")
            return

        # 🔹 Add tenant_id, location, metadata into the same json_data like reference
        import uuid
        generated_tenant_id = str(uuid.uuid4()).replace('-', '')[:24]  # Generate 24-char tenant_id like in image
        
        json_data["image_url"] = f"/uploads/{filename}"
        

        # Save JSON output
        json_filename = filename.rsplit(".", 1)[0] + ".json"
        json_path = os.path.join(OUTPUT_FOLDER, json_filename)
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)

        # Save to vector DB
        add_invoice_to_db(json_data, filename, generated_tenant_id, location)
        
        # Save to MongoDB in same structure as reference image
        row_data = {
            "filename": filename,
            "tenant_id": generated_tenant_id,
            "location": location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": json_data
        }
        mongo_db.insert_invoice(row_data)

        print(f"[SUCCESS] {filename} processed successfully.")

    except Exception as e:
        print(f"[ERROR] Failed processing {filename}: {e}")


@app.route('/upload', methods=['POST'])
@app.route('/web-upload', methods=['POST'])
def web_upload():
    file = request.files.get('invoice_file')
    camera_data = request.form.get('camera_image') #in web i am sebding as invoice_file

    tenant_id = request.form.get("tenant_id", "defaultTenant")
    location = request.form.get("location", "Unknown")

    if not file and not camera_data:
        return jsonify({"error": "No file or camera image provided"}), 400

    # Save the uploaded file or base64 image
    if camera_data:
        import base64
        import uuid

        image_data = camera_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        filename = f"camera_{uuid.uuid4().hex}.png"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(save_path, "wb") as f:
            f.write(image_bytes)
    else:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

    # Process in background
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=5)
    executor.submit(process_invoice_background, save_path, filename, tenant_id, location)

    # Redirect to table page like the original upload function
    return redirect(url_for('table_page'))



#-----------------------------------------------------------------------------------


if __name__ == '__main__':
    app.run(debug=True)
