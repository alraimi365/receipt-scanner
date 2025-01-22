from flask import Flask, request, jsonify
import os
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import re
from models import *

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load pre-trained Donut model and processor
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "naver-clova-ix/donut-base-finetuned-cord-v2"
model = VisionEncoderDecoderModel.from_pretrained(model_name)
processor = DonutProcessor.from_pretrained(model_name)

# Ensure model is on the correct device
model.to(device)

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

        # # Perform structured data extraction using the pre-trained model
        # output = generate_outputs(file_path)
        # extracted_data = decode_clean(output)

        # img = load_image(file_path)
        # # extracted_data = ocr(img)
        # extracted_data = TrOCR(img)

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

def generate_outputs(image_path):
    """Run the model to generate outputs from the image."""
    # Load the image
    image = Image.open(image_path)
    print(f"Image Format: {image.format}, Size: {image.size}, Mode: {image.mode}")

    # Ensure the image is in RGB format
    image = image.convert("RGB")

    # Prepare decoder inputs
    task_prompt = "<s_cord-v2>"
    decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)  # Move to device
    print(f"Decoder Input IDs: {decoder_input_ids}")

    # Preprocess image for the model
    pixel_values = processor(image, return_tensors="pt").pixel_values.to(device)  # Move to device
    print(f"Pixel Values Shape: {pixel_values.shape}")

    # Confirm device alignment
    print(f"Model device: {next(model.parameters()).device}")
    print(f"Pixel Values device: {pixel_values.device}")
    print(f"Decoder Input IDs device: {decoder_input_ids.device}")

    # Generate outputs
    print("Generating outputs...")
    outputs = model.generate(
        pixel_values,
        decoder_input_ids=decoder_input_ids,
        max_length=model.decoder.config.max_position_embeddings,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )
    return outputs

def decode_clean(outputs):
    """Decode and clean up the model's outputs."""
    # Decode and clean up the generated sequence
    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()  # Remove first task start token

    # Convert the cleaned sequence into structured JSON
    parsed_output = processor.token2json(sequence)
    return parsed_output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
