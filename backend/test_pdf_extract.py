from app.ocr import extract_text_from_pdf
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf(pdf_path):
    """Create a test PDF file with some order data."""
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Add text to the PDF
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Test Order Document")
    c.drawString(100, 730, "Order ID: PDF-123")
    c.drawString(100, 710, "Customer: Jane Smith")
    c.drawString(100, 690, "Items:")
    c.drawString(120, 670, "SKU: PDF-001, Quantity: 3, Price: $20.00")
    c.drawString(120, 650, "SKU: PDF-002, Quantity: 1, Price: $45.75")
    c.drawString(100, 630, "Shipping Address: 456 Oak St, Somewhere, USA 54321")
    
    # Add a second page with more data
    c.showPage()
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Additional Order Notes")
    c.drawString(100, 730, "Please deliver after 6 PM")
    c.drawString(100, 710, "Customer phone: 555-123-4567")
    
    c.save()

def test_pdf_extraction():
    # Path to sample documents directory
    sample_docs_dir = os.path.join('data', 'sample_docs')
    
    # Create test PDF
    pdf_file = os.path.join(sample_docs_dir, 'test_order.pdf')
    create_test_pdf(pdf_file)
    
    print(f"Created test PDF at {pdf_file}")
    print("\nExtracting text from PDF...")
    
    # Extract text from the PDF
    extracted_text = extract_text_from_pdf(pdf_file)
    
    print("\nExtracted Text:")
    print("-" * 50)
    print(extracted_text)
    print("-" * 50)
    
    # Verify text extraction worked properly
    success = all(keyword in extracted_text for keyword in 
                 ["Order ID: PDF-123", "Jane Smith", "PDF-001", "456 Oak St", "Additional Order Notes"])
    
    print(f"\nExtraction {'successful' if success else 'failed'}")
    
    return success

if __name__ == "__main__":
    # Add reportlab to requirements if needed
    try:
        from reportlab.pdfgen import canvas
    except ImportError:
        print("Installing reportlab...")
        import subprocess
        subprocess.check_call(["pip", "install", "reportlab"])
    
    test_pdf_extraction() 