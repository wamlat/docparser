import pdfplumber
import pytesseract
from PIL import Image
import os
import sys
import subprocess
from app.utils import detect_file_type

# Configure Tesseract path - update this path to where you installed Tesseract
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Diagnostic function to check Tesseract installation
def check_tesseract_installation():
    diagnostic_info = {
        "tesseract_exists": False,
        "tesseract_path": tesseract_path,
        "version": None,
        "error": None,
        "directory_exists": False,
        "executables_found": []
    }
    
    # Check if tesseract executable exists
    if os.path.exists(tesseract_path):
        diagnostic_info["tesseract_exists"] = True
        
        # Try to execute tesseract to get version
        try:
            result = subprocess.run([tesseract_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                diagnostic_info["version"] = result.stdout.strip()
            else:
                diagnostic_info["error"] = f"Error running tesseract: {result.stderr}"
        except Exception as e:
            diagnostic_info["error"] = f"Exception when running tesseract: {str(e)}"
    
    # Check directory
    tesseract_dir = os.path.dirname(tesseract_path)
    if os.path.isdir(tesseract_dir):
        diagnostic_info["directory_exists"] = True
        
        # List executables in directory
        for file in os.listdir(tesseract_dir):
            if file.endswith('.exe') or file.endswith('.dll'):
                diagnostic_info["executables_found"].append(file)
    
    return diagnostic_info

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from all pages
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from each page
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
    except Exception as e:
        # Handle any exceptions that might occur during PDF processing
        text = f"Error extracting text from PDF: {str(e)}"
    
    return text

def extract_text_from_image(image_path):
    """
    Extract text from an image file using Tesseract OCR.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # First check if Tesseract is properly installed
        diagnostic = check_tesseract_installation()
        if not diagnostic["tesseract_exists"]:
            return f"Error: Tesseract executable not found at {tesseract_path}. Diagnostic info: {diagnostic}"
        
        if diagnostic["error"]:
            return f"Error: Tesseract is installed but not working correctly. {diagnostic['error']}. Diagnostic info: {diagnostic}"
        
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(img)
        
        return text
    except pytesseract.TesseractNotFoundError:
        diagnostic = check_tesseract_installation()
        return f"Error: Tesseract OCR is not installed or not in PATH. Diagnostic info: {diagnostic}"
    except Exception as e:
        # Handle any exceptions that might occur during OCR
        return f"Error extracting text from image: {str(e)}"

def extract_text_from_txt(txt_path):
    """
    Extract text from a plain text file.
    
    Args:
        txt_path (str): Path to the text file
        
    Returns:
        str: Content of the text file
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        # Handle any exceptions that might occur when reading the file
        return f"Error reading text file: {str(e)}"

def extract_text(file_path):
    """
    Unified text extraction pipeline - determines file type and uses the appropriate extraction method.
    
    Args:
        file_path (str): Path to the file to extract text from
        
    Returns:
        dict: Dictionary containing the extracted text and metadata
              {
                  'text': 'extracted text content',
                  'file_type': 'pdf|image|txt',
                  'success': True|False,
                  'error': 'error message if any'
              }
    """
    result = {
        'text': '',
        'file_type': 'unknown',
        'success': False,
        'error': None
    }
    
    try:
        # Detect file type
        file_type = detect_file_type(file_path)
        result['file_type'] = file_type
        
        # Extract text based on file type
        if file_type == 'pdf':
            result['text'] = extract_text_from_pdf(file_path)
            result['success'] = not result['text'].startswith('Error')
        elif file_type == 'image':
            result['text'] = extract_text_from_image(file_path)
            result['success'] = not result['text'].startswith('Error')
        elif file_type == 'txt':
            result['text'] = extract_text_from_txt(file_path)
            result['success'] = not result['text'].startswith('Error')
        else:
            result['error'] = f"Unsupported file type: {file_type}"
            return result
        
        # Check if extraction was successful
        if not result['success']:
            result['error'] = result['text']
        
    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
    
    return result 