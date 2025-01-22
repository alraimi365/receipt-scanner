from flask import Flask, request, jsonify
import os
from models import *
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return jsonify({"message": "Receipt Scanner API with Donut is running!"})

@app.route('/upload_receipt', methods=['POST'])
def upload_receipt():
    file = request.files.get('receipt')

    if not file:
        return jsonify({"error": "No receipt uploaded!"}), 400

    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    try:
        file.save(file_path)

        # Perform structured data extraction using OCR

        extracted_data = ocr2(file_path)
        print(extracted_data)

        # Remove the file after processing
        os.remove(file_path)

        # Return the extracted information
        return jsonify(extracted_data), 200

    except Exception as e:
        # Handle exceptions and return an error response
        print(f"Error: {str(e)}")  # Log error details for debugging
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

app.run(
    host=os.getenv('FLASK_HOST', '0.0.0.0'),
    port=int(os.getenv('FLASK_PORT', 5000)),
    debug=os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
)
