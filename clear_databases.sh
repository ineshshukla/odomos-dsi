#!/bin/bash
# Clear all databases and restart services

set -e

echo "🗑️  Clearing All Databases"
echo "========================="

# Stop all services
echo ""
echo "1️⃣  Stopping all services..."
docker-compose stop

# Clear database files from each service
echo ""
echo "2️⃣  Removing database files..."

services=("authentication" "document-ingestion" "document-parsing" "information-structuring" "risk-prediction")

for service in "${services[@]}"; do
    echo "   Clearing ${service}..."
    docker-compose run --rm --no-deps "$service" bash -c "rm -f /app/*.db /app/database.db" 2>/dev/null || true
done

# Remove any persisted volumes with databases
echo ""
echo "3️⃣  Clearing storage volumes..."
docker-compose run --rm --no-deps document-ingestion bash -c "rm -rf /app/storage/uploads/* /app/storage/temp/*" 2>/dev/null || true
docker-compose run --rm --no-deps document-parsing bash -c "rm -rf /app/storage/parsed/* /app/storage/temp/*" 2>/dev/null || true

# Remove shared storage if exists
docker volume rm odomos-dsi_shared_storage 2>/dev/null || echo "   No shared volume to remove"

echo ""
echo "4️⃣  Restarting services..."
docker-compose up -d

echo ""
echo "5️⃣  Waiting for services to initialize..."
sleep 5

# Check service health
echo ""
echo "6️⃣  Checking service health..."
for port in 8010 8001 8002 8003 8004 3000; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}" &>/dev/null; then
        echo "   ✅ Port ${port} responding"
    else
        echo "   ⚠️  Port ${port} not responding yet (may still be starting)"
    fi
done

echo ""
echo "========================="
echo "✅ Database cleanup complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. All databases have been cleared"
echo "   2. Services are restarting with fresh databases"
echo "   3. You may need to recreate super admin:"
echo "      docker-compose exec authentication python create_super_admin.py"
echo ""
echo "   4. All users and documents have been removed"
echo "   5. Ready for fresh testing"
