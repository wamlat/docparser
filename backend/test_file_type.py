from app.utils import detect_file_type
import os

def test_file_type_detection():
    # Get path to sample documents
    sample_docs_dir = os.path.join('data', 'sample_docs')
    
    # Test with text file
    txt_file = os.path.join(sample_docs_dir, 'test.txt')
    print(f"Testing with {txt_file}")
    print(f"Detected file type: {detect_file_type(txt_file)}")
    print()
    
    # Create test files for other types if they don't exist
    # Test with fake PDF file
    pdf_file = os.path.join(sample_docs_dir, 'test.pdf')
    if not os.path.exists(pdf_file):
        with open(pdf_file, 'w') as f:
            f.write("Fake PDF content")
    
    print(f"Testing with {pdf_file}")
    print(f"Detected file type: {detect_file_type(pdf_file)}")
    print()
    
    # Test with fake PNG file
    png_file = os.path.join(sample_docs_dir, 'test.png')
    if not os.path.exists(png_file):
        with open(png_file, 'w') as f:
            f.write("Fake PNG content")
    
    print(f"Testing with {png_file}")
    print(f"Detected file type: {detect_file_type(png_file)}")
    print()
    
    # Test with fake JPG file
    jpg_file = os.path.join(sample_docs_dir, 'test.jpg')
    if not os.path.exists(jpg_file):
        with open(jpg_file, 'w') as f:
            f.write("Fake JPG content")
    
    print(f"Testing with {jpg_file}")
    print(f"Detected file type: {detect_file_type(jpg_file)}")
    print()
    
    # Test with unknown file type
    unknown_file = os.path.join(sample_docs_dir, 'test.xyz')
    if not os.path.exists(unknown_file):
        with open(unknown_file, 'w') as f:
            f.write("Unknown file type content")
    
    print(f"Testing with {unknown_file}")
    print(f"Detected file type: {detect_file_type(unknown_file)}")

if __name__ == "__main__":
    test_file_type_detection() 