import pdfplumber
import pytesseract
from PIL import Image
import os
from app.utils import detect_file_type

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
        # Open the image using PIL
        img = Image.open(image_path)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(img)
        
        return text
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract OCR is not installed or not in PATH. Please install Tesseract OCR."
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