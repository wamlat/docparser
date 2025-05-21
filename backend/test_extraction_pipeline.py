from app.ocr import extract_text
import os

def test_extraction_pipeline():
    """Test the unified text extraction pipeline with different file types."""
    # Path to sample documents directory
    sample_docs_dir = os.path.join('data', 'sample_docs')
    
    # Test with text file
    txt_file = os.path.join(sample_docs_dir, 'test.txt')
    pdf_file = os.path.join(sample_docs_dir, 'test_order.pdf')
    
    if not os.path.exists(txt_file):
        print(f"Error: Test file {txt_file} not found")
        return False
    
    if not os.path.exists(pdf_file):
        print(f"Error: Test file {pdf_file} not found")
        print("Please run test_pdf_extract.py first to create the test PDF")
        return False
    
    # Test text file extraction
    print(f"Testing extraction from text file: {txt_file}")
    txt_result = extract_text(txt_file)
    print(f"File type detected: {txt_result['file_type']}")
    print(f"Extraction successful: {txt_result['success']}")
    if not txt_result['success']:
        print(f"Error: {txt_result['error']}")
    else:
        print(f"First 100 chars of extracted text: {txt_result['text'][:100]}...")
    print()
    
    # Test PDF file extraction
    print(f"Testing extraction from PDF file: {pdf_file}")
    pdf_result = extract_text(pdf_file)
    print(f"File type detected: {pdf_result['file_type']}")
    print(f"Extraction successful: {pdf_result['success']}")
    if not pdf_result['success']:
        print(f"Error: {pdf_result['error']}")
    else:
        print(f"First 100 chars of extracted text: {pdf_result['text'][:100]}...")
    print()
    
    # Test with an unknown file type
    unknown_file = os.path.join(sample_docs_dir, 'test.xyz')
    if os.path.exists(unknown_file):
        print(f"Testing extraction from unknown file type: {unknown_file}")
        unknown_result = extract_text(unknown_file)
        print(f"File type detected: {unknown_result['file_type']}")
        print(f"Extraction successful: {unknown_result['success']}")
        if not unknown_result['success']:
            print(f"Error: {unknown_result['error']}")
        print()
    
    # Test with image would depend on Tesseract installation
    # We'll check if the test_order.png exists and try it
    img_file = os.path.join(sample_docs_dir, 'test_order.png')
    if os.path.exists(img_file):
        print(f"Testing extraction from image file: {img_file}")
        img_result = extract_text(img_file)
        print(f"File type detected: {img_result['file_type']}")
        print(f"Extraction successful: {img_result['success']}")
        if not img_result['success']:
            print(f"Error: {img_result['error']}")
        else:
            print(f"First 100 chars of extracted text: {img_result['text'][:100]}...")
    
    # Overall success: both PDF and TXT extraction succeeded
    return txt_result['success'] and pdf_result['success']

if __name__ == "__main__":
    test_extraction_pipeline() 