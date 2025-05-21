import os
import sys
import pytesseract
from PIL import Image, ImageOps
import argparse

# Set Tesseract path for Windows
if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_image_ocr(image_path):
    """Test OCR on a single image file."""
    print(f"Testing OCR on image: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return
    
    try:
        print("Attempting to open and process image...")
        
        # Try different methods
        methods = [
            ("RGB", "Default"),
            ("L", "Grayscale"),
            ("1", "Black and White"),
            ("RGB", "Auto Contrast")
        ]
        
        for mode, desc in methods:
            print(f"\nTrying {desc} mode ({mode})...")
            try:
                # Open image
                img = Image.open(image_path).convert(mode)
                
                # Apply enhancement for auto contrast method
                if desc == "Auto Contrast":
                    img = ImageOps.autocontrast(img)
                    print("  - Applied auto contrast")
                
                # Save a copy for debugging
                debug_dir = "debug_images"
                os.makedirs(debug_dir, exist_ok=True)
                debug_path = os.path.join(debug_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}_{desc}.png")
                img.save(debug_path)
                print(f"  - Saved debug image to {debug_path}")
                
                # Process with different PSM modes
                psm_modes = [3, 6, 4, 1]
                
                for psm in psm_modes:
                    print(f"  - Using PSM mode {psm}...")
                    text = pytesseract.image_to_string(
                        img,
                        config=f'--psm {psm} --oem 3'
                    )
                    
                    # Show preview of extracted text
                    preview = text.strip()[:100] + "..." if len(text.strip()) > 100 else text.strip()
                    print(f"    Result: {'No text extracted' if not preview else preview}")
                    print(f"    Text length: {len(text.strip())}")
                
            except Exception as e:
                print(f"  - Error with {desc} mode: {str(e)}")
        
    except Exception as e:
        print(f"Overall error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Test OCR on image files')
    parser.add_argument('image_path', nargs='?', help='Path to the image file to test')
    
    args = parser.parse_args()
    
    # If no image path is provided, check if there are images in the data directory
    if not args.image_path:
        data_dirs = [
            os.path.join('data', 'temp'),
            os.path.join('data', 'sample_docs'),
            'data'
        ]
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                print(f"Looking for images in {data_dir}...")
                for file in os.listdir(data_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_path = os.path.join(data_dir, file)
                        print(f"Found image: {image_path}")
                        test_image_ocr(image_path)
                        return
        
        print("No image path provided and no images found in default directories.")
        print("Usage: python test_image_ocr.py [path_to_image]")
        return
    
    test_image_ocr(args.image_path)

if __name__ == "__main__":
    main() 