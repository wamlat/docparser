# 📄 Intelligent Order Document Parser

A powerful document parsing system for extracting structured data from order documents in various formats (PDF, images, text files).

## 🚀 Features

- **Multi-format Support**: Process PDF, PNG, JPG, and TXT files
- **OCR Integration**: Extract text from images and scanned PDFs using Tesseract OCR
- **Intelligent Entity Recognition**: Use NER (Named Entity Recognition) with a BERT-based model
- **Regex Pattern Fallbacks**: Reliable extraction of common patterns when NER fails
- **Confidence Scoring**: Evaluate extraction reliability with confidence scores
- **Warning Flags**: Low confidence extractions are clearly marked
- **Persistent Storage**: Save results for future reference and analysis
- **API Endpoints**: Upload, parse, list, and download processed documents
- **User Interface**: Modern React frontend for visualization and interaction

## 🔧 Prerequisites

- Python 3.8+
- Node.js 16+
- Tesseract OCR ([Installation instructions](#tesseract-installation))
- Docker (optional for containerized deployment)

## 🔍 Tesseract Installation

### Windows
1. Download installer from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
2. Add the Tesseract installation directory to your PATH environment variable
3. Verify installation: `tesseract --version`

### Mac
```bash
brew install tesseract
```

### Linux
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

## 📋 Installation

### Method 1: Local Development Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### Method 2: Docker Deployment
```bash
docker-compose up -d
```

## 🏁 Running the Application

### Local Development
#### Backend
```bash
cd backend
flask run
```

#### Frontend
```bash
cd frontend
npm run dev
```

### Docker
```bash
docker-compose up -d
```

## 🖥️ Usage

1. Navigate to the application (http://localhost:3000 for dev or http://localhost for Docker)
2. Upload an order document (PDF, image, or text file)
3. View the extracted text and structured data
4. Check confidence scores and warnings for reliability
5. Download the results as JSON if needed

## 🗃️ API Endpoints

- `POST /upload` - Upload a document file
- `GET /parse` - Parse the latest uploaded document
- `GET /results` - List all saved parsed results
- `GET /download` - Download the latest parsed result
- `GET /download/<filename>` - Download a specific parsed result

## 📊 Example Input/Output

### Example Input Document:
```
Order ID: ORD-12345
Customer: John Smith
Shipping Address: 123 Main St, Anytown, USA
Items:
- SKU: X123, Quantity: 20, Price: $42.99
- SKU: Y456, Quantity: 5, Price: $15.50
```

### Example Output JSON:
```json
{
  "customer": "John Smith",
  "order_id": "ORD-12345",
  "shipping_address": "123 Main St, Anytown, USA",
  "line_items": [
    {
      "sku": "X123",
      "quantity": 20,
      "price": 42.99
    },
    {
      "sku": "Y456",
      "quantity": 5,
      "price": 15.50
    }
  ],
  "confidence": {
    "customer": 0.95,
    "order_id": 0.98,
    "shipping_address": 0.92,
    "line_items": 0.97,
    "overall": 0.955
  },
  "extraction_details": {
    "customer": {
      "value": "John Smith",
      "confidence": 0.95,
      "source": "regex"
    },
    "order_id": {
      "value": "ORD-12345",
      "confidence": 0.98,
      "source": "regex"
    },
    "shipping_address": {
      "value": "123 Main St, Anytown, USA",
      "confidence": 0.92,
      "source": "regex"
    },
    "line_items": [
      {
        "sku": {
          "value": "X123",
          "confidence": 0.95,
          "source": "regex"
        },
        "quantity": {
          "value": 20,
          "confidence": 0.97,
          "source": "regex"
        },
        "price": {
          "value": 42.99,
          "confidence": 0.98,
          "source": "regex"
        }
      },
      {
        "sku": {
          "value": "Y456",
          "confidence": 0.96,
          "source": "regex"
        },
        "quantity": {
          "value": 5,
          "confidence": 0.97,
          "source": "regex"
        },
        "price": {
          "value": 15.50,
          "confidence": 0.98,
          "source": "regex"
        }
      }
    ]
  }
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python test_ner.py
python test_api_ner.py
```

## 👨‍💻 Development

This project is structured as follows:

```
docparser/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── ner_model.py
│   │   ├── parser.py
│   │   └── ocr.py
│   ├── data/
│   │   ├── temp/
│   │   └── parsed/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   └── package.json
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.