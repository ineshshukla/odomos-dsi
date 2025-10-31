#!/usr/bin/env python3
"""
Run script for Risk Prediction Service
"""
import uvicorn
from app.config import PORT

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
