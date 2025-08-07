"""
Quote Master Pro - Phase 2 Setup Script
Automated environment setup for enhanced testing implementation
"""
import os
import subprocess
import sys
from pathlib import Path

def setup_testing_environment():
    """Set up the enhanced testing environment for Phase 2"""
    
    print("🚀 Setting up Quote Master Pro Phase 2 Testing Environment...")
    
    # Create test directories
    test_dirs = [
        "tests/unit/advanced",
        "tests/integration/workflows", 
        "tests/performance/benchmarks",
        "tests/security/validation",
        "tests/e2e/complete"
    ]
    
    for directory in test_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Install testing dependencies
    testing_packages = [
        "pytest-benchmark==4.0.0",
        "pytest-asyncio==0.21.1", 
        "pytest-xdist==3.3.1",
        "pytest-mock==3.11.1",
        "pytest-cov==4.1.0",
        "locust==2.17.0",
        "memory-profiler==0.61.0",
        "httpx==0.24.1",
        "faker==19.6.2"
    ]
    
    print("\n📦 Installing testing dependencies...")
    for package in testing_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✅ Installed: {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
    
    # Create VS Code settings
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    # VS Code extensions
    extensions = {
        "recommendations": [
            "ms-python.python",
            "ms-python.flake8", 
            "ms-python.pytest",
            "hbenl.vscode-test-explorer",
            "ryanluker.vscode-coverage-gutters",
            "ms-vscode.test-adapter-converter",
            "formulahendry.code-runner",
            "ms-python.black-formatter",
            "ms-python.isort"
        ]
    }
    
    import json
    with open(vscode_dir / "extensions.json", "w") as f:
        json.dump(extensions, f, indent=2)
    print("✅ Created VS Code extensions.json")
    
    # Update pytest configuration
    pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=90
    --durations=10
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests  
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
asyncio_mode = auto
"""
    
    with open("pytest.ini", "w") as f:
        f.write(pytest_config)
    print("✅ Updated pytest.ini configuration")
    
    print("\n🎯 Phase 2 setup complete! Ready for enhanced testing implementation.")
    print("\nNext steps:")
    print("1. Open VS Code in this directory")
    print("2. Install recommended extensions") 
    print("3. Run: pytest tests/ --co to verify setup")
    print("4. Begin implementing advanced test cases")

if __name__ == "__main__":
    setup_testing_environment()
