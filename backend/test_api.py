import requests
import os
import json

def test_upload_and_parse():
    """Test the API by uploading a file and then parsing it."""
    # Path to test file
    txt_file = os.path.join('data', 'sample_docs', 'test.txt')
    
    if not os.path.exists(txt_file):
        print(f"Error: Test file {txt_file} not found")
        return False
    
    # Base URL
    base_url = 'http://localhost:5000'
    
    # Upload the file
    print(f"Uploading {txt_file}...")
    with open(txt_file, 'rb') as file:
        files = {'file': (os.path.basename(txt_file), file, 'text/plain')}
        response = requests.post(f"{base_url}/upload", files=files)
    
    # Check if upload was successful
    if response.status_code != 201:
        print(f"Error: Upload failed with status code {response.status_code}")
        print(response.text)
        return False
    
    upload_result = response.json()
    print(f"Upload successful.")
    print(f"File type detected: {upload_result['extraction']['file_type']}")
    print(f"Extraction success: {upload_result['extraction']['success']}")
    print(f"Text preview: {upload_result['extraction']['text'][:100]}...")
    print()
    
    # Access the parse endpoint
    print("Accessing /parse endpoint...")
    response = requests.get(f"{base_url}/parse")
    
    # Check if parse was successful
    if response.status_code != 200:
        print(f"Error: Parse failed with status code {response.status_code}")
        print(response.text)
        return False
    
    parse_result = response.json()
    print(f"Parse successful.")
    print(f"File: {parse_result['file']}")
    print(f"File type: {parse_result['file_type']}")
    print(f"Text preview: {parse_result['text'][:100]}...")
    
    return True

if __name__ == "__main__":
    test_upload_and_parse() 