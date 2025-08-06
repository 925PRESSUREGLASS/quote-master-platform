"""
Quote Master Pro - Main FastAPI Application
"""

import uvicorn
from src.api.main import create_application

# Create the application using the factory function
app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )