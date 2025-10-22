# ⚙️ Feature Engineering Service

**Purpose:** Prepare features for ML models

## 🎯 Responsibilities
- Convert text to embeddings (BioClinicalBERT)
- Encode categorical variables
- Handle missing data imputation
- Normalize numerical features
- Create hybrid tabular + text features

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **Text Embeddings:** BioClinicalBERT, sentence-transformers
- **Data Processing:** pandas, numpy
- **ML Libraries:** scikit-learn
- **Feature Store:** Optional (Feast, Tecton)

## 📋 API Endpoints
```
POST /api/v1/features        # Generate features
GET  /api/v1/status/{id}     # Check feature generation status
GET  /api/v1/result/{id}     # Get processed features
```

## 🔄 Service Communication
- **Input:** Structured JSON from Information Structuring Service
- **Output:** Processed features to Risk Prediction Service
- **Dependencies:** Information Structuring Service, ML models

## 📁 Project Structure
```
feature-engineering/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Data models
│   ├── routes/              # API endpoints
│   ├── services/            # Feature engineering logic
│   │   ├── embedding_service.py
│   │   ├── categorical_encoder.py
│   │   └── feature_pipeline.py
│   ├── utils/               # Utility functions
│   └── config.py            # Configuration
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This file
```

## 🚀 Development Status
**Status:** 📋 Planned (Future implementation)
**Owner:** TBD
**Priority:** Medium
