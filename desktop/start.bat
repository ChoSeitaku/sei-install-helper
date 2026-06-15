@echo off
chcp 65001 >nul 2>&1
echo Starting Zhuangle Desktop...
cd /d "%~dp0"
"node_modules\electron\dist\electron.exe" .
