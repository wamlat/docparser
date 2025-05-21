from app import app
from flask import jsonify, request, send_from_directory
import os
import uuid
import json
import datetime
import werkzeug
from app.ocr import extract_text
from app.parser import parse_order_document

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
    return jsonify({"message": "Hello, world!"})

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a unique filename to avoid collisions
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
        
        # Save the file to the upload folder
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Extract text from the uploaded file
        extraction_result = extract_text(file_path)
        
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
        
        # Parse the extracted text using NER
        parsed_data = parse_order_document(extraction_result['text'])
        
        # Save the parsed result to the parsed folder
        save_parsed_result(parsed_data, os.path.basename(latest_file))
        
        return jsonify({
            "file": os.path.basename(latest_file),
            "file_type": extraction_result['file_type'],
            "text": extraction_result['text'],
            "parsed_data": parsed_data
        })
        
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
        
        # Parse the extracted text using NER
        parsed_data = parse_order_document(extraction_result['text'])
        
        # Save the parsed result
        output_path = save_parsed_result(parsed_data, os.path.basename(latest_file))
        
        # Serve the file for download
        return send_from_directory(
            directory=PARSED_FOLDER,
            path=os.path.basename(output_path),
            as_attachment=True
        )
        
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