#!/usr/bin/env python3
import requests
import zipfile
import io

# Create simple PDFs
def create_minimal_pdf(text):
    return f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td ({text}) Tj ET
endstream endobj
xref
0 5
trailer<</Size 5/Root 1 0 R>>
%%EOF""".encode()

# Create ZIP
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as zf:
    for i in range(1, 4):
        pdf = create_minimal_pdf(f"Report {i}")
        zf.writestr(f"report_{i}.pdf", pdf)
zip_buffer.seek(0)

# Test upload (with mock token)
try:
    from jose import jwt
    token = jwt.encode({
        "type": "access", 
        "role": "clinic_admin", 
        "sub": "test_user",
        "organization": "Test Clinic"
    }, "your-secret-key-change-this-in-production-2024", algorithm="HS256")
    
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': ('test.zip', zip_buffer, 'application/zip')}
    
    print("Uploading ZIP with 3 PDFs...")
    r = requests.post('http://localhost:8001/documents/upload', files=files, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
