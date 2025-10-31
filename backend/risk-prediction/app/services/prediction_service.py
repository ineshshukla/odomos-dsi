"""
Prediction Service - Core logic for risk prediction using BioGPT model
"""
import torch
import time
import logging
from typing import Dict, Optional
from transformers import AutoTokenizer, BioGptForSequenceClassification
from scipy.special import softmax
import numpy as np
from sqlalchemy.orm import Session

from app.models.database import Prediction
from app.config import MODEL_PATH, RISK_THRESHOLDS, MIN_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

class PredictionService:
    """Service for generating BI-RADS predictions using BioGPT model"""
    
    def __init__(self, db: Session, model_path: str = MODEL_PATH):
        self.db = db
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained BioGPT model"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = BioGptForSequenceClassification.from_pretrained(self.model_path)
            
            # Check for GPU
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def _prepare_text_from_structured_data(self, structured_data: Dict) -> str:
        """
        Convert structured data to text format for the model.
        Uses the training data format fields (excluding birads).
        """
        # Extract key fields from structured data (matching training format)
        observations = []
        
        # Add reason for examination
        if structured_data.get("reason") and structured_data["reason"] != "unknown":
            observations.append(f"Reason: {structured_data['reason']}")
        
        # Add patient demographics
        if structured_data.get("age") and structured_data["age"] != "unknown":
            observations.append(f"Age: {structured_data['age']}")
        
        if structured_data.get("children") and structured_data["children"] != "unknown":
            observations.append(f"Children: {structured_data['children']}")
        
        if structured_data.get("lmp") and structured_data["lmp"] != "unknown":
            observations.append(f"LMP: {structured_data['lmp']}")
        
        if structured_data.get("hormonal_therapy") and structured_data["hormonal_therapy"] != "unknown":
            observations.append(f"Hormonal Therapy: {structured_data['hormonal_therapy']}")
        
        # Add family history
        if structured_data.get("family_history") and structured_data["family_history"] != "unknown":
            observations.append(f"Family History: {structured_data['family_history']}")
        
        # Add clinical observations (main findings)
        if structured_data.get("observations") and structured_data["observations"] != "unknown":
            observations.append(f"Observations: {structured_data['observations']}")
        
        # Add conclusion/impression
        if structured_data.get("conclusion") and structured_data["conclusion"] != "unknown":
            observations.append(f"Conclusion: {structured_data['conclusion']}")
        
        # Add recommendations
        if structured_data.get("recommendations") and structured_data["recommendations"] != "unknown":
            observations.append(f"Recommendations: {structured_data['recommendations']}")
        
        # Combine all into a single text
        report_text = " ".join(observations)
        
        # If report is too short or empty, add a default
        if len(report_text.strip()) < 20:
            report_text = "Mammography report with limited information available."
        
        return report_text
    
    def _determine_risk_level(self, predicted_birads: str) -> str:
        """Determine risk level based on BI-RADS score"""
        for risk_level, birads_scores in RISK_THRESHOLDS.items():
            if predicted_birads in birads_scores:
                return risk_level
        return "unknown"
    
    async def generate_prediction(
        self,
        document_id: str,
        structured_data: Dict,
        structuring_id: Optional[str] = None
    ) -> Prediction:
        """
        Generate risk prediction from structured data.
        
        Args:
            document_id: Document identifier
            structured_data: Structured mammography data
            structuring_id: Optional structuring result ID
            
        Returns:
            Prediction object with results
        """
        start_time = time.time()
        
        try:
            # Check if prediction already exists
            existing_prediction = self.db.query(Prediction).filter(
                Prediction.document_id == document_id
            ).first()
            
            if existing_prediction:
                logger.info(f"Prediction already exists for document {document_id}")
                return existing_prediction
            
            # Prepare text from structured data
            report_text = self._prepare_text_from_structured_data(structured_data)
            logger.info(f"Prepared text for prediction (length: {len(report_text)})")
            
            # Tokenize
            inputs = self.tokenizer(
                report_text,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=512
            )
            
            # Move to device
            inputs = {key: val.to(self.device) for key, val in inputs.items()}
            
            # Generate prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Process results
            logits = outputs.logits.cpu().numpy()[0]
            probabilities = softmax(logits)
            predicted_label_id = int(np.argmax(probabilities))
            predicted_birads = str(self.model.config.id2label[predicted_label_id])
            confidence_score = float(probabilities[predicted_label_id])
            
            # Create probability dictionary
            prob_dict = {
                str(self.model.config.id2label[i]): float(prob)
                for i, prob in enumerate(probabilities)
            }
            
            # Determine risk level
            risk_level = self._determine_risk_level(predicted_birads)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create prediction record
            prediction = Prediction(
                document_id=document_id,
                structuring_id=structuring_id,
                predicted_birads=predicted_birads,
                predicted_label_id=str(predicted_label_id),
                confidence_score=confidence_score,
                probabilities=prob_dict,
                risk_level=risk_level,
                model_version="biogpt-v1",
                model_path=self.model_path,
                input_text=report_text[:500],  # Store first 500 chars
                processing_time=processing_time,
                status="completed"
            )
            
            self.db.add(prediction)
            self.db.commit()
            self.db.refresh(prediction)
            
            logger.info(
                f"Prediction completed for document {document_id}: "
                f"BI-RADS={predicted_birads}, confidence={confidence_score:.3f}, "
                f"risk={risk_level}"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction failed for document {document_id}: {e}")
            
            # Store failed prediction
            prediction = Prediction(
                document_id=document_id,
                structuring_id=structuring_id,
                predicted_birads="unknown",
                predicted_label_id="unknown",
                confidence_score=0.0,
                probabilities={},
                risk_level="unknown",
                status="failed",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
            
            self.db.add(prediction)
            self.db.commit()
            self.db.refresh(prediction)
            
            raise
    
    def get_prediction_by_document(self, document_id: str) -> Optional[Prediction]:
        """Get prediction by document ID"""
        return self.db.query(Prediction).filter(
            Prediction.document_id == document_id
        ).first()
    
    def get_prediction_by_id(self, prediction_id: str) -> Optional[Prediction]:
        """Get prediction by prediction ID"""
        return self.db.query(Prediction).filter(
            Prediction.id == prediction_id
        ).first()
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None
