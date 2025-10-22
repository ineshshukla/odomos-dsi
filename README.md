# 🩺 Mammography Report Analysis & Cancer Risk Stratification System

## 1️⃣ Problem Overview
Hospitals receive mammography reports in various formats — PDFs, scanned images, or text files — often with inconsistent structure.  
These reports contain critical diagnostic information (e.g., gland density, findings, BIRADS score).  
The goal is to **automate ingestion, structuring, and risk prediction** from such reports using a combination of document parsing, LLM-based structuring, and ML-based risk modeling.

---

## 2️⃣ Microservice Architecture

### 🏗️ Service Overview

The system is designed as a collection of microservices, each handling a specific domain of the mammography report analysis pipeline.

### 📥 **Document Ingestion Service**
**Purpose:** Handle file uploads and initial document processing  
**Responsibilities:**
- Accept PDF, image, and text file uploads
- File validation and security checks
- Store files in appropriate storage (S3, local filesystem)
- Trigger document parsing workflow

**API Endpoints:**
```
POST /api/v1/upload          # Upload document
GET  /api/v1/status/{id}     # Check processing status
```

---

### 🔍 **Document Parsing Service**
**Purpose:** Extract text content from various document formats  
**Responsibilities:**
- Use `docling` for OCR and text extraction
- Convert PDFs, scanned images to markdown/text
- Handle different document formats and quality
- Return structured markdown output

**Implementation:**
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("input.pdf")

with open("output.md", "w", encoding="utf-8") as f:
    f.write(result.document.export_to_markdown())
```

**Output Example:**
```markdown
Mammography Report - June 25, 2022  
Findings: Very dense glandular tissue. No suspicious lymph nodes.  
Assessment: ACR Type D bilaterally. BIRADS 0 bilaterally.  
Recommendation: Correlation with ultrasound recommended.
```

---

### 🏗️ **Information Structuring Service**
**Purpose:** Convert extracted text into structured JSON  
**Responsibilities:**
- Use medical LLMs (BioGPT, Llama-3-Med) for structuring
- Extract key fields (date, density, findings, BIRADS, etc.)
- Handle missing data scenarios
- Return structured JSON output

**Model:** Medical LLM (e.g., `BioGPT`, `Llama-3-Med`, `GPT-4-Medical`)

**Example Output:**
```json
{
  "date": "2022-06-25",
  "indication": "Mastalgia",
  "density": "ACR Type D",
  "findings": {
    "calcifications": false,
    "architectural_distortion": false,
    "lymph_nodes": "No suspicious lymph nodes"
  },
  "birads_score": 0,
  "recommendation": "Correlation with ultrasound recommended"
}
```

If BIRADS is missing, the LLM can either infer it based on text cues or leave it as `null` for further ML estimation.

---

### ⚙️ **Feature Engineering Service**
**Purpose:** Prepare features for ML models  
**Responsibilities:**
- Convert text to embeddings (BioClinicalBERT)
- Encode categorical variables
- Handle missing data imputation
- Normalize numerical features

**Feature Preparation:**
After structuring, each report becomes a **hybrid of tabular and textual data**:

| density | calcifications | lymph_nodes | report_text_embedding | birads_score |
| ------- | -------------- | ----------- | --------------------- | ------------ |
| ACR D   | 0              | None        | [0.12, 0.08, ...]     | 0            |
| ACR C   | 1              | Suspicious  | [0.31, 0.22, ...]     | 3            |

**Textual data** → converted into embeddings using a pre-trained model (e.g., `BioClinicalBERT`, `OpenAI embeddings`).  
**Tabular data** → numeric and categorical values normalized/encoded.

---

### 🎯 **Risk Prediction Service**
**Purpose:** Predict cancer risk and BIRADS scores  
**Responsibilities:**
- Run hybrid ML models (tabular + text)
- Generate risk predictions
- Handle model inference

**Model Architecture — Hybrid Tabular + Text:**

```
     ┌─────────────────────────────┐
     │  Structured Tabular Data    │
     └──────────────┬──────────────┘
                    │
             [Tabular ML Model]
                    │
                    ▼
          Tabular Feature Embeddings
                    │
                    ▼
    ┌───────────────────────────────┐
    │   Text Embeddings (BioBERT)   │
    └───────────────────────────────┘
                    │
             [Fusion Layer]
                    │
                    ▼
           Risk Prediction Output
```

**Implementation Options:**
- Simple ensemble (average/weighted voting)
- Concatenation of both embeddings into a shallow MLP
- Gradient Boosted Trees (e.g., XGBoost) for tabular, concatenated with text vector

**Model Objective (Loss Function):**
If the dataset includes **BIRADS scores**, this becomes a **classification problem**:
```
Loss = CrossEntropyLoss(predicted_birads, true_birads)
```

---

### 🎓 **Model Training Service**
**Purpose:** Train and update ML models  
**Responsibilities:**
- Train hybrid models on structured data
- Model versioning and evaluation
- Active learning integration

**Training Approach:**
If not all reports include BIRADS, you can:
- Train a regression/classification model on available BIRADS data
- Use that model to pseudo-label the rest (semi-supervised learning)
- Or, predict a custom binary outcome like *"high-risk vs low-risk"*

---

### 🌐 **API Gateway Service**
**Purpose:** Route requests and handle cross-cutting concerns  
**Responsibilities:**
- Request routing to appropriate services
- Authentication and authorization
- Rate limiting and monitoring

---

### 📢 **Notification Service**
**Purpose:** Handle notifications and alerts  
**Responsibilities:**
- Send alerts for high-risk predictions
- Email/SMS notifications
- Integration with hospital systems

---

## 3️⃣ Service Communication Flow

### 🔄 **Request Flow**
```
Client → API Gateway → Document Ingestion → Document Parsing → Information Structuring → Feature Engineering → Risk Prediction → Notification
```

### 📋 **Service Dependencies**
- **Document Ingestion** → **Document Parsing** (triggers parsing after upload)
- **Document Parsing** → **Information Structuring** (passes extracted text)
- **Information Structuring** → **Feature Engineering** (passes structured JSON)
- **Feature Engineering** → **Risk Prediction** (passes processed features)
- **Risk Prediction** → **Notification** (triggers alerts for high-risk cases)

### 🎯 **Your Microservices (Ingestion + Parsing + Structuring)**
You will be responsible for **3 microservices**:
1. **Document Ingestion Service** - File handling and upload management
2. **Document Parsing Service** - OCR and text extraction using docling
3. **Information Structuring Service** - LLM-based data structuring

---

## 4️⃣ When Would RAG Be Needed?

RAG (Retrieval-Augmented Generation) is useful **only if**:

* You need the model to reference medical guidelines or literature dynamically.
* You want to provide **evidence-backed explanations** ("based on ACR 2023 standards...").

In this microservice architecture, RAG would be implemented as a separate service that could be called by the **Information Structuring Service** when needed.

---

## 5️⃣ Dataset Example

Example report:

> "Mammography in Two Views from June 25, 2022. Indication: Mastalgia.
> Very dense glandular tissue. No microcalcifications.
> Assessment: ACR Type D. BIRADS 0 bilaterally.
> Correlation with ultrasound is recommended."

Such reports flow through the microservices as follows:

1. **Document Ingestion** → stores the report file
2. **Document Parsing** → extracts text content
3. **Information Structuring** → converts to structured JSON
4. **Feature Engineering** → prepares ML features
5. **Risk Prediction** → generates risk assessment

---

## 6️⃣ Complete Microservice Flow

```
               Input
                │
                ▼
       [PDF / Image / Text Report]
                │
         ┌──────┴───────┐
         │ Document     │
         │ Ingestion    │
         └──────┬───────┘
                │
                ▼
         ┌──────┴───────┐
         │ Document     │
         │ Parsing      │
         └──────┬───────┘
                │
                ▼
         ┌──────┴───────┐
         │ Information  │
         │ Structuring  │
         └──────┬───────┘
                │
                ▼
         ┌──────┴───────┐
         │ Feature      │
         │ Engineering  │
         └──────┬───────┘
                │
                ▼
         ┌──────┴───────┐
         │ Risk         │
         │ Prediction   │
         └──────┬───────┘
                │
                ▼
       ➤ Risk / BIRADS Prediction
```

---

## 7️⃣ Technology Stack by Microservice

### 📥 **Document Ingestion Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| File Storage | `AWS S3`, `MinIO`, or local filesystem |
| Validation | `python-magic`, `Pillow` |
| Database | `PostgreSQL` or `MongoDB` for metadata |

### 🔍 **Document Parsing Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| OCR & Parsing | `docling` |
| Image Processing | `Pillow`, `OpenCV` |
| Queue System | `Redis`, `RabbitMQ` |

### 🏗️ **Information Structuring Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| LLM Integration | `BioGPT`, `GPT-4-Med`, `Llama-3-Med` |
| Prompt Engineering | `LangChain`, `LlamaIndex` |
| API Clients | `httpx`, `openai` |

### ⚙️ **Feature Engineering Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| Text Embeddings | `BioClinicalBERT`, `sentence-transformers` |
| Data Processing | `pandas`, `numpy` |
| ML Libraries | `scikit-learn` |

### 🎯 **Risk Prediction Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| ML Models | `XGBoost`, `LightGBM`, `PyTorch` |
| Model Serving | `MLflow`, `TorchServe` |
| Monitoring | `Prometheus`, `Grafana` |

### 🎓 **Model Training Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| ML Pipeline | `MLflow`, `Kubeflow` |
| Experiment Tracking | `Weights & Biases`, `MLflow` |
| Model Registry | `MLflow Model Registry` |

### 🌐 **API Gateway Service**
| Component | Technology |
| --------- | ---------- |
| Gateway | `Kong`, `NGINX`, or custom `FastAPI` |
| Load Balancing | `HAProxy`, `NGINX` |
| Authentication | `JWT`, `OAuth2` |
| Rate Limiting | `Redis` |

### 📢 **Notification Service**
| Component | Technology |
| --------- | ---------- |
| Framework | `FastAPI` |
| Email | `SendGrid`, `AWS SES` |
| SMS | `Twilio`, `AWS SNS` |
| Webhooks | `httpx` |

### 🐳 **Infrastructure & Deployment**
| Component | Technology |
| --------- | ---------- |
| Containerization | `Docker` |
| Orchestration | `Kubernetes`, `Docker Compose` |
| Service Discovery | `Consul`, `etcd` |
| Monitoring | `Prometheus`, `Grafana`, `Jaeger` |

---

## 8️⃣ Summary

✅ **Architecture:** Microservice-based system with clear domain boundaries  
✅ **Your Services:** Document Ingestion, Parsing, and Information Structuring  
✅ **Input:** Mammography reports (PDF, image, or text)  
✅ **Parsing:** Docling (auto OCR + text extraction → Markdown)  
✅ **Structuring:** LLM extracts features into JSON  
✅ **Model:** Hybrid ML (tabular + text embeddings)  
✅ **Output:** Cancer risk / BIRADS classification  
✅ **RAG:** Optional, for guideline-grounded responses  
✅ **Deployment:** Containerized microservices with API Gateway  
✅ **Future:** Add active learning to evolve post-deployment

