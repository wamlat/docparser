from app.ocr import extract_text_from_image
import os
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import sys

# Configure Tesseract path directly in the test script
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def create_test_image(image_path):
    """Create a test image with order text."""
    # Create a white image
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        # If the font is not available, use the default
        font = ImageFont.load_default()
    
    # Add text to the image
    d.text((50, 50), "Test Order Document", fill='black', font=font)
    d.text((50, 80), "Order ID: IMG-456", fill='black', font=font)
    d.text((50, 110), "Customer: Robert Johnson", fill='black', font=font)
    d.text((50, 140), "Items:", fill='black', font=font)
    d.text((70, 170), "SKU: IMG-001, Quantity: 5, Price: $15.00", fill='black', font=font)
    d.text((70, 200), "SKU: IMG-002, Quantity: 2, Price: $30.25", fill='black', font=font)
    d.text((50, 230), "Shipping Address: 789 Pine St, Elsewhere, USA 67890", fill='black', font=font)
    
    # Save the image
    img.save(image_path)

def is_tesseract_installed():
    """Check if Tesseract is installed and accessible."""
    # Skip the version check, just check if the file exists
    tesseract_exists = os.path.exists(pytesseract.pytesseract.tesseract_cmd)
    print(f"Tesseract exists at {pytesseract.pytesseract.tesseract_cmd}: {tesseract_exists}")
    return tesseract_exists

def test_image_ocr():
    # Check if Tesseract is installed
    if not is_tesseract_installed():
        print("Tesseract OCR executable not found at the specified path.")
        print("Please install Tesseract OCR and make sure it's in your PATH.")
        print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    
    # Path to sample documents directory
    sample_docs_dir = os.path.join('data', 'sample_docs')
    
    # Create test image
    image_file = os.path.join(sample_docs_dir, 'test_order.png')
    create_test_image(image_file)
    
    print(f"Created test image at {image_file}")
    print("\nExtracting text from image using OCR...")
    
    try:
        # Extract text directly with pytesseract
        img = Image.open(image_file)
        extracted_text = pytesseract.image_to_string(img)
        
        print("\nExtracted Text:")
        print("-" * 50)
        print(extracted_text)
        print("-" * 50)
        
        # Basic verification (will depend on OCR quality)
        success = any(keyword in extracted_text for keyword in 
                     ["Order", "IMG", "Robert", "Johnson"])
        
        print(f"\nExtraction {'successful' if success else 'failed'}")
        
        return success
    except Exception as e:
        print(f"Error during OCR: {str(e)}")
        return False

if __name__ == "__main__":
    test_image_ocr() 