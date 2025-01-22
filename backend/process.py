import cv2
import numpy as np

def load_and_resize_image(image_path, max_width=1920, max_height=1080):
    """Loads an image and resizes it to fit within specified dimensions."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"[ERROR] Could not load the image at {image_path}.")
    
    print("[DEBUG] Image loaded successfully.")

    # Calculate scaling factor to maintain aspect ratio
    height, width = image.shape[:2]
    scaling_factor = min(max_width / width, max_height / height)
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)

    resized_image = cv2.resize(image, (new_width, new_height))
    print("[DEBUG] Resized image to fit within dimensions.")
    return resized_image

def find_receipt_contour(image, min_contour_area=10000):
    """Finds the largest rectangular contour in the image, assumed to be the receipt."""
    # Convert to grayscale and detect edges
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_image, threshold1=50, threshold2=150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Check contour sizes
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_contour_area:
            print("[DEBUG] Contour area too small. Skipping.")
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4:  # Check if it is a rectangle
            print("[DEBUG] Receipt contour found.")
            return approx
    print("[DEBUG] No significant rectangular contour found.")
    return None

def enhance_image_contrast(image, gamma=1.2):
    """Enhances the contrast of the image and applies gamma correction."""
    # Normalize the image for better contrast
    contrast_enhanced = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    
    # Apply gamma correction
    gamma_corrected = np.array(255 * (contrast_enhanced / 255) ** gamma, dtype=np.uint8)
    print("[DEBUG] Enhanced contrast and applied gamma correction.")

    # Apply thresholding for better text clarity
    _, thresholded = cv2.threshold(gamma_corrected, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    print("[DEBUG] Applied thresholding for clear text.")
    return thresholded

def process_receipt(image_path, cropped_output_path, enhanced_output_path, min_contour_area=10000):
    """Main function to process the receipt image."""
    try:
        # Step 1: Load and resize the image
        resized_image = load_and_resize_image(image_path)

        # Step 2: Find the receipt contour if necessary
        receipt_contour = find_receipt_contour(resized_image, min_contour_area)
        if receipt_contour is None:
            print("[DEBUG] Assuming receipt is already cropped.")
            cropped_gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
        else:
            # Crop to the receipt contour
            x, y, w, h = cv2.boundingRect(receipt_contour)
            cropped_image = resized_image[y:y+h, x:x+w]
            cropped_gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(cropped_output_path, cropped_image)
            print(f"[DEBUG] Cropped image saved as {cropped_output_path}.")

        # Step 3: Enhance the image for OCR
        enhanced_image = enhance_image_contrast(cropped_gray)
        cv2.imwrite(enhanced_output_path, enhanced_image)
        print(f"[DEBUG] Enhanced image saved as {enhanced_output_path}.")

        # Display results
        # cv2.imshow("Enhanced Receipt", enhanced_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        return enhanced_image

    except Exception as e:
        print(f"[ERROR] {e}")

# # Run the processing pipeline
# image_path = "./sample_receipt.jpg"
# cropped_output_path = "cropped_receipt.jpg"
# enhanced_output_path = "enhanced_contrast_receipt.jpg"
# process_receipt(image_path, cropped_output_path, enhanced_output_path)
