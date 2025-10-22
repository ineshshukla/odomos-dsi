# 🔧 Shared Components

**Purpose:** Common utilities and shared code across all microservices

## 🎯 Responsibilities
- Common data models and schemas
- Shared utility functions
- Database connection utilities
- Authentication helpers
- Logging and monitoring utilities
- Common configuration management

## 📁 Project Structure
```
shared/
├── __init__.py
├── models/                  # Common Pydantic models
│   ├── __init__.py
│   ├── base_models.py
│   ├── mammography_models.py
│   └── response_models.py
├── utils/                   # Common utilities
│   ├── __init__.py
│   ├── database.py
│   ├── auth.py
│   ├── logging.py
│   ├── validation.py
│   └── helpers.py
├── config/                  # Common configuration
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── middleware/              # Common middleware
│   ├── __init__.py
│   ├── cors.py
│   ├── error_handling.py
│   └── request_logging.py
└── README.md               # This file
```

## 🚀 Development Status
**Status:** 📋 Planned (Shared across all services)
**Owner:** All teams
**Priority:** High
