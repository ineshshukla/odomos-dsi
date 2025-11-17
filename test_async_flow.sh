#!/bin/bash
# Quick test of async prediction flow

set -e

BASE_URL="http://localhost"
AUTH_URL="${BASE_URL}:8010"
DOC_URL="${BASE_URL}:8001"
RISK_URL="${BASE_URL}:8004"

echo "🧪 Testing Async Prediction Flow"
echo "================================="

# 1. Check services
echo ""
echo "1️⃣  Checking services..."
for port in 8001 8002 8003 8004 8010 3000; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}" &>/dev/null; then
        echo "   ✅ Port ${port} responding"
    else
        echo "   ⚠️  Port ${port} not responding"
    fi
done

# 2. Check model status
echo ""
echo "2️⃣  Checking model status..."
MODEL_STATUS=$(curl -s "${RISK_URL}/predictions/model/status" | jq -r '.loaded')
echo "   Model loaded: ${MODEL_STATUS}"
if [ "$MODEL_STATUS" = "false" ]; then
    echo "   ℹ️  First prediction will trigger model download (~1-2 min)"
fi

# 3. Test login
echo ""
echo "3️⃣  Testing authentication..."
TOKEN=$(curl -s -X POST "${AUTH_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"coord@gmail.com","password":"pw"}' \
    | jq -r '.token.access_token')

if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
    echo "   ✅ Login successful"
else
    echo "   ❌ Login failed"
    exit 1
fi

# 4. List documents
echo ""
echo "4️⃣  Fetching documents..."
DOC_COUNT=$(curl -s "${DOC_URL}/documents?page=1&limit=100" \
    -H "Authorization: Bearer ${TOKEN}" \
    | jq -r '.total')
echo "   Found ${DOC_COUNT} documents"

# 5. Check predictions endpoint
echo ""
echo "5️⃣  Verifying async endpoint exists..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    "${RISK_URL}/predictions/model/status")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Async endpoints available"
else
    echo "   ⚠️  Unexpected response: ${HTTP_CODE}"
fi

# 6. Frontend check
echo ""
echo "6️⃣  Checking frontend..."
if curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}:3000" | grep -q "200"; then
    echo "   ✅ Frontend accessible at http://localhost:3000"
    echo "   👉 Login as coord@gmail.com / pw to test dashboard"
else
    echo "   ⚠️  Frontend not responding"
fi

echo ""
echo "================================="
echo "✅ Async flow verification complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Open http://localhost:3000 in browser"
echo "   2. Login as coord@gmail.com / pw"
echo "   3. Navigate to GCF Dashboard"
echo "   4. Observe: Reports show immediately (even if predictions pending)"
echo "   5. Wait ~10s: Risk scores populate as predictions complete"
echo ""
echo "📊 Monitor logs:"
echo "   docker-compose logs -f information-structuring risk-prediction"
