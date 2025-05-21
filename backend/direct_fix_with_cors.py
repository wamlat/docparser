from flask import Flask, jsonify, request, send_from_directory, render_template_string
import os
import uuid
import json
import datetime
from flask_cors import CORS
from app.ocr import extract_text
from app.parser_v2 import parse_order_document  # Use the fixed parser

app = Flask(__name__)
# Enable CORS with explicit configuration
CORS(app, resources={r"/*": {
    "origins": "*",  # Allow all origins
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "expose_headers": ["Content-Disposition"]
}})

# Create necessary directories for uploaded files and parsed results
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'temp')
PARSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'parsed')

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, PARSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Document Parser API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
            h1 { color: #333; }
            .endpoint { background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .method { font-weight: bold; color: #0066cc; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Document Parser API</h1>
            <p>Welcome to the Document Parser API. Use the following endpoints:</p>
            
            <div class="endpoint">
                <span class="method">POST</span> /upload - Upload a document file
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> /parse - Parse the most recently uploaded document
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> /test - <a href="/test">Open test interface</a>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test')
def test_interface():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Parser Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .btn { background-color: #3498db; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
            .result { background-color: #f9f9f9; padding: 15px; border-radius: 4px; margin-top: 20px; }
            pre { white-space: pre-wrap; }
            table { width: 100%; border-collapse: collapse; }
            th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Document Parser Test Interface</h1>
        
        <div class="container">
            <h2>Upload Document</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="documentFile" accept=".pdf,.png,.jpg,.jpeg,.txt">
                <button class="btn" type="submit">Upload</button>
            </form>
            <div id="uploadResult" class="result" style="display: none;"></div>
        </div>
        
        <div class="container">
            <h2>Parse Document</h2>
            <button class="btn" id="parseBtn">Parse Latest Document</button>
            <div id="parseResult" class="result" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const fileInput = document.getElementById('documentFile');
                const resultDiv = document.getElementById('uploadResult');
                
                if (!fileInput.files.length) {
                    resultDiv.innerHTML = '<span style="color: red;">Please select a file first</span>';
                    resultDiv.style.display = 'block';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                resultDiv.innerHTML = 'Uploading...';
                resultDiv.style.display = 'block';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    resultDiv.innerHTML = '<span style="color: red;">Error: ' + error.message + '</span>';
                }
            });
            
            document.getElementById('parseBtn').addEventListener('click', async function() {
                const resultDiv = document.getElementById('parseResult');
                resultDiv.innerHTML = 'Parsing...';
                resultDiv.style.display = 'block';
                
                try {
                    // Add timestamp to avoid caching
                    const timestamp = new Date().getTime();
                    const response = await fetch(`/parse?t=${timestamp}`);
                    const data = await response.json();
                    
                    if (data.parsed_data) {
                        let html = '<h3>Parsed Results:</h3>';
                        
                        // Create table for general data
                        html += '<table>';
                        html += '<tr><th>Field</th><th>Value</th><th>Confidence</th></tr>';
                        
                        for (const [key, value] of Object.entries(data.parsed_data)) {
                            if (key !== 'line_items') {
                                html += `<tr>
                                    <td>${key}</td>
                                    <td>${value.value || ''}</td>
                                    <td>${value.confidence || 'N/A'}</td>
                                </tr>`;
                            }
                        }
                        html += '</table>';
                        
                        // Create table for line items if they exist
                        if (data.parsed_data.line_items && data.parsed_data.line_items.length > 0) {
                            html += '<h3>Line Items:</h3>';
                            html += '<table>';
                            html += '<tr><th>SKU</th><th>Quantity</th><th>Unit Price</th><th>Confidence</th></tr>';
                            
                            data.parsed_data.line_items.forEach(item => {
                                html += `<tr>
                                    <td>${item.sku || ''}</td>
                                    <td>${item.quantity || ''}</td>
                                    <td>${item.unit_price || ''}</td>
                                    <td>${item.confidence || 'N/A'}</td>
                                </tr>`;
                            });
                            html += '</table>';
                        } else {
                            html += '<p>No line items found</p>';
                        }
                        
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<span style="color: red;">Error: ' + error.message + '</span>';
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename with UUID
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = str(uuid.uuid4()) + file_extension
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Check file type by content
        if file_extension.lower() == '.pdf':
            if not os.path.getsize(file_path) > 0:
                return jsonify({"error": "Empty PDF file"}), 400
            print(f"Confirmed PDF file by content check: {file_path}")
        elif file_extension.lower() in ['.jpg', '.jpeg', '.png']:
            if not os.path.getsize(file_path) > 0:
                return jsonify({"error": "Empty image file"}), 400
            print(f"Confirmed image file: {file_path}")
        elif file_extension.lower() == '.txt':
            if not os.path.getsize(file_path) > 0:
                return jsonify({"error": "Empty text file"}), 400
            print(f"Confirmed text file: {file_path}")
        
        # Extract text with OCR and parse
        print(f"Processing file: {file.filename}")
        print(f"File saved to: {file_path}")
        
        extraction_result = extract_text(file_path)
        print(f"Extraction result: {extraction_result['success']}")
        
        if extraction_result['success']:
            # Parse directly for immediate response
            print("DIRECT FIX: Calling parser_v2.parse_order_document directly")
            parsed_data = parse_order_document(extraction_result['text'])
            return jsonify({
                "success": True,
                "filename": file.filename,
                "extraction_success": extraction_result['success'],
                "parsed_data": parsed_data
            })
        else:
            return jsonify({
                "success": False,
                "error": "Text extraction failed",
                "filename": file.filename
            }), 400
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/parse', methods=['GET'])
def parse_document():
    # Get the latest uploaded file
    try:
        files = os.listdir(UPLOAD_FOLDER)
        if not files:
            return jsonify({"error": "No uploaded files found"}), 404
        
        # Sort files by modification time (newest first)
        latest_file = sorted(
            [os.path.join(UPLOAD_FOLDER, f) for f in files],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )[0]
        
        # Extract text from the file
        extraction_result = extract_text(latest_file)
        
        if not extraction_result['success']:
            return jsonify({
                "success": False,
                "error": "Text extraction failed"
            }), 400
        
        # Parse the document
        print("DIRECT FIX: Calling parser_v2.parse_order_document from /parse endpoint")
        parsed_data = parse_order_document(extraction_result['text'])
        
        return jsonify({
            "success": True,
            "parsed_data": parsed_data
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

print("==== STARTING DOCUMENT PARSER SERVER ON PORT 5001 ====")
if __name__ == "__main__":
    # Run without debug mode and without auto-reloading
    app.run(debug=False, host='127.0.0.1', port=5001, use_reloader=False) 