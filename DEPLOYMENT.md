# Production Deployment Guide

## Overview of Changes

This document outlines the production deployment improvements implemented in the HR Analytics Dashboard application.

### 1. Application Improvements

#### FastAPI Configuration
- Implemented Pydantic settings management
- Added structured logging with rotation
- Added request ID tracking
- Implemented rate limiting
- Enhanced error handling and health checks
- Improved CORS configuration

#### Security Enhancements
- Added comprehensive security middleware
  * Request validation (XSS, SQL injection protection)
  * Security headers (CSP, HSTS)
  * Request/Response logging
  * Rate limiting protection
- Implemented secure configuration handling

### 2. Docker Configuration

#### Base Image
- Multi-stage build process
- Non-root user execution
- Read-only filesystem
- Resource limits and container policies

#### Security
- Limited container capabilities
- Health check implementation
- Proper logging configuration
- Dependency optimization

## Deployment Process

### Prerequisites
- AWS CLI configured
- Docker installed
- GitHub repository access
- Required environment variables

### Environment Variables

Create a `.env.prod` file with the following variables:
```env
# Application Settings
APP_ENV=production
DEBUG=false
APP_TITLE="HR Analytics Dashboard"
APP_VERSION=1.0.0

# Security Settings
SECRET_KEY=<your-secret-key>
ALLOWED_ORIGINS=["https://your-domain.com"]
RATE_LIMIT_PER_SECOND=10

# Database Settings
DATABASE_URL=postgresql://user:password@db:5432/hr_analytics
REDIS_URL=redis://:password@redis:6379/0

# AWS Settings (for GitHub Actions)
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=<your-aws-region>
```

### Deployment Steps

1. **Local Testing**
```bash
# Build and run locally
docker-compose -f docker-compose.prod.yml up -d

# Verify health check
curl http://localhost:8000/health
```

2. **GitHub Actions Deployment**
- Push changes to the main branch
- GitHub Actions will automatically:
  * Run tests
  * Build Docker image
  * Perform security scan
  * Deploy to AWS ECS
  * Verify deployment
  * Send notification

3. **Manual Deployment**
```bash
# Build the image
docker build -t hr-analytics:latest .

# Push to ECR
aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com
docker tag hr-analytics:latest aws_account_id.dkr.ecr.region.amazonaws.com/hr-analytics:latest
docker push aws_account_id.dkr.ecr.region.amazonaws.com/hr-analytics:latest
```

### Monitoring

1. **Health Check**
- Endpoint: `/health`
- Monitors: Database, Redis, and integration services
- Returns: Status, uptime, and version information

2. **Logs**
- Structured JSON logging
- Log rotation enabled
- Request ID tracking for tracing
- Security event logging

3. **Metrics**
- Prometheus metrics available at `/metrics`
- Grafana dashboards for visualization
- Resource utilization monitoring
- Request rate and latency tracking

### Security Considerations

1. **Application Security**
- Input validation
- CORS restrictions
- Rate limiting
- Security headers
- Request validation

2. **Infrastructure Security**
- Non-root container execution
- Read-only filesystem
- Limited container capabilities
- Network isolation
- Resource constraints

### Troubleshooting

1. **Common Issues**
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Verify environment variables
- Check security group settings
- Validate database connections

2. **Health Check Failures**
- Verify database connectivity
- Check Redis connection
- Validate integration services
- Review resource utilization

### Rollback Procedure

1. **Using GitHub Actions**
- Revert the commit
- Push to main branch
- Actions will automatically rollback

2. **Manual Rollback**
```bash
# Get previous task definition
aws ecs describe-task-definition --task-definition hr-analytics:previous

# Update service
aws ecs update-service --cluster hr-analytics-cluster --service hr-analytics-service --task-definition hr-analytics:previous
```

## Support

For deployment issues or questions:
1. Check the logs first
2. Review the health check endpoint
3. Consult the monitoring dashboards
4. Contact the DevOps team

## Future Improvements

1. **Monitoring**
- Enhanced metric collection
- Custom Grafana dashboards
- Alert rule refinement

2. **Security**
- Regular dependency updates
- Automated security scanning
- Enhanced access controls

3. **Performance**
- Cache optimization
- Query performance monitoring
- Resource scaling rules
