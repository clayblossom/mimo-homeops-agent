#!/usr/bin/env bash
# MiMo HomeOps Agent Pro — Dev runner
set -e

cd "$(dirname "$0")/.."

echo "=== MiMo HomeOps Agent Pro — Dev Mode ==="

# Backend
echo "[1/2] Starting backend..."
cd backend
if [ ! -d ".venv" ]; then
    echo "  Creating Python venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
else
    source .venv/bin/activate
fi

echo "  Backend on http://0.0.0.0:8700"
uvicorn app.main:app --host 0.0.0.0 --port 8700 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo "[2/2] Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  Installing frontend deps..."
    npm install --silent
fi
echo "  Frontend on http://0.0.0.0:5173"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both services starting..."
echo "   Backend:  http://localhost:8700"
echo "   Frontend: http://localhost:5173"
echo "   API docs: http://localhost:8700/docs"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
