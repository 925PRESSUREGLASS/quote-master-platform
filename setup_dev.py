#!/usr/bin/env python3
"""
Development setup script for Quote Master Pro
Implements Claude Opus suggestions for complete application setup
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import List, Dict, Any

def print_step(message: str) -> None:
    """Print a setup step with formatting"""
    print(f"\n🚀 {message}")
    print("=" * (len(message) + 3))

def print_success(message: str) -> None:
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str) -> None:
    """Print error message"""
    print(f"❌ {message}")

def print_info(message: str) -> None:
    """Print info message"""
    print(f"ℹ️  {message}")

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {result.stderr}")
        return result
    
    if result.stdout:
        print(result.stdout)
    
    return result

def check_requirements() -> bool:
    """Check if all requirements are met"""
    print_step("Checking Requirements")
    
    requirements = [
        ("python", "python --version"),
        ("pip", "pip --version"),
        ("node", "node --version"),
        ("npm", "npm --version"),
    ]
    
    missing = []
    for name, command in requirements:
        result = run_command(command, check=False)
        if result.returncode != 0:
            missing.append(name)
            print_error(f"{name} not found")
        else:
            print_success(f"{name} found: {result.stdout.strip()}")
    
    if missing:
        print_error(f"Missing requirements: {', '.join(missing)}")
        return False
    
    return True

def setup_python_environment() -> bool:
    """Set up Python virtual environment"""
    print_step("Setting up Python Environment")
    
    # Check if virtual environment exists
    venv_path = Path(".venv")
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        result = run_command("python -m venv .venv")
        if result.returncode != 0:
            return False
    else:
        print_success("Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix/Linux/MacOS
        activate_cmd = "source .venv/bin/activate"
        pip_cmd = ".venv/bin/pip"
    
    # Install Python dependencies
    print_info("Installing Python dependencies...")
    result = run_command(f"{pip_cmd} install -r requirements.txt")
    if result.returncode != 0:
        print_error("Failed to install Python dependencies")
        return False
    
    # Install development dependencies
    if Path("requirements/dev.txt").exists():
        print_info("Installing development dependencies...")
        result = run_command(f"{pip_cmd} install -r requirements/dev.txt")
        if result.returncode != 0:
            print_info("Development dependencies installation failed, continuing...")
    
    print_success("Python environment set up successfully")
    return True

def setup_frontend() -> bool:
    """Set up frontend dependencies"""
    print_step("Setting up Frontend")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print_info("Frontend directory not found, skipping frontend setup")
        return True
    
    os.chdir("frontend")
    
    # Install dependencies
    print_info("Installing frontend dependencies...")
    result = run_command("npm install")
    if result.returncode != 0:
        print_error("Failed to install frontend dependencies")
        os.chdir("..")
        return False
    
    os.chdir("..")
    print_success("Frontend dependencies installed successfully")
    return True

def setup_database() -> bool:
    """Set up database and run migrations"""
    print_step("Setting up Database")
    
    # Check if Alembic is configured
    if not Path("alembic.ini").exists():
        print_error("Alembic not configured. Please run: alembic init alembic")
        return False
    
    # Run database migrations
    print_info("Running database migrations...")
    if os.name == 'nt':
        alembic_cmd = ".venv\\Scripts\\alembic"
    else:
        alembic_cmd = ".venv/bin/alembic"
    
    result = run_command(f"{alembic_cmd} upgrade head")
    if result.returncode != 0:
        print_error("Database migration failed")
        return False
    
    print_success("Database migrations completed successfully")
    return True

def create_env_file() -> bool:
    """Create .env file from template if it doesn't exist"""
    print_step("Setting up Environment Variables")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print_success(".env file already exists")
        return True
    
    if env_template.exists():
        print_info("Creating .env file from template...")
        import shutil
        shutil.copy(env_template, env_file)
        print_success(".env file created from template")
        print_info("Please edit .env file with your actual configuration values")
    else:
        print_info("No .env template found, creating basic .env file...")
        with open(env_file, 'w') as f:
            f.write("""# Quote Master Pro Environment Configuration
# Update these values with your actual configuration

APP_NAME="Quote Master Pro"
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-this
DEBUG=True

# Database
DATABASE_URL=sqlite:///./quote_master_pro.db

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
""")
        print_success("Basic .env file created")
        print_info("Please edit .env file with your actual configuration values")
    
    return True

def setup_git_hooks() -> bool:
    """Set up Git hooks for development"""
    print_step("Setting up Git Hooks")
    
    # Create pre-commit hook
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print_info("Git hooks directory not found, skipping git hooks setup")
        return True
    
    pre_commit_hook = hooks_dir / "pre-commit"
    
    if not pre_commit_hook.exists():
        print_info("Creating pre-commit hook...")
        with open(pre_commit_hook, 'w') as f:
            f.write("""#!/bin/sh
# Pre-commit hook for Quote Master Pro

echo "Running pre-commit checks..."

# Run Python linting
echo "Running Python linting..."
if command -v flake8 >/dev/null 2>&1; then
    flake8 src/ --max-line-length=100 --ignore=E203,W503
    if [ $? -ne 0 ]; then
        echo "Python linting failed. Please fix the issues before committing."
        exit 1
    fi
fi

# Run tests
echo "Running tests..."
if command -v pytest >/dev/null 2>&1; then
    pytest tests/ -x -q
    if [ $? -ne 0 ]; then
        echo "Tests failed. Please fix the issues before committing."
        exit 1
    fi
fi

echo "Pre-commit checks passed!"
exit 0
""")
        
        # Make the hook executable
        os.chmod(pre_commit_hook, 0o755)
        print_success("Pre-commit hook created")
    else:
        print_success("Pre-commit hook already exists")
    
    return True

def verify_setup() -> bool:
    """Verify that the setup was successful"""
    print_step("Verifying Setup")
    
    # Test Python imports
    print_info("Testing Python imports...")
    test_imports = [
        "import src.main",
        "from src.api.main import app",
        "from src.core.config import get_settings",
    ]
    
    for import_test in test_imports:
        result = run_command(f"python -c \"{import_test}\"", check=False)
        if result.returncode != 0:
            print_error(f"Import test failed: {import_test}")
            return False
        else:
            print_success(f"Import test passed: {import_test}")
    
    # Test frontend build (if exists)
    frontend_path = Path("frontend")
    if frontend_path.exists():
        print_info("Testing frontend build...")
        os.chdir("frontend")
        result = run_command("npm run build", check=False)
        os.chdir("..")
        
        if result.returncode != 0:
            print_error("Frontend build failed")
            return False
        else:
            print_success("Frontend build successful")
    
    print_success("All verification tests passed!")
    return True

def print_next_steps() -> None:
    """Print next steps for the user"""
    print_step("Next Steps")
    
    print("""
🎉 Quote Master Pro setup completed successfully!

Next steps:

1. 📝 Edit your .env file with actual configuration values:
   - Add your OpenAI API key
   - Add your Anthropic API key  
   - Configure email settings
   - Update database URL if needed

2. 🚀 Start the development server:
   Backend:  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   Frontend: cd frontend && npm run dev

3. 🧪 Run tests:
   pytest tests/

4. 📚 Check the documentation:
   - README.md - Project overview
   - DEVELOPMENT_READY.md - Development guide
   - NEXT_DEVELOPMENT_PHASE.md - Phase 2 roadmap

5. 🌐 Access the application:
   - API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

6. 🔧 Additional setup (optional):
   - Set up Redis for caching: docker run -d -p 6379:6379 redis:latest
   - Set up PostgreSQL for production
   - Configure monitoring with Grafana/Prometheus

Happy coding! 🚀
    """)

def main():
    """Main setup function"""
    print("🎯 Quote Master Pro - Development Setup")
    print("Implementing Claude Opus suggestions for comprehensive setup\n")
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    setup_steps = [
        ("Requirements Check", check_requirements),
        ("Environment File", create_env_file),
        ("Python Environment", setup_python_environment),
        ("Frontend Setup", setup_frontend),
        ("Database Setup", setup_database),
        ("Git Hooks", setup_git_hooks),
        ("Setup Verification", verify_setup),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        try:
            success = step_function()
            if not success:
                failed_steps.append(step_name)
                print_error(f"Step failed: {step_name}")
        except Exception as e:
            failed_steps.append(step_name)
            print_error(f"Step failed with exception: {step_name}")
            print_error(f"Error: {str(e)}")
    
    if failed_steps:
        print_step("Setup Summary")
        print_error(f"Setup completed with {len(failed_steps)} failed step(s):")
        for step in failed_steps:
            print(f"  - {step}")
        print_info("Please review the errors above and run the setup again")
        sys.exit(1)
    else:
        print_step("Setup Summary")
        print_success("All setup steps completed successfully!")
        print_next_steps()

if __name__ == "__main__":
    main()
