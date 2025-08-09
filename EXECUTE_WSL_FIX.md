# 🚀 EXECUTE WSL FIX - STEP BY STEP GUIDE

## **IMPORTANT: Follow These Exact Steps**

### **Step 1: Open PowerShell as Administrator**

1. **Press `Windows Key + X`**
2. **Select "Windows PowerShell (Admin)" or "Terminal (Admin)"**
3. **Click "Yes" when prompted by User Account Control**
4. **Verify you see "Administrator" in the title bar**

### **Step 2: Navigate to Project Directory**

```powershell
# Navigate to your Quote Master Pro project
cd "C:\Users\95cle\Desktop\925WEB"

# Verify you're in the right location
ls scripts/
```

### **Step 3: Execute the WSL Fix Script**

```powershell
# Run the comprehensive WSL fix
.\scripts\complete_wsl_fix.ps1
```

### **Step 4: Follow Script Prompts**

The script will ask several questions:

1. **Install Ubuntu 22.04?** → Type `y` and press Enter
2. **Download Docker Desktop?** → Type `y` if not installed
3. **Restart computer now?** → Type `y` when ready

### **Step 5: After Restart**

1. **Run the post-reboot verification script** (will be on your Desktop)
2. **Start Docker Desktop**
3. **Configure Docker WSL integration**

---

## **ALTERNATIVE: Manual WSL Fix Steps**

If the automated script has issues, follow these manual steps:

### **Manual Step 1: Enable Windows Features**

```powershell
# Run these commands in Administrator PowerShell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Containers /all /norestart
```

### **Manual Step 2: Download WSL2 Kernel**

```powershell
# Download and install WSL2 kernel update
$url = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$output = "$env:TEMP\wsl_update_x64.msi"
Invoke-WebRequest -Uri $url -OutFile $output
Start-Process msiexec.exe -Wait -ArgumentList "/i $output /quiet"
```

### **Manual Step 3: Configure WSL**

```powershell
# Set WSL 2 as default
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu-22.04
```

### **Manual Step 4: Create WSL Config**

```powershell
# Create optimized WSL configuration
$config = @"
[wsl2]
memory=4GB
processors=2
swap=1GB
localhostForwarding=true

[experimental]
sparseVhd=true
"@

$config | Out-File -FilePath "$env:USERPROFILE\.wslconfig" -Encoding utf8 -Force
```

### **Manual Step 5: Restart**

```powershell
# Restart to complete installation
Restart-Computer -Force
```

---

## **POST-RESTART VERIFICATION**

After restart, open PowerShell and run:

```powershell
# Check WSL installation
wsl --list --verbose

# Should show Ubuntu-22.04 running version 2
```

Expected output:
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Stopped         2
```

### **Start Docker Desktop**

1. **Launch Docker Desktop**
2. **Go to Settings → General**
3. **Enable "Use the WSL 2 based engine"**
4. **Go to Resources → WSL Integration**
5. **Enable integration with Ubuntu-22.04**

### **Test Docker Integration**

```powershell
# Navigate to project
cd "C:\Users\95cle\Desktop\925WEB"

# Test Docker Compose
docker-compose -f docker-compose.prod.yml ps

# Should work without errors
```

---

## **VERIFICATION CHECKLIST**

After completing the fix, verify:

- [ ] WSL 2 is installed and running
- [ ] Ubuntu-22.04 distribution is available
- [ ] Docker Desktop starts without errors
- [ ] Docker WSL integration is enabled
- [ ] `docker-compose ps` works in your project
- [ ] Quote Master Pro containers can be started

---

## **EXPECTED TIMELINE**

- **Setup Phase**: 10-15 minutes
- **Download Phase**: 5-10 minutes
- **Restart Required**: 2-3 minutes
- **Verification**: 5 minutes
- **Total Time**: ~30 minutes

---

## **TROUBLESHOOTING**

### **If WSL install fails:**
```powershell
# Check Windows version (needs 10 v2004+ or 11)
Get-ComputerInfo | Select WindowsProductName, WindowsVersion

# Update Windows if needed
```

### **If Docker won't start:**
```powershell
# Reset Docker to factory defaults
& "C:\Program Files\Docker\Docker\Docker Desktop.exe" --reset-to-factory
```

### **If integration fails:**
```powershell
# Reinstall WSL integration
wsl --unregister Ubuntu-22.04
wsl --install -d Ubuntu-22.04
```

---

## **NEXT STEPS AFTER FIX**

Once WSL is working:

1. **Full Docker Deployment**
   ```bash
   cd C:\Users\95cle\Desktop\925WEB
   .\scripts\deploy_production.sh
   ```

2. **Enable Monitoring Stack**
   ```bash
   docker-compose -f docker-compose.prod.yml --profile monitoring up -d
   ```

3. **Health Check**
   ```bash
   python scripts/production_health_check.py --url http://localhost
   ```

---

## **🎯 READY TO EXECUTE?**

**FOLLOW THESE EXACT STEPS:**

1. **Close this file**
2. **Right-click on PowerShell → "Run as administrator"**
3. **Navigate to project: `cd "C:\Users\95cle\Desktop\925WEB"`**
4. **Run script: `.\scripts\complete_wsl_fix.ps1`**
5. **Follow all prompts**
6. **Restart when asked**
7. **Return here for post-restart verification**

**Your Quote Master Pro will then have full Docker containerization support! 🚀**
