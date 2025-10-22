#!/usr/bin/env python3
"""
Debug what text was actually extracted from the document
"""
import requests
import sys
from pathlib import Path

# Service configuration
PARSING_URL = "http://localhost:8002"
API_KEY = "demo-api-key-123"

def get_extracted_text(document_id: str):
    """Get the extracted text from parsing service"""
    try:
        response = requests.get(
            f"{PARSING_URL}/parsing/result/document/{document_id}",
            params={"api_key": API_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('extracted_text', '')
        else:
            print(f"❌ Failed to get extracted text: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 debug_extracted_text.py <document_id>")
        return
    
    document_id = sys.argv[1]
    print(f"🔍 Getting extracted text for document: {document_id}")
    
    extracted_text = get_extracted_text(document_id)
    
    if extracted_text:
        print(f"\n📄 Extracted Text ({len(extracted_text)} characters):")
        print("=" * 60)
        print(extracted_text)
        print("=" * 60)
        
        # Check for specific fields
        print(f"\n🔍 Field Analysis:")
        fields_to_check = ['age', 'children', 'lmp', 'hormonal', 'birth', 'year', 'old']
        
        for field in fields_to_check:
            if field.lower() in extracted_text.lower():
                print(f"✅ Found '{field}' in text")
            else:
                print(f"❌ '{field}' not found in text")
    else:
        print("❌ Could not retrieve extracted text")

if __name__ == "__main__":
    main()
