from app import app
from flask import jsonify, request, send_from_directory, render_template_string
import os
import uuid
import json
import datetime
import werkzeug
import importlib
from app.ocr import extract_text
# Import parser only when needed to avoid circular imports

# Create necessary directories for uploaded files and parsed results
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'temp')
PARSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'parsed')

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
    # Simple test interface for the API
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Order Document Parser Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #2c3e50;
            }
            .container {
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .btn {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }
            .result {
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
            }
            .debug {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 4px;
                white-space: pre-wrap;
                font-family: monospace;
                font-size: 12px;
                margin-top: 20px;
                max-height: 300px;
                overflow: auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Direct API Order Document Parser</h1>
        <div class="container">
            <h2>Upload Order Document</h2>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" id="fileInput" name="file" accept=".pdf,.png,.jpg,.jpeg,.txt">
                </div>
                <button type="submit" class="btn">Upload & Parse</button>
            </form>
        </div>

        <div class="result" id="result" style="display: none;">
            <h2>Parsed Data</h2>
            <div>
                <strong>Customer:</strong> <span id="customer"></span>
            </div>
            <div>
                <strong>Order ID:</strong> <span id="orderId"></span>
            </div>
            <div>
                <strong>Shipping Address:</strong> <span id="address"></span>
            </div>
            <h3>Line Items</h3>
            <table id="lineItems">
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Quantity</th>
                        <th>Price</th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
        </div>

        <div class="debug" id="debug" style="display: none;"></div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', function(event) {
                event.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file to upload');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                // First upload the file
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Upload:', data);
                    
                    // Then parse the document
                    return fetch('/parse');
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Parse:', data);
                    displayResults(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('debug').innerText = 'Error: ' + error.message;
                    document.getElementById('debug').style.display = 'block';
                });
            });
            
            function displayResults(data) {
                if (data.parsed_data) {
                    // Display parsed data
                    document.getElementById('customer').innerText = data.parsed_data.customer || 'N/A';
                    document.getElementById('orderId').innerText = data.parsed_data.order_id || 'N/A';
                    document.getElementById('address').innerText = data.parsed_data.shipping_address || 'N/A';
                    
                    // Display line items
                    const tableBody = document.getElementById('lineItems').getElementsByTagName('tbody')[0];
                    tableBody.innerHTML = '';
                    
                    if (data.parsed_data.line_items && data.parsed_data.line_items.length > 0) {
                        data.parsed_data.line_items.forEach(item => {
                            const row = tableBody.insertRow();
                            
                            const skuCell = row.insertCell();
                            skuCell.innerText = item.sku || 'N/A';
                            
                            const qtyCell = row.insertCell();
                            qtyCell.innerText = item.quantity || 'N/A';
                            
                            const priceCell = row.insertCell();
                            priceCell.innerText = item.price ? '$' + item.price : 'N/A';
                        });
                    } else {
                        const row = tableBody.insertRow();
                        const cell = row.insertCell();
                        cell.colSpan = 3;
                        cell.innerText = 'No line items found';
                    }
                    
                    document.getElementById('result').style.display = 'block';
                }
                
                // Display debug info
                document.getElementById('debug').innerText = JSON.stringify(data, null, 2);
                document.getElementById('debug').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        print("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        print("No selected filename")
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        try:
            print(f"Processing file: {file.filename}")
            
            # Read file content, but allow empty files
            file_content = file.read(1024)  # Read only the first 1024 bytes to check
            file.seek(0)  # Reset file pointer for later use
            
            # Generate a unique filename to avoid collisions
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
            
            # Save the file to the upload folder without content validation
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            print(f"File saved to: {file_path}")
            
            # Extract text from the uploaded file
            extraction_result = extract_text(file_path)
            print(f"Extraction result: {extraction_result['success']}")
            
            return jsonify({
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "original_filename": file.filename,
                "file_path": file_path,
                "extraction": {
                    "success": extraction_result['success'],
                    "file_type": extraction_result['file_type'],
                    "text": extraction_result['text'][:1000] + "..." if len(extraction_result['text']) > 1000 else extraction_result['text'],
                    "error": extraction_result['error']
                }
            }), 201
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    
    print(f"File type not allowed: {file.filename}")
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
                "error": "Text extraction failed",
                "details": extraction_result['error']
            }), 500
        
        # Import parser module to ensure latest code is used
        print("Importing and reloading parser_v2 module... FORCED RELOAD")
        import sys
        if 'app.parser_v2' in sys.modules:
            del sys.modules['app.parser_v2']
        import app.parser_v2
        importlib.reload(app.parser_v2)
        from app.parser_v2 import parse_order_document
        
        # Parse the extracted text using NER
        parsed_data = parse_order_document(extraction_result['text'])
        
        # Save the parsed result to the parsed folder
        save_parsed_result(parsed_data, os.path.basename(latest_file))
        
        # Create response with no-cache headers
        response = jsonify({
            "file": os.path.basename(latest_file),
            "file_type": extraction_result['file_type'],
            "text": extraction_result['text'],
            "parsed_data": parsed_data,
            "timestamp": datetime.datetime.now().isoformat()  # Add timestamp to ensure it's fresh
        })
        
        # Set cache prevention headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def save_parsed_result(parsed_data, original_filename):
    """
    Save the parsed result to a JSON file in the parsed folder.
    
    Args:
        parsed_data (dict): The structured data parsed from the document
        original_filename (str): The name of the original file that was parsed
    
    Returns:
        str: The path of the saved JSON file
    """
    # Use order_id as filename if available, otherwise use timestamp
    if parsed_data.get('order_id'):
        filename = f"{parsed_data['order_id']}.json"
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{original_filename}.json"
    
    # Save the file
    output_path = os.path.join(PARSED_FOLDER, filename)
    with open(output_path, 'w') as f:
        json.dump(parsed_data, f, indent=2)
    
    return output_path

@app.route('/download', methods=['GET'])
def download_result():
    """Download the latest parsed result as a JSON file."""
    try:
        # Get the latest parsed result (reusing parse_document logic)
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
                "error": "Text extraction failed",
                "details": extraction_result['error']
            }), 500
        
        # Import parser module to ensure latest code is used
        print("Importing and reloading parser_v2 module... FORCED RELOAD")
        import sys
        if 'app.parser_v2' in sys.modules:
            del sys.modules['app.parser_v2']
        import app.parser_v2
        importlib.reload(app.parser_v2)
        from app.parser_v2 import parse_order_document
        
        # Parse the extracted text using NER
        parsed_data = parse_order_document(extraction_result['text'])
        
        # Save the parsed result
        output_path = save_parsed_result(parsed_data, os.path.basename(latest_file))
        
        # Serve the file for download
        response = send_from_directory(
            directory=PARSED_FOLDER,
            path=os.path.basename(output_path),
            as_attachment=True
        )
        
        # Set cache prevention headers
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/results', methods=['GET'])
def list_results():
    """List all available parsed results."""
    try:
        # Get all JSON files in the parsed folder
        files = [f for f in os.listdir(PARSED_FOLDER) if f.endswith('.json')]
        
        # Sort files by modification time (newest first)
        sorted_files = sorted(
            [os.path.join(PARSED_FOLDER, f) for f in files],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )
        
        # Extract metadata for each file
        results = []
        for file_path in sorted_files:
            filename = os.path.basename(file_path)
            modified_time = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Try to get order_id from the file contents
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    order_id = data.get('order_id', 'Unknown')
                    customer = data.get('customer', 'Unknown')
            except:
                order_id = 'Error reading file'
                customer = 'Error reading file'
            
            results.append({
                "filename": filename,
                "order_id": order_id,
                "customer": customer,
                "timestamp": modified_time,
                "download_url": f"/download/{filename}"
            })
        
        return jsonify({
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_specific_result(filename):
    """Download a specific parsed result by filename."""
    try:
        file_path = os.path.join(PARSED_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file for download
        return send_from_directory(
            directory=PARSED_FOLDER,
            path=filename,
            as_attachment=True
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 