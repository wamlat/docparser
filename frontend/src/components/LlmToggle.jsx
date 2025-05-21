import React, { useState, useEffect } from 'react';

function LlmToggle({ onToggle }) {
  const [isLlmEnabled, setIsLlmEnabled] = useState(false);

  useEffect(() => {
    // Check URL query parameter on component mount
    const queryParams = new URLSearchParams(window.location.search);
    const llmParam = queryParams.get('llm');
    if (llmParam === 'true') {
      setIsLlmEnabled(true);
    }
  }, []);

  const handleToggle = () => {
    const newValue = !isLlmEnabled;
    setIsLlmEnabled(newValue);
    
    // Update URL with query parameter
    const url = new URL(window.location);
    if (newValue) {
      url.searchParams.set('llm', 'true');
    } else {
      url.searchParams.delete('llm');
    }
    window.history.pushState({}, '', url);
    
    // Call parent callback
    if (onToggle) {
      onToggle(newValue);
    }
  };

  return (
    <div className="flex items-center space-x-2 my-2">
      <label htmlFor="llm-toggle" className="text-sm font-medium">
        LLM Mode: {isLlmEnabled ? 'ON' : 'OFF'}
      </label>
      <button
        id="llm-toggle"
        onClick={handleToggle}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
          isLlmEnabled ? 'bg-green-500' : 'bg-gray-300'
        }`}
      >
        <span className="sr-only">Use LLM Parser</span>
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            isLlmEnabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        ></span>
      </button>
      <span className="text-xs text-gray-500">
        {isLlmEnabled 
          ? 'Using GPT-3.5 Turbo for all documents' 
          : 'Using NER+regex with LLM fallback'}
      </span>
    </div>
  );
}

export default LlmToggle; 