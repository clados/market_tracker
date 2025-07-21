#!/bin/bash

# Migration script for Kalshi Market Tracker
# This script runs Alembic migrations locally against the RDS database

set -e

echo "🔧 Setting up migration environment..."

# For local development, use local database
# For production, uncomment the RDS section below
export DATABASE_URL="postgresql://dbadmin:password@localhost:5432/marketdb"

echo "📊 Database URL: postgresql://dbadmin:***@localhost:5432/marketdb"

# Uncomment the following lines for RDS deployment:
# RDS_ENDPOINT="kalshi-market-tracker-staging-rds-instance.cshk56mliado.us-west-2.rds.amazonaws.com"
# DB_PASSWORD=$(aws secretsmanager get-secret-value \
#   --secret-id "/copilot/kalshi-market-tracker/staging/secrets/DB_CREDENTIALS" \
#   --query 'SecretString' \
#   --output text | jq -r '.password')
# export DATABASE_URL="postgresql://dbadmin:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/marketdb"

# Change to backend directory for dependencies
cd backend

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Change to migrations directory
cd migrations

# Set environment variable for Alembic to use
echo "🔧 Setting DATABASE_URL environment variable..."
export ALEMBIC_DATABASE_URL="${DATABASE_URL}"

# Run migrations
echo "🚀 Running database migrations..."
alembic upgrade head

echo "✅ Migrations completed successfully!" 