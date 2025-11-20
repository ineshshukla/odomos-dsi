#!/usr/bin/env python3
"""
Startup script for risk-prediction service
Ensures model is loaded before starting the server
"""
import os
import sys
import logging
# Only import transformers if needed, or handle import error
try:
    from transformers import AutoTokenizer, BioGptForSequenceClassification
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload_model():
    """Preload the BioGPT model or wake up the Space"""
    try:
        # 1. Check if using Hugging Face Space
        use_space = os.getenv("USE_HF_SPACE", "false").lower() == "true"
        
        if use_space:
            space_name = os.getenv("HF_SPACE_NAME", "ishro/biogpt-aura")
            token = os.getenv("HUGGINGFACE_API_TOKEN")
            logger.info(f"🚀 Waking up Hugging Face Space: {space_name}...")
            
            try:
                from gradio_client import Client
                # Initializing the client connects to the Space and wakes it up
                client = Client(space_name, hf_token=token)
                logger.info(f"✅ Connected to Space: {space_name}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to connect to Space: {e}")
                # Don't return False here, we might want to fall back or just start anyway
                # But if the user explicitly wants Space, maybe we should warn loudly
                return False

        # 2. Fallback to Local/HF Hub Model
        model_repo = os.getenv("HUGGINGFACE_MODEL_REPO", "ishro/biogpt-aura")
        logger.info(f"🔄 Loading BioGPT model from {model_repo}...")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_repo)
        model = BioGptForSequenceClassification.from_pretrained(model_repo)
        
        logger.info("✅ Model loaded successfully!")
        logger.info(f"   Model config: {model.config.num_labels} classes")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to preload model: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting risk-prediction service...")
    
    # Preload model
    if preload_model():
        logger.info("✅ Model preloaded, starting server...")
        # Start the actual service
        os.system("python run.py")
    else:
        logger.error("❌ Model preload failed, but starting server anyway...")
        os.system("python run.py")
