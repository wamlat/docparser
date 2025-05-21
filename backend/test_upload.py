import requests
import os

def test_upload():
    # Path to the test file
    file_path = os.path.join('data', 'sample_docs', 'test.txt')
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return
    
    # URL for the upload endpoint
    url = 'http://localhost:5000/upload'
    
    # Open the file in binary mode
    with open(file_path, 'rb') as file:
        # Create a files dictionary for the request
        files = {'file': (os.path.basename(file_path), file, 'text/plain')}
        
        # Make the POST request
        response = requests.post(url, files=files)
        
        # Print the response status code and content
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_upload() 