from app.ocr import extract_text_from_txt
import os

def test_txt_extraction():
    # Path to test.txt in sample_docs
    txt_file = os.path.join('data', 'sample_docs', 'test.txt')
    
    # Make sure the file exists
    if not os.path.exists(txt_file):
        print(f"Error: Test file {txt_file} not found")
        return False
    
    print(f"Extracting text from {txt_file}...")
    
    # Extract text
    extracted_text = extract_text_from_txt(txt_file)
    
    print("\nExtracted Text:")
    print("-" * 50)
    print(extracted_text)
    print("-" * 50)
    
    # Verify text extraction
    success = all(keyword in extracted_text for keyword in 
                 ["Order ID: TEST123", "John Doe", "ABC-001"])
    
    print(f"\nExtraction {'successful' if success else 'failed'}")
    
    return success

if __name__ == "__main__":
    test_txt_extraction() 