@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo    Installing Electron...
echo ========================================

cd /d "%~dp0"

:: Set Chinese mirror
set ELECTRON_MIRROR=https://registry.npmmirror.com/-/binary/electron/
set ELECTRON_CUSTOM_DIR=electron/v28.1.0

:: Install dependencies
echo Installing dependencies...
call yarn install

:: Install electron binary
echo Downloading electron binary...
call node node_modules\electron\install.js

echo.
echo ========================================
echo Installation complete!
echo Run: npx electron .
echo ========================================
pause
