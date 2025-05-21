import os
import mimetypes

def detect_file_type(file_path):
    """
    Detect file type based on extension.
    
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
        return 'pdf'
    
    # Check for image (png, jpg, jpeg)
    if extension in ['.png', '.jpg', '.jpeg']:
        return 'image'
    
    # Check for text file
    if extension == '.txt':
        return 'txt'
    
    # Unknown file type
    return 'unknown' 