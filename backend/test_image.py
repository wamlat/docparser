import os
import sys
import pytesseract
from PIL import Image, ImageOps

# Set Tesseract path for Windows
if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_image(image_path):
    """Test if an image can be opened and processed"""
    print(f"Testing image: {image_path}")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return
    
    # Check file size
    file_size = os.path.getsize(image_path)
    print(f"File size: {file_size} bytes")
    
    if file_size == 0:
        print("Error: File is empty")
        return
    
    if file_size < 100:
        print("Warning: File is suspiciously small for an image")
    
    try:
        # Try to open the image
        img = Image.open(image_path)
        print(f"Image format: {img.format}")
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        
        # Try to perform OCR
        text = pytesseract.image_to_string(img)
        if text.strip():
            print(f"OCR succeeded. Extracted {len(text.strip())} characters.")
            print(f"Sample: {text.strip()[:50]}...")
        else:
            print("OCR succeeded but extracted no text.")
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_image(sys.argv[1])
    else:
        print("Usage: python test_image.py <path_to_image>") 