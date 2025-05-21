from app import app
from flask import jsonify, request, send_from_directory
import os
import uuid
import werkzeug
from app.ocr import extract_text

# Create a temporary directory for uploaded files
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'temp')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        
        return jsonify({
            "file": os.path.basename(latest_file),
            "file_type": extraction_result['file_type'],
            "text": extraction_result['text'],
            "parsed_data": {
                # For now, just return the raw text
                # In the next phase, we'll implement actual parsing
                "raw_text": extraction_result['text']
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 