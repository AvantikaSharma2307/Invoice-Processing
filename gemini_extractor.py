# gemini_extractor.py

import os
import re
import json
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # Load from .env if needed

# Load API key from env or fallback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAlr__Kff7n4tDrJoEhmx471Ek-u78E3B0")

def resize_image(path, max_size=(1024, 1024)):
    """Resize and convert image to RGB."""
    img = Image.open(path)
    img = img.convert("RGB")
    img.thumbnail(max_size)
    return img

def configure_gemini(api_key: str):
    """Configure Gemini API and return model."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("models/gemini-2.0-flash")

def save_output_json(output_text: str, image_path: str):
    """Save extracted data to JSON in output/ directory."""
    try:
        os.makedirs("output", exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/{base_name}_{timestamp}.json"

        # Convert response to valid JSON if possible
        try:
            json_data = json.loads(output_text)
        except json.JSONDecodeError:
            # fallback: wrap raw text
            json_data = {"raw_output": output_text}

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        print(f"✅ Output saved to: {output_file}")
        return output_file
    except Exception as e:
        print("❌ Failed to save output JSON:", e)

        
def extract_invoice_fields(image_path: str):
    """Extract structured invoice fields using Gemini and save result with consistent keys."""
    try:
        image = resize_image(image_path)
        model = configure_gemini(GEMINI_API_KEY)

        # 🔧 Updated prompt with exact keys to ensure consistency
        prompt = (
            "Extract the following fields from the invoice and return a valid JSON object using EXACTLY these keys:\n"
            "\n"
            "invoice_number: string\n"
            "date: string (invoice date)\n"
            "due_date: string (if present)\n"
            "company_name: string (seller or issuing company)\n"
            "company_address: string\n"
            "email: string (company email if any)\n"
            "phone: string (if present)\n"
            "customer_name: string (person billed to)\n"
            "billing_address: string\n"
            "shipping_address: string\n"
            "subtotal: string (total before tax and discount)\n"
            "discount: string (if any)\n"
            "tax: string (if present)\n"
            "total: string (final amount due)\n"
            "bank_name: string (if any)\n"
            "bank_account: string (if any)\n"
            "\n"
            "items: list of objects, each with:\n"
            "  - description: string\n"
            "  - quantity: string or number\n"
            "  - unit_price: string\n"
            "  - total: string (price * quantity)\n"
            "\n"
            "Return only the JSON object. If any field is missing in the invoice, skip it or leave it blank."
        )

        print("📤 Sending image to Gemini with structured prompt...")
        response = model.generate_content([prompt, image])
        extracted_text = response.text

        # Clean up the response - remove markdown code blocks if present
        cleaned_text = re.sub(r"^```json\s*|\s*```$", "", extracted_text.strip(), flags=re.MULTILINE)
        
        try:
            # Check if the JSON is complete (has matching braces and brackets)
            open_braces = cleaned_text.count('{')
            close_braces = cleaned_text.count('}')
            open_brackets = cleaned_text.count('[')
            close_brackets = cleaned_text.count(']')
            
            if open_braces > close_braces:
                cleaned_text += '}' * (open_braces - close_braces)
            if open_brackets > close_brackets:
                cleaned_text += ']' * (open_brackets - close_brackets)
            
            # Try to parse as JSON
            json_data = json.loads(cleaned_text)
            # Save to output JSON
            save_output_json(json.dumps(json_data, indent=2), image_path)
            return json_data
        except json.JSONDecodeError:
            # If parsing fails, return the cleaned text
            save_output_json(cleaned_text, image_path)
            return cleaned_text

    except Exception as e:
        print("❌ Gemini extraction error:", e)
        return {"error": str(e)}


