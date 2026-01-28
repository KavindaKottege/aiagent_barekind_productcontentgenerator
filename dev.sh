#!/bin/bash

# Development startup script
# Usage: ./dev.sh [start|stop|logs]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[DEV]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# PID file locations
PID_DIR="$PROJECT_DIR/.dev-pids"
mkdir -p "$PID_DIR"

start_services() {
    log "Starting Docker services (PostgreSQL + Redis)..."
    docker-compose up -d

    log "Waiting for PostgreSQL to be ready..."
    until docker exec dev_postgres pg_isready -U devuser -d candidfounders_db > /dev/null 2>&1; do
        sleep 1
    done
    log "PostgreSQL is ready!"

    log "Waiting for Redis to be ready..."
    until docker exec dev_redis redis-cli ping > /dev/null 2>&1; do
        sleep 1
    done
    log "Redis is ready!"

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    log "Running database migrations..."
    cd "$BACKEND_DIR"
    alembic upgrade head

    log "Seeding development data..."
    python scripts/seed_dev.py || warn "Seed script may have already run (this is fine)"

    log "Starting FastAPI backend on port 8000..."
    cd "$BACKEND_DIR"
    uvicorn app.main:app --reload --port 8000 > "$PID_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"

    log "Starting ARQ worker..."
    cd "$BACKEND_DIR"
    arq app.workers.worker_settings.WorkerSettings > "$PID_DIR/worker.log" 2>&1 &
    echo $! > "$PID_DIR/worker.pid"

    log "Starting Next.js frontend on port 3000..."
    cd "$FRONTEND_DIR"
    npm run dev > "$PID_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"

    sleep 2

    echo ""
    log "All services started!"
    echo ""
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  pgAdmin:   http://localhost:5050"
    echo ""
    echo "  Login:     dev@example.com / devpassword"
    echo ""
    echo "  Logs:      ./dev.sh logs"
    echo "  Stop:      ./dev.sh stop"
    echo ""
}

stop_services() {
    log "Stopping services..."

    # Stop Node/Python processes
    for service in backend worker frontend; do
        if [ -f "$PID_DIR/$service.pid" ]; then
            pid=$(cat "$PID_DIR/$service.pid")
            if kill -0 "$pid" 2>/dev/null; then
                log "Stopping $service (PID $pid)..."
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$PID_DIR/$service.pid"
        fi
    done

    # Also kill any orphaned processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "arq app.workers" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true

    log "Stopping Docker services..."
    docker-compose down

    log "All services stopped!"
}

show_logs() {
    echo "=== Backend Log (last 20 lines) ==="
    tail -20 "$PID_DIR/backend.log" 2>/dev/null || echo "No backend log"
    echo ""
    echo "=== Worker Log (last 20 lines) ==="
    tail -20 "$PID_DIR/worker.log" 2>/dev/null || echo "No worker log"
    echo ""
    echo "=== Frontend Log (last 20 lines) ==="
    tail -20 "$PID_DIR/frontend.log" 2>/dev/null || echo "No frontend log"
    echo ""
    echo "For live logs, use: tail -f .dev-pids/*.log"
}

case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|logs]"
        exit 1
        ;;
esac
