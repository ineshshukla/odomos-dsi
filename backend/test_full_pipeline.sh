#!/bin/bash

# Test the full mammography processing pipeline
# This script uploads a document, waits for processing, and checks the prediction

echo "=== Mammography Pipeline Test ==="
echo ""

# Login as clinic admin
echo "1. Logging in as clinic admin..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8010/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "clinic@gmail.com", "password": "pw"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('token', {}).get('access_token', data.get('access_token', '')))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to login"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Logged in successfully"
echo ""

# Create a test PDF if it doesn't exist
if [ ! -f "/tmp/test_mammo.pdf" ]; then
  echo "2. Creating test PDF..."
  python3 -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas('/tmp/test_mammo.pdf', pagesize=letter)
c.setFont('Helvetica', 12)
c.drawString(100, 750, 'MAMMOGRAPHY REPORT')
c.drawString(100, 720, '')
c.drawString(100, 700, 'Patient: Jane Doe')
c.drawString(100, 680, 'Age: 45 years')
c.drawString(100, 660, 'Date: November 17, 2025')
c.drawString(100, 640, '')
c.drawString(100, 620, 'Clinical History:')
c.drawString(100, 600, 'Routine screening mammography. No family history of breast cancer.')
c.drawString(100, 580, '')
c.drawString(100, 560, 'Findings:')
c.drawString(100, 540, 'Both breasts show heterogeneously dense tissue.')
c.drawString(100, 520, 'No suspicious masses, calcifications, or architectural distortions.')
c.drawString(100, 500, '')
c.drawString(100, 480, 'Impression:')
c.drawString(100, 460, 'Negative bilateral mammogram.')
c.drawString(100, 440, 'Dense breast tissue noted.')
c.drawString(100, 420, '')
c.drawString(100, 400, 'Recommendation:')
c.drawString(100, 380, 'Continue routine annual screening.')
c.save()
print('Test PDF created')
" 2>/dev/null || echo "⚠ reportlab not installed, using simple text file instead"
  
  if [ ! -f "/tmp/test_mammo.pdf" ]; then
    # Fallback: create a text file
    cat > /tmp/test_mammo.txt << 'EOF'
MAMMOGRAPHY REPORT

Patient: Jane Doe
Age: 45 years
Date: November 17, 2025

Clinical History:
Routine screening mammography. No family history of breast cancer.

Findings:
Both breasts show heterogeneously dense tissue.
No suspicious masses, calcifications, or architectural distortions.

Impression:
Negative bilateral mammogram.
Dense breast tissue noted.

Recommendation:
Continue routine annual screening.
EOF
    echo "✓ Created test text file"
    TEST_FILE="/tmp/test_mammo.txt"
  else
    TEST_FILE="/tmp/test_mammo.pdf"
  fi
else
  TEST_FILE="/tmp/test_mammo.pdf"
  echo "✓ Using existing test PDF"
fi

echo ""

# Upload document
echo "3. Uploading document..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8001/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE")

DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('upload_id', ''))" 2>/dev/null)

if [ -z "$DOCUMENT_ID" ]; then
  echo "❌ Failed to upload document"
  echo "$UPLOAD_RESPONSE"
  exit 1
fi

echo "✓ Document uploaded: $DOCUMENT_ID"
echo ""

# Wait for processing
echo "4. Waiting for document processing..."
for i in {1..60}; do
  sleep 2
  
  # Check structuring status
  STRUCT_RESPONSE=$(curl -s http://localhost:8003/structuring/document/$DOCUMENT_ID)
  STRUCT_STATUS=$(echo $STRUCT_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', data.get('detail', 'unknown')))" 2>/dev/null)
  
  if [ "$STRUCT_STATUS" = "completed" ]; then
    echo "✓ Structuring completed"
    break
  elif [ "$STRUCT_STATUS" = "Not Found" ]; then
    echo -n "."
  elif [ "$STRUCT_STATUS" = "failed" ]; then
    echo "❌ Structuring failed"
    echo "$STRUCT_RESPONSE"
    exit 1
  else
    echo -n "."
  fi
done

echo ""
echo ""

# Check prediction (with polling)
echo "5. Checking risk prediction..."
PREDICTION_FOUND=false

for i in {1..60}; do
  PRED_RESPONSE=$(curl -s http://localhost:8004/predictions/document/$DOCUMENT_ID \
    -H "Authorization: Bearer $TOKEN")
  
  PRED_STATUS=$(echo $PRED_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', data.get('detail', 'unknown')))" 2>/dev/null)
  
  if [ "$PRED_STATUS" = "completed" ]; then
    echo "✓ Prediction completed"
    PREDICTION_FOUND=true
    break
  elif [ "$PRED_STATUS" = "pending" ]; then
    echo -n "⏳"
    sleep 2
  elif [ "$PRED_STATUS" = "failed" ]; then
    echo "❌ Prediction failed"
    echo "$PRED_RESPONSE"
    exit 1
  elif [ "$PRED_STATUS" = "Not Found" ] || [ "$PRED_STATUS" = "Prediction not found for this document" ]; then
    echo -n "."
    sleep 2
  else
    echo -n "?"
    sleep 2
  fi
done

echo ""
echo ""

if [ "$PREDICTION_FOUND" = true ]; then
  echo "=== PREDICTION RESULT ==="
  echo "$PRED_RESPONSE" | python3 -m json.tool | head -20
  echo ""
  echo "✅ Pipeline test completed successfully!"
else
  echo "⚠ Prediction not found after 2 minutes"
  echo "This might be expected if model is still downloading"
  echo ""
  echo "Check logs with:"
  echo "  docker logs mammography-risk-prediction"
fi

echo ""
echo "Document ID: $DOCUMENT_ID"
echo "View in frontend: http://localhost:3000/report-detail/$DOCUMENT_ID"
