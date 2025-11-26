# Data Model - GD_python

## Overview

The GD_python system operates with a sophisticated data model designed to support advanced BPMN v2 generation, quality assessment, and multi-provider AI integration. This document outlines the core data structures, relationships, and processing flows.

## Core Data Entities

### 1. **Generation Request Data Model**

#### **BPMNGenerationRequest**
```python
@dataclass
class BPMNGenerationRequest:
    """Complete BPMN generation request with all parameters"""
    
    # Input Data
    process_description: str                    # Primary process description
    pdf_content: Optional[str] = None          # Extracted PDF content
    business_context: Optional[BusinessContext] = None  # Enhanced context
    
    # Generation Parameters
    diagram_type: DiagramType = DiagramType.BPMN_ACTIVITY
    template_type: str = "BPMN_ACTIVITY_TEMPLATE"
    quality_target: float = 0.8               # Target quality score (0.0-1.0)
    
    # AI Configuration
    ai_provider: AIProvider = AIProvider.GEMINI
    model_name: str = "models/gemini-2.0-flash"
    api_key: str                              # Provider API key
    base_url: Optional[str] = None            # Custom API endpoint
    
    # Processing Options
    use_iterative_improvement: bool = True    # Enable quality optimization
    max_iterations: int = 10                  # Maximum improvement cycles
    enable_validation: bool = True            # BPMN 2.0 compliance check
    
    # Metadata
    user_id: Optional[str] = None             # User identifier
    session_id: str                           # Generation session ID
    timestamp: datetime                       # Request timestamp
    
    def validate(self) -> List[ValidationError]:
        """Validate request parameters"""
        errors = []
        
        if not self.process_description.strip():
            errors.append(ValidationError("Process description is required"))
        
        if not (0.0 <= self.quality_target <= 1.0):
            errors.append(ValidationError("Quality target must be between 0.0 and 1.0"))
        
        if self.max_iterations < 1:
            errors.append(ValidationError("Max iterations must be >= 1"))
            
        return errors
```

#### **BusinessContext**
```python
@dataclass
class BusinessContext:
    """Enhanced business context extracted from PDF or user input"""
    
    # Core Business Information
    business_domain: str                      # Industry/domain (e.g., "banking", "healthcare")
    process_type: str                         # Process category (e.g., "operational", "strategic")
    stakeholders: List[Stakeholder]           # Involved parties
    
    # Process Details
    objectives: List[str]                     # Business objectives
    constraints: List[str]                    # Business constraints
    regulations: List[str]                    # Regulatory requirements
    
    # Process Flow Information
    main_activities: List[str]                # Key process activities
    decision_points: List[str]                # Decision criteria
    data_objects: List[str]                   # Data entities involved
    
    # Quality Metrics
    success_criteria: List[str]               # Success measurements
    kpis: List[str]                          # Key performance indicators
    
    # Metadata
    confidence_score: float                   # AI confidence in extraction (0.0-1.0)
    source_document: Optional[str] = None     # Source PDF filename
    extraction_method: str = "ai_analysis"    # "ai_analysis" or "text_extraction"
    
    def to_context_string(self) -> str:
        """Convert to formatted context string for AI prompts"""
        context_parts = [
            f"Business Domain: {self.business_domain}",
            f"Process Type: {self.process_type}",
            f"Stakeholders: {', '.join([s.name for s in self.stakeholders])}",
            f"Objectives: {'; '.join(self.objectives)}",
            f"Main Activities: {'; '.join(self.main_activities)}"
        ]
        
        if self.constraints:
            context_parts.append(f"Constraints: {'; '.join(self.constraints)}")
        
        return "\n".join(context_parts)
```

#### **Stakeholder**
```python
@dataclass
class Stakeholder:
    """Business stakeholder information"""
    
    name: str                                 # Stakeholder name/role
    role: str                                # Functional role
    responsibilities: List[str]               # Key responsibilities
    involvement_level: str                    # "primary", "secondary", "reviewer"
    
    # BPMN Mapping
    swim_lane: Optional[str] = None          # Assigned swim lane
    actor_type: str = "human"                # "human", "system", "external"
```

### 2. **BPMN Generation Results**

#### **BPMNGenerationResult**
```python
@dataclass
class BPMNGenerationResult:
    """Complete result of BPMN generation process"""
    
    # Generation Status
    success: bool                             # Overall generation success
    session_id: str                           # Generation session ID
    
    # Generated Content
    bpmn_xml: str                            # Final BPMN XML content
    plantuml_code: str                       # PlantUML source code
    diagram_image: Optional[bytes] = None     # Generated diagram image
    
    # Quality Assessment
    quality_metrics: QualityMetrics          # Detailed quality assessment
    final_quality_score: float               # Final quality score (0.0-1.0)
    
    # Generation Process
    generation_history: List[GenerationIteration]  # Iterative improvements
    total_iterations: int                     # Number of improvement cycles
    improvement_achieved: float               # Quality improvement delta
    
    # AI Provider Information
    ai_provider_used: AIProvider             # Primary AI provider
    model_used: str                          # AI model identifier
    total_tokens_used: int                   # Total token consumption
    generation_cost: Optional[float] = None   # Cost estimate (if available)
    
    # Performance Metrics
    total_generation_time: float             # Total processing time (seconds)
    pdf_analysis_time: Optional[float] = None # PDF processing time
    ai_generation_time: float                # AI generation time
    validation_time: float                   # Validation processing time
    
    # Error Information
    errors: List[GenerationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime                       # Generation completion time
    version: str = "4.0.0"                  # System version
    
    def get_summary(self) -> Dict[str, Any]:
        """Get generation summary for logging/reporting"""
        return {
            'success': self.success,
            'quality_score': self.final_quality_score,
            'iterations': self.total_iterations,
            'generation_time': self.total_generation_time,
            'ai_provider': self.ai_provider_used.value,
            'model': self.model_used,
            'tokens_used': self.total_tokens_used
        }
```

#### **GenerationIteration**
```python
@dataclass
class GenerationIteration:
    """Single iteration in the quality improvement process"""
    
    iteration_number: int                     # Iteration sequence (1, 2, 3...)
    
    # Iteration Input
    input_prompt: str                         # AI prompt for this iteration
    previous_bpmn: Optional[str] = None       # Previous iteration BPMN
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # Iteration Output
    generated_bpmn: str                       # Generated BPMN XML
    quality_score: float                      # Quality assessment score
    quality_details: QualityMetrics          # Detailed quality breakdown
    
    # Iteration Metadata
    ai_response_time: float                   # AI generation time
    tokens_used: int                          # Token consumption
    timestamp: datetime                       # Iteration timestamp
    
    # Quality Analysis
    improvements_made: List[str] = field(default_factory=list)
    remaining_issues: List[str] = field(default_factory=list)
    
    def calculate_improvement(self, previous_score: float) -> float:
        """Calculate improvement over previous iteration"""
        return self.quality_score - previous_score if previous_score else 0.0
```

### 3. **Quality Assessment Data Model**

#### **QualityMetrics**
```python
@dataclass
class QualityMetrics:
    """Comprehensive BPMN quality assessment"""
    
    # Overall Quality
    overall_score: float                      # Weighted average (0.0-1.0)
    
    # Structural Quality (40% weight)
    structural_quality: StructuralQuality
    
    # Semantic Quality (35% weight)  
    semantic_quality: SemanticQuality
    
    # Syntactic Quality (25% weight)
    syntactic_quality: SyntacticQuality
    
    # Assessment Metadata
    assessment_timestamp: datetime
    assessment_method: str = "mcp_server"     # Assessment approach used
    confidence_level: float                   # Confidence in assessment (0.0-1.0)
    
    def calculate_weighted_score(self) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'structural': 0.40,
            'semantic': 0.35,
            'syntactic': 0.25
        }
        
        weighted_score = (
            self.structural_quality.score * weights['structural'] +
            self.semantic_quality.score * weights['semantic'] +
            self.syntactic_quality.score * weights['syntactic']
        )
        
        return round(weighted_score, 3)
    
    def get_improvement_suggestions(self) -> List[str]:
        """Get prioritized improvement suggestions"""
        suggestions = []
        
        # Prioritize by impact and current score
        if self.structural_quality.score < 0.8:
            suggestions.extend(self.structural_quality.improvement_suggestions)
        
        if self.semantic_quality.score < 0.8:
            suggestions.extend(self.semantic_quality.improvement_suggestions)
        
        if self.syntactic_quality.score < 0.8:
            suggestions.extend(self.syntactic_quality.improvement_suggestions)
        
        return suggestions[:5]  # Top 5 suggestions
```

#### **StructuralQuality**
```python
@dataclass
class StructuralQuality:
    """BPMN structural quality assessment"""
    
    score: float                              # Overall structural score (0.0-1.0)
    
    # Flow Analysis
    has_start_event: bool                     # Proper start event
    has_end_events: bool                      # Proper end events
    flow_completeness: float                  # All paths complete (0.0-1.0)
    
    # Gateway Analysis
    gateway_usage: float                      # Appropriate gateway usage (0.0-1.0)
    gateway_balance: bool                     # Balanced splits/joins
    
    # Pool and Lane Analysis
    pool_organization: float                  # Pool structure quality (0.0-1.0)
    lane_clarity: float                       # Lane assignment clarity (0.0-1.0)
    
    # Process Complexity
    complexity_score: float                   # Process complexity (0.0-1.0, lower is better)
    activity_count: int                       # Total activities
    gateway_count: int                        # Total gateways
    
    # Issues and Improvements
    structural_issues: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    
    def analyze_complexity(self) -> str:
        """Analyze process complexity level"""
        if self.activity_count <= 10 and self.gateway_count <= 3:
            return "simple"
        elif self.activity_count <= 20 and self.gateway_count <= 7:
            return "moderate"
        else:
            return "complex"
```

#### **SemanticQuality**
```python
@dataclass
class SemanticQuality:
    """BPMN semantic quality assessment"""
    
    score: float                              # Overall semantic score (0.0-1.0)
    
    # Business Alignment
    business_relevance: float                 # Relevance to business context (0.0-1.0)
    process_completeness: float               # Process coverage completeness (0.0-1.0)
    stakeholder_representation: float         # Stakeholder coverage (0.0-1.0)
    
    # Naming and Labels
    naming_consistency: float                 # Consistent naming (0.0-1.0)
    label_clarity: float                      # Clear, meaningful labels (0.0-1.0)
    
    # Domain Alignment
    domain_terminology: float                 # Appropriate domain terms (0.0-1.0)
    business_rule_representation: float       # Business rules coverage (0.0-1.0)
    
    # Context Alignment
    objective_alignment: List[str]            # Aligned business objectives
    missing_elements: List[str]               # Potentially missing elements
    
    # Improvements
    semantic_issues: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
```

#### **SyntacticQuality**
```python
@dataclass
class SyntacticQuality:
    """BPMN syntactic quality assessment"""
    
    score: float                              # Overall syntactic score (0.0-1.0)
    
    # BPMN 2.0 Compliance
    bpmn_compliance: bool                     # Valid BPMN 2.0 XML
    schema_validation: bool                   # Schema validation passed
    
    # XML Structure
    xml_well_formed: bool                     # Well-formed XML
    namespace_correct: bool                   # Correct BPMN namespace
    
    # Element Validity
    element_validity: float                   # Valid BPMN elements (0.0-1.0)
    attribute_completeness: float             # Required attributes (0.0-1.0)
    
    # Relationship Validity
    flow_validity: bool                       # Valid sequence flows
    reference_integrity: bool                 # Valid element references
    
    # Errors and Issues
    validation_errors: List[ValidationError] = field(default_factory=list)
    compliance_warnings: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
```

### 4. **AI Provider Integration Data Model**

#### **AIProvider**
```python
class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    OLLAMA = "ollama"
```

#### **AIConfig**
```python
@dataclass
class AIConfig:
    """AI provider configuration"""
    
    provider: AIProvider                      # Provider type
    api_key: str                             # Authentication key
    model: str                               # Model identifier
    base_url: Optional[str] = None           # Custom API endpoint
    
    # Request Configuration
    max_tokens: Optional[int] = None         # Maximum response tokens
    temperature: float = 0.1                 # Generation creativity (0.0-1.0)
    timeout: int = 300                       # Request timeout (seconds)
    
    # Provider-Specific Settings
    provider_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.api_key and self.provider != AIProvider.OLLAMA:
            return False
        
        if not self.model:
            return False
        
        if not (0.0 <= self.temperature <= 1.0):
            return False
            
        return True
```

#### **AIResponse**
```python
@dataclass
class AIResponse:
    """AI provider response data"""
    
    # Response Content
    content: str                              # Generated content
    
    # Response Metadata
    model_used: str                           # Actual model used
    tokens_used: int                          # Token consumption
    response_time: float                      # Generation time (seconds)
    
    # Quality Indicators
    finish_reason: str                        # Completion reason
    confidence_score: Optional[float] = None  # Response confidence
    
    # Provider Information
    provider: AIProvider                      # Provider used
    request_id: str                           # Provider request ID
    timestamp: datetime                       # Response timestamp
    
    # Cost Information
    estimated_cost: Optional[float] = None    # Estimated cost (USD)
    
    def is_complete(self) -> bool:
        """Check if response is complete"""
        return self.finish_reason in ["stop", "end_turn", "complete"]
```

### 5. **Template and Configuration Data Model**

#### **TemplateConfig**
```python
@dataclass
class TemplateConfig:
    """BPMN template configuration"""
    
    # Template Identity
    template_id: str                          # Unique template identifier
    template_name: str                        # Human-readable name
    template_type: DiagramType                # Diagram type
    
    # Template Content
    base_template: str                        # Base template content
    placeholders: List[str]                   # Available placeholders
    
    # Configuration
    default_quality_target: float = 0.8      # Default quality target
    supports_iterative: bool = True           # Supports improvement
    
    # Customization
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    style_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    version: str = "1.0"                     # Template version
    created_by: str = "system"               # Template creator
    last_modified: datetime = field(default_factory=datetime.now)
```

#### **DiagramType**
```python
class DiagramType(Enum):
    """Supported diagram types"""
    BPMN_ACTIVITY = "bpmn_activity"
    BPMN_COLLABORATION = "bpmn_collaboration"
    BPMN_PROCESS = "bpmn_process"
    SEQUENCE_DIAGRAM = "sequence"
    CLASS_DIAGRAM = "class"
    COMPONENT_DIAGRAM = "component"
```

### 6. **Session and History Data Model**

#### **GenerationSession**
```python
@dataclass
class GenerationSession:
    """User generation session tracking"""
    
    # Session Identity
    session_id: str                           # Unique session ID
    user_id: Optional[str] = None            # User identifier
    
    # Session Data
    requests: List[BPMNGenerationRequest] = field(default_factory=list)
    results: List[BPMNGenerationResult] = field(default_factory=list)
    
    # Session Metadata
    start_time: datetime                      # Session start
    last_activity: datetime                   # Last activity
    total_generations: int = 0                # Total generations
    
    # Performance Tracking
    total_tokens_used: int = 0                # Cumulative tokens
    total_cost: float = 0.0                   # Cumulative cost
    average_quality: float = 0.0              # Average quality score
    
    def add_generation(self, request: BPMNGenerationRequest, 
                      result: BPMNGenerationResult) -> None:
        """Add generation to session"""
        self.requests.append(request)
        self.results.append(result)
        self.total_generations += 1
        self.last_activity = datetime.now()
        
        # Update aggregates
        self.total_tokens_used += result.total_tokens_used
        if result.generation_cost:
            self.total_cost += result.generation_cost
        
        # Recalculate average quality
        if self.results:
            self.average_quality = sum(r.final_quality_score for r in self.results) / len(self.results)
```

### 7. **Error and Validation Data Model**

#### **GenerationError**
```python
@dataclass
class GenerationError:
    """Generation error information"""
    
    error_type: str                           # Error category
    error_message: str                        # Error description
    error_code: Optional[str] = None         # Error code
    
    # Context
    component: str                            # Component where error occurred
    iteration: Optional[int] = None          # Iteration number (if applicable)
    
    # Technical Details
    stack_trace: Optional[str] = None        # Technical stack trace
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Resolution
    is_recoverable: bool = False             # Can be recovered
    suggested_action: Optional[str] = None   # Suggested user action
```

#### **ValidationError**
```python
@dataclass
class ValidationError:
    """Validation error details"""
    
    message: str                             # Error message
    field: Optional[str] = None             # Field name (if applicable)
    value: Optional[Any] = None             # Invalid value
    constraint: Optional[str] = None        # Violated constraint
    
    severity: str = "error"                 # "error", "warning", "info"
    error_code: Optional[str] = None        # Validation error code
```

## Data Processing Flows

### 1. **PDF Processing Flow**

```python
# PDF → BusinessContext transformation
pdf_content: str → 
    pdf_analyzer.analyze() → 
        BusinessContext(
            business_domain=extracted_domain,
            stakeholders=identified_stakeholders,
            main_activities=process_activities,
            objectives=business_objectives
        )
```

### 2. **Quality Assessment Flow**

```python
# BPMN XML → QualityMetrics transformation
bpmn_xml: str →
    quality_assessor.assess() →
        QualityMetrics(
            overall_score=calculated_score,
            structural_quality=StructuralQuality(...),
            semantic_quality=SemanticQuality(...),
            syntactic_quality=SyntacticQuality(...)
        )
```

### 3. **Iterative Improvement Flow**

```python
# Quality-driven improvement cycle
initial_bpmn: str →
    quality_assessment: QualityMetrics →
        improvement_suggestions: List[str] →
            enhanced_prompt: str →
                improved_bpmn: str →
                    new_quality_assessment: QualityMetrics
```

## Database Schema (Optional Integration)

### 1. **Core Tables**

```sql
-- Generation Sessions
CREATE TABLE generation_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    start_time TIMESTAMP,
    last_activity TIMESTAMP,
    total_generations INT DEFAULT 0,
    total_tokens_used INT DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0,
    average_quality DECIMAL(4,3) DEFAULT 0
);

-- Generation Requests
CREATE TABLE generation_requests (
    request_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES generation_sessions(session_id),
    process_description TEXT,
    diagram_type VARCHAR(50),
    ai_provider VARCHAR(50),
    model_name VARCHAR(100),
    quality_target DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generation Results
CREATE TABLE generation_results (
    result_id VARCHAR(255) PRIMARY KEY,
    request_id VARCHAR(255) REFERENCES generation_requests(request_id),
    success BOOLEAN,
    bpmn_xml TEXT,
    plantuml_code TEXT,
    final_quality_score DECIMAL(4,3),
    total_iterations INT,
    generation_time DECIMAL(8,3),
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Metrics
CREATE TABLE quality_metrics (
    metric_id VARCHAR(255) PRIMARY KEY,
    result_id VARCHAR(255) REFERENCES generation_results(result_id),
    overall_score DECIMAL(4,3),
    structural_score DECIMAL(4,3),
    semantic_score DECIMAL(4,3),
    syntactic_score DECIMAL(4,3),
    assessment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. **Indexing Strategy**

```sql
-- Performance indexes
CREATE INDEX idx_sessions_user_time ON generation_sessions(user_id, start_time);
CREATE INDEX idx_requests_session ON generation_requests(session_id);
CREATE INDEX idx_results_request ON generation_results(request_id);
CREATE INDEX idx_metrics_result ON quality_metrics(result_id);
CREATE INDEX idx_results_quality ON generation_results(final_quality_score);
```

## Data Serialization

### 1. **JSON Serialization**

```python
class BPMNDataEncoder(json.JSONEncoder):
    """Custom JSON encoder for BPMN data objects"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

# Usage
def serialize_result(result: BPMNGenerationResult) -> str:
    return json.dumps(result, cls=BPMNDataEncoder, indent=2)
```

### 2. **Data Validation**

```python
from pydantic import BaseModel, validator

class BPMNGenerationRequestModel(BaseModel):
    """Pydantic model for request validation"""
    
    process_description: str
    quality_target: float
    ai_provider: str
    
    @validator('quality_target')
    def quality_target_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Quality target must be between 0.0 and 1.0')
        return v
    
    @validator('process_description')
    def description_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Process description cannot be empty')
        return v
```

---

*This data model documentation provides comprehensive coverage of all data structures used in the GD_python system, supporting both current functionality and future extensibility.*