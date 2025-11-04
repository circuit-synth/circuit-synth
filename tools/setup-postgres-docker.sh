#!/bin/bash
# Setup PostgreSQL in Docker for TAC-X
# Creates database, user, and runs migrations

set -e

echo "=========================================="
echo "TAC-X PostgreSQL Setup (Docker)"
echo "=========================================="

# Configuration
CONTAINER_NAME="tacx-postgres"
DB_NAME="tacx"
DB_USER="tacx"
DB_PASS="tacx"
DB_PORT="5433"  # Use 5433 to avoid conflict with system PostgreSQL

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
fi

# Start PostgreSQL container
echo ""
echo "Starting PostgreSQL container..."
docker run --name $CONTAINER_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASS \
    -e POSTGRES_DB=$DB_NAME \
    -p $DB_PORT:5432 \
    -d postgres:15

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 3

# Test connection with retry logic
echo ""
echo "Testing connection..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready!"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "  Waiting for PostgreSQL to start... (attempt $RETRY_COUNT/$MAX_RETRIES)"
            sleep 2
        else
            echo "❌ PostgreSQL connection failed after $MAX_RETRIES attempts"
            echo ""
            echo "Debug info:"
            docker logs $CONTAINER_NAME | tail -20
            exit 1
        fi
    fi
done

# Export DATABASE_URL for migration runner
export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:$DB_PORT/$DB_NAME"

echo ""
echo "=========================================="
echo "PostgreSQL Setup Complete!"
echo "=========================================="
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASS"
echo ""
echo "DATABASE_URL:"
echo "  $DATABASE_URL"
echo ""
echo "To run migrations:"
echo "  export DATABASE_URL=\"$DATABASE_URL\""
echo "  python3 adws/database/run_migrations.py"
echo ""
echo "To connect with psql:"
echo "  docker exec -it $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME"
echo ""
echo "To stop container:"
echo "  docker stop $CONTAINER_NAME"
echo ""
echo "To remove container:"
echo "  docker rm $CONTAINER_NAME"
echo ""
