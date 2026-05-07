#!/usr/bin/env bash
# MiMo HomeOps Agent Pro — Disk cleanup
set -e

cd "$(dirname "$0")/.."

echo "=== Disk Cleanup ==="
echo "Before:"
df -h / | tail -1

# Python caches
echo "[1/5] Cleaning __pycache__..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Node build artifacts (keep node_modules)
echo "[2/5] Cleaning build artifacts..."
rm -rf frontend/dist frontend/build 2>/dev/null || true

# Logs
echo "[3/5] Cleaning logs..."
rm -rf logs/*.log 2>/dev/null || true

# Report cache (keep last 10)
echo "[4/5] Pruning old reports..."
if [ -d "backend/reports/generated" ]; then
    cd backend/reports/generated
    ls -t *.md 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    cd ../../..
fi

# SQLite vacuum
echo "[5/5] Vacuuming SQLite..."
if [ -f "backend/data/homeops.db" ]; then
    sqlite3 backend/data/homeops.db "VACUUM;"
    echo "  DB vacuumed."
fi

echo ""
echo "After:"
df -h / | tail -1
