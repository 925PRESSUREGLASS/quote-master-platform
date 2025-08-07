# WSL Setup and Fix Script for Quote Master Pro
# Run this script as Administrator in PowerShell

Write-Host "🔧 Setting up WSL for Quote Master Pro..." -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green

# Enable WSL feature
Write-Host "📋 Step 1: Enabling WSL feature..." -ForegroundColor Cyan
try {
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    Write-Host "✅ WSL feature enabled successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to enable WSL feature: $_" -ForegroundColor Red
}

# Enable Virtual Machine Platform
Write-Host "📋 Step 2: Enabling Virtual Machine Platform..." -ForegroundColor Cyan
try {
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    Write-Host "✅ Virtual Machine Platform enabled successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to enable Virtual Machine Platform: $_" -ForegroundColor Red
}

# Enable Hyper-V (if available)
Write-Host "📋 Step 3: Checking Hyper-V..." -ForegroundColor Cyan
try {
    $hyperv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
    if ($hyperv.State -eq "Disabled") {
        dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V /all /norestart
        Write-Host "✅ Hyper-V enabled successfully" -ForegroundColor Green
    } else {
        Write-Host "✅ Hyper-V is already enabled" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Hyper-V not available or failed to enable (this is OK for WSL2)" -ForegroundColor Yellow
}

# Set WSL 2 as default version
Write-Host "📋 Step 4: Setting WSL 2 as default..." -ForegroundColor Cyan
try {
    wsl --set-default-version 2
    Write-Host "✅ WSL 2 set as default version" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not set WSL 2 as default (will set after reboot)" -ForegroundColor Yellow
}

# Download and install Ubuntu (optional)
Write-Host "📋 Step 5: Installing Ubuntu distribution..." -ForegroundColor Cyan
$installUbuntu = Read-Host "Do you want to install Ubuntu 22.04 LTS? (y/n)"
if ($installUbuntu -eq "y" -or $installUbuntu -eq "Y") {
    try {
        wsl --install -d Ubuntu-22.04
        Write-Host "✅ Ubuntu 22.04 installation initiated" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Ubuntu installation failed or already exists" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 WSL setup completed!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart your computer to complete WSL installation" -ForegroundColor White
Write-Host "2. After restart, open PowerShell and run: wsl --list --verbose" -ForegroundColor White  
Write-Host "3. Start Docker Desktop - it should now work with WSL2" -ForegroundColor White
Write-Host "4. Return to your Quote Master Pro project and run: docker-compose up redis" -ForegroundColor White

$reboot = Read-Host "`nDo you want to restart now? (y/n)"
if ($reboot -eq "y" -or $reboot -eq "Y") {
    Write-Host "🔄 Restarting computer in 10 seconds..." -ForegroundColor Yellow
    Start-Sleep 10
    Restart-Computer -Force
}
