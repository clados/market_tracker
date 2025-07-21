./setup_market_tracker.sh setup    # Complete setup

./setup_market_tracker.sh db       # Just database
./setup_market_tracker.sh migrate  # Just migrations
./setup_market_tracker.sh process  # Just data processing

./setup_market_tracker.sh status    # Check current status
./setup_market_tracker.sh cleanup   # Clean up containers

docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb
docker exec -it market-tracker-postgres psql -U dbadmin -d marketdb -c "SELECT COUNT(*) as total_history FROM price_history;"