import os
import mimetypes

def detect_file_type(file_path):
    """
    Detect file type based on extension and basic content checking.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: 'pdf', 'image', 'txt', or 'unknown'
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")
    
    # Get file extension (lowercase)
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    
    # Check for PDF
    if extension == '.pdf':
        # Optionally check first few bytes for %PDF header
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    print(f"Confirmed PDF file by content check: {file_path}")
                else:
                    print(f"Warning: File has .pdf extension but doesn't start with %PDF: {file_path}")
        except Exception as e:
            print(f"Warning: Could not check PDF content: {str(e)}")
        return 'pdf'
    
    # Check for image (png, jpg, jpeg)
    if extension in ['.png', '.jpg', '.jpeg']:
        # Don't try to validate image content here - let PIL handle that in OCR function
        return 'image'
    
    # Check for text file
    if extension == '.txt':
        # Try to read the file as text to validate
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(100)  # Just read a bit to check if it's text
                print(f"Confirmed text file: {file_path}")
        except Exception as e:
            print(f"Warning: File has .txt extension but might not be a text file: {str(e)}")
        return 'txt'
    
    # Try to guess based on file content for unknown extensions
    try:
        # Check if it might be text
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100)
            if all(c.isprintable() or c.isspace() for c in content):
                print(f"File appears to be text based on content: {file_path}")
                return 'txt'
    except Exception:
        pass
    
    # Check if it might be PDF
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header == b'%PDF':
                print(f"File appears to be PDF based on content: {file_path}")
                return 'pdf'
    except Exception:
        pass
    
    # Unknown file type
    print(f"Unknown file type: {file_path} with extension {extension}")
    return 'unknown' 