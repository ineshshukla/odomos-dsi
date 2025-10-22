# 🩺 Mammography Report Analysis & Cancer Risk Stratification System

## 1️⃣ Problem Overview
Hospitals receive mammography reports in various formats — PDFs, scanned images, or text files — often with inconsistent structure.  
These reports contain critical diagnostic information (e.g., gland density, findings, BIRADS score).  
The goal is to **automate ingestion, structuring, and risk prediction** from such reports using a combination of document parsing, LLM-based structuring, and ML-based risk modeling.

---

## 2️⃣ System Workflow

### Step 1: Document Ingestion & Parsing
**Tool:** `docling`  
- Automatically detects whether the input is a PDF, image, or text file.
- Applies OCR if needed (for scanned documents).
- Converts content into structured Markdown or text.

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("input.pdf")

with open("output.md", "w", encoding="utf-8") as f:
    f.write(result.document.export_to_markdown())
````

**Output Example:**

```markdown
Mammography Report - June 25, 2022  
Findings: Very dense glandular tissue. No suspicious lymph nodes.  
Assessment: ACR Type D bilaterally. BIRADS 0 bilaterally.  
Recommendation: Correlation with ultrasound recommended.
```

---

### Step 2: Information Extraction (Structuring)

**Model:** Medical LLM (e.g., `BioGPT`, `Llama-3-Med`, `GPT-4-Medical`)

**Task:** Convert the extracted markdown text into a structured JSON format.

Example output:

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

### Step 3: Handling Missing Data

**Approach:**

* If a few features are missing → fill using mean/median or predictive imputation.
* If an entire field (like `birads_score`) is missing → model can be trained to predict it based on textual and tabular signals.

---

### Step 4: Feature Preparation

After structuring, each report becomes a **hybrid of tabular and textual data**:

| density | calcifications | lymph_nodes | report_text_embedding | birads_score |
| ------- | -------------- | ----------- | --------------------- | ------------ |
| ACR D   | 0              | None        | [0.12, 0.08, ...]     | 0            |
| ACR C   | 1              | Suspicious  | [0.31, 0.22, ...]     | 3            |

**Textual data** → converted into embeddings using a pre-trained model (e.g., `BioClinicalBERT`, `OpenAI embeddings`).
**Tabular data** → numeric and categorical values normalized/encoded.

---

### Step 5: Model Architecture — Hybrid Tabular + Text

**Concept:**
A combination of two models — one for tabular features and one for text embeddings.

**Diagram (conceptual):**

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

* Simple ensemble (average/weighted voting)
* Concatenation of both embeddings into a shallow MLP
* Gradient Boosted Trees (e.g., XGBoost) for tabular, concatenated with text vector

---

### Step 6: Model Objective (Loss Function)

If the dataset includes **BIRADS scores**, this becomes a **classification problem**:

```
Loss = CrossEntropyLoss(predicted_birads, true_birads)
```

If not all reports include BIRADS, you can:

* Train a regression/classification model on available BIRADS data.
* Use that model to pseudo-label the rest (semi-supervised learning).
* Or, predict a custom binary outcome like *“high-risk vs low-risk”*.

---

### Step 7: Model Deployment & Evolution

The model can be deployed as:

* **API Endpoint** → Receives new reports → Returns structured JSON + risk prediction.
* **Retraining Loop** → Periodically update with new reports (active learning).

However, the model won’t **automatically learn** after deployment unless you add a retraining pipeline that collects feedback or new labeled data.

---

## 3️⃣ When Would RAG Be Needed?

RAG (Retrieval-Augmented Generation) is useful **only if**:

* You need the model to reference medical guidelines or literature dynamically.
* You want to provide **evidence-backed explanations** ("based on ACR 2023 standards...").

In this workflow, RAG is **optional** — since you’re primarily extracting and classifying from the report itself.

---

## 4️⃣ Dataset Example

Example report:

> “Mammography in Two Views from June 25, 2022. Indication: Mastalgia.
> Very dense glandular tissue. No microcalcifications.
> Assessment: ACR Type D. BIRADS 0 bilaterally.
> Correlation with ultrasound is recommended.”

Such reports can be used to:

* Train models to extract structured data (LLM fine-tuning or few-shot prompting)
* Predict BIRADS or risk classification based on textual and tabular cues

---

## 5️⃣ Summary of the Complete Flow

```
               Input
                │
                ▼
       [PDF / Image / Text Report]
                │
         ┌──────┴───────┐
         │  Docling OCR │
         └──────┬───────┘
                ▼
         Extracted Markdown
                │
                ▼
          LLM-Based Structuring
                │
                ▼
       Clean Tabular + Text Data
                │
                ▼
   Text Embedding + Feature Encoding
                │
                ▼
  Hybrid ML Model (Tabular + Text)
                │
                ▼
       ➤ Risk / BIRADS Prediction
```

---

## 6️⃣ Key Libraries and Tools

| Task            | Library                                    |
| --------------- | ------------------------------------------ |
| Parsing + OCR   | `docling`                                  |
| LLM Structuring | `BioGPT`, `GPT-4-Med`, `Llama-3-Med`       |
| Text Embeddings | `BioClinicalBERT`, `sentence-transformers` |
| ML Model        | `XGBoost`, `LightGBM`, or `sklearn`        |
| Deployment      | `FastAPI`, `Docker`, `Streamlit`           |

---

## 7️⃣ Summary

✅ **Input:** Mammography reports (PDF, image, or text)
✅ **Parsing:** Docling (auto OCR + text extraction → Markdown)
✅ **Structuring:** LLM extracts features into JSON
✅ **Model:** Hybrid ML (tabular + text embeddings)
✅ **Output:** Cancer risk / BIRADS classification
✅ **RAG:** Optional, for guideline-grounded responses
✅ **Future:** Add active learning to evolve post-deployment

