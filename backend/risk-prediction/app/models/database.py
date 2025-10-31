"""
Database models for Risk Prediction Service
"""
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Prediction(Base):
    """Prediction model for storing risk predictions"""
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, unique=True, index=True)
    structuring_id = Column(String, nullable=True)
    
    # Prediction results
    predicted_birads = Column(String, nullable=False)
    predicted_label_id = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=False)
    
    # Risk categorization
    risk_level = Column(String, nullable=False)  # high, medium, low, needs_assessment
    
    # Coordinator review
    review_status = Column(String, default="New")  # New, Under Review, Follow-up Initiated, Review Complete
    coordinator_notes = Column(String, nullable=True)
    reviewed_by = Column(String, nullable=True)  # User ID of the coordinator
    reviewed_at = Column(DateTime, nullable=True)
    
    # Model information
    model_version = Column(String, default="biogpt-v1")
    model_path = Column(String, nullable=True)
    
    # Processing metadata
    input_text = Column(String, nullable=True)  # Concatenated structured data
    processing_time = Column(Float, nullable=True)  # Time taken in seconds
    status = Column(String, default="completed")  # completed, failed
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
