# 📥 Document Ingestion Service

**Purpose:** Handle file uploads and initial document processing

## 🎯 Responsibilities
- Accept PDF, image, and text file uploads
- File validation and security checks
- Store files in appropriate storage (S3, local filesystem)
- Trigger document parsing workflow
- Track processing status

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **File Storage:** AWS S3, MinIO, or local filesystem
- **Validation:** python-magic, Pillow
- **Database:** PostgreSQL or MongoDB for metadata
- **Queue:** Redis/RabbitMQ for async processing

## 📋 API Endpoints
```
POST /api/v1/upload          # Upload document
GET  /api/v1/status/{id}     # Check processing status
GET  /api/v1/documents       # List uploaded documents
DELETE /api/v1/documents/{id} # Delete document
```

## 🔄 Service Communication
- **Input:** File uploads from clients
- **Output:** Triggers Document Parsing Service
- **Dependencies:** Document Parsing Service, Storage Service

## 📁 Project Structure
```
document-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Database models
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
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
