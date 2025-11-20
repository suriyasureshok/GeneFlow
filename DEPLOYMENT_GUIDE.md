# 🚀 GeneFlow Deployment & Operations Guide

Complete guide for deploying, managing, and operating GeneFlow in production environments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Performance Tuning](#performance-tuning)

---

## Local Development

### Prerequisites

- Python 3.10+
- pip or conda
- 4GB RAM minimum
- Google API Key

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/suriyasureshok/geneflow.git
cd GeneFlow

# 2. Create virtual environment
python -m venv gene
gene\Scripts\activate  # Windows
source gene/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cat > .env << EOF
GOOGLE_API_KEY=your_api_key_here
LOG_LEVEL=DEBUG
SESSION_MAX_AGE_HOURS=24
EOF

# 5. Run application
python main.py
```

### Verification

```bash
# Check dependencies
python -c "import streamlit, google.generativeai, Bio; print('All OK')"

# Test basic import
python -c "from src.agents.unified_coordinator import UnifiedCoordinator; print('Import OK')"

# Launch UI
streamlit run src/ui/Home.py
# Should open at http://localhost:8501
```

---

## Production Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Load Balancer (nginx/haproxy)           │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼────┐         ┌───▼────┐
    │Streamlit│         │Streamlit│
    │ App #1  │         │ App #2  │
    └───┬────┘         └───┬────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   Shared Storage  │
        ├─────────────────┤
        │ Redis: Sessions │
        │ PgSQL: Analytics│
        │ S3: Artifacts   │
        └─────────────────┘
```

### Environment Configuration

**Production .env**:
```env
# API Configuration
GOOGLE_API_KEY=sk-xxxxxxx

# Application
LOG_LEVEL=INFO
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# Session Management
SESSION_MAX_AGE_HOURS=48
SESSION_STORAGE_PATH=/data/sessions

# Performance
CACHE_ENABLED=true
REDIS_URL=redis://redis-master:6379/0

# Database
DATABASE_URL=postgresql://user:pass@db:5432/geneflow
SQLALCHEMY_ECHO=false

# Monitoring
METRICS_STORAGE_PATH=/data/metrics
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9090

# Security
ENABLE_AUTH=true
AUTH_TYPE=oauth2
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_secret
```

### Requirements (prod)

```bash
# requirements-prod.txt
-r requirements.txt

# Production servers
gunicorn==21.2.0
uvicorn==0.24.0

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Caching
redis==5.0.1

# Monitoring
prometheus-client==0.19.0
python-json-logger==2.0.7

# Security
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6

# Production optimization
orjson==3.9.10
ujson==5.9.0
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database initialized and migrated
- [ ] Redis cache configured
- [ ] SSL certificates installed
- [ ] Load balancer configured
- [ ] Monitoring enabled
- [ ] Backup strategy in place
- [ ] Alerting configured
- [ ] Rate limiting enabled
- [ ] API keys secured (vault/secrets manager)

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /data/sessions /data/metrics /data/plots

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
EXPOSE 8501
CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.9'

services:
  geneflow:
    build: .
    ports:
      - "8501:8501"
    environment:
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://user:password@postgres:5432/geneflow
      LOG_LEVEL: INFO
    depends_on:
      - redis
      - postgres
    volumes:
      - ./sessions:/data/sessions
      - ./metrics:/data/metrics
      - ./geneflow_plots:/data/plots
    networks:
      - geneflow-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - geneflow-network
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: geneflow
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: geneflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - geneflow-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - geneflow
    networks:
      - geneflow-network
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:

networks:
  geneflow-network:
    driver: bridge
```

### Nginx Configuration

```nginx
upstream geneflow_app {
    server geneflow:8501;
}

server {
    listen 80;
    server_name geneflow.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name geneflow.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy configuration
    location / {
        proxy_pass http://geneflow_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=geneflow_limit:10m rate=10r/s;
    limit_req zone=geneflow_limit burst=20 nodelay;
}
```

### Build and Deploy

```bash
# Build image
docker build -t geneflow:latest .

# Tag for registry
docker tag geneflow:latest registry.example.com/geneflow:latest

# Push to registry
docker push registry.example.com/geneflow:latest

# Deploy with compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f geneflow

# Scale services
docker-compose up -d --scale geneflow=3
```

---

## Cloud Deployment

### Google Cloud Platform

#### Setup Steps

```bash
# 1. Create GCP project
gcloud projects create geneflow-project
gcloud config set project geneflow-project

# 2. Enable APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com

# 3. Create Cloud SQL instance
gcloud sql instances create geneflow-db \
    --database-version=POSTGRES_15 \
    --tier=db-g1-small \
    --region=us-central1

# 4. Create memorystore for Redis
gcloud redis instances create geneflow-cache \
    --size=2 \
    --region=us-central1 \
    --tier=basic

# 5. Deploy to Cloud Run
gcloud run deploy geneflow \
    --source . \
    --region=us-central1 \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --timeout=600 \
    --max-instances=10 \
    --set-env-vars="GOOGLE_API_KEY=${GOOGLE_API_KEY},DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"
```

#### Cloud Run Configuration

```yaml
# app.yaml
runtime: python310

env: standard
entrypoint: python main.py

env_variables:
  PORT: "8501"
  STREAMLIT_SERVER_HEADLESS: "true"

runtime_config:
  operating_system: ubuntu22
  runtime_version: "3.10"

min_instances: 1
max_instances: 10
```

#### Cloud Storage Setup

```bash
# Create bucket for artifacts
gsutil mb gs://geneflow-artifacts

# Configure bucket for public access (if needed)
gsutil iam ch serviceAccount:default@geneflow.iam.gserviceaccount.com:roles/storage.objectViewer gs://geneflow-artifacts
```

### AWS Deployment

#### ECR and ECS

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name geneflow --region us-east-1

# 2. Build and push image
docker build -t geneflow:latest .
docker tag geneflow:latest ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/geneflow:latest
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/geneflow:latest

# 3. Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier geneflow-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password ${DB_PASSWORD}

# 4. Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id geneflow-cache \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1

# 5. Deploy to ECS
aws ecs create-service \
    --cluster geneflow-cluster \
    --service-name geneflow-service \
    --task-definition geneflow-task \
    --desired-count 3 \
    --launch-type FARGATE
```

---

## Monitoring & Maintenance

### Health Checks

```python
# health_check.py
from src.agents.unified_coordinator import UnifiedCoordinator
from src.core.session_manager import SessionManager
from src.core.monitoring import PerformanceMonitor
import time

def health_check():
    """Comprehensive health check"""
    checks = {
        "api_key": False,
        "session_manager": False,
        "performance_monitor": False,
        "coordinator": False,
        "response_time": None
    }
    
    try:
        # Check API key
        import os
        if os.getenv("GOOGLE_API_KEY"):
            checks["api_key"] = True
    except Exception as e:
        print(f"API key check failed: {e}")
    
    try:
        # Check session manager
        sm = SessionManager()
        sm.get_all_sessions()
        checks["session_manager"] = True
    except Exception as e:
        print(f"Session manager check failed: {e}")
    
    try:
        # Check performance monitor
        pm = PerformanceMonitor()
        pm.get_summary_stats()
        checks["performance_monitor"] = True
    except Exception as e:
        print(f"Performance monitor check failed: {e}")
    
    try:
        # Check coordinator
        start = time.time()
        coord = UnifiedCoordinator()
        result = coord.process_message("test")
        checks["response_time"] = time.time() - start
        checks["coordinator"] = result['success']
    except Exception as e:
        print(f"Coordinator check failed: {e}")
    
    all_healthy = all(v for k, v in checks.items() if k != "response_time")
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": time.time(),
        "checks": checks
    }

if __name__ == "__main__":
    import json
    print(json.dumps(health_check(), indent=2))
```

### Prometheus Metrics

```python
# metrics_exporter.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from src.core.monitoring import PerformanceMonitor

# Metrics
execution_counter = Counter(
    'geneflow_executions_total',
    'Total executions',
    ['agent', 'success']
)

execution_duration = Histogram(
    'geneflow_execution_duration_seconds',
    'Execution duration',
    ['agent']
)

token_usage = Counter(
    'geneflow_tokens_total',
    'Total tokens used',
    ['agent', 'type']  # type: input or output
)

active_sessions = Gauge(
    'geneflow_active_sessions',
    'Active sessions count'
)

api_cost = Counter(
    'geneflow_api_cost_usd',
    'Total API cost in USD'
)

def update_metrics():
    """Update metrics from monitor"""
    monitor = PerformanceMonitor()
    stats = monitor.get_summary_stats()
    
    # Update gauges
    session_manager = SessionManager()
    active_sessions.set(len(session_manager.get_all_sessions()))
    
    # Update counters from stats
    api_cost._value.get()  # Current value
    api_cost._value._value = stats.get('total_cost', 0)

if __name__ == "__main__":
    start_http_server(8000)
    print("Prometheus metrics available at http://localhost:8000")
```

### Logging

```python
# Configure structured logging
import logging
import json
from pythonjsonlogger import jsonlogger

# Setup JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Analysis complete", extra={
    "sequence_length": 1000,
    "gc_percent": 42.5,
    "execution_time": 45.3
})
```

### Monitoring Stack

```yaml
# docker-compose with monitoring
version: '3.9'

services:
  geneflow:
    # ... (as before)
    environment:
      ENABLE_PROMETHEUS: "true"
      PROMETHEUS_PORT: "9090"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  prometheus_data:
  grafana_data:
```

---

## Troubleshooting

### Common Issues

#### Issue: Out of Memory

```bash
# Check memory usage
docker stats geneflow

# Limit memory
docker run -m 2g geneflow:latest

# Reduce session/metrics storage
SESSION_MAX_AGE_HOURS=12  # Shorter expiration
CLEANUP_INTERVAL_HOURS=6  # More frequent cleanup
```

#### Issue: Slow Responses

```bash
# Check database
EXPLAIN ANALYZE SELECT * FROM sessions;

# Monitor cache hit rate
redis-cli INFO stats

# Scale horizontally
docker-compose up -d --scale geneflow=5
```

#### Issue: High API Costs

```bash
# Monitor token usage
coordinator.get_performance_stats()['total_tokens']

# Reduce analysis scope
MAX_SEQUENCE_LENGTH=50000  # Limit input

# Enable caching
CACHE_ENABLED=true
REDIS_URL=redis://redis:6379/0
```

#### Issue: Session Losses

```bash
# Ensure persistence
- type: volume
  source: sessions_data
  target: /data/sessions

# Verify storage path
- ls -la /data/sessions/
- du -sh /data/sessions/
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --verbose

# Run specific module with debug
python -m pdb src/agents/adk_coordinator.py
```

---

## Performance Tuning

### Optimization Strategies

```python
# 1. Connection pooling
from sqlalchemy.pool import QueuePool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)

# 2. Query optimization
from sqlalchemy import text
session.execute(
    text("CREATE INDEX idx_sessions_user ON sessions(user_id)")
)

# 3. Caching strategy
from redis import Redis
cache = Redis.from_url(REDIS_URL)

# 4. Async processing
from celery import Celery
app = Celery('geneflow')

@app.task
def analyze_pipeline(sequence):
    return coordinator.run_pipeline(sequence)
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8501/

# Using Locust
pip install locust
locust -f locustfile.py -u 100 -r 10

# Using k6
k6 run load_test.js
```

### Capacity Planning

| Users | Instances | Cores | RAM | Cost/mo |
|-------|-----------|-------|-----|---------|
| 10 | 1 | 1 | 2GB | $50 |
| 50 | 3 | 2 | 4GB | $300 |
| 100 | 5 | 4 | 8GB | $800 |
| 500 | 15 | 8 | 16GB | $3000 |

---

## Maintenance Tasks

### Daily

```bash
# Check system health
docker-compose ps
docker-compose logs --tail 100

# Monitor resources
docker stats

# Check API quota
curl -H "Authorization: Bearer $TOKEN" \
  https://www.googleapis.com/compute/v1/projects/geneflow/global/quotas
```

### Weekly

```bash
# Backup data
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
tar czf sessions_backup_$(date +%Y%m%d).tar.gz /data/sessions

# Cleanup old sessions
python -c "from src.core.session_manager import SessionManager; SessionManager().cleanup_old_sessions()"

# Export metrics
python -c "from src.core.monitoring import PerformanceMonitor; PerformanceMonitor().export_metrics()"
```

### Monthly

```bash
# Review performance trends
SELECT date, avg_latency_ms, total_cost FROM metrics GROUP BY date;

# Update dependencies
pip list --outdated
pip install --upgrade pip
pip install -U -r requirements-prod.txt

# Security audit
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image geneflow:latest
```

---

## Security Hardening

### Network Security

```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: geneflow-network-policy
spec:
  podSelector:
    matchLabels:
      app: geneflow
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress
    ports:
    - protocol: TCP
      port: 8501
```

### Secrets Management

```bash
# Using Vault
vault kv put secret/geneflow \
  google_api_key=sk-xxxxx \
  db_password=xxxxx \
  oauth_secret=xxxxx

# Using Kubernetes Secrets
kubectl create secret generic geneflow-secrets \
  --from-env-file=.env.prod
```

### API Security

```python
# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/analyze")
@limiter.limit("5/minute")
def analyze(request: AnalysisRequest):
    pass

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://domain.com"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

---

**Last Updated**: November 2024
**Version**: 1.0.0
