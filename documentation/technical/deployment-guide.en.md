# Deployment Guide - GD_python System

## 📋 Deployment Overview

This guide describes the complete deployment process for the GD_python system across different environments - from local development through staging to cloud production. It covers installation, configuration, performance optimization, and monitoring.

## 🎯 System Requirements

### Minimum Requirements

**Hardware:**
- CPU: 2 cores, 2.0 GHz
- RAM: 4 GB
- Disk: 10 GB disk space
- Network: 100 Mbps (for API calls)

**Software:**
- Python 3.8+ (recommended 3.11+)
- Java 8+ (for PlantUML)
- Git
- OS: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### Production Recommended

**Hardware:**
- CPU: 4+ cores, 3.0+ GHz
- RAM: 16+ GB
- Disk: 100+ GB SSD
- Network: 1 Gbps

**Software:**
- Python 3.11+
- Java 17+ LTS
- Docker 20.10+
- Nginx/Apache (reverse proxy)
- PostgreSQL/MySQL (production DB)

---

## 🚀 Local Installation (Development)

### 1. Repository Cloning

```bash
# Clone project
git clone https://github.com/ThrennPL/GD_python.git
cd GD_python

# Check branch
git checkout feature/bpmn-v2-clean-architecture
```

### 2. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Dependencies Installation

```bash
# Basic dependencies
pip install -r config/requirements.txt

# Optional: development dependencies
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

```bash
# Copy template .env
cp .env.template .env

# Edit configuration
# Windows
notepad .env
# Linux/macOS
nano .env
```

**Minimal `.env` configuration:**
```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key_here
LANGUAGE=en
PLANTUML_JAR_PATH=plantuml.jar
```

### 5. Download PlantUML

```bash
# Automatic PlantUML download
python -c "
import urllib.request
urllib.request.urlretrieve(
    'https://github.com/plantuml/plantuml/releases/download/v1.2023.13/plantuml-1.2023.13.jar',
    'plantuml.jar'
)
print('PlantUML downloaded')
"
```

### 6. Installation Test

```bash
# Test basic functionality
python -c "
import sys
print(f'Python: {sys.version}')

try:
    from bpmn_v2.ai_config import create_bpmn_config
    config = create_bpmn_config()
    print('✅ BPMN v2 configuration OK')
except Exception as e:
    print(f'❌ BPMN configuration error: {e}')

try:
    from utils.pdf.ai_pdf_analyzer import AIPDFAnalyzer
    print('✅ PDF analysis OK')
except Exception as e:
    print(f'❌ PDF analysis error: {e}')
"

# Test AI connection
python -m bpmn_v2.test_env_config
```

### 7. Application Launch

```bash
# Desktop Application (PyQt5)
python src/main.py

# Web Application (Streamlit)
streamlit run src/streamlit_app.py

# Alternative Streamlit command
python -m streamlit run streamlit_app.py --server.port 8501
```

---

## 🐳 Docker Deployment

### 1. Image Building

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Python dependencies
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PlantUML
RUN wget https://github.com/plantuml/plantuml/releases/download/v1.2023.13/plantuml-1.2023.13.jar \
    -O plantuml.jar

# Application code
COPY . .

# Environment setup
ENV PYTHONPATH=/app
ENV PLANTUML_JAR_PATH=/app/plantuml.jar

# Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command
CMD ["streamlit", "run", "src/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Building:**
```bash
# Build image
docker build -t gd-python:latest .

# Tag for registry
docker tag gd-python:latest registry.example.com/gd-python:v4.0.0
```

### 2. Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  gd-python:
    build: .
    container_name: gd-python-app
    ports:
      - "8501:8501"
    environment:
      - MODEL_PROVIDER=gemini
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LANGUAGE=en
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
      - ./output:/app/output
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: gd-python-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - gd-python
    restart: unless-stopped

  # Optional: Database
  postgres:
    image: postgres:15-alpine
    container_name: gd-python-db
    environment:
      - POSTGRES_DB=gd_python
      - POSTGRES_USER=gd_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Launch:**
```bash
# Environment
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "DB_PASSWORD=secure_password" >> .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f gd-python

# Stop services
docker-compose down
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. ECS Fargate

**Task Definition (task-definition.json):**
```json
{
    "family": "gd-python-task",
    "networkMode": "awsvpc",
    "requiresAttributes": [
        {"name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"},
        {"name": "ecs.capability.task-eni"}
    ],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "gd-python",
            "image": "account.dkr.ecr.region.amazonaws.com/gd-python:latest",
            "portMappings": [
                {
                    "containerPort": 8501,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "MODEL_PROVIDER", "value": "gemini"},
                {"name": "LANGUAGE", "value": "en"}
            ],
            "secrets": [
                {
                    "name": "GOOGLE_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:region:account:secret:gd-python/api-keys-abcdef:GOOGLE_API_KEY::"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/gd-python",
                    "awslogs-region": "us-west-2",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
```

**Deployment commands:**
```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin account.dkr.ecr.us-west-2.amazonaws.com

# Push image
docker tag gd-python:latest account.dkr.ecr.us-west-2.amazonaws.com/gd-python:latest
docker push account.dkr.ecr.us-west-2.amazonaws.com/gd-python:latest

# Update service
aws ecs update-service --cluster gd-python-cluster --service gd-python-service --force-new-deployment
```

#### 2. Lambda Functions (Serverless)

**serverless.yml:**
```yaml
service: gd-python-serverless

provider:
  name: aws
  runtime: python3.11
  region: us-west-2
  timeout: 900
  memorySize: 3008
  environment:
    MODEL_PROVIDER: gemini
    GOOGLE_API_KEY: ${env:GOOGLE_API_KEY}

functions:
  generateBPMN:
    handler: lambda_handler.generate_bpmn
    events:
      - http:
          path: /api/bpmn/generate
          method: post
    layers:
      - arn:aws:lambda:us-west-2:account:layer:plantuml-layer:1

  analyzePDF:
    handler: lambda_handler.analyze_pdf
    events:
      - http:
          path: /api/pdf/analyze
          method: post

plugins:
  - serverless-python-requirements
```

### Google Cloud Platform

#### 1. Cloud Run

**cloudbuild.yaml:**
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/gd-python:$COMMIT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/gd-python:$COMMIT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'gd-python'
    - '--image'
    - 'gcr.io/$PROJECT_ID/gd-python:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--set-env-vars'
    - 'MODEL_PROVIDER=gemini,LANGUAGE=en'
    - '--set-secrets'
    - 'GOOGLE_API_KEY=projects/$PROJECT_ID/secrets/google-api-key:latest'

images:
  - 'gcr.io/$PROJECT_ID/gd-python:$COMMIT_SHA'
```

**Deployment:**
```bash
# Enable APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Create secret
echo "your_google_api_key" | gcloud secrets create google-api-key --data-file=-

# Deploy
gcloud builds submit --config cloudbuild.yaml

# Set traffic
gcloud run services update-traffic gd-python --to-latest --region=us-central1
```

### Azure Container Instances

**azure-deploy.yaml:**
```yaml
apiVersion: 2018-10-01
location: eastus
name: gd-python-app
properties:
  containers:
  - name: gd-python
    properties:
      image: myregistry.azurecr.io/gd-python:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 4
      ports:
      - port: 8501
        protocol: TCP
      environmentVariables:
      - name: MODEL_PROVIDER
        value: gemini
      - name: LANGUAGE
        value: en
      - name: GOOGLE_API_KEY
        secureValue: your_google_api_key_here
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8501
  restartPolicy: Always
type: Microsoft.ContainerInstance/containerGroups
```

---

## 🔧 Production Configuration

### 1. Nginx Reverse Proxy

**nginx.conf:**
```nginx
upstream gd_python {
    server gd-python:8501;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 50M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://gd_python;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /health {
        proxy_pass http://gd_python/_stcore/health;
        access_log off;
    }
}
```

### 2. SSL Certificates (Let's Encrypt)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Systemd Service

**gd-python.service:**
```ini
[Unit]
Description=GD_python Application
After=network.target

[Service]
Type=simple
User=gd_python
Group=gd_python
WorkingDirectory=/opt/gd_python
Environment=PATH=/opt/gd_python/venv/bin
ExecStart=/opt/gd_python/venv/bin/streamlit run src/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable gd-python.service
sudo systemctl start gd-python.service
sudo systemctl status gd-python.service
```

---

## 📊 Monitoring and Logging

### 1. Logging Configuration

**logging_config.yaml:**
```yaml
version: 1
disable_existing_loggers: false

formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
  simple:
    format: '%(levelname)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
    
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/gd_python.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/errors.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  bpmn_v2:
    level: DEBUG
    handlers: [console, file]
    propagate: no

  utils.pdf:
    level: INFO
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console, file, error_file]
```

### 2. Prometheus Metrics

**metrics.py:**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
bpmn_requests_total = Counter('bpmn_requests_total', 'Total BPMN generation requests')
bpmn_generation_duration = Histogram('bpmn_generation_duration_seconds', 'BPMN generation duration')
bpmn_quality_score = Gauge('bpmn_quality_score', 'Last BPMN quality score')
pdf_analysis_requests = Counter('pdf_analysis_requests_total', 'Total PDF analysis requests')

def start_metrics_server(port=9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
    print(f"Metrics server started on port {port}")
```

### 3. Health Checks

**health.py:**
```python
import os
from datetime import datetime
from typing import Dict, Any

def health_check() -> Dict[str, Any]:
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0",
        "checks": {
            "database": check_database(),
            "ai_provider": check_ai_provider(),
            "plantuml": check_plantuml(),
            "disk_space": check_disk_space(),
            "memory": check_memory_usage()
        }
    }

def check_ai_provider() -> Dict[str, Any]:
    """Check AI provider connectivity"""
    try:
        from bpmn_v2.ai_config import create_bpmn_config
        config = create_bpmn_config()
        return {"status": "ok", "provider": config.provider.value}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

---

## 🔐 Production Security

### 1. Environment Variables

```bash
# Production secrets management
export GOOGLE_API_KEY="$(aws secretsmanager get-secret-value --secret-id google-api-key --query SecretString --output text)"
export DB_PASSWORD="$(vault kv get -field=password secret/gd-python/db)"
```

### 2. Firewall Rules

```bash
# UFW configuration
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8501/tcp   # Block direct Streamlit access
sudo ufw enable
```

### 3. User Management

```bash
# Create service user
sudo useradd -r -s /bin/false gd_python
sudo usermod -a -G docker gd_python

# Set permissions
sudo chown -R gd_python:gd_python /opt/gd_python
sudo chmod 750 /opt/gd_python
```

---

## 📈 Performance Optimization

### 1. Caching

**Redis configuration:**
```yaml
# docker-compose.yml addition
redis:
  image: redis:alpine
  container_name: gd-python-redis
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**Application caching:**
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 2. Database Optimization

**PostgreSQL configuration:**
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

### 3. Load Balancing

**HAProxy configuration:**
```
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend gd_python_frontend
    bind *:80
    default_backend gd_python_backend

backend gd_python_backend
    balance roundrobin
    option httpchk GET /_stcore/health
    server app1 gd-python-1:8501 check
    server app2 gd-python-2:8501 check
    server app3 gd-python-3:8501 check
```

---

## 🧪 Deployment Testing

### 1. Smoke Tests

```bash
#!/bin/bash
# smoke_test.sh

BASE_URL="https://yourdomain.com"

echo "🧪 Running smoke tests..."

# Health check
curl -f "$BASE_URL/health" || exit 1
echo "✅ Health check passed"

# Basic functionality
curl -X POST "$BASE_URL/api/bpmn/generate" \
  -H "Content-Type: application/json" \
  -d '{"description": "Simple test process"}' || exit 1
echo "✅ BPMN generation test passed"

echo "🎉 All smoke tests passed!"
```

### 2. Load Testing

```python
# load_test.py
import asyncio
import aiohttp
import time

async def test_endpoint(session, url):
    async with session.post(url, json={"description": "Test process"}) as response:
        return response.status == 200

async def load_test(concurrent_requests=10, duration=60):
    """Run load test for specified duration with concurrent requests"""
    async with aiohttp.ClientSession() as session:
        url = "https://yourdomain.com/api/bpmn/generate"
        
        start_time = time.time()
        successful_requests = 0
        total_requests = 0
        
        while time.time() - start_time < duration:
            tasks = [test_endpoint(session, url) for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_requests += sum(1 for r in results if r is True)
            total_requests += len(results)
            
            await asyncio.sleep(1)
        
        success_rate = (successful_requests / total_requests) * 100
        print(f"Success rate: {success_rate:.2f}% ({successful_requests}/{total_requests})")

if __name__ == "__main__":
    asyncio.run(load_test())
```

---

## 🔄 Backup and Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/gd_python"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -h localhost -U gd_user gd_python | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Application files backup
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" -C /opt gd_python

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 2. Disaster Recovery

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR="/var/backups/gd_python"
RESTORE_FILE="$1"

if [ -z "$RESTORE_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop application
docker-compose down

# Restore database
gunzip -c "$BACKUP_DIR/$RESTORE_FILE" | psql -h localhost -U gd_user gd_python

# Restart application
docker-compose up -d

echo "Restore completed from: $RESTORE_FILE"
```

---

## 📋 Deployment Checklist

### Pre-deployment

- [ ] Code review completed
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] Backup strategy in place

### Deployment

- [ ] Application deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logging working
- [ ] Load balancer configured
- [ ] Firewall rules applied
- [ ] SSL redirect working
- [ ] Performance monitoring active

### Post-deployment

- [ ] Smoke tests passed
- [ ] Load testing completed
- [ ] Error monitoring configured
- [ ] Backup tested
- [ ] Rollback plan verified
- [ ] Team notified
- [ ] Documentation updated
- [ ] Post-mortem scheduled (if issues)

This guide provides comprehensive coverage of all deployment aspects for the GD_python system. Adapt configurations to your specific environment requirements.