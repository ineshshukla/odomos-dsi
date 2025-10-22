# 🔍 Document Parsing Service

**Purpose:** Extract text content from various document formats

## 🎯 Responsibilities
- Use `docling` for OCR and text extraction
- Convert PDFs, scanned images to markdown/text
- Handle different document formats and quality
- Return structured markdown output
- Process files asynchronously

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **OCR & Parsing:** docling
- **Image Processing:** Pillow, OpenCV
- **Queue System:** Redis, RabbitMQ
- **Storage:** File system or cloud storage

## 📋 API Endpoints
```
POST /api/v1/parse           # Parse document
GET  /api/v1/status/{id}     # Check parsing status
GET  /api/v1/result/{id}     # Get parsed result
```

## 🔄 Service Communication
- **Input:** File paths from Document Ingestion Service
- **Output:** Extracted text/markdown to Information Structuring Service
- **Dependencies:** Document Ingestion Service, Storage Service

## 📁 Project Structure
```
document-parsing/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Data models
│   ├── routes/              # API endpoints
│   ├── services/            # Parsing logic
│   │   ├── docling_service.py
│   │   └── ocr_service.py
│   ├── utils/               # Utility functions
│   └── config.py            # Configuration
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This file
```

## 🚀 Development Status
**Status:** 🚧 To be implemented
**Owner:** You
**Priority:** High
