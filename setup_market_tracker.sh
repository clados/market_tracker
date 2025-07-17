#!/bin/bash

# Market Tracker Setup Script
# Replaces Docker Compose with a sequential setup approach
# Sets up PostgreSQL, runs migrations, and processes data

set -e

echo "🚀 Setting up Market Tracker environment..."

# Configuration
DB_NAME="marketdb"
DB_USER="dbadmin"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"
CONTAINER_NAME="market-tracker-postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to setup PostgreSQL
setup_postgres() {
    print_status "Setting up PostgreSQL database..."
    
    # Check if container already exists
    if docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_status "PostgreSQL container already exists, starting it..."
        docker start "$CONTAINER_NAME"
    else
        print_status "Creating PostgreSQL container..."
        docker run -d --name "$CONTAINER_NAME" \
            -e POSTGRES_DB="$DB_NAME" \
            -e POSTGRES_USER="$DB_USER" \
            -e POSTGRES_PASSWORD="$DB_PASSWORD" \
            -p "$DB_PORT:5432" \
            -v market_tracker_pgdata:/var/lib/postgresql/data \
            postgres:15
        
        print_status "Waiting for PostgreSQL to start..."
        sleep 10
    fi
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    until docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME"; do
        sleep 2
    done
    
    print_success "PostgreSQL is ready"
}

# Function to setup Python environment for migrations
setup_migrations_env() {
    print_status "Setting up Python environment for migrations..."
    
    # Create virtual environment for migrations if it doesn't exist
    if [ ! -d "jobs/migrations/venv" ]; then
        print_status "Creating Python virtual environment for migrations..."
        python3 -m venv jobs/migrations/venv
    fi
    
    # Activate virtual environment
    print_status "Activating migrations virtual environment..."
    source jobs/migrations/venv/bin/activate
    
    # Install dependencies for migrations
    print_status "Installing migration dependencies..."
    pip install -r jobs/migrations/requirements.txt
    
    print_success "Migrations Python environment setup complete"
}

# Function to setup Python environment for data processor
setup_data_processor_env() {
    print_status "Setting up Python environment for data processor..."
    
    # Create virtual environment for data processor if it doesn't exist
    if [ ! -d "jobs/data-processor/venv" ]; then
        print_status "Creating Python virtual environment for data processor..."
        python3 -m venv jobs/data-processor/venv
    fi
    
    # Activate virtual environment
    print_status "Activating data processor virtual environment..."
    source jobs/data-processor/venv/bin/activate
    
    # Install dependencies for data processor
    print_status "Installing data processor dependencies..."
    pip install -r jobs/data-processor/requirements.txt
    
    print_success "Data processor Python environment setup complete"
}

# Function to run migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Set database URL
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Change to migrations directory
    cd jobs/migrations
    
    # Activate migrations virtual environment
    print_status "Activating migrations virtual environment..."
    source venv/bin/activate
    
    # Run migrations
    print_status "Executing Alembic migrations..."
    alembic upgrade head
    
    cd ../..
    print_success "Migrations completed successfully"
}

# Function to run data processor
run_data_processor() {
    print_status "Running data processor..."
    
    # Set database URL
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Check for Kalshi credentials
    if [ ! -f "jobs/data-processor/.env.local" ]; then
        print_warning ".env.local file not found in jobs/data-processor/"
        print_warning "You can create it with: cp jobs/data-processor/env.local.example jobs/data-processor/.env.local"
        print_warning "Then edit it to add your KALSHI_KEY_ID"
    fi
    
    # Change to data processor directory
    cd jobs/data-processor
    
    # Activate data processor virtual environment
    print_status "Activating data processor virtual environment..."
    source venv/bin/activate
    
    # Check if kalshi.pem exists
    if [ ! -f "kalshi.pem" ]; then
        print_warning "kalshi.pem file not found. Data processor may not work without Kalshi credentials."
    fi
    
    # Run the data processor
    print_status "Starting data processor job..."
    python job.py
    
    cd ../..
    print_success "Data processor completed"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Stop PostgreSQL container
    if docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_status "Stopping PostgreSQL container..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
    
    # Remove volume (optional - uncomment to delete all data)
    # docker volume rm market_tracker_pgdata 2>/dev/null || echo "Volume not found"
    
    print_success "Cleanup completed"
}

# Function to show status
show_status() {
    print_status "Current status:"
    
    if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_success "PostgreSQL container is running"
    else
        print_warning "PostgreSQL container is not running"
    fi
    
    if [ -d "jobs/migrations/venv" ]; then
        print_success "Migrations Python virtual environment exists"
    else
        print_warning "Migrations Python virtual environment not found"
    fi
    
    if [ -d "jobs/data-processor/venv" ]; then
        print_success "Data processor Python virtual environment exists"
    else
        print_warning "Data processor Python virtual environment not found"
    fi
}

# Function to show help
show_help() {
    echo "Market Tracker Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Complete setup (PostgreSQL + migrations + data processor)"
    echo "  db        - Setup PostgreSQL database only"
    echo "  migrate   - Run migrations only"
    echo "  process   - Run data processor only"
    echo "  status    - Show current status"
    echo "  cleanup   - Clean up containers and volumes"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Complete setup"
    echo "  $0 db        # Setup database only"
    echo "  $0 migrate   # Run migrations only"
}

# Main script logic
case "${1:-setup}" in
    "setup")
        check_docker
        setup_postgres
        setup_migrations_env
        setup_data_processor_env
        run_migrations
        run_data_processor
        print_success "Market Tracker setup completed successfully!"
        ;;
    "db")
        check_docker
        setup_postgres
        print_success "Database setup completed!"
        ;;
    "migrate")
        check_docker
        setup_migrations_env
        run_migrations
        print_success "Migrations completed!"
        ;;
    "process")
        check_docker
        setup_data_processor_env
        run_data_processor
        print_success "Data processing completed!"
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 