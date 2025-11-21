#!/usr/bin/env python3
"""
Script to delete all documents from the Docker databases and storage
"""
import requests
from jose import jwt

# Configuration
API_BASE_URL = "http://localhost:3000"
SECRET_KEY = "your-secret-key-change-me-in-production"
ALGORITHM = "HS256"

# Create admin token
token = jwt.encode({
    "type": "access", 
    "role": "clinic_admin", 
    "sub": "admin_user",
    "organization": "Admin"
}, SECRET_KEY, algorithm=ALGORITHM)

headers = {'Authorization': f'Bearer {token}'}

print("🗑️  Deleting all documents from the system...")
print("=" * 60)

# Get all documents (paginated)
page = 1
page_size = 100
total_deleted = 0

while True:
    print(f"\n📄 Fetching page {page}...")
    
    try:
        response = requests.get(
            f"{API_URL}/documents/",
            headers=headers,
            params={'page': page, 'limit': page_size},
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch documents: {response.status_code}")
            print(f"Response: {response.text}")
            break
        
        data = response.json()
        documents = data.get('documents', [])
        
        if not documents:
            print("✅ No more documents to delete")
            break
        
        print(f"   Found {len(documents)} documents on this page")
        
        # Delete each document
        for doc in documents:
            doc_id = doc.get('upload_id')
            filename = doc.get('file_info', {}).get('filename', 'unknown')
            
            print(f"   🗑️  Deleting: {filename} (ID: {doc_id})")
            
            try:
                delete_response = requests.delete(
                    f'{API_BASE_URL}/documents/{doc_id}',
                    headers=headers,
                    timeout=10
                )
                
                if delete_response.status_code == 200:
                    total_deleted += 1
                    print(f"      ✅ Deleted successfully")
                else:
                    print(f"      ❌ Failed to delete: {delete_response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ Error deleting: {str(e)}")
        
        # Move to next page
        page += 1
        
    except Exception as e:
        print(f"❌ Error fetching documents: {str(e)}")
        break

print("\n" + "=" * 60)
print(f"✅ Deletion complete! Total documents deleted: {total_deleted}")
print("\n💡 Note: This clears the database entries and file references.")
print("   Physical files in storage directories remain until container restart.")
