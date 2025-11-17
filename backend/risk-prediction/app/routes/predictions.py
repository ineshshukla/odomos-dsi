"""
Prediction routes for risk assessment
"""
from fastapi import APIRouter, Depends, HTTPException
import asyncio
from typing import Dict
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
from app.models.database import SessionLocal, Prediction as PredictionModel

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
    print(f"📥 Received prediction request for document: {request.document_id}")
    print(f"   Structuring ID: {request.structuring_id}")
    
    try:
        prediction_service = PredictionService(db)
        prediction = await prediction_service.generate_prediction(
            document_id=request.document_id,
            structured_data=request.structured_data,
            structuring_id=request.structuring_id
        )
        
        print(f"   ✅ Prediction completed with status: {prediction.status}")
        return PredictionResponse(
            prediction_id=prediction.id,
            document_id=prediction.document_id,
            status=prediction.status,
            message="Prediction completed successfully" if prediction.status == "completed" 
                    else f"Prediction failed: {prediction.error_message}"
        )
        
    except Exception as e:
        print(f"   ❌ Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/model/status", tags=["predictions"])
async def model_status(db: Session = Depends(get_db)):
    """Return whether the model is currently loaded"""
    service = PredictionService(db)
    return {"loaded": service.is_model_loaded(), "model_path": service.model_path}


@router.post("/predict-async", response_model=PredictionResponse, include_in_schema=False)
async def predict_async(
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    """Queue a prediction to run asynchronously and return immediately (internal use).

    This inserts/updates a pending Prediction record and schedules background work
    that will perform the actual model inference and update the record when done.
    """
    # Ensure a pending record exists
    existing = db.query(PredictionModel).filter(PredictionModel.document_id == request.document_id).first()
    if not existing:
        pending = PredictionModel(
            document_id=request.document_id,
            structuring_id=request.structuring_id,
            predicted_birads="unknown",
            predicted_label_id="unknown",
            confidence_score=0.0,
            probabilities={},
            risk_level="unknown",
            status="pending",
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
        prediction_id = pending.id
    else:
        existing.status = "pending"
        db.commit()
        prediction_id = existing.id

    # Background task to perform prediction using its own DB session
    async def _background_predict():
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 Starting background prediction for document {request.document_id}")
        
        session = SessionLocal()
        try:
            svc = PredictionService(session)
            # Force recompute so we overwrite the pending row
            result = await svc.generate_prediction(
                document_id=request.document_id,
                structured_data=request.structured_data,
                structuring_id=request.structuring_id,
                force_recompute=True,
            )
            logger.info(f"✅ Background prediction completed for document {request.document_id}: {result.status}")
        except Exception as e:
            logger.error(f"❌ Background prediction failed for document {request.document_id}: {str(e)}", exc_info=True)
            # Update the record with failure
            try:
                row = session.query(PredictionModel).filter(PredictionModel.document_id == request.document_id).first()
                if row:
                    row.status = "failed"
                    row.error_message = str(e)
                    session.commit()
                    logger.info(f"Updated prediction record to failed status")
            except Exception as update_error:
                logger.error(f"Failed to update error status: {str(update_error)}")
        finally:
            session.close()
            logger.info(f"🔚 Background task finished for document {request.document_id}")

    task = asyncio.create_task(_background_predict())
    # Add callback to log any unhandled exceptions
    def log_task_exception(t):
        if t.exception():
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unhandled exception in background task: {t.exception()}", exc_info=t.exception())
    task.add_done_callback(log_task_exception)

    return PredictionResponse(prediction_id=prediction_id, document_id=request.document_id, status="pending", message="Prediction queued")

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
        
        # Create prediction record if it doesn't exist yet (for pending predictions)
        if not prediction:
            prediction = Prediction(
                document_id=document_id,
                predicted_birads="unknown",
                predicted_label_id="unknown",
                confidence_score=0.0,
                probabilities={},
                risk_level="pending",
                status="pending",
                review_status=review_update.review_status,
                coordinator_notes=review_update.coordinator_notes,
                reviewed_by=current_user.get("sub"),
                reviewed_at=datetime.utcnow()
            )
            db.add(prediction)
        else:
            # Update existing prediction
            prediction.review_status = review_update.review_status
            prediction.coordinator_notes = review_update.coordinator_notes
            prediction.reviewed_by = current_user.get("sub")
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
