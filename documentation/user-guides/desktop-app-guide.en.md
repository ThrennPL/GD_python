# Desktop Application User Guide - GD_python

## Overview

The GD_python desktop application is a powerful PyQt5-based tool for generating professional UML and BPMN diagrams using artificial intelligence. This guide provides comprehensive instructions for using all features of the desktop application.

## Getting Started

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, Linux Ubuntu 18.04+
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Internet**: Required for AI model access

### Installation

1. **Download and Extract**
   ```bash
   git clone https://github.com/ThrennPL/GD_python
   cd GD_python
   ```

2. **Install Dependencies**
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Configure Environment**
   - Copy `.env.template` to `.env`
   - Fill in your API keys and configuration

4. **Download PlantUML**
   - Download `plantuml.jar` from https://plantuml.com/download
   - Place in project root directory

5. **Launch Application**
   ```bash
   python main.py
   ```

## Main Interface

### Application Layout

The desktop application features a clean, intuitive interface with the following sections:

#### 1. **Menu Bar**
- **File**: New, Open, Save, Export options
- **Edit**: Copy, Paste, Preferences
- **Tools**: Validation, Quality Check, PlantUML Preview
- **Help**: Documentation, About, Shortcuts

#### 2. **Toolbar**
- Quick access to common functions
- Generate, Validate, Export buttons
- Language toggle (Polish/English)
- AI provider selection

#### 3. **Main Work Area**
- **Input Panel** (left): Process description and configuration
- **Output Panel** (right): Generated diagrams and code
- **Properties Panel** (bottom): Metadata and quality metrics

#### 4. **Status Bar**
- Generation progress
- AI provider status
- Quality score indicator
- Processing time display

### Key Features

#### 🎯 **BPMN v2 Generation**
- Iterative quality optimization
- Real-time progress monitoring
- Automatic compliance checking
- Enterprise-ready XML output

#### 📄 **PDF Integration**
- Intelligent document analysis
- Context extraction
- Multi-page processing
- Smart method selection

#### 🌐 **Multi-language Support**
- Polish and English interfaces
- Localized prompt templates
- Cultural context adaptation

## Step-by-Step Workflow

### 1. Configure AI Provider

1. **Open Preferences** (Edit → Preferences)
2. **Select AI Provider**:
   - **OpenAI**: Requires OpenAI API key
   - **Google Gemini**: Requires Google API key  
   - **Anthropic Claude**: Requires Anthropic API key
   - **Ollama**: Requires local Ollama installation

3. **Configure Settings**:
   ```
   API Key: [Your API key]
   Model: [Select appropriate model]
   Quality Target: 0.8 (adjustable)
   Max Iterations: 10
   ```

4. **Test Connection**: Click "Test API" to verify configuration

### 2. Create BPMN Process

#### Basic Process Generation

1. **Select Template**
   - Choose "BPMN" from template dropdown
   - Select domain if applicable (Banking, Manufacturing, etc.)

2. **Enter Process Description**
   ```
   Example:
   "Customer loan application process in bank:
   1. Customer submits loan application
   2. Bank verifies customer documents
   3. Credit scoring analysis
   4. Risk assessment by analyst
   5. Approval or rejection decision
   6. Notification to customer"
   ```

3. **Configure Generation Parameters**
   - **Quality Target**: 0.7-0.9 (higher = better quality, longer time)
   - **Process Type**: Business, Technical, Regulatory
   - **Max Iterations**: 5-15 iterations
   - **Auto-validate**: Enable for automatic validation

4. **Generate Diagram**
   - Click "Generate BPMN v2" button
   - Monitor progress in real-time
   - Review quality score and iterations

#### Advanced BPMN Features

**Iterative Quality Optimization**:
- System automatically improves diagram quality
- Real-time feedback on optimization progress
- Configurable quality thresholds
- Detailed iteration history

**Regulatory Compliance** (Banking):
```
Template: BPMN - Banking Domain
Include: KYC requirements, AML checks, PSD2 compliance
Quality Target: 0.9 (high compliance standard)
```

### 3. PDF Document Analysis

#### Upload and Process PDF

1. **Select PDF Input**
   - Click "Load PDF" button
   - Choose document (max 50MB for direct processing)

2. **Configure Analysis**
   - **Analysis Mode**: AI (recommended) or Text Extraction
   - **Target Diagram**: BPMN, Use Case, Component
   - **Context Type**: Business Process, Technical Requirements

3. **Process Document**
   - System automatically selects optimal processing method:
     - **Direct PDF** (≤2MB): AI analysis with full context
     - **Text Extraction** (>2MB): Faster text-based processing
   - Monitor extraction progress

4. **Review Extracted Context**
   ```
   Actors: Customer, Bank Employee, System
   Processes: Application, Verification, Decision
   Business Rules: Credit limit, Risk threshold
   Data Flows: Application data, Credit report
   ```

5. **Generate Diagram from PDF Context**
   - Automatic template selection
   - Enriched context in prompts
   - Higher accuracy with domain knowledge

### 4. PlantUML Diagram Generation

#### Traditional UML Diagrams

1. **Select UML Template**:
   - **Activity**: Process flows with swimlanes
   - **Sequence**: System interactions over time
   - **Class**: Object-oriented design
   - **Component**: System architecture
   - **Use Case**: Functional requirements

2. **Enter Description**:
   ```
   Activity Diagram Example:
   "Online banking login process with two-factor authentication"
   
   Sequence Diagram Example:
   "API call flow between mobile app, gateway, and backend services"
   ```

3. **Generate and Review**:
   - PlantUML code generated automatically
   - SVG visualization rendered
   - Syntax validation performed
   - Export options available

### 5. Quality Assurance and Validation

#### Automatic Validation

**BPMN Validation**:
- BPMN 2.0 standard compliance
- Business logic verification
- Flow completeness check
- Syntax correctness validation

**Quality Metrics**:
- **Structural Quality** (0.0-1.0): BPMN compliance
- **Business Logic** (0.0-1.0): Process coherence  
- **Completeness** (0.0-1.0): Coverage of requirements
- **Clarity** (0.0-1.0): Diagram readability

#### Manual Review and Editing

1. **Code Editor**:
   - Built-in PlantUML/BPMN editor
   - Syntax highlighting
   - Auto-completion
   - Error detection

2. **Visual Preview**:
   - Real-time diagram rendering
   - Zoom and pan controls
   - Export to multiple formats

3. **Quality Dashboard**:
   - Detailed quality breakdown
   - Improvement suggestions
   - Historical quality tracking

## Advanced Features

### 1. Batch Processing

Process multiple documents or descriptions:

1. **Batch Mode**: File → Batch Process
2. **Add Items**: Multiple PDFs or text files
3. **Configure Template**: Single template for all items
4. **Execute Batch**: Automatic processing with progress tracking
5. **Review Results**: Quality summary and error reports

### 2. Template Customization

Create custom prompt templates:

1. **Template Editor**: Tools → Template Editor
2. **Base Template**: Start from existing template
3. **Customize Prompts**: Modify instructions and examples
4. **Test Template**: Validate with sample inputs
5. **Save Custom**: Add to template library

### 3. Integration with External Tools

#### Export Options

**BPMN Export**:
- `.bpmn` (Camunda Modeler)
- `.xml` (Generic BPMN 2.0)
- `.svg` (Vector graphics)
- `.png` (Raster graphics)

**PlantUML Export**:
- `.puml` (PlantUML source)
- `.svg` (Vector graphics)
- `.png` (Raster graphics)
- `.xmi` (Model interchange)

#### Integration APIs

```python
# External tool integration
from src.bpmn_integration import create_bpmn_integration

# Generate BPMN programmatically
bpmn_integration = create_bpmn_integration(
    api_key="your-key",
    model_provider="gemini"
)

success, xml, metadata = bpmn_integration.generate_bpmn_process(
    user_input="Process description...",
    quality_target=0.8
)
```

## Troubleshooting

### Common Issues

#### 1. **AI Provider Connection Failed**

**Symptoms**: Cannot connect to AI service  
**Solutions**:
- Verify API key in Preferences
- Check internet connection
- Confirm provider service status
- Try alternative provider

#### 2. **Poor Diagram Quality**

**Symptoms**: Low quality scores, incomplete diagrams  
**Solutions**:
- Increase quality target (0.8-0.9)
- Provide more detailed process description
- Add specific business rules and constraints
- Use domain-specific templates

#### 3. **PDF Processing Fails**

**Symptoms**: Cannot extract context from PDF  
**Solutions**:
- Ensure PDF is text-based (not scanned)
- Check file size (max 50MB)
- Try text extraction mode
- Verify PDF is not password-protected

#### 4. **PlantUML Rendering Issues**

**Symptoms**: Diagram not displaying correctly  
**Solutions**:
- Verify PlantUML.jar is in project directory
- Check Java installation
- Update PlantUML to latest version
- Validate PlantUML syntax

### Performance Optimization

#### System Performance

**Memory Usage**:
- Close unused tabs
- Clear generation history
- Restart application periodically

**Processing Speed**:
- Lower quality targets for faster generation
- Use text extraction for large PDFs
- Enable caching for repeated operations

#### AI Provider Optimization

**Token Usage**:
- Use concise process descriptions
- Avoid redundant information
- Select appropriate model size

**Response Time**:
- Choose local providers for speed
- Use smaller models for simple diagrams
- Configure reasonable timeouts

## Keyboard Shortcuts

### File Operations
- **Ctrl+N**: New document
- **Ctrl+O**: Open file
- **Ctrl+S**: Save current
- **Ctrl+Shift+E**: Export diagram

### Generation
- **F5**: Generate diagram
- **Ctrl+F5**: Regenerate with quality optimization
- **F6**: Validate current diagram
- **Shift+F6**: Run quality check

### View and Navigation
- **Ctrl+1**: Focus on input panel
- **Ctrl+2**: Focus on output panel
- **Ctrl+Plus**: Zoom in diagram
- **Ctrl+Minus**: Zoom out diagram
- **Ctrl+0**: Reset zoom

### Language and Templates
- **Alt+L**: Toggle language (Polish/English)
- **Alt+T**: Change template
- **Alt+P**: Open preferences

## Tips and Best Practices

### Writing Effective Process Descriptions

#### 1. **Structure Your Description**
```
Good Example:
"Banking loan approval process:
- Customer submits online application with required documents
- System performs automatic credit scoring (BIK check)
- If score > 700: automatic approval for amounts < 50,000 PLN
- If score 500-700: manual analyst review required
- If score < 500: automatic rejection with appeal option
- Approved loans require contract signing and funds transfer
- All decisions logged for audit and customer notification sent"

Poor Example:
"Bank process for loans and stuff, checking people's credit"
```

#### 2. **Include Business Rules**
- Specify decision criteria
- Include thresholds and limits
- Mention compliance requirements
- Add error scenarios

#### 3. **Define Actors Clearly**
- Use specific role names
- Distinguish between human and system actors
- Group related actors when appropriate

### BPMN v2 Quality Optimization

#### Quality Targets by Use Case
- **Draft/Concept**: 0.6-0.7
- **Business Documentation**: 0.7-0.8
- **Implementation Ready**: 0.8-0.9
- **Compliance/Audit**: 0.9+

#### Iteration Guidelines
- Start with 5-7 iterations for standard processes
- Use 10-15 for complex or regulatory processes
- Monitor progress - quality usually plateaus after optimal point

### PDF Document Preparation

#### Optimal Document Types
- Business process documentation
- Requirements specifications
- User manuals and procedures
- Policy and regulatory documents

#### Document Quality Tips
- Use clear headings and structure
- Include process flow descriptions
- Specify roles and responsibilities
- Document business rules and exceptions

---

## Support and Resources

### Documentation
- **User Guides**: Complete documentation in Polish and English
- **API Reference**: Technical documentation for developers
- **Video Tutorials**: Step-by-step video guides

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and tips
- **Examples**: Sample processes and templates

### Professional Support
- **Enterprise Support**: Priority support for business users
- **Training**: Custom training sessions available
- **Consulting**: Implementation and optimization services

---

*This user guide provides comprehensive coverage of the GD_python desktop application. For specific technical questions or advanced use cases, please refer to the API documentation or contact support.*