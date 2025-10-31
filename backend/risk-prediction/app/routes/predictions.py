"""
Prediction routes for risk assessment
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import (
    PredictionRequest,
    PredictionResponse,
    PredictionResult,
    ReviewStatusUpdate,
    ErrorResponse
)
from app.services.prediction_service import PredictionService
from app.utils.auth_middleware import get_any_user, get_current_user

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_risk(
    request: PredictionRequest,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Generate risk prediction from structured data (authenticated users)"""
    
    try:
        prediction_service = PredictionService(db)
        prediction = await prediction_service.generate_prediction(
            document_id=request.document_id,
            structured_data=request.structured_data,
            structuring_id=request.structuring_id
        )
        
        return PredictionResponse(
            prediction_id=prediction.id,
            document_id=prediction.document_id,
            status=prediction.status,
            message="Prediction completed successfully" if prediction.status == "completed" 
                    else f"Prediction failed: {prediction.error_message}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/document/{document_id}", response_model=PredictionResult)
async def get_prediction_by_document(
    document_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get prediction by document ID (authenticated users)"""
    
    prediction_service = PredictionService(db)
    prediction = prediction_service.get_prediction_by_document(document_id)
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found for this document")
    
    return PredictionResult(
        prediction_id=prediction.id,
        document_id=prediction.document_id,
        structuring_id=prediction.structuring_id,
        predicted_birads=prediction.predicted_birads,
        predicted_label_id=int(prediction.predicted_label_id) if prediction.predicted_label_id.isdigit() else 0,
        confidence_score=prediction.confidence_score,
        probabilities=prediction.probabilities,
        risk_level=prediction.risk_level,
        review_status=prediction.review_status,
        coordinator_notes=prediction.coordinator_notes,
        reviewed_by=prediction.reviewed_by,
        reviewed_at=prediction.reviewed_at,
        model_version=prediction.model_version,
        processing_time=prediction.processing_time,
        status=prediction.status,
        created_at=prediction.created_at
    )

@router.get("/{prediction_id}", response_model=PredictionResult)
async def get_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_any_user),
    db: Session = Depends(get_db)
):
    """Get prediction by prediction ID (authenticated users)"""
    
    prediction_service = PredictionService(db)
    prediction = prediction_service.get_prediction_by_id(prediction_id)
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return PredictionResult(
        prediction_id=prediction.id,
        document_id=prediction.document_id,
        structuring_id=prediction.structuring_id,
        predicted_birads=prediction.predicted_birads,
        predicted_label_id=int(prediction.predicted_label_id) if prediction.predicted_label_id.isdigit() else 0,
        confidence_score=prediction.confidence_score,
        probabilities=prediction.probabilities,
        risk_level=prediction.risk_level,
        review_status=prediction.review_status,
        coordinator_notes=prediction.coordinator_notes,
        reviewed_by=prediction.reviewed_by,
        reviewed_at=prediction.reviewed_at,
        model_version=prediction.model_version,
        processing_time=prediction.processing_time,
        status=prediction.status,
        created_at=prediction.created_at
    )

@router.post("/predict-internal", response_model=PredictionResponse, include_in_schema=False)
async def predict_risk_internal(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Internal endpoint for service-to-service communication (no auth required)"""
    
    try:
        prediction_service = PredictionService(db)
        prediction = await prediction_service.generate_prediction(
            document_id=request.document_id,
            structured_data=request.structured_data,
            structuring_id=request.structuring_id
        )
        
        return PredictionResponse(
            prediction_id=prediction.id,
            document_id=prediction.document_id,
            status=prediction.status,
            message="Prediction completed successfully" if prediction.status == "completed" 
                    else f"Prediction failed: {prediction.error_message}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.delete("/{document_id}/delete-internal", include_in_schema=False)
async def delete_prediction_internal(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Internal endpoint to delete prediction (no auth required)"""
    
    try:
        from app.models.database import Prediction
        prediction = db.query(Prediction).filter(Prediction.document_id == document_id).first()
        if prediction:
            db.delete(prediction)
            db.commit()
        
        return {"message": "Prediction deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.patch("/document/{document_id}/review")
async def update_review_status(
    document_id: str,
    review_update: ReviewStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update review status for a prediction (GCF Coordinators only)"""
    
    # Only GCF coordinators can update review status
    if current_user.get("role") != "gcf_coordinator":
        raise HTTPException(
            status_code=403, 
            detail="Only GCF coordinators can update review status"
        )
    
    try:
        from app.models.database import Prediction
        from datetime import datetime
        
        prediction = db.query(Prediction).filter(Prediction.document_id == document_id).first()
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found for this document")
        
        # Update review fields
        prediction.review_status = review_update.review_status
        prediction.coordinator_notes = review_update.coordinator_notes
        prediction.reviewed_by = current_user.get("sub")  # User ID
        prediction.reviewed_at = datetime.utcnow()
        prediction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(prediction)
        
        return PredictionResult(
            prediction_id=prediction.id,
            document_id=prediction.document_id,
            structuring_id=prediction.structuring_id,
            predicted_birads=prediction.predicted_birads,
            predicted_label_id=int(prediction.predicted_label_id),
            confidence_score=prediction.confidence_score,
            probabilities=prediction.probabilities,
            risk_level=prediction.risk_level,
            review_status=prediction.review_status,
            coordinator_notes=prediction.coordinator_notes,
            reviewed_by=prediction.reviewed_by,
            reviewed_at=prediction.reviewed_at,
            model_version=prediction.model_version,
            processing_time=prediction.processing_time,
            status=prediction.status,
            created_at=prediction.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
