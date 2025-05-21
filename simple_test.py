import os
import sys

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print(f"Python version: {sys.version}")
print(f"Checking if file exists at: {tesseract_path}")

if os.path.isfile(tesseract_path):
    print(f"File exists!")
else:
    print(f"File does NOT exist!") 