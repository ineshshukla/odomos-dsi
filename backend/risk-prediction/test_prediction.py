#!/usr/bin/env python3
"""
Test script to verify the BioGPT model is working in the risk-prediction service
"""
import requests
import json

# Sample structured data for testing
test_structured_data = {
    "observations": "Dense fibroglandular tissue. A 12mm irregular, spiculated mass is noted in the upper outer quadrant of the left breast.",
    "impression": "Suspicious finding.",
    "birads_assessment": None,
    "recommendations": "Ultrasound-guided biopsy is recommended."
}

def test_prediction():
    print("🧪 Testing Risk Prediction Service...")
    print("=" * 60)
    
    # Test health endpoint first
    try:
        response = requests.get("http://localhost:8004/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"   {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("📊 Testing prediction with sample radiology report...")
    print("=" * 60)
    
    # Test prediction
    payload = {
        "document_id": "test-doc-123",
        "structuring_id": "test-struct-456",
        "structured_data": test_structured_data
    }
    
    try:
        response = requests.post(
            "http://localhost:8004/predictions/predict-internal",
            json=payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Prediction successful!")
            print(f"\n📋 Results:")
            print(f"   Predicted BI-RADS: {result.get('predicted_birads')}")
            print(f"   Risk Level: {result.get('risk_level')}")
            print(f"   Confidence: {result.get('confidence_score'):.2%}")
            print(f"\n   Probabilities:")
            for birads, prob in result.get('probabilities', {}).items():
                print(f"      BI-RADS {birads}: {prob:.2%}")
        else:
            print(f"\n❌ Prediction failed!")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_prediction()
