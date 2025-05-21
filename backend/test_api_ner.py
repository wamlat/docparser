import requests
import os
import json

def test_ner_api():
    """Test the NER API integration"""
    print("===== TESTING NER API INTEGRATION =====")
    
    # Path to test file
    txt_file = os.path.join('data', 'sample_docs', 'test.txt')
    
    if not os.path.exists(txt_file):
        print(f"Error: Test file {txt_file} not found")
        return False
    
    # Base URL
    base_url = 'http://localhost:5000'
    
    # 1. Upload the file
    print(f"\n1. Uploading {txt_file}...")
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
    
    # 2. Parse the uploaded document
    print("\n2. Parsing the uploaded document...")
    response = requests.get(f"{base_url}/parse")
    
    # Check if parse was successful
    if response.status_code != 200:
        print(f"Error: Parse failed with status code {response.status_code}")
        print(response.text)
        return False
    
    parse_result = response.json()
    
    print("Parse successful. Structured data:")
    print(json.dumps(parse_result["parsed_data"], indent=2))
    
    # Verify that we have some structured data
    parsed_data = parse_result["parsed_data"]
    if not parsed_data.get("customer") and not parsed_data.get("order_id") and not parsed_data.get("line_items"):
        print("Warning: Parsed data is missing key fields")
    
    # 3. Download the result as JSON
    print("\n3. Downloading the result as JSON...")
    response = requests.get(f"{base_url}/download", stream=True)
    
    # Check if download was successful
    if response.status_code != 200:
        print(f"Error: Download failed with status code {response.status_code}")
        print(response.text)
        return False
    
    # Save the downloaded file
    download_path = os.path.join('data', 'temp', 'api_test_result.json')
    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
    print(f"Downloaded result saved to {download_path}")
    
    # Load and verify the downloaded JSON
    with open(download_path, 'r') as f:
        json_data = json.load(f)
    
    print("Downloaded JSON content:")
    print(json.dumps(json_data, indent=2))
    
    print("\n===== NER API INTEGRATION TEST COMPLETE =====")
    return True

if __name__ == "__main__":
    test_ner_api() 