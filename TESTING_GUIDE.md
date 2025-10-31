# Testing Guide for GCF Coordinator Dashboard

## Summary

✅ **All backend services are running and working!**
✅ **BioGPT model is loaded and making predictions!**
✅ **Database migration completed (clinic_name column added)**
✅ **Frontend dashboard ready to display real data**

### ⚠️ Important Note

Old documents uploaded before the latest fixes will NOT have predictions. You need to:
1. **Upload a NEW document** as clinic admin
2. Wait for it to complete: Upload → Parse → Structure → Predict
3. Login as GCF coordinator to see it with predictions

### Quick Test

```bash
# Check if all services are running
cd /Users/jallu/odomos-dsi/backend
./setup_and_run.sh status

# Test prediction service manually
cd risk-prediction
python test_prediction.py
```

Expected output: "Prediction successful! Predicted BI-RADS: 2, Risk Level: low"

## Testing Steps

### Backend Changes

1. **Authentication Service** (`backend/authentication/`)
   - Updated JWT token to include `organization` and `full_name` fields
   - File: `app/routes/auth.py`

2. **Document Ingestion Service** (`backend/document-ingestion/`)
   - Added `clinic_name` field to Document model
   - Document uploads now save the organization name from JWT token
   - List documents API now returns `clinic_name` and `upload_timestamp`
   - Files modified:
     - `app/models/database.py` - Added clinic_name column
     - `app/models/schemas.py` - Added clinic_name to DocumentStatus schema
     - `app/services/document_service.py` - Save clinic_name during upload
     - `app/routes/documents.py` - Include clinic_name in responses

### Frontend Changes

1. **GCF Dashboard** (`frontend/app/gcf-dashboard/page.tsx`)
   - Replaced placeholder data with real API calls
   - Fetches documents using `listDocuments()` API
   - Fetches predictions for each document using `getRiskPrediction()` API
   - Displays:
     - Risk Score (High/Medium/Low/Pending)
     - BI-RADS category with confidence percentage
     - Document filename
     - Clinic name
     - Submission date
   - Real-time auto-refresh every 10 seconds
   - Dynamic filtering by risk level and clinic
   - KPIs calculated from real data

2. **Type Definitions** (`frontend/lib/types.ts`)
   - Added `predicted` status to DocumentStatus
   - Added `clinic_name` and `upload_timestamp` fields

## Test Credentials

### Clinic Admin
- Email: `admin@gmail.com`
- Password: `pw`
- Organization: `Test Clinic`

### GCF Coordinator
- Email: `coord@gmail.com`
- Password: `pw`
- Organization: `GCF Program`

## Testing Steps

### Step 1: Start Backend Services

```bash
cd /Users/jallu/odomos-dsi/backend
./setup_and_run.sh start
```

Verify all 5 services are running:
- Authentication (port 8010)
- Document Ingestion (port 8001)
- Document Parsing (port 8002)
- Information Structuring (port 8003)
- Risk Prediction (port 8004)

### Step 2: Start Frontend

```bash
cd /Users/jallu/odomos-dsi/frontend
pnpm dev
```

### Step 3: Upload Documents as Clinic Admin

1. Open browser to `http://localhost:3000`
2. Login with clinic admin credentials (`admin@gmail.com` / `pw`)
3. You'll be redirected to the Clinic Portal
4. Upload a mammography report (PDF or text file)
5. Watch the document status progress:
   - Uploaded → Parsed → Structured → (Predicted)
6. The document will auto-refresh every 5 seconds

### Step 4: View Documents as GCF Coordinator

1. Logout from clinic admin
2. Login with GCF coordinator credentials (`coord@gmail.com` / `pw`)
3. You'll be redirected to the GCF Dashboard
4. The dashboard will show all documents from all clinics
5. For each document that's been structured, you'll see:
   - Risk Score badge (High/Medium/Low)
   - BI-RADS category with confidence percentage
   - Document filename
   - Clinic name (organization of the uploader)
   - Submission date
   - Review status

### Step 5: Test Filtering

1. **Search**: Type in the search box to filter by filename, clinic name, or document ID
2. **Risk Filter**: Select "High Risk", "Medium Risk", "Low Risk", or "Pending Assessment"
3. **Clinic Filter**: Select a specific clinic (dynamically populated from uploaded documents)

### Step 6: Verify KPIs

The KPI cards at the top should show real-time data:
- **New Reports Today**: Count of documents uploaded today
- **High-Risk Cases Pending**: Count of high-risk documents not marked as "Review Complete"
- **Medium-Risk Cases**: Count of all medium-risk documents
- **Total Reports Processed**: Total count of all documents

## Expected Flow

1. **Upload** (Clinic Admin) → Document saved with clinic name
2. **Parse** (Automatic) → Text extracted from PDF
3. **Structure** (Automatic) → Gemini API extracts structured data
4. **Predict** (Automatic) → BioGPT model predicts BI-RADS and risk level
5. **Display** (GCF Coordinator) → Dashboard shows all documents with predictions

## Auto-Refresh

- **Clinic Portal**: Refreshes every 5 seconds to show processing status updates
- **GCF Dashboard**: Refreshes every 10 seconds to show new documents and predictions

## Troubleshooting

### No Documents Appear
- Check that you're logged in as GCF coordinator
- Verify backend services are running: `./setup_and_run.sh status`
- Check browser console for API errors

### Predictions Not Showing
- Wait for document status to reach "structured" (may take 30-60 seconds)
- Check if Gemini API key is configured in `information-structuring/.env`
- Check risk-prediction logs: `tail -f logs/risk-prediction.log`

### Clinic Name Shows "Unknown Clinic"
- This happens for documents uploaded before the update
- New uploads will show the correct organization name
- You may need to delete old documents and re-upload

### Database Migration Needed
If you get database errors about missing `clinic_name` column:

```bash
cd /Users/jallu/odomos-dsi/backend/document-ingestion
# Backup existing data
cp document_ingestion.db document_ingestion.db.backup

# Delete and recreate database (WARNING: loses data)
rm document_ingestion.db

# Restart services to recreate tables
cd ..
./setup_and_run.sh restart
```

## API Endpoints Used

### Frontend → Backend

1. **List Documents** (GCF Dashboard)
   ```
   GET http://localhost:8001/documents/?page=1&limit=100
   ```

2. **Get Risk Prediction**
   ```
   GET http://localhost:8004/predictions/document/{document_id}
   ```

3. **Upload Document** (Clinic Portal)
   ```
   POST http://localhost:8001/documents/upload
   ```

## Testing Edge Cases

1. **No Predictions Yet**: Upload a document and check GCF dashboard immediately - should show "Pending"
2. **Multiple Clinics**: Create another clinic admin user and upload documents - coordinator should see both
3. **Failed Predictions**: Upload a non-medical document - prediction may fail, should show error gracefully
4. **Large Dataset**: Upload 10+ documents - pagination and filtering should work smoothly

## Notes

- The BioGPT model is loaded on first prediction request (may take 10-15 seconds)
- Gemini API requires internet connection and valid API key
- Document parsing works best with PDF files containing radiology reports
- Risk levels are determined by BI-RADS categories:
  - High: BI-RADS 4, 5, 6
  - Medium: BI-RADS 3
  - Low: BI-RADS 1, 2
  - Needs Assessment: BI-RADS 0
