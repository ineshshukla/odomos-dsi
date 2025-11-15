#!/usr/bin/env python3
"""
Test script to verify HuggingFace model download and loading.
Run this before starting the full service to ensure model access.
"""

import sys
import os
from transformers import AutoTokenizer, BioGptForSequenceClassification
import torch

# Configuration
HUGGINGFACE_REPO = "ishro/biogpt-aura"

def test_model_download():
    """Test downloading and loading model from HuggingFace"""
    
    print("="*60)
    print("HuggingFace Model Download Test")
    print("="*60)
    print(f"\nRepository: {HUGGINGFACE_REPO}")
    
    try:
        print("\n1. Downloading/Loading Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_REPO)
        print("   ✓ Tokenizer loaded successfully")
        
        print("\n2. Downloading/Loading Model...")
        model = BioGptForSequenceClassification.from_pretrained(HUGGINGFACE_REPO)
        print("   ✓ Model loaded successfully")
        
        print("\n3. Model Configuration:")
        print(f"   - Model type: {model.config.model_type}")
        print(f"   - Number of labels: {model.config.num_labels}")
        print(f"   - Label mappings: {model.config.id2label}")
        
        print("\n4. Device Check:")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"   - Available device: {device}")
        if device.type == "cuda":
            print(f"   - GPU name: {torch.cuda.get_device_name(0)}")
            print(f"   - GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        print("\n5. Moving model to device...")
        model.to(device)
        model.eval()
        print(f"   ✓ Model moved to {device}")
        
        print("\n6. Testing prediction...")
        test_text = "Mammography shows normal breast tissue. No masses or calcifications detected. BI-RADS category 1."
        inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        predicted_class = outputs.logits.argmax(-1).item()
        predicted_label = model.config.id2label[predicted_class]
        print(f"   ✓ Prediction successful!")
        print(f"   - Input text: {test_text[:100]}...")
        print(f"   - Predicted BI-RADS: {predicted_label}")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nThe model is ready to use in the risk-prediction service!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\n" + "="*60)
        print("TROUBLESHOOTING STEPS:")
        print("="*60)
        print("\n1. Check HuggingFace repository exists:")
        print(f"   https://huggingface.co/{HUGGINGFACE_REPO}")
        print("\n2. If repository is private, login to HuggingFace:")
        print("   huggingface-cli login")
        print("\n3. Check internet connection")
        print("\n4. Try clearing cache:")
        print("   rm -rf ~/.cache/huggingface/")
        print("\n5. Check disk space (model is ~1.5 GB)")
        
        return False


if __name__ == "__main__":
    success = test_model_download()
    sys.exit(0 if success else 1)
