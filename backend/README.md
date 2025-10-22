# 🏥 Mammography Report Analysis - Backend Services

This directory contains all the microservices for the mammography report analysis system.

## 📁 Service Structure

```
backend/
├── document-ingestion/     # Document upload and file handling
├── document-parsing/       # OCR and text extraction using docling
├── information-structuring/ # LLM-based data structuring
├── feature-engineering/    # Feature preparation for ML models
├── risk-prediction/        # ML model inference and risk assessment
├── model-training/         # Model training and versioning
├── api-gateway/           # Request routing and cross-cutting concerns
├── notification/          # Alerts and notifications
├── shared/                # Common utilities and shared code
├── infrastructure/        # Docker, K8s, and deployment configs
└── docs/                  # API documentation and architecture docs
```

## 🚀 Quick Start

1. **Your Services (to be implemented):**
   - `document-ingestion/` - File upload and validation
   - `document-parsing/` - OCR and text extraction
   - `information-structuring/` - LLM-based structuring

2. **Other Services (future implementation):**
   - `feature-engineering/` - Feature preparation
   - `risk-prediction/` - ML inference
   - `model-training/` - Model training pipeline
   - `api-gateway/` - Request routing
   - `notification/` - Alerts and notifications

## 🔧 Development Setup

Each service is containerized and can be run independently. See individual service READMEs for specific setup instructions.

## 📋 Service Dependencies

```
Client → API Gateway → Document Ingestion → Document Parsing → Information Structuring → Feature Engineering → Risk Prediction → Notification
```

## 🐳 Docker Compose

Use `docker-compose.yml` in the root to run all services together for development.
