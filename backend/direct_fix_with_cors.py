from flask import Flask, jsonify, request, send_from_directory
import os
import uuid
import json
import datetime
from flask_cors import CORS
from app.ocr import extract_text
from app.parser_v2 import parse_order_document  # Use the new parser directly

app = Flask(__name__)
# Enable CORS with explicit configuration
CORS(app, resources={r"/*": {
    "origins": "*",  # Allow all origins
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "expose_headers": ["Content-Disposition"],
    "supports_credentials": False,
    "max_age": 600
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
    return jsonify({"message": "Fixed parser server running. Use /upload endpoint to start."})

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
            
            # Generate a unique filename to avoid collisions
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{str(uuid.uuid4())}.{file_extension}"
            
            # Save the file to the upload folder
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            print(f"File saved to: {file_path}")
            
            # Extract text from the uploaded file
            extraction_result = extract_text(file_path)
            print(f"Extraction result: {extraction_result['success']}")
            
            # Immediately parse the document using the new parser_v2
            if extraction_result['success']:
                print("DIRECT FIX: Calling parser_v2.parse_order_document directly")
                parsed_data = parse_order_document(extraction_result['text'])
                
                # Save parsed result
                if parsed_data.get('order_id'):
                    output_filename = f"{parsed_data['order_id']}.json"
                else:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"{timestamp}_{unique_filename}.json"
                    
                output_path = os.path.join(PARSED_FOLDER, output_filename)
                with open(output_path, 'w') as f:
                    json.dump(parsed_data, f, indent=2)
                
                return jsonify({
                    "message": "FIXED PARSER: File processed successfully",
                    "filename": unique_filename,
                    "original_filename": file.filename,
                    "file_path": file_path,
                    "parsed_data": parsed_data,
                    "extraction": {
                        "success": extraction_result['success'],
                        "file_type": extraction_result['file_type'],
                        "text": extraction_result['text'][:500] + "..." if len(extraction_result['text']) > 500 else extraction_result['text']
                    }
                }), 200
            else:
                return jsonify({
                    "message": "File uploaded but text extraction failed",
                    "filename": unique_filename,
                    "original_filename": file.filename,
                    "file_path": file_path,
                    "extraction": {
                        "success": extraction_result['success'],
                        "file_type": extraction_result['file_type'],
                        "error": extraction_result['error']
                    }
                }), 400
            
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
        
        # Parse the extracted text using parser_v2
        print("DIRECT FIX: Calling parser_v2.parse_order_document from /parse endpoint")
        parsed_data = parse_order_document(extraction_result['text'])
        
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

# Serve the test HTML file
@app.route('/test', methods=['GET'])
def test_page():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'direct_test.html')

@app.route('/download', methods=['GET'])
def download_result():
    """Download the latest parsed result as a JSON file."""
    try:
        # Get the latest parsed result
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
        
        # Parse the extracted text using parser_v2
        parsed_data = parse_order_document(extraction_result['text'])
        
        # Create a filename for the parsed result
        if parsed_data.get('order_id'):
            output_filename = f"{parsed_data['order_id']}.json"
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{timestamp}_{os.path.basename(latest_file)}.json"
        
        # Save the parsed result
        output_path = os.path.join(PARSED_FOLDER, output_filename)
        with open(output_path, 'w') as f:
            json.dump(parsed_data, f, indent=2)
        
        # Serve the file for download
        return send_from_directory(
            directory=PARSED_FOLDER,
            path=output_filename,
            as_attachment=True
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n\n==== STARTING DIRECT FIX SERVER WITH CORS ON PORT 5001 ====\n")
    print("This is a completely separate server that directly uses parser_v2.py")
    print("Access test interface at: http://localhost:5001/test")
    print("Send files directly to: http://localhost:5001/upload\n\n")
    app.run(debug=True, port=5001)  # Use a different port 