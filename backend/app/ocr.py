import pdfplumber
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
import os
import sys
from app.utils import detect_file_type

# Set Tesseract path for Windows
if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
        print(f"Processing image: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            return f"Error: Image file not found: {image_path}"
        
        # Check file size to detect non-image files
        file_size = os.path.getsize(image_path)
        print(f"Image file size: {file_size} bytes")
        
        if file_size < 100:
            # Try to read the file as text if it's suspiciously small for an image
            try:
                with open(image_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content and len(content) > 0:
                        print("File appears to be text, not an image. Returning content as is.")
                        return content
            except UnicodeDecodeError:
                # Not a text file, continue with image processing
                print("Not a text file, continuing with image processing")
                pass
        
        # Try a more robust way to open the image
        try:
            # Open the image using PIL with specific mode
            img = Image.open(image_path).convert('RGB')
            
            # Get image details for debugging
            print(f"Image format: {img.format}")
            print(f"Image size: {img.size}")
            print(f"Image mode: {img.mode}")
            
            # Enhance image for better OCR
            img = ImageOps.autocontrast(img)
            
            # Use pytesseract to extract text with improved configuration
            text = pytesseract.image_to_string(
                img,
                config='--psm 3 --oem 3'  # Page segmentation mode 3, OCR Engine mode 3
            )
            
            if not text or text.strip() == '':
                # Try a different psm mode
                print("No text found with first OCR attempt, trying different settings...")
                text = pytesseract.image_to_string(
                    img,
                    config='--psm 6 --oem 3'  # Page segmentation mode 6 (assume a single block of text)
                )
            
            if not text or text.strip() == '':
                return "Warning: No text was extracted from the image. The image may be blank or not contain readable text."
            
            return text
            
        except UnidentifiedImageError:
            print("UnidentifiedImageError: Cannot identify image format")
            
            # Check if this is actually a text file with wrong extension
            try:
                with open(image_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content and len(content) > 0:
                        print("File appears to be text, not an image. Returning content as is.")
                        return content
            except UnicodeDecodeError:
                # Not a text file
                pass
                
            return f"Error: Cannot identify image file format for {os.path.basename(image_path)}"
            
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract OCR is not installed or not in PATH. Please install Tesseract OCR."
    except Exception as e:
        # Handle any exceptions that might occur during OCR
        print(f"Error extracting text from image: {str(e)}")
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
    except UnicodeDecodeError:
        # Try different encodings if UTF-8 fails
        try:
            with open(txt_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            return f"Error reading text file with alternative encoding: {str(e)}"
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
        # Check if file exists
        if not os.path.exists(file_path):
            result['error'] = f"File not found: {file_path}"
            return result
        
        # Get file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            result['error'] = f"File is empty: {file_path}"
            return result
            
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
        
        # If text is empty but no error occurred, set a warning
        if result['success'] and not result['text'].strip():
            result['text'] = "No text content could be extracted from this file."
        
    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
    
    return result 