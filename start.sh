#!/bin/bash

echo "========================================="
echo "   装了吗 - 软件安装助手"
echo "   今天你装了吗？"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── 1. 启动服务端 ───
echo "[1/3] Starting server..."
cd "$SCRIPT_DIR/server"

# Install Python dependencies if needed
if [ ! -d "$SCRIPT_DIR/server/venv" ] && [ ! -f "$SCRIPT_DIR/server/.deps_installed" ]; then
    echo "  Installing Python dependencies..."
    pip install -r requirements.txt -q && touch .deps_installed
fi

python main.py &
SERVER_PID=$!
cd "$SCRIPT_DIR"
sleep 2

# ─── 2. 启动管理后台（如已安装依赖）───
ADMIN_PID=""
if [ -d "$SCRIPT_DIR/admin/node_modules" ]; then
    echo "[2/3] Starting admin panel..."
    cd "$SCRIPT_DIR/admin"
    npm start &
    ADMIN_PID=$!
    cd "$SCRIPT_DIR"
else
    echo "[2/3] Admin panel skipped (run: cd admin && npm install)"
fi

# ─── 3. 启动桌面应用（如已安装依赖）───
DESKTOP_PID=""
if [ -d "$SCRIPT_DIR/desktop/node_modules" ]; then
    echo "[3/3] Starting desktop app..."
    cd "$SCRIPT_DIR/desktop"
    npm start &
    DESKTOP_PID=$!
    cd "$SCRIPT_DIR"
else
    echo "[3/3] Desktop app skipped (run: cd desktop && npm install)"
fi

echo ""
echo "========================================="
echo "  Services started!"
echo ""
echo "  前端页面:     http://localhost:8000/app"
echo "  服务端 API:   http://localhost:8000/api"
echo "  管理后台:     http://localhost:3001"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop all services"

cleanup() {
    echo ""
    echo "Stopping services..."
    [ -n "$SERVER_PID" ] && kill $SERVER_PID 2>/dev/null
    [ -n "$ADMIN_PID" ] && kill $ADMIN_PID 2>/dev/null
    [ -n "$DESKTOP_PID" ] && kill $DESKTOP_PID 2>/dev/null
    exit
}

trap cleanup INT TERM
wait
