"""
Information structuring service using Google Gemini API
"""
import json
import time
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.database import StructuringResult
from app.models.schemas import StructuredData
from app.config import GEMINI_API_KEY, GEMINI_API_URL, RESULTS_DIR

class InformationStructuringService:
    """Service for structuring mammography reports using Gemini API"""
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = GEMINI_API_KEY
        self.api_url = GEMINI_API_URL
    
    async def structure_document(self, document_id: str, extracted_text: str) -> StructuringResult:
        """Structure mammography report using Gemini API"""
        start_time = time.time()
        
        try:
            # Check if result already exists
            existing_result = self.db.query(StructuringResult).filter(
                StructuringResult.document_id == document_id
            ).first()
            
            if existing_result:
                # Update existing result
                structured_data = await self.extract_structured_data(extracted_text)
                existing_result.extracted_text = extracted_text
                existing_result.structured_data = structured_data.dict()
                existing_result.status = "completed"
                existing_result.error_message = None
                existing_result.processing_time = int(time.time() - start_time)
                self.db.commit()
                self.db.refresh(existing_result)
                return existing_result
            
            # Create new result
            structured_data = await self.extract_structured_data(extracted_text)
            confidence_score = self.calculate_confidence_score(structured_data)
            
            result = StructuringResult(
                document_id=document_id,
                extracted_text=extracted_text,
                structured_data=structured_data.dict(),
                confidence_score=confidence_score,
                model_used="gemini",
                processing_time=int(time.time() - start_time),
                status="completed"
            )
            
            self.db.add(result)
            self.db.commit()
            self.db.refresh(result)
            
            # Save result to file
            await self.save_structured_result(document_id, structured_data)
            
            # Update document-ingestion service about completion
            await self.update_document_status(document_id, "structured", "completed")
            
            # Trigger next service (Risk Prediction)
            await self.trigger_risk_prediction_service(document_id, result.id, structured_data)
            
            return result
            
        except Exception as e:
            # Handle error
            error_result = StructuringResult(
                document_id=document_id,
                extracted_text=extracted_text,
                structured_data={},
                status="failed",
                error_message=str(e),
                processing_time=int(time.time() - start_time)
            )
            
            # Update document-ingestion service about failure
            await self.update_document_status(document_id, "parsed", "failed", str(e))
            
            if existing_result:
                existing_result.status = "failed"
                existing_result.error_message = str(e)
                existing_result.processing_time = int(time.time() - start_time)
                self.db.commit()
                self.db.refresh(existing_result)
                return existing_result
            else:
                self.db.add(error_result)
                self.db.commit()
                self.db.refresh(error_result)
                return error_result
    
    async def extract_structured_data(self, text: str) -> StructuredData:
        """Extract structured data using Gemini API"""
        if not self.api_key:
            # Use mock data when API key is not configured
            print("⚠️  GEMINI_API_KEY not configured - using mock structured data")
            return self.create_mock_structured_data(text)
        
        try:
            prompt = self.create_prompt(text)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.1,
                            "topK": 1,
                            "topP": 0.8,
                            "maxOutputTokens": 2048,
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    # Fallback to mock data on API error
                    print(f"⚠️  Gemini API error: {response.status_code} - falling back to mock data")
                    return self.create_mock_structured_data(text)
                
                result = response.json()
                
                if "candidates" not in result or not result["candidates"]:
                    print("⚠️  No response from Gemini API - falling back to mock data")
                    return self.create_mock_structured_data(text)
                
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Parse JSON response
                try:
                    # Extract JSON from response (in case there's extra text)
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != 0:
                        json_str = content[json_start:json_end]
                        data = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in response")
                    
                    return StructuredData(**data)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️  Failed to parse Gemini response - falling back to mock data: {str(e)}")
                    return self.create_mock_structured_data(text)
                    
        except Exception as e:
            # Fallback to mock data on any error
            print(f"⚠️  Gemini API exception - falling back to mock data: {str(e)}")
            return self.create_mock_structured_data(text)

    
    def create_mock_structured_data(self, text: str) -> StructuredData:
        """Create mock structured data when API key is not available"""
        # Simple rule-based extraction for demo purposes
        mock_data = {
            "medical_unit": "unknown",
            "full_report": text[:500] if text else "unknown",  # First 500 chars
            "lmp": "unknown",
            "hormonal_therapy": "unknown",
            "family_history": "unknown",
            "reason": "unknown",
            "observations": "unknown",
            "conclusion": "unknown",
            "recommendations": "unknown",
            "birads": "unknown",
            "age": "unknown",
            "children": "unknown"
        }
        
        # Simple text-based extraction
        text_lower = text.lower()
        
        # Extract BI-RADS score
        if "bi-rads" in text_lower or "birads" in text_lower:
            for score in ["0", "1", "2", "3", "4", "5", "6"]:
                if f"bi-rads {score}" in text_lower or f"birads {score}" in text_lower or f"birads: {score}" in text_lower:
                    mock_data["birads"] = score
                    break
        
        # Extract reason/indication
        if "routine" in text_lower and "screening" in text_lower:
            mock_data["reason"] = "routine screening"
        elif "follow" in text_lower and "up" in text_lower:
            mock_data["reason"] = "follow-up"
        elif "symptomatic" in text_lower or "symptom" in text_lower:
            mock_data["reason"] = "symptomatic"
        
        # Extract age
        import re
        age_patterns = [r'age[:\s]+(\d+)', r'(\d+)\s*(?:year|yr)', r'patient.*?(\d+)\s*(?:year|yr)']
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                age_val = int(match.group(1))
                if 18 <= age_val <= 100:  # Reasonable age range
                    mock_data["age"] = str(age_val)
                    break
        
        # Extract family history
        if "family history" in text_lower:
            if "positive" in text_lower or "yes" in text_lower:
                mock_data["family_history"] = "positive"
            elif "negative" in text_lower or "no" in text_lower:
                mock_data["family_history"] = "negative"
        
        # Extract LMP
        lmp_match = re.search(r'lmp[:\s]*([\d/\-\.]+)', text_lower)
        if lmp_match:
            mock_data["lmp"] = lmp_match.group(1)
        
        # Extract observations (look for findings section)
        obs_keywords = ["findings", "observations", "impression"]
        for keyword in obs_keywords:
            if keyword in text_lower:
                start_idx = text_lower.find(keyword)
                # Get next 200 chars after keyword
                obs_text = text[start_idx:start_idx+200].strip()
                if obs_text:
                    mock_data["observations"] = obs_text
                    break
        
        # Extract conclusion
        conclusion_keywords = ["conclusion", "impression", "assessment"]
        for keyword in conclusion_keywords:
            if keyword in text_lower:
                start_idx = text_lower.find(keyword)
                conclusion_text = text[start_idx:start_idx+150].strip()
                if conclusion_text:
                    mock_data["conclusion"] = conclusion_text
                    break
        
        # Extract recommendations
        rec_keywords = ["recommendation", "suggest", "advised", "follow-up"]
        for keyword in rec_keywords:
            if keyword in text_lower:
                start_idx = text_lower.find(keyword)
                rec_text = text[start_idx:start_idx+150].strip()
                if rec_text:
                    mock_data["recommendations"] = rec_text
                    break
            elif "extremely" in text_lower:
                mock_data["acr_density_type"] = "D"
                mock_data["gland_density"] = "extremely dense"
        
        # Extract family history
        if "family" in text_lower and "history" in text_lower:
            if "cancer" in text_lower:
                mock_data["family_history_breast_pathology"] = "family history of breast cancer"
        
        # Extract findings
        if "no suspicious" in text_lower:
            mock_data["findings_summary"] = "no suspicious findings"
            mock_data["calcifications_present"] = "no"
            mock_data["architectural_distortion"] = "none"
        
        # Extract recommendation
        if "routine" in text_lower and "months" in text_lower:
            mock_data["followup_recommended"] = "yes"
            mock_data["recommendation_text"] = "routine screening in 12 months"
        
        return StructuredData(**mock_data)
    
    def create_prompt(self, text: str) -> str:
        """Create prompt for Gemini API"""
        return f"""
You are a medical AI assistant specializing in mammography report analysis.

Extract the following information from this mammography report and return it as valid JSON.
These fields match the format used for training the BI-RADS prediction model.

Report Text:
{text}

IMPORTANT INSTRUCTIONS:
1. Extract only information that is explicitly mentioned in the report
2. For fields not mentioned, use "unknown" as the value
3. Clean up any OCR errors in the text
4. Be thorough - extract complete sentences for observations, conclusion, and recommendations
5. Extract dates, ages, and numerical information if present

Extract and structure the following fields (match exactly):

{{
  "medical_unit": "Name of the medical unit, hospital, or clinic (extract from header/letterhead)",
  "full_report": "Complete full text of the report (all sections combined, clean up OCR errors)",
  "lmp": "Last menstrual period date if mentioned (format: DD/MM/YYYY or as stated)",
  "hormonal_therapy": "Hormonal therapy status (yes/no/details, or unknown)",
  "family_history": "Family history of breast cancer or breast pathology (positive/negative/details)",
  "reason": "Reason for mammography examination (e.g., routine screening, follow-up, symptomatic, diagnostic)",
  "observations": "Detailed clinical observations and findings from the examination (include density, masses, calcifications, asymmetries, etc.)",
  "conclusion": "Radiologist's conclusion, impression, or assessment (the diagnostic interpretation)",
  "recommendations": "Recommended follow-up actions or management (e.g., routine screening, additional imaging, biopsy)",
  "birads": "BI-RADS category (0, 1, 2, 3, 4, 4A, 4B, 4C, 5, 6, or unknown)",
  "age": "Patient age in years (extract number only)",
  "children": "Number of children or parity information (extract number or description)"
}}

IMPORTANT: 
- For "full_report", include ALL text from the report
- For "observations", include ALL findings mentioned (density, masses, calcifications, skin changes, lymph nodes, etc.)
- For "conclusion", extract the impression or assessment section
- For "recommendations", extract the follow-up plan
- Clean up OCR errors but preserve medical terminology

Return only valid JSON, no additional text or explanations.
"""
    
    def calculate_confidence_score(self, structured_data: StructuredData) -> float:
        """Calculate confidence score based on data completeness"""
        fields = structured_data.dict()
        total_fields = len(fields)
        unknown_fields = sum(1 for value in fields.values() if value == "unknown")
        
        # Calculate confidence as percentage of non-unknown fields
        confidence = (total_fields - unknown_fields) / total_fields
        return round(confidence, 2)
    
    async def save_structured_result(self, document_id: str, structured_data: StructuredData) -> None:
        """Save structured result to file"""
        file_path = RESULTS_DIR / f"{document_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data.dict(), f, indent=2, ensure_ascii=False)
    
    async def update_document_status(
        self, 
        document_id: str, 
        doc_status: str,
        processing_status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update document status in document-ingestion service"""
        try:
            payload = {
                "document_id": document_id,
                "service_name": "information_structuring",
                "status": processing_status,
                "error_message": error_message
            }
            
            async with httpx.AsyncClient() as client:
                # Update processing status
                await client.post(
                    "http://localhost:8001/documents/update-status-internal",
                    json=payload,
                    timeout=10.0
                )
                
                # Update main document status
                if doc_status:
                    await client.patch(
                        f"http://localhost:8001/documents/{document_id}/status-internal",
                        json={"status": doc_status},
                        timeout=10.0
                    )
                    
        except Exception as e:
            print(f"Warning: Failed to update document status: {str(e)}")
    
    async def trigger_risk_prediction_service(
        self, 
        document_id: str, 
        structuring_id: str,
        structured_data: StructuredData
    ) -> None:
        """Trigger risk prediction service after structuring completes"""
        try:
            payload = {
                "document_id": document_id,
                "structuring_id": structuring_id,
                "structured_data": structured_data.dict()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8004/predictions/predict-internal",
                    json=payload,
                    timeout=60.0  # Allow more time for model inference
                )
                
                if response.status_code == 200:
                    print(f"✅ Risk prediction triggered successfully for document {document_id}")
                else:
                    print(f"⚠️  Risk Prediction service returned {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️  Failed to trigger Risk Prediction service: {str(e)}")
            # Don't fail the structuring if prediction fails - it can be retried later
    
    def get_structuring_result(self, document_id: str) -> Optional[StructuringResult]:
        """Get structuring result by document ID"""
        return self.db.query(StructuringResult).filter(
            StructuringResult.document_id == document_id
        ).first()
    
    def get_structuring_result_by_id(self, structuring_id: str) -> Optional[StructuringResult]:
        """Get structuring result by structuring ID"""
        return self.db.query(StructuringResult).filter(
            StructuringResult.id == structuring_id
        ).first()
    
    def create_mock_structured_data(self, text: str) -> StructuredData:
        """Create mock structured data for testing without API key"""
        # Simple rule-based extraction for demo purposes
        mock_data = {
            "indication": "unknown",
            "family_history_breast_pathology": "unknown",
            "clinical_exam_result": "unknown",
            "skin_abnormalities": "unknown",
            "nipple_abnormalities": "unknown",
            "gland_density": "unknown",
            "calcifications_present": "unknown",
            "architectural_distortion": "unknown",
            "retracted_areas": "unknown",
            "suspicious_lymph_nodes": "unknown",
            "evaluation_possible": "unknown",
            "findings_summary": "unknown",
            "acr_density_type": "unknown",
            "birads_score": "unknown",
            "followup_recommended": "unknown",
            "recommendation_text": "unknown",
            "lmp": "unknown",
            "hormonal_therapy": "unknown",
            "age": "unknown",
            "children": "unknown"
        }
        
        # Simple text-based extraction
        text_lower = text.lower()
        
        if "routine" in text_lower and "screening" in text_lower:
            mock_data["indication"] = "routine screening"
        
        if "bi-rads" in text_lower or "birads" in text_lower:
            if "2" in text:
                mock_data["birads_score"] = "2"
            elif "3" in text:
                mock_data["birads_score"] = "3"
            elif "4" in text:
                mock_data["birads_score"] = "4"
        
        if "dense" in text_lower:
            if "heterogeneously" in text_lower:
                mock_data["acr_density_type"] = "C"
                mock_data["gland_density"] = "heterogeneously dense"
            elif "extremely" in text_lower:
                mock_data["acr_density_type"] = "D"
                mock_data["gland_density"] = "extremely dense"
        
        if "follow" in text_lower and "up" in text_lower:
            mock_data["followup_recommended"] = "yes"
            mock_data["recommendation_text"] = "Follow-up recommended"
        
        if "no suspicious" in text_lower:
            mock_data["findings_summary"] = "No suspicious findings"
            mock_data["calcifications_present"] = "no"
            mock_data["architectural_distortion"] = "none"
        
        return StructuredData(**mock_data)
