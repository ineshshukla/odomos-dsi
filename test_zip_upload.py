#!/usr/bin/env python3
"""
Test script for ZIP upload functionality
Creates a test ZIP file with sample PDFs and tests the upload endpoint
"""

import io
import zipfile
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8001"  # Document ingestion service
TOKEN = None  # Set this to a valid JWT token for testing

def create_test_pdfs(count=5):
    """Create sample PDF files in memory (minimal PDF structure)"""
    pdf_files = []
    
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    
    for i in range(count):
        filename = f"test_report_{i+1:03d}.pdf"
        pdf_files.append((filename, pdf_content))
    
    return pdf_files

def create_test_zip(pdf_files):
    """Create a ZIP file in memory with the given PDF files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in pdf_files:
            zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    return zip_buffer

def test_zip_upload(zip_file, token=None):
    """Test the ZIP upload endpoint"""
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    files = {
        'file': ('test_reports.zip', zip_file, 'application/zip')
    }
    
    data = {
        'description': 'Test batch upload'
    }
    
    print("🚀 Uploading ZIP file to API...")
    response = requests.post(
        f"{API_BASE_URL}/documents/upload-zip",
        files=files,
        data=data,
        headers=headers
    )
    
    return response

def main():
    print("=" * 60)
    print("ZIP Upload Functionality Test")
    print("=" * 60)
    
    # Check if token is set
    if not TOKEN:
        print("\n⚠️  Warning: No authentication token set!")
        print("To test with authentication, set the TOKEN variable in this script.")
        print("You can get a token by logging in through the frontend.\n")
        response = input("Continue without authentication? (y/n): ")
        if response.lower() != 'y':
            print("Exiting.")
            return
    
    # Create test PDFs
    print("\n📄 Creating test PDF files...")
    pdf_count = 5
    pdf_files = create_test_pdfs(pdf_count)
    print(f"✅ Created {pdf_count} test PDF files")
    
    # Create ZIP file
    print("\n📦 Creating ZIP archive...")
    zip_file = create_test_zip(pdf_files)
    zip_size = len(zip_file.getvalue())
    print(f"✅ Created ZIP file ({zip_size} bytes)")
    
    # Test upload
    print("\n🌐 Testing upload endpoint...")
    try:
        response = test_zip_upload(zip_file, TOKEN)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Body:")
        print("-" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Total Documents: {result.get('total_documents', 0)}")
            print(f"   Documents uploaded:")
            for i, doc in enumerate(result.get('documents', [])[:3], 1):
                print(f"      {i}. {doc.get('file_info', {}).get('filename', 'N/A')} "
                      f"(ID: {doc.get('upload_id', 'N/A')[:8]}...)")
            if len(result.get('documents', [])) > 3:
                print(f"      ... and {len(result['documents']) - 3} more")
        else:
            print(f"❌ Error!")
            try:
                error_data = response.json()
                print(f"   Detail: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   Make sure the document-ingestion service is running on port 8001")
        print("   You can start it with: docker-compose up document-ingestion")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
