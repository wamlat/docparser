import React from 'react';

function ResultsDisplay({ parsedData, extractedText }) {
  if (!parsedData && !extractedText) {
    return null;
  }

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
    <div>
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
                href="http://localhost:5000/download"
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
  );
}

export default ResultsDisplay; 