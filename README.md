# Market Tracker

A real-time market tracking application that aggregates data from Kalshi and Polymarket prediction markets.

## Architecture

- **Frontend**: React/TypeScript with Tailwind CSS
- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL
- **Data Processing**: Separate scheduled jobs for Kalshi and Polymarket APIs
- **Deployment**: AWS Copilot with containerized services

## Components

- **Web Interface**: Single-column market cards with infinite scrolling
- **Data Processors**: Automated jobs fetching market data and price history
- **API Layer**: RESTful endpoints for market data and filtering
- **Database**: Stores markets, price history, and market changes

## Quick Start

```bash
# Complete setup
./setup_market_tracker.sh setup

# Individual components
./setup_market_tracker.sh db       # Database only
./setup_market_tracker.sh migrate  # Run migrations
./setup_market_tracker.sh process  # Start data processing

# Status and maintenance
./setup_market_tracker.sh status   # Check system status
./setup_market_tracker.sh cleanup  # Clean up containers
```

## Database Management

```bash
# Connect to database
docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb

# Check data counts
docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb -c "SELECT COUNT(*) as total_history FROM price_history;"

# Clear all data
docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb -c "TRUNCATE TABLE price_history, market_changes, markets CASCADE;"
```

## AWS Secrets Setup

```bash
# Create Kalshi private key secret
aws secretsmanager create-secret \
    --name "/kalshi-market-tracker/kalshi-private-key" \
    --description "Kalshi private key for data processor job" \
    --secret-string "$(cat jobs/data-processor/kalshi.pem)"

# Create Kalshi API key secret
aws secretsmanager create-secret \
    --name "/kalshi-market-tracker/kalshi-key-id" \
    --description "Kalshi API key ID for data processor job" \
    --secret-string "YOUR_ACTUAL_KEY_ID_HERE"
```

## Copilot Commands

```bash
# Drop all tables
copilot svc exec --name backend --command "bash -c 'cd /app && python -c \"from database import get_engine; from models import Base; engine = get_engine(); Base.metadata.drop_all(engine); print(\\\"Tables dropped\\\")\"'"

# Check migration status
copilot svc exec --name backend --command "bash -c 'export ALEMBIC_DATABASE_URL=\"postgresql://postgres:\$(echo \$DB_SECRET | jq -r .password)@\$DB_HOST:\$DB_PORT/\$DB_NAME\" && cd /app/migrations && alembic current'"
```