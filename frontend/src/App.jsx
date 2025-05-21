import React, { useState, useRef } from 'react';
import FileUpload from './components/FileUpload';
import ResultsDisplay from './components/ResultsDisplay';
import LlmToggle from './components/LlmToggle';
import './App.css';

// Using the Vite proxy configuration
const API_BASE_URL = '/api';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [parsedData, setParsedData] = useState(null);
  const [error, setError] = useState('');
  const [useLlm, setUseLlm] = useState(false);
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
      const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }
      
      // Then parse the document with the appropriate query parameter
      const parseUrl = new URL(`${API_BASE_URL}/parse`);
      parseUrl.searchParams.append('t', new Date().getTime()); // Cache busting
      if (useLlm) {
        parseUrl.searchParams.append('llm', 'true');
      }
      
      const parseResponse = await fetch(parseUrl);
      if (!parseResponse.ok) {
        throw new Error(`Parsing failed: ${parseResponse.statusText}`);
      }
      
      const result = await parseResponse.json();
      console.log('Parsed data:', result);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      setParsedData(result.parsed_data);
      setExtractedText(result.text);
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.response?.data?.error || 'An error occurred during processing');
    } finally {
      setUploading(false);
    }
  };

  const handleLlmToggle = (isEnabled) => {
    setUseLlm(isEnabled);
    console.log("LLM mode set to:", isEnabled);
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
        <LlmToggle onToggle={handleLlmToggle} />
        
        <FileUpload 
          file={file}
          setFile={setFile}
          onUpload={handleUpload}
          uploading={uploading}
        />
        
        {error && (
          <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        <ResultsDisplay 
          parsedData={parsedData}
          extractedText={extractedText}
        />
      </div>
    </div>
  );
}

export default App; 