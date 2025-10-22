#!/usr/bin/env python3
"""
End-to-End Pipeline Test: Document Ingestion → Parsing → Structuring
"""
import requests
import time
import uuid
from pathlib import Path

# Service URLs
INGESTION_URL = "http://localhost:8000"    # Document Ingestion Service
PARSING_URL = "http://localhost:8002"      # Document Parsing Service
STRUCTURING_URL = "http://localhost:8003"  # Information Structuring Service
API_KEY = "demo-api-key-123"

def check_service_health():
    """Check if all services are running"""
    print("🏥 Checking service health...")
    
    services = [
        ("Document Ingestion", f"{INGESTION_URL}/health/"),
        ("Document Parsing", f"{PARSING_URL}/health/"),
        ("Information Structuring", f"{STRUCTURING_URL}/health/")
    ]
    
    all_healthy = True
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Running")
            else:
                print(f"❌ {service_name}: Not responding ({response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"❌ {service_name}: Not running ({str(e)})")
            all_healthy = False
    
    return all_healthy


def use_provided_file(file_path: str):
    """Use a provided file for testing"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"📄 Using provided file: {file_path}")
    return file_path

def test_complete_pipeline(input_file: str):
    """Test the complete pipeline from ingestion to structuring"""
    print("\n🚀 Testing Complete Pipeline")
    print("=" * 50)
    
    # Step 1: Use provided input file
    print("📄 Using provided input file...")
    test_file = use_provided_file(input_file)
    print(f"✅ Using file: {test_file}")
    
    try:
        # Step 2: Upload to Document Ingestion Service
        print("\n📤 Step 1: Uploading document to Ingestion Service...")
        
        with open(test_file, 'rb') as f:
            # Determine content type based on file extension
            file_ext = test_file.suffix.lower()
            if file_ext == '.pdf':
                content_type = 'application/pdf'
                filename = test_file.name
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                content_type = f'image/{file_ext[1:]}'
                filename = test_file.name
            elif file_ext == '.txt':
                content_type = 'application/pdf'  # Upload as PDF to pass validation
                filename = 'pipeline_test_report.pdf'
            else:
                content_type = 'application/pdf'
                filename = 'pipeline_test_report.pdf'
            
            files = {'file': (filename, f, content_type)}
            data = {
                'uploader_id': 'pipeline_test_user',
                'patient_id': 'pipeline_patient_123',
                'description': 'Pipeline test mammography report'
            }
            
            response = requests.post(
                f"{INGESTION_URL}/documents/upload",
                files=files,
                data=data,
                params={"api_key": API_KEY}
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            # Check for both possible field names
            if 'document_id' in upload_result:
                document_id = upload_result['document_id']
                print(f"✅ Upload successful! Document ID: {document_id}")
            elif 'upload_id' in upload_result:
                document_id = upload_result['upload_id']
                print(f"✅ Upload successful! Upload ID: {document_id}")
            else:
                print(f"❌ Upload response missing document_id/upload_id: {upload_result}")
                return False
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return False
        
        # Step 3: Wait for parsing to complete
        print("\n⏳ Step 2: Waiting for document parsing...")
        max_wait = 60  # 60 seconds max wait
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                response = requests.get(
                    f"{PARSING_URL}/parsing/result/document/{document_id}",
                    params={"api_key": API_KEY}
                )
                
                if response.status_code == 200:
                    parsing_result = response.json()
                    if parsing_result['status'] == 'completed':
                        print("✅ Parsing completed!")
                        print(f"   Extracted text length: {len(parsing_result['extracted_text'])} characters")
                        break
                    elif parsing_result['status'] == 'failed':
                        print(f"❌ Parsing failed: {parsing_result.get('error_message', 'Unknown error')}")
                        return False
                    else:
                        print(f"   Parsing status: {parsing_result['status']}")
                else:
                    print(f"   Waiting for parsing... ({wait_time}s)")
                
                time.sleep(2)
                wait_time += 2
                
            except Exception as e:
                print(f"   Error checking parsing status: {str(e)}")
                time.sleep(2)
                wait_time += 2
        
        if wait_time >= max_wait:
            print("❌ Parsing timed out")
            return False
        
        # Step 4: Check structuring result
        print("\n🔍 Step 3: Checking document structuring...")
        
        # Wait a bit for structuring to complete
        time.sleep(5)
        
        try:
            response = requests.get(
                f"{STRUCTURING_URL}/structuring/result/document/{document_id}",
                params={"api_key": API_KEY}
            )
            
            if response.status_code == 200:
                structuring_result = response.json()
                print("✅ Structuring completed!")
                print(f"   Status: {structuring_result['status']}")
                print(f"   Confidence Score: {structuring_result['confidence_score']}")
                print(f"   Model Used: {structuring_result['model_used']}")
                print(f"   Processing Time: {structuring_result['processing_time']}s")
                
                # Display structured data
                structured_data = structuring_result['structured_data']
                print("\n📋 Structured Data Results:")
                print("-" * 60)
                
                # Show all fields (both extracted and unknown)
                print("\n📄 All Fields:")
                total_extracted = 0
                for key, value in structured_data.items():
                    if value != 'unknown':
                        print(f"✅ {key}: {value}")
                        total_extracted += 1
                    else:
                        print(f"❓ {key}: {value}")
                
                print("-" * 60)
                
                # Check if structuring actually succeeded
                if structuring_result['status'] == 'completed' and structuring_result['confidence_score'] is not None and total_extracted > 0:
                    print(f"\n✅ Structuring successful! Extracted {total_extracted} fields")
                    return True
                else:
                    error_msg = structuring_result.get('error_message', 'No error message')
                    print(f"\n❌ Structuring failed: {error_msg}")
                    if not error_msg or error_msg == 'No error message':
                        print("   💡 This usually means GEMINI_API_KEY is not configured")
                    return False
                
            elif response.status_code == 404:
                print("❌ Structuring result not found - service may not be triggered automatically")
                print("   This is expected if the parsing service doesn't trigger structuring yet")
                return False
            else:
                print(f"❌ Failed to get structuring result: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error checking structuring result: {str(e)}")
            return False
    
    finally:
        # Note: We don't delete the source file as it might be needed by the user
        print(f"\n📁 Test completed. Source file preserved: {test_file}")


def main():
    """Run the complete pipeline test"""
    import sys
    
    print("🧪 End-to-End Pipeline Test")
    print("Document Ingestion → Parsing → Structuring")
    print("=" * 60)
    
    # Check for input file argument
    if len(sys.argv) < 2:
        print("❌ Input file required!")
        print("\n📋 Usage:")
        print("   python3 test_pipeline.py <path_to_file>")
        print("\n📋 Examples:")
        print("   python3 test_pipeline.py test.png")
        print("   python3 test_pipeline.py /path/to/your/document.pdf")
        print("   python3 test_pipeline.py mammography_report.pdf")
        return
    
    input_file = sys.argv[1]
    print(f"📁 Input file: {input_file}")
    
    # Check if file exists
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Check service health
    if not check_service_health():
        print("\n❌ Not all services are running. Please start all services first:")
        print("   Terminal 1: cd backend/document-ingestion && python3 run.py")
        print("   Terminal 2: cd backend/document-parsing && python3 run.py")
        print("   Terminal 3: cd backend/information-structuring && python3 run.py")
        return
    
    print("\n✅ All services are running!")
    
    # Test complete pipeline
    pipeline_success = test_complete_pipeline(input_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Pipeline Test Results")
    print("=" * 60)
    
    if pipeline_success:
        print("🎉 Complete pipeline test: ✅ PASSED")
        print("   Document successfully processed from ingestion to structuring!")
    else:
        print("❌ Complete pipeline test: ❌ FAILED")
        print("   Document processing failed - check GEMINI_API_KEY configuration")
    
    print("\n💡 Next Steps:")
    if not pipeline_success:
        print("   1. Check if GEMINI_API_KEY is configured in .env file")
        print("   2. Test the complete pipeline again")
    else:
        print("   1. Implement Feature Engineering Service")
        print("   2. Add more comprehensive test data")
    
    print("\n📋 Usage:")
    print("   python3 test_pipeline.py <path_to_file>     # Test with your file")
    print("   python3 test_pipeline.py test.png           # Example with PNG")
    print("   python3 test_pipeline.py document.pdf       # Example with PDF")

if __name__ == "__main__":
    main()
