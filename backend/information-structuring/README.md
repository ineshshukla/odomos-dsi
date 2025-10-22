# 🏗️ Information Structuring Service

**Purpose:** Convert extracted text into structured JSON using medical LLMs

## 🎯 Responsibilities
- Use medical LLMs (BioGPT, Llama-3-Med) for structuring
- Extract key fields (date, density, findings, BIRADS, etc.)
- Handle missing data scenarios
- Return structured JSON output
- Validate and clean extracted data

## 🛠️ Technology Stack
- **Framework:** FastAPI
- **LLM Integration:** BioGPT, GPT-4-Med, Llama-3-Med
- **Prompt Engineering:** LangChain, LlamaIndex
- **API Clients:** httpx, openai
- **Validation:** Pydantic models

## 📋 API Endpoints
```
POST /api/v1/structure       # Structure extracted text
GET  /api/v1/status/{id}     # Check structuring status
GET  /api/v1/result/{id}     # Get structured result
POST /api/v1/validate        # Validate structured data
```

## 🔄 Service Communication
- **Input:** Extracted text from Document Parsing Service
- **Output:** Structured JSON to Feature Engineering Service
- **Dependencies:** Document Parsing Service, LLM APIs

## 📁 Project Structure
```
information-structuring/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/              # Pydantic models
│   │   ├── mammography_report.py
│   │   └── structured_data.py
│   ├── routes/              # API endpoints
│   ├── services/            # Structuring logic
│   │   ├── llm_service.py
│   │   ├── prompt_templates.py
│   │   └── data_validator.py
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
