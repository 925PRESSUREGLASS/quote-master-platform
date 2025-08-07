@echo off
echo 🔧 WSL Fix Script for Quote Master Pro
echo.
echo This script will fix WSL issues for Docker Desktop
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running with Administrator privileges
) else (
    echo ❌ This script requires Administrator privileges!
    echo Please run as Administrator
    echo Right-click on this file and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo 📋 Step 1: Enabling WSL feature...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
if %errorLevel% == 0 (
    echo ✅ WSL feature enabled successfully
) else (
    echo ❌ Failed to enable WSL feature
)

echo.
echo 📋 Step 2: Enabling Virtual Machine Platform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
if %errorLevel% == 0 (
    echo ✅ Virtual Machine Platform enabled successfully
) else (
    echo ❌ Failed to enable Virtual Machine Platform
)

echo.
echo 📋 Step 3: Enabling Hyper-V (if available)...
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
if %errorLevel% == 0 (
    echo ✅ Hyper-V enabled successfully
) else (
    echo ⚠️ Hyper-V not available (this is OK for WSL2)
)

echo.
echo 🎉 WSL setup completed!
echo.
echo 📋 Next steps:
echo 1. Restart your computer to complete WSL installation
echo 2. After restart, open PowerShell and run: wsl --list --verbose
echo 3. Start Docker Desktop - it should now work with WSL2
echo 4. Return to your Quote Master Pro project and run: docker-compose up redis
echo.

set /p reboot="Do you want to restart now? (y/n): "
if /i "%reboot%"=="y" (
    echo 🔄 Restarting computer in 10 seconds...
    timeout /t 10
    shutdown /r /t 0
) else (
    echo Please restart manually when ready
)

pause
