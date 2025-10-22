# 🎓 Model Training Service

**Purpose:** Train and update ML models with versioning and evaluation

## 🎯 Responsibilities
- Train hybrid models on structured data
- Model versioning and evaluation
- Active learning integration
- Hyperparameter optimization
- Model performance monitoring

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **ML Pipeline:** MLflow, Kubeflow
- **Experiment Tracking:** Weights & Biases, MLflow
- **Model Registry:** MLflow Model Registry
- **Training:** PyTorch, XGBoost, scikit-learn

## 📋 API Endpoints
```
POST /api/v1/train           # Start training job
GET  /api/v1/jobs            # List training jobs
GET  /api/v1/jobs/{id}       # Get training job status
POST /api/v1/evaluate        # Evaluate model
GET  /api/v1/models          # List trained models
```

## 🔄 Service Communication
- **Input:** Training data from database/feature store
- **Output:** Trained models to Risk Prediction Service
- **Dependencies:** Database, Feature Engineering Service

## 📁 Project Structure
```
model-training/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Data models
│   ├── routes/              # API endpoints
│   ├── services/            # Training logic
│   │   ├── training_service.py
│   │   ├── model_evaluator.py
│   │   └── hyperparameter_tuner.py
│   ├── training/            # Training scripts
│   │   ├── data_loader.py
│   │   ├── model_architectures.py
│   │   └── training_pipeline.py
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
**Priority:** Low
