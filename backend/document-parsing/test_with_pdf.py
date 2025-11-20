#!/usr/bin/env python3
"""
Test Document Parsing Service with a real PDF file
"""
import requests
import uuid
from pathlib import Path

# Service configuration
PARSING_URL = "http://localhost:8002"
API_KEY = "demo-api-key-123"

def test_with_pdf(pdf_path: str):
    """Test parsing with a real PDF file"""
    print(f"🔍 Testing with PDF: {pdf_path}")
    print("=" * 50)
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Generate unique document ID
    document_id = f"pdf-test-{uuid.uuid4().hex[:8]}"
    
    try:
        # Test parsing request
        # Use internal endpoint to bypass auth for testing
        # Also ensure path is correct for inside the container
        container_file_path = f"/app/{Path(pdf_path).name}"
        
        payload = {
            "document_id": document_id,
            "file_path": container_file_path
        }
        
        print(f"📤 Sending parsing request...")
        print(f"Document ID: {document_id}")
        print(f"File path (container): {container_file_path}")
        
        response = requests.post(
            f"{PARSING_URL}/parsing/parse-internal",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Parsing successful!")
            print(f"Parsing ID: {result['parsing_id']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            
            # Get the full result
            print("\n📋 Getting full parsing result...")
            result_response = requests.get(
                f"{PARSING_URL}/parsing/result/{result['parsing_id']}",
                params={"api_key": API_KEY}
            )
            
            if result_response.status_code == 200:
                full_result = result_response.json()
                print("✅ Full result retrieved!")
                print(f"Status: {full_result['status']}")
                print(f"Extracted text length: {len(full_result['extracted_text'])} characters")
                print("\n📄 Extracted text:")
                print("-" * 60)
                print(full_result['extracted_text'])
                print("-" * 60)
            else:
                print(f"❌ Failed to get full result: {result_response.status_code}")
                print(result_response.text)
                
        else:
            print(f"❌ Parsing failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def create_sample_pdf():
    """Create a sample PDF for testing"""
    print("📄 Creating sample PDF...")
    
    # Create a simple text file that looks like a mammography report
    sample_content = """
    MAMMOGRAPHY REPORT
    
    Patient Information:
    Name: Jane Smith
    DOB: 01/15/1975
    Patient ID: 12345
    
    Exam Information:
    Date: 2024-01-15
    Indication: Routine screening mammography
    Technique: Digital mammography, bilateral CC and MLO views
    
    Clinical History:
    Patient presents for routine screening mammography.
    No breast symptoms or concerns.
    
    Findings:
    BREAST COMPOSITION: The breasts are heterogeneously dense, which may
    obscure small masses.
    
    RIGHT BREAST: No suspicious masses, architectural distortion, or
    suspicious calcifications identified.
    
    LEFT BREAST: No suspicious masses, architectural distortion, or
    suspicious calcifications identified.
    
    Assessment:
    BI-RADS Category 2: Benign findings
    
    Recommendation:
    Routine screening mammography in 12 months.
    
    Radiologist: Dr. Smith
    Date: 2024-01-15
    """
    
    # Save as text file (you can convert to PDF manually)
    sample_file = Path("sample_mammography_report.txt")
    sample_file.write_text(sample_content)
    
    print(f"✅ Created sample file: {sample_file}")
    print("💡 To test with a real PDF:")
    print("   1. Convert this file to PDF using LibreOffice or online converter")
    print("   2. Run: python3 test_with_pdf.py your_file.pdf")
    
    return sample_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test with provided PDF file
        pdf_path = sys.argv[1]
        test_with_pdf(pdf_path)
    else:
        # Create sample file and show instructions
        print("🧪 PDF Testing for Document Parsing Service")
        print("=" * 50)
        
        sample_file = create_sample_pdf()
        
        print("\n📋 Usage:")
        print("  python3 test_with_pdf.py <path_to_pdf_file>")
        print("\n📋 Example:")
        print("  python3 test_with_pdf.py sample_mammography_report.pdf")
        print("  python3 test_with_pdf.py /path/to/your/document.pdf")
