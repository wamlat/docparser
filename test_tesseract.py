import pytesseract
import sys
import os

# Set the path explicitly
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def check_tesseract():
    print(f"Python version: {sys.version}")
    print(f"Checking if Tesseract exists at: {tesseract_path}")
    
    # Check if the file exists
    if os.path.isfile(tesseract_path):
        print(f"✓ File exists at the specified path")
    else:
        print(f"✗ File does NOT exist at the specified path")
        return False
    
    # Try to get Tesseract version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"✗ Error getting Tesseract version: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running Tesseract OCR diagnostic test...\n")
    if check_tesseract():
        print("\nTesseract is properly configured!")
    else:
        print("\nTesseract configuration failed. Please check your installation and path settings.")
        print("Make sure the tesseract.exe is at the specified path and the required DLLs are available.") 