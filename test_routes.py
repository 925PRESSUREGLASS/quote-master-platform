#!/usr/bin/env python3
"""Test script to debug service quotes router loading."""

import sys
import traceback

def test_service_quotes_import():
    """Test importing service quotes router."""
    print("=" * 50)
    print("Testing service_quotes router import...")
    print("=" * 50)
    
    try:
        from src.api.routers.service_quotes import router
        print("✓ Router imported successfully")
        print(f"✓ Router prefix: {router.prefix}")
        print(f"✓ Router tags: {router.tags}")
        print(f"✓ Number of routes: {len(router.routes)}")
        
        print("\nRoutes found:")
        for i, route in enumerate(router.routes):
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                print(f"  {i+1}. {list(route.methods)} {route.path}")
            else:
                print(f"  {i+1}. {route}")
                
        return True
        
    except Exception as e:
        print(f"✗ Error importing service_quotes router: {e}")
        traceback.print_exc()
        return False

def test_main_app_import():
    """Test importing main app."""
    print("\n" + "=" * 50)
    print("Testing main app import...")
    print("=" * 50)
    
    try:
        from src.api.main import app
        print("✓ Main app imported successfully")
        
        print(f"\nApp routes found ({len(app.routes)}):")
        for i, route in enumerate(app.routes):
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', 'N/A')
                print(f"  {i+1}. {methods} {route.path}")
            else:
                print(f"  {i+1}. {route}")
                
        return True
        
    except Exception as e:
        print(f"✗ Error importing main app: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_service_quotes_import()
    success2 = test_main_app_import()
    
    if success1 and success2:
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ SOME TESTS FAILED")
        print("=" * 50)
        sys.exit(1)
