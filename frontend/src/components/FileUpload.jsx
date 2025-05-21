import React, { useRef } from 'react';

function FileUpload({ file, setFile, onUpload, uploading }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div>
      <div 
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <p className="text-gray-500 mb-2">
          {file ? `Selected file: ${file.name}` : 'Drag and drop your document here'}
        </p>
        <p className="text-gray-400 text-sm">Supported formats: PDF, PNG, JPG, TXT</p>
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileChange} 
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          className="hidden" 
        />
        <button 
          className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
        >
          Or select a file
        </button>
      </div>
      
      <div className="mt-4 flex justify-center">
        <button 
          className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded disabled:bg-gray-300"
          onClick={onUpload}
          disabled={!file || uploading}
        >
          {uploading ? 'Processing...' : 'Upload & Parse'}
        </button>
      </div>
    </div>
  );
}

export default FileUpload; 