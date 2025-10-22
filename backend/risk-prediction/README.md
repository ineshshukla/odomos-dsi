# 🎯 Risk Prediction Service

**Purpose:** Predict cancer risk and BIRADS scores using hybrid ML models

## 🎯 Responsibilities
- Run hybrid ML models (tabular + text)
- Generate risk predictions
- Handle model inference
- Provide confidence scores
- Model versioning and A/B testing

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **ML Models:** XGBoost, LightGBM, PyTorch
- **Model Serving:** MLflow, TorchServe
- **Monitoring:** Prometheus, Grafana
- **Feature Store:** Optional integration

## 📋 API Endpoints
```
POST /api/v1/predict         # Generate risk prediction
GET  /api/v1/status/{id}     # Check prediction status
GET  /api/v1/result/{id}     # Get prediction result
GET  /api/v1/models          # List available models
POST /api/v1/models/{id}/predict # Predict with specific model
```

## 🔄 Service Communication
- **Input:** Processed features from Feature Engineering Service
- **Output:** Risk predictions to Notification Service
- **Dependencies:** Feature Engineering Service, Trained models

## 📁 Project Structure
```
risk-prediction/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Data models
│   ├── routes/              # API endpoints
│   ├── services/            # Prediction logic
│   │   ├── model_service.py
│   │   ├── inference_engine.py
│   │   └── prediction_validator.py
│   ├── ml_models/           # Model files and configs
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
