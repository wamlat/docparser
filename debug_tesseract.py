import os
import sys
import subprocess

# Path to tesseract
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("Tesseract OCR Diagnostic Tool")
print("-" * 40)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Checking Tesseract at: {tesseract_path}")

if os.path.exists(tesseract_path):
    print(f"✓ Tesseract executable found at: {tesseract_path}")
    
    # Try to execute tesseract directly
    try:
        result = subprocess.run([tesseract_path, '--version'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ Tesseract version output:\n{result.stdout}")
        else:
            print(f"✗ Tesseract returned error code: {result.returncode}")
            print(f"  Error: {result.stderr}")
    except Exception as e:
        print(f"✗ Failed to execute tesseract: {str(e)}")
else:
    print(f"✗ Tesseract executable NOT found at: {tesseract_path}")
    
# Check if directory exists
tesseract_dir = os.path.dirname(tesseract_path)
if os.path.isdir(tesseract_dir):
    print(f"✓ Tesseract directory exists: {tesseract_dir}")
    print("Files in directory:")
    for file in os.listdir(tesseract_dir):
        if file.endswith('.exe') or file.endswith('.dll'):
            print(f"  - {file}")
else:
    print(f"✗ Tesseract directory does NOT exist: {tesseract_dir}")

print("\nPossible solutions if Tesseract is not working:")
print("1. Reinstall Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
print("2. Make sure to add Tesseract to your PATH during installation")
print("3. Check that all required DLLs are present in the Tesseract directory")
print("4. Verify that the path in your code matches the actual installation path") 