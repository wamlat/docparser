import React, { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [parsedData, setParsedData] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
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
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setError('');

    try {
      // Upload the file
      const uploadResponse = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      console.log('Upload response:', uploadResponse.data);
      setExtractedText(uploadResponse.data.extraction.text);

      // Parse the document
      const parseResponse = await axios.get(`${API_BASE_URL}/parse`);
      console.log('Parse response:', parseResponse.data);
      setParsedData(parseResponse.data.parsed_data);
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.response?.data?.error || 'An error occurred during processing');
    } finally {
      setUploading(false);
    }
  };

  const hasWarnings = (item) => {
    if (!parsedData?.extraction_details) return false;
    
    // Check if any fields in this item have warnings
    const details = parsedData.extraction_details;
    return Object.values(details).some(field => field.warning === true);
  };

  const getFieldWarningClass = (fieldName) => {
    if (!parsedData?.extraction_details) return '';
    const details = parsedData.extraction_details;
    
    if (details[fieldName]?.warning) {
      return 'bg-yellow-100 border-yellow-300';
    }
    return '';
  };

  const getLineItemWarningClass = (item, fieldName) => {
    if (!item[fieldName]?.warning) return '';
    return 'bg-yellow-100 border-yellow-300';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">Intelligent Order Document Parser</h1>
      
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-6">
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
        
        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        <div className="mt-4 flex justify-center">
          <button 
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded disabled:bg-gray-300"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Processing...' : 'Upload & Parse'}
          </button>
        </div>
        
        {extractedText && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-2">Extracted Text</h2>
            <div className="border rounded-lg p-4 bg-gray-50">
              <pre className="whitespace-pre-wrap text-sm">{extractedText}</pre>
            </div>
          </div>
        )}
        
        {parsedData && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-2">Parsed Data</h2>
            <div className="border rounded-lg p-4 bg-gray-50">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className={`p-2 border rounded ${getFieldWarningClass('customer')}`}>
                  <strong>Customer:</strong> {parsedData.customer}
                  {parsedData.extraction_details?.customer?.warning && (
                    <span className="ml-2 text-yellow-600 text-xs">⚠️ Low confidence</span>
                  )}
                </div>
                <div className={`p-2 border rounded ${getFieldWarningClass('order_id')}`}>
                  <strong>Order ID:</strong> {parsedData.order_id}
                  {parsedData.extraction_details?.order_id?.warning && (
                    <span className="ml-2 text-yellow-600 text-xs">⚠️ Low confidence</span>
                  )}
                </div>
                <div className={`p-2 border rounded col-span-2 ${getFieldWarningClass('shipping_address')}`}>
                  <strong>Shipping Address:</strong> {parsedData.shipping_address}
                  {parsedData.extraction_details?.shipping_address?.warning && (
                    <span className="ml-2 text-yellow-600 text-xs">⚠️ Low confidence</span>
                  )}
                </div>
              </div>
              
              <h3 className="font-semibold mb-2">Line Items</h3>
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-200">
                    <th className="border p-2 text-left">SKU</th>
                    <th className="border p-2 text-left">Quantity</th>
                    <th className="border p-2 text-left">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedData.line_items.map((item, index) => (
                    <tr key={index}>
                      <td className={`border p-2 ${getLineItemWarningClass(parsedData.extraction_details?.line_items[index], 'sku')}`}>
                        {item.sku}
                        {parsedData.extraction_details?.line_items[index]?.sku?.warning && (
                          <span className="ml-2 text-yellow-600 text-xs">⚠️</span>
                        )}
                      </td>
                      <td className={`border p-2 ${getLineItemWarningClass(parsedData.extraction_details?.line_items[index], 'quantity')}`}>
                        {item.quantity}
                        {parsedData.extraction_details?.line_items[index]?.quantity?.warning && (
                          <span className="ml-2 text-yellow-600 text-xs">⚠️</span>
                        )}
                      </td>
                      <td className={`border p-2 ${getLineItemWarningClass(parsedData.extraction_details?.line_items[index], 'price')}`}>
                        ${item.price.toFixed(2)}
                        {parsedData.extraction_details?.line_items[index]?.price?.warning && (
                          <span className="ml-2 text-yellow-600 text-xs">⚠️</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              <div className="mt-4">
                <strong>Overall Confidence:</strong> 
                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1">
                  <div 
                    className={`h-2.5 rounded-full ${
                      parsedData.confidence.overall >= 0.8 ? 'bg-green-500' :
                      parsedData.confidence.overall >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${parsedData.confidence.overall * 100}%` }}
                  ></div>
                </div>
                <div className="text-right text-sm text-gray-500">
                  {(parsedData.confidence.overall * 100).toFixed(0)}%
                </div>
              </div>
              
              <div className="mt-4 flex justify-end">
                <a 
                  href={`${API_BASE_URL}/download`}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Download JSON
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 