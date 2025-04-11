"""
HR Analytics Dashboard Application

A FastAPI-based web application for HR analytics and monitoring.
"""

__version__ = "1.0.0"
__author__ = "HR Analytics Team"
__description__ = "HR-focused multimodal analytics platform"

# Version of the API
API_VERSION = "v1"

# Import all routers
from app.routers import analytics, users, monitoring
