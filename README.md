# Invoice Processing System

This is an AI-powered invoice processing system that uses Google's Gemini AI for extracting information from invoice images and provides a web interface for managing and searching through processed invoices.

## Features

- 📷 Upload invoice images or capture via camera
- 🤖 AI-powered invoice data extraction
- 📊 Table view of all processed invoices
- 🔍 Vector-based semantic search functionality
- 📱 Responsive web interface
- 💾 Automatic data storage and retrieval
- 📄 Detailed invoice viewing

## Prerequisites

1. Python 3.8 or higher
2. Google Gemini API key
3. Virtual environment (recommended)

## Installation

1. Clone the repository or download the source code:
```bash
git clone <repository-url>
cd Img-doc-processing
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv imgenv
imgenv\Scripts\activate

# Linux/Mac
python -m venv imgenv
source imgenv/bin/activate
```

3. Install required packages:
```bash
pip install flask werkzeug google-generativeai faiss-cpu Pillow python-dotenv sentence-transformers
```

4. Create a `.env` file in the project root and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Project Structure

```
Img-doc processing/
├── app.py              # Main Flask application
├── gemini_extractor.py # Gemini AI integration
├── vector_store.py     # Vector database for search
├── templates/          # HTML templates
│   ├── scanner.html    # Upload interface
│   └── table.html      # Results view
├── uploads/           # Uploaded images storage
├── output/           # Processed JSON storage
└── faiss_store/      # Vector database storage
```

## Running the Application

1. Make sure your virtual environment is activated:
```bash
# Windows
imgenv\Scripts\activate

# Linux/Mac
source imgenv/bin/activate
```

2. Start the Flask application:
```bash
python app.py
```

3. Access the application in your web browser:
- Main Scanner Page: http://127.0.0.1:5000/scan
- Table View: http://127.0.0.1:5000/table
- All Invoices View: http://127.0.0.1:5000/invoices

## Usage

1. **Uploading Invoices**:
   - Go to `/scan`
   - Upload an image file or use camera capture
   - The system will process the image and extract information

2. **Viewing Invoices**:
   - Go to `/table` for a tabular view of all invoices
   - Go to `/invoices` for a detailed view of all invoices
   - Click on invoice images to view the original document

3. **Searching Invoices**:
   - Use the search bar at the top of the table view
   - Search by any invoice field (number, company name, amount, etc.)
   - Results will be displayed in the same table format

## File Formats

- Supported image formats: JPG, PNG
- All processed data is stored in JSON format
- Vector embeddings are stored using FAISS

## Endpoints

- `/scan` - Upload interface
- `/table` - Tabular view of invoices
- `/invoices` - Detailed view of all invoices
- `/search` - Search functionality
- `/uploads/<filename>` - Access uploaded files
- `/submit_selected` - Handle batch operations on selected invoices

## Important Notes

1. The system requires an active internet connection for:
   - Gemini AI API calls
   - Initial model downloads for sentence transformers

2. Storage:
   - Uploaded images are stored in the `uploads/` directory
   - Processed data is stored in `output/`
   - Vector database files are stored in `faiss_store/`

3. Security:
   - This is a development server, not suitable for production use
   - Implement proper security measures before deploying
   - Keep your Gemini API key confidential

## Troubleshooting

1. If images fail to process:
   - Check your Gemini API key
   - Ensure the image is clear and readable
   - Verify supported file format (JPG/PNG)

2. If search isn't working:
   - Check if vector store files exist in faiss_store/
   - Ensure sentence-transformers model downloaded successfully

3. If endpoints return 404:
   - Make sure you're using the correct URLs
   - Check if all required directories exist
