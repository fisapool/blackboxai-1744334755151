from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import psutil
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

@router.get("/metrics")
async def metrics():
    """
    Get Prometheus metrics
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/system")
async def system_metrics() -> Dict[str, Any]:
    """
    Get system metrics including CPU, memory, and disk usage
    """
    try:
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": {
                "connections": len(psutil.net_connections()),
                "interfaces": list(psutil.net_if_stats().keys())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching system metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching system metrics")

@router.get("/services")
async def service_status() -> List[Dict[str, Any]]:
    """
    Get status of all integrated services
    """
    try:
        # TODO: Implement actual service status checks
        services = [
            {
                "name": "database",
                "status": "healthy",
                "latency_ms": 45,
                "last_check": datetime.utcnow().isoformat()
            },
            {
                "name": "redis",
                "status": "healthy",
                "latency_ms": 12,
                "last_check": datetime.utcnow().isoformat()
            },
            {
                "name": "ml_service",
                "status": "healthy",
                "latency_ms": 89,
                "last_check": datetime.utcnow().isoformat()
            }
        ]
        return services
    except Exception as e:
        logger.error(f"Error checking service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error checking service status")

@router.get("/logs")
async def recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent application logs
    """
    try:
        # TODO: Implement actual log fetching from log storage
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Application running normally",
                "service": "web_api"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching logs")

@router.get("/alerts")
async def active_alerts() -> List[Dict[str, Any]]:
    """
    Get active system alerts
    """
    try:
        # TODO: Implement actual alert fetching from alert manager
        return [
            {
                "id": "cpu_high_001",
                "severity": "warning",
                "message": "CPU usage above 80%",
                "triggered_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching alerts")
