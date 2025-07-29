./setup_market_tracker.sh setup    # Complete setup

./setup_market_tracker.sh db       # Just database
./setup_market_tracker.sh migrate  # Just migrations
./setup_market_tracker.sh process  # Just data processing

./setup_market_tracker.sh status    # Check current status
./setup_market_tracker.sh cleanup   # Clean up containers

docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb
docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb -c "SELECT COUNT(*) as total_history FROM price_history;"

docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb -c "TRUNCATE TABLE price_history, market_changes, markets CASCADE;"

aws secretsmanager create-secret \
    --name "/kalshi-market-tracker/kalshi-private-key" \
    --description "Kalshi private key for data processor job" \
    --secret-string "$(cat jobs/data-processor/kalshi.pem)"


aws secretsmanager create-secret \
    --name "/kalshi-market-tracker/kalshi-key-id" \
    --description "Kalshi API key ID for data processor job" \
    --secret-string "YOUR_ACTUAL_KEY_ID_HERE"


copilot svc exec --name backend --command "bash -c 'cd /app && python -c \"from database import get_engine; from models import Base; engine = get_engine(); Base.metadata.drop_all(engine); print(\\\"Tables dropped\\\")\"'"

copilot svc exec --name backend --command "bash -c 'export ALEMBIC_DATABASE_URL=\"postgresql://postgres:\$(echo \$DB_SECRET | jq -r .password)@\$DB_HOST:\$DB_PORT/\$DB_NAME\" && cd /app/migrations && alembic current'"