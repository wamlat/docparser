from app.ocr import check_tesseract_installation
import json

def run_diagnostic():
    print("Running Tesseract diagnostic...")
    diagnostic_info = check_tesseract_installation()
    
    # Format the output nicely
    print("\nDiagnostic Results:")
    print(f"Tesseract Path: {diagnostic_info['tesseract_path']}")
    print(f"Tesseract Exists: {diagnostic_info['tesseract_exists']}")
    print(f"Directory Exists: {diagnostic_info['directory_exists']}")
    print(f"Version: {diagnostic_info['version']}")
    print(f"Error: {diagnostic_info['error']}")
    
    if diagnostic_info['executables_found']:
        print("\nExecutables found in directory:")
        for exe in diagnostic_info['executables_found']:
            print(f"  - {exe}")
    else:
        print("\nNo executables found in directory")
    
    # Print full diagnostic as JSON
    print("\nFull diagnostic information:")
    print(json.dumps(diagnostic_info, indent=2))
    
    # Print recommendations
    print("\nRecommendations:")
    if not diagnostic_info['tesseract_exists']:
        print("- Tesseract executable not found. Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Make sure to install it to the path specified in your code or update the path in your code")
    elif diagnostic_info['error']:
        print("- Tesseract is installed but there was an error running it")
        print("- Check that all required DLLs are in the Tesseract directory")
        print("- Try reinstalling Tesseract OCR and make sure to add it to your PATH during installation")
    else:
        print("- Tesseract appears to be correctly installed!")
        print("- If you're still having issues, check that the Python wrapper (pytesseract) is installed: pip install pytesseract")

if __name__ == "__main__":
    run_diagnostic() 