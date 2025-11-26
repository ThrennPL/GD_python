# System Architecture - GD_python

## Architectural Overview

The GD_python system is built as a modern, modular architecture supporting multiple AI providers, dual interface deployment (desktop and web), and enterprise-grade BPMN v2 generation capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GD_python System Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   Desktop App   │    │    Web App      │                   │
│  │    (PyQt5)      │    │  (Streamlit)    │                   │
│  └─────────────────┘    └─────────────────┘                   │
│           │                       │                           │
│           └───────────────────────┼───────────────────────────┤
│                                   │                           │
│  ┌─────────────────────────────────────────────────────────────┤
│  │                Core Services Layer                          │
│  ├─────────────────────────────────────────────────────────────┤
│  │                                                             │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ │ BPMN v2      │ │ AI           │ │ PDF          │        │
│  │ │ Generation   │ │ Integration  │ │ Analysis     │        │
│  │ │ Engine       │ │ Layer        │ │ Engine       │        │
│  │ └──────────────┘ └──────────────┘ └──────────────┘        │
│  │                                                             │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ │ PlantUML     │ │ Quality      │ │ Template     │        │
│  │ │ Generator    │ │ Assurance    │ │ Manager      │        │
│  │ └──────────────┘ └──────────────┘ └──────────────┘        │
│  └─────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┤
│  │              Infrastructure Layer                           │
│  ├─────────────────────────────────────────────────────────────┤
│  │                                                             │
│  │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │
│  │ │ Configuration │ │ Logging   │ │ Monitoring │ │ Security │  │
│  │ │ Management   │ │ System    │ │ & Metrics  │ │ Layer    │  │
│  │ └────────────┘ └────────────┘ └────────────┘ └──────────┘  │
│  └─────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┤
│  │                External Integrations                        │
│  ├─────────────────────────────────────────────────────────────┤
│  │                                                             │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ │ OpenAI  │ │ Google  │ │Anthropic│ │ Ollama  │ │PlantUML │ │
│  │ │ API     │ │ Gemini  │ │ Claude  │ │ Local   │ │ JAR     │ │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│  └─────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. **Application Layer**

#### **Desktop Application (PyQt5)**
- **Location**: `main.py`, `src/`
- **Purpose**: Native desktop experience with full feature access
- **Key Features**:
  - Rich GUI with advanced controls
  - Local file operations
  - Integrated PlantUML preview
  - Advanced configuration options

#### **Web Application (Streamlit)**
- **Location**: `streamlit_app.py`, `src/`
- **Purpose**: Browser-based access with responsive design
- **Key Features**:
  - Cross-platform compatibility
  - Mobile-responsive interface
  - Real-time collaboration potential
  - Easy deployment and updates

### 2. **Core Services Layer**

#### **BPMN v2 Generation Engine**
- **Location**: `bpmn_v2/`
- **Purpose**: Advanced BPMN generation with iterative quality optimization

**Components**:
```python
bpmn_v2/
├── ai_integration.py          # AI provider abstractions
├── ai_config.py              # Dynamic AI configuration
├── complete_pipeline.py      # End-to-end BPMN pipeline
├── iterative_pipeline.py     # Quality optimization engine
├── mcp_server_simple.py      # BPMN quality assessment
└── quality_metrics.py        # Quality measurement framework
```

**Key Features**:
- Multi-provider AI support (OpenAI, Gemini, Claude, Ollama)
- Iterative quality improvement
- Real-time progress monitoring
- BPMN 2.0 compliance validation

#### **AI Integration Layer**
- **Location**: `src/bpmn_integration.py`
- **Purpose**: Unified AI interface with provider abstraction

**Architecture**:
```python
class AIConfig:
    provider: AIProvider
    api_key: str
    model: str
    base_url: Optional[str]

class AIClientFactory:
    @staticmethod
    def create_client(config: AIConfig) -> AIClient
    
class BPMNIntegration:
    def generate_bpmn_process() -> Tuple[bool, str, Dict]
    def validate_bpmn() -> Tuple[bool, float, Dict]
```

#### **PDF Analysis Engine**
- **Location**: `utils/pdf/`
- **Purpose**: Intelligent document analysis with context extraction

**Smart Processing**:
```python
class AIPDFAnalyzer:
    def analyze_pdf(self, pdf_path: str) -> BusinessContext
    def select_processing_method(self, file_size: int) -> str
    def extract_business_context(self, content: str) -> BusinessContext
```

**Processing Methods**:
- **Direct PDF Analysis**: AI-powered full context extraction (≤2MB)
- **Text Extraction**: Fast text-based processing (>2MB)
- **Hybrid Approach**: Automatic method selection based on capabilities

### 3. **Infrastructure Layer**

#### **Configuration Management**
- **Location**: `.env.template`, configuration files
- **Purpose**: Dynamic environment-based configuration

**Configuration Hierarchy**:
```
1. Environment Variables (.env)
2. Command Line Arguments
3. GUI Overrides
4. Default Values
```

**Key Configuration Areas**:
```bash
# AI Configuration
MODEL_PROVIDER=gemini
API_KEY=your_key
API_DEFAULT_MODEL=models/gemini-2.0-flash

# BPMN v2 Settings
BPMN_QUALITY_THRESHOLD=0.8
BPMN_MAX_ITERATIONS=10
BPMN_AUTO_VALIDATE=true

# Application Settings
APP_LANGUAGE=pl
LOG_LEVEL=INFO
SECURITY_ENABLED=true
```

#### **Logging and Monitoring**
- **Location**: `utils/logger_utils.py`, `logs/`
- **Purpose**: Comprehensive logging and performance monitoring

**Logging Architecture**:
```python
logger_config = {
    'level': 'INFO',
    'format': '%(asctime)s [%(levelname)s] %(message)s',
    'handlers': [
        FileHandler('logs/app.log'),
        StreamHandler()
    ]
}
```

**Monitoring Metrics**:
- Generation time and success rates
- Quality score distributions
- AI provider performance
- Resource utilization
- Error rates and patterns

## Data Flow Architecture

### 1. **BPMN Generation Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User Input      │───▶│ Template        │───▶│ AI Provider     │
│ (Text/PDF)      │    │ Processing      │    │ (OpenAI/Gemini) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Context         │    │ Prompt          │    │ Generated       │
│ Enrichment      │    │ Generation      │    │ BPMN XML        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Quality         │    │ Iterative       │    │ Final Output    │
│ Assessment      │    │ Improvement     │    │ & Export        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. **PDF Processing Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ PDF Upload      │───▶│ File Analysis   │───▶│ Method          │
│                 │    │ (Size/Type)     │    │ Selection       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Content         │    │ Business        │    │ Enhanced        │
│ Extraction      │    │ Context         │    │ Diagram         │
│                 │    │ Analysis        │    │ Generation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3. **Quality Optimization Flow**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Initial         │───▶│ Quality         │───▶│ Improvement     │
│ Generation      │    │ Assessment      │    │ Analysis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Iteration       │◀───│ Quality Check   │◀───│ Enhanced        │
│ Loop            │    │                 │    │ Generation      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Target          │    │ Final           │    │ Export &        │
│ Quality?        │───▶│ Validation      │───▶│ Delivery        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Security Architecture

### 1. **Authentication and Authorization**

**API Key Management**:
```python
class SecureKeyManager:
    def store_key(self, provider: str, key: str) -> None
    def retrieve_key(self, provider: str) -> Optional[str]
    def validate_key(self, provider: str, key: str) -> bool
    def encrypt_storage(self, data: str) -> str
```

**Security Layers**:
- Environment variable protection
- In-memory key storage only
- Secure API communication (HTTPS)
- No persistent credential storage

### 2. **Data Protection**

**Privacy Controls**:
```python
class DataProtection:
    def anonymize_content(self, text: str) -> str
    def sanitize_input(self, content: str) -> str
    def audit_log_access(self, operation: str) -> None
```

**Data Handling Policies**:
- Local processing preferred
- Minimal external API data transfer
- No persistent storage of sensitive content
- Configurable data retention policies

### 3. **Secure Communication**

**API Communication**:
```python
class SecureAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.session = requests.Session()
        self.session.verify = True  # SSL verification
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, endpoint: str, data: Dict) -> Response
```

## Scalability and Performance

### 1. **Horizontal Scaling**

**Web Application Scaling**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Load Balancer   │───▶│ Streamlit       │    │ Streamlit       │
│                 │    │ Instance 1      │    │ Instance 2      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Shared          │    │ AI Provider     │    │ File Storage    │
│ Configuration   │    │ Pool            │    │ System          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**AI Provider Load Balancing**:
```python
class AIProviderPool:
    def __init__(self, providers: List[AIConfig]):
        self.providers = providers
        self.load_balancer = RoundRobinBalancer()
    
    def get_provider(self) -> AIConfig:
        return self.load_balancer.next_provider()
    
    def handle_failure(self, provider: AIConfig):
        self.load_balancer.mark_failed(provider)
```

### 2. **Performance Optimization**

**Caching Strategy**:
```python
class GenerationCache:
    def cache_result(self, input_hash: str, result: Dict) -> None
    def get_cached_result(self, input_hash: str) -> Optional[Dict]
    def invalidate_cache(self, pattern: str) -> None
    
    # Redis-based for distributed caching
    # Memory-based for single instance
```

**Resource Management**:
```python
class ResourceManager:
    def limit_concurrent_requests(self, max_requests: int = 10)
    def manage_memory_usage(self, max_memory_mb: int = 2048)
    def timeout_long_requests(self, timeout_seconds: int = 300)
```

### 3. **Database Integration** (Optional)

**Support for Multiple Backends**:
```python
class DatabaseConnector:
    def __init__(self, db_type: str, connection_params: Dict):
        if db_type == 'mysql':
            self.connector = MySQLConnector(connection_params)
        elif db_type == 'postgresql':
            self.connector = PostgreSQLConnector(connection_params)
        elif db_type == 'sqlite':
            self.connector = SQLiteConnector(connection_params)
    
    def save_generation_history(self, result: GenerationResult)
    def retrieve_user_history(self, user_id: str) -> List[GenerationResult]
```

## Deployment Architecture

### 1. **Local Development**

```
Developer Machine
├── Python 3.8+ Environment
├── Required Dependencies (pip install -r requirements.txt)
├── PlantUML JAR file
├── Environment Configuration (.env)
└── AI Provider API Keys
```

### 2. **Production Deployment Options**

#### **Docker Container Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py"]
```

**Docker Compose Setup**:
```yaml
version: '3.8'
services:
  gd-python-web:
    build: .
    ports:
      - "8501:8501"
    environment:
      - MODEL_PROVIDER=gemini
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./temp:/app/temp

  gd-python-desktop:
    build: .
    command: python main.py
    environment:
      - DISPLAY=${DISPLAY}
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
```

#### **Cloud Deployment**

**AWS Deployment**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Application     │    │ Elastic         │    │ RDS Database    │
│ Load Balancer   │───▶│ Container       │───▶│ (Optional)      │
│ (ALB)           │    │ Service (ECS)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ CloudWatch      │    │ S3 Storage      │    │ Parameter       │
│ Monitoring      │    │ (Files/Logs)    │    │ Store (Secrets) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Google Cloud Deployment**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cloud Load      │    │ Cloud Run       │    │ Cloud SQL       │
│ Balancer        │───▶│ Instances       │───▶│ (Optional)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cloud           │    │ Cloud Storage   │    │ Secret          │
│ Monitoring      │    │ (Files/Logs)    │    │ Manager         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3. **Enterprise Deployment**

**Multi-Environment Setup**:
```
Production Environment
├── Web Application Cluster (3+ instances)
├── Load Balancer with SSL termination
├── Database Cluster (High Availability)
├── Monitoring and Alerting
├── Backup and Disaster Recovery
└── Security Scanning and Compliance

Staging Environment
├── Single Web Instance
├── Test Database
├── Integration Testing
└── Performance Testing

Development Environment
├── Local Development
├── Feature Branch Testing
├── Unit Testing
└── Code Quality Checks
```

## Integration Architecture

### 1. **External Tool Integration**

**Enterprise Architect Integration**:
```python
class EAIntegration:
    def export_to_ea(self, bpmn_xml: str, project_path: str) -> bool
    def import_from_ea(self, project_path: str) -> str
    def sync_with_repository(self, ea_repository: str) -> None
```

**Camunda Integration**:
```python
class CamundaIntegration:
    def deploy_to_camunda(self, bpmn_xml: str, deployment_name: str) -> str
    def start_process_instance(self, process_key: str, variables: Dict) -> str
    def query_process_instances(self, process_key: str) -> List[Dict]
```

### 2. **API Integration Points**

**RESTful API Design**:
```python
# FastAPI integration example
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class GenerationRequest(BaseModel):
    process_description: str
    quality_target: float = 0.8
    template_type: str = "BPMN"

@app.post("/api/v1/generate")
async def generate_diagram(request: GenerationRequest):
    # Integration with GD_python core services
    pass

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0"}
```

**Webhook Support**:
```python
class WebhookManager:
    def register_webhook(self, url: str, events: List[str]) -> str
    def trigger_webhook(self, event: str, payload: Dict) -> None
    def validate_webhook_signature(self, signature: str, payload: str) -> bool
```

### 3. **CI/CD Integration**

**GitHub Actions Workflow**:
```yaml
name: GD_python CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
      - name: Quality checks
        run: |
          flake8 src/
          mypy src/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment commands
```

## Future Architecture Considerations

### 1. **Microservices Evolution**

**Service Decomposition**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ BPMN Generation │    │ PDF Analysis    │    │ Quality         │
│ Service         │    │ Service         │    │ Assessment      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Template        │    │ AI Provider     │    │ Monitoring      │
│ Service         │    │ Gateway         │    │ Service         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. **Cloud-Native Features**

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gd-python-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gd-python-web
  template:
    metadata:
      labels:
        app: gd-python-web
    spec:
      containers:
      - name: gd-python
        image: gd-python:latest
        ports:
        - containerPort: 8501
        env:
        - name: MODEL_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: gd-python-config
              key: model-provider
```

### 3. **AI/ML Pipeline Integration**

**MLOps Integration**:
```python
class MLPipeline:
    def train_custom_model(self, training_data: List[Dict]) -> str
    def deploy_model(self, model_id: str, environment: str) -> str
    def monitor_model_performance(self, model_id: str) -> Dict
    def retrain_model(self, model_id: str, feedback_data: List[Dict]) -> str
```

---

*This architecture documentation provides a comprehensive overview of the GD_python system design, supporting both current capabilities and future scalability requirements.*