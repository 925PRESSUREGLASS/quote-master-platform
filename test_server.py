"""
Minimal test server to debug service quotes routing
"""
import sys
sys.path.append('.')

from fastapi import FastAPI
from src.api.routers import service_quotes

# Create minimal app
app = FastAPI(title="Test Service Quotes")

# Add the service quotes router
app.include_router(
    service_quotes.router,
    prefix="/api/v1",
    tags=["Service Quotes"]
)

@app.get("/")
def root():
    return {"message": "Test server running"}

@app.get("/test/service-quotes")
def test_service_quotes():
    """Test endpoint to verify service quotes router is loaded"""
    router_routes = []
    try:
        from src.api.routers.service_quotes import router as sq_router
        for route in sq_router.routes:
            if hasattr(route, 'path'):
                router_routes.append({
                    "path": getattr(route, 'path', 'unknown'),
                    "methods": list(getattr(route, 'methods', []))
                })
        return {
            "service_quotes_loaded": True,
            "router_routes_count": len(router_routes),
            "routes": router_routes
        }
    except Exception as e:
        return {
            "service_quotes_loaded": False,
            "error": str(e)
        }

@app.get("/debug/routes")
def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            try:
                routes.append({
                    "path": getattr(route, 'path', 'unknown'),
                    "methods": list(getattr(route, 'methods', []))
                })
            except Exception as e:
                routes.append({
                    "path": f"error: {str(e)}",
                    "methods": []
                })
    return {"routes": routes, "total": len(routes)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
