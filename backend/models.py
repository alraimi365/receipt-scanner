from PIL import Image
import pytesseract
from process import process_receipt
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

def load_image(path):
    image = Image.open(path)
    return image

def ocr(img):
    # Extract text
    text = pytesseract.image_to_string(img)
    return text

def ocr2(path):
    # Extract text
    cropped_output_path = "cropped_receipt.jpg"
    enhanced_output_path = "enhanced_contrast_receipt.jpg"
    enhanced_image = process_receipt(path, cropped_output_path, enhanced_output_path)
    text = pytesseract.image_to_string(enhanced_image)
    return text

def TrOCR(img):

    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    pixel_values = processor(images=img, return_tensors="pt").pixel_values

    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text


