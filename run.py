import os
import sys
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    print("=" * 70)
    print("  🚀 Starting DevOps Multi-Cloud Cost & Resource Monitoring Dashboard")
    print("=" * 70)
    print("  📍 Interactive Dashboard UI: http://localhost:8000")
    print("  📚 Swagger API Documentation: http://localhost:8000/docs")
    print("  📊 Prometheus Metrics:        http://localhost:8000/metrics")
    print("  💓 Healthcheck:               http://localhost:8000/healthz")
    print("=" * 70)

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
