@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo =========================================
echo    装了吗 - 软件安装助手
echo    今天你装了吗？
echo =========================================
echo.

set "ROOT=%~dp0"

:: ─── 1. 启动服务端 ───
echo [1/3] Starting server...
cd /d "%ROOT%server"

:: Install Python dependencies if needed
if not exist ".deps_installed" (
    echo   Installing Python dependencies...
    pip install -r requirements.txt -q
    type nul > .deps_installed
)

start "Zhuangle-Server" cmd /k "python main.py"
cd /d "%ROOT%"
timeout /t 3 /nobreak >nul

:: ─── 2. 启动管理后台（如已安装依赖）───
if exist "%ROOT%admin\node_modules" (
    echo [2/3] Starting admin panel...
    cd /d "%ROOT%admin"
    start "Zhuangle-Admin" cmd /k "npm start"
    cd /d "%ROOT%"
) else (
    echo [2/3] Admin panel skipped (run: cd admin ^&^& npm install)
)

:: ─── 3. 启动桌面应用（如已安装依赖）───
if exist "%ROOT%desktop\node_modules" (
    echo [3/3] Starting desktop app...
    cd /d "%ROOT%desktop"
    start "Zhuangle-Desktop" cmd /k "npm start"
    cd /d "%ROOT%"
) else (
    echo [3/3] Desktop app skipped (run: cd desktop ^&^& npm install)
)

echo.
echo =========================================
echo   Services started!
echo.
echo   前端页面:     http://localhost:8000/app
echo   服务端 API:   http://localhost:8000/api
echo   管理后台:     http://localhost:3001
echo =========================================
echo.
pause
