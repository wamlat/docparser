import
os
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(f'Checking if file exists: {tesseract_path}')
print(f'File exists: {os.path.exists(tesseract_path)}')
