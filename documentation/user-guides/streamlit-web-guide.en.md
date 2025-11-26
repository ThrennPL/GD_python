# Streamlit Web Application Guide - GD_python

## Overview

The GD_python Streamlit web application provides an accessible, browser-based interface for generating professional UML and BPMN diagrams using artificial intelligence. This guide covers all features of the web application interface.

## Getting Started

### Access Methods

#### 1. **Local Installation**
```bash
# Clone and setup
git clone https://github.com/ThrennPL/GD_python
cd GD_python
pip install -r config/requirements.txt

# Launch web app
streamlit run streamlit_app.py
# or
./scripts/run_streamlit.bat
```

#### 2. **Direct Browser Access**
- Navigate to: `http://localhost:8501`
- No additional software required
- Works on mobile devices

### Browser Requirements
- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

## Interface Overview

### Main Layout

The Streamlit application features an intuitive single-page interface:

#### **Sidebar Configuration**
- AI Provider selection and API keys
- Template and language settings
- Quality parameters and options
- PDF upload and analysis controls

#### **Main Content Area**
- Process description input
- Real-time generation progress
- Interactive diagram display
- Quality metrics and metadata

#### **Results Section**
- Generated diagram visualization
- Download options
- Quality analysis
- Generation history

## Configuration Setup

### 1. AI Provider Configuration

#### **Sidebar: AI Configuration**

**Step 1: Select Provider**
```
Provider Options:
○ Google Gemini (Recommended)
○ OpenAI GPT-4
○ Anthropic Claude
○ Ollama (Local)
```

**Step 2: Enter API Key**
```
API Key: [Your API key here]
Test Connection: [Test Button]
```

**Step 3: Select Model**
```
Available Models:
- Gemini: models/gemini-2.0-flash
- OpenAI: gpt-4, gpt-4-turbo
- Claude: claude-3-sonnet-20240229
- Ollama: llama2, codellama
```

#### **Environment Variables Alternative**
Create `.env` file:
```bash
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key
API_DEFAULT_MODEL=models/gemini-2.0-flash
BPMN_QUALITY_THRESHOLD=0.8
```

### 2. Language and Template Settings

#### **Language Selection**
```
🌍 Interface Language:
○ Polski (Polish)
○ English
```

#### **Template Configuration**
```
📋 Diagram Template:
- BPMN (Business Process)
- Activity (Process Flow)
- Sequence (System Interactions)
- Class (Object Design)
- Component (System Architecture)
- Use Case (Requirements)
```

### 3. Quality Parameters

#### **BPMN v2 Quality Settings**
```
🎯 Quality Target: [0.8] (0.5-1.0)
🔄 Max Iterations: [10] (5-20)
⏱️ Timeout: [5 minutes]
✅ Auto Validate: [Enabled]
🔄 Auto Improve: [Enabled]
```

## Core Features

### 1. BPMN v2 Generation with Quality Optimization

#### **Basic Process Generation**

**Step 1: Enter Process Description**
```
📝 Process Description:

Banking customer onboarding process:

1. Customer initiates account opening online
2. System verifies customer identity (eID/biometrics)
3. Customer fills application form with personal data
4. System performs automatic KYC checks
5. If KYC positive: continue to credit scoring
6. Credit analyst reviews application manually
7. Final approval/rejection decision
8. Account creation and card issuance
9. Customer notification and activation
```

**Step 2: Configure Generation**
```
Process Type: [Business Process]
Quality Target: [0.8]
Domain: [Banking]
```

**Step 3: Generate BPMN**
- Click **"🚀 Generate BPMN v2"**
- Monitor real-time progress
- View quality optimization iterations

#### **Advanced BPMN Features**

**Iterative Quality Optimization**:
```
Iteration 1: Basic structure (Quality: 0.6)
Iteration 2: Add decision points (Quality: 0.7)
Iteration 3: Refine flows (Quality: 0.78)
Iteration 4: Add error handling (Quality: 0.82)
✅ Target quality reached!
```

**Real-time Progress Monitoring**:
```
🔄 Generating BPMN Process...
Progress: ████████░░ 80%
Current Quality: 0.78 / 0.80 target
Iteration: 4/10
Estimated Time: 15 seconds remaining
```

**Quality Metrics Display**:
```
📊 Generation Results:
✅ Final Quality Score: 0.85 / 0.80
🔄 Iterations Used: 5 / 10
⏱️ Total Time: 45 seconds
🤖 Model: models/gemini-2.0-flash
🏢 Provider: Google Gemini
```

### 2. Interactive Diagram Display

#### **BPMN Diagram Viewer**

The web app features an interactive BPMN.js-powered viewer:

**Features**:
- **Zoom Controls**: In, Out, Fit, Reset
- **Pan and Navigate**: Click and drag
- **Download Options**: SVG, PNG formats
- **Quality Warnings**: Visual indicators for issues

**Viewer Controls**:
```
🔍+ Zoom In    🔍- Zoom Out    📐 Fit Screen    🏠 Reset View
💾 Download SVG    📱 Mobile Responsive
```

**Example Display**:
```
📊 BPMN Diagram Viewer
╭─────────────────────────────────────────────────╮
│  [Start] → [KYC Check] → <Decision> → [End]    │
│     ↓                        ↓                  │
│  [Manual Review]         [Rejection]            │
╰─────────────────────────────────────────────────╯
⚠️ Warning: Cross-process flows detected
ℹ️ BPMN v2 requires message flows between pools
```

### 3. PDF Document Analysis

#### **Smart PDF Processing**

**Upload Interface**:
```
📄 PDF Document Analysis
┌─────────────────────────────────┐
│  Drag and drop PDF files here  │
│         or click to browse      │
│     Supported: PDF up to 50MB  │
└─────────────────────────────────┘
```

**Processing Options**:
```
🔍 Analysis Method:
○ AI Analysis (Recommended) - Full context extraction
○ Text Extraction - Faster processing
○ Auto Select - Based on file size

📋 Target Diagram:
○ BPMN Process
○ Use Case Diagram  
○ Component Architecture
```

**Processing Results**:
```
✅ PDF Analysis Complete!

📊 Extracted Context:
👥 Actors: Customer, Bank Employee, Compliance Officer
🔄 Processes: Application, Verification, Approval, Notification
📋 Business Rules: KYC requirements, Credit limits, Risk thresholds
📈 Data Flows: Personal data, Credit report, Decision outcome
⚠️ Risk Factors: AML check, PEP screening, Sanctions verification

📄 Document Summary:
- Pages: 15
- Processing time: 12 seconds
- Method: Direct PDF (AI)
- Quality: High context extraction
```

### 4. Multi-Language Support

#### **Language Toggle**
```
🌍 Language Settings:
Current: Polski 🇵🇱
Switch to: English 🇺🇸

📝 Template Language:
○ Polish prompts (localized business terms)
○ English prompts (international standards)

🏢 Domain Adaptation:
○ Polish banking (NBP, KNF regulations)
○ International banking (Basel, PSD2)
```

#### **Localized Output**
```
Polish Output Example:
- Aktorzy: "Klient", "Pracownik banku"
- Procesy: "Weryfikacja tożsamości"
- Decyzje: "Czy KYC pozytywny?"

English Output Example:
- Actors: "Customer", "Bank Employee"
- Processes: "Identity Verification"
- Decisions: "Is KYC positive?"
```

## Step-by-Step Workflows

### Workflow 1: Quick BPMN Generation

**Time Required**: 2-3 minutes

1. **Open Application**
   - Navigate to `http://localhost:8501`
   - Wait for interface to load

2. **Basic Configuration**
   - Select "Google Gemini" in sidebar
   - Enter API key
   - Click "Test Connection"

3. **Enter Process Description**
   ```
   Simple Example:
   "Customer support ticket resolution process"
   ```

4. **Generate with Defaults**
   - Click "Generate BPMN v2"
   - Accept default quality (0.8)
   - Wait for completion (~30 seconds)

5. **Review and Download**
   - Review generated diagram
   - Click "Download BPMN XML"
   - Save for use in other tools

### Workflow 2: High-Quality Regulatory Process

**Time Required**: 5-10 minutes

1. **Configure for High Quality**
   ```
   Quality Target: 0.9
   Max Iterations: 15
   Domain: Banking
   Template: BPMN - Banking Domain
   ```

2. **Detailed Process Description**
   ```
   Comprehensive Example:
   "Anti-Money Laundering (AML) transaction monitoring process:
   
   1. System monitors all customer transactions in real-time
   2. AI algorithm flags suspicious patterns (threshold >10,000 EUR)
   3. If flagged: automatic hold on transaction pending review
   4. AML specialist reviews transaction history and customer profile
   5. Risk assessment using FATF guidelines and local regulations
   6. If high risk: escalate to AML manager for decision
   7. If low risk: release transaction with monitoring note
   8. All decisions logged for regulatory reporting (UOKIK)
   9. Quarterly reports generated for NBP submission
   10. Customer notification only after investigation complete"
   ```

3. **Monitor Quality Optimization**
   - Watch iteration progress
   - Review quality improvements
   - Note regulatory compliance elements

4. **Validate Results**
   - Check compliance patterns
   - Verify decision points
   - Confirm regulatory flows

### Workflow 3: PDF-to-Diagram Generation

**Time Required**: 3-5 minutes

1. **Prepare PDF Document**
   - Ensure document contains process descriptions
   - Maximum size: 50MB
   - Text-based (not scanned images)

2. **Upload and Configure**
   ```
   📄 Upload PDF: [Select file]
   🔍 Analysis: AI Analysis
   📋 Target: BPMN Process
   🌍 Language: Auto-detect
   ```

3. **Process Document**
   - Click "Analyze PDF"
   - Monitor extraction progress
   - Review extracted context

4. **Generate Enhanced Diagram**
   - Process description auto-populated
   - Enhanced with PDF context
   - Generate with high quality settings

5. **Compare and Refine**
   - Compare with original document
   - Refine if necessary
   - Export final version

## Advanced Features

### 1. Batch Processing

Process multiple documents efficiently:

```
📁 Batch Mode:
┌─────────────────────────────────┐
│  Add multiple files:            │
│  • process1.pdf                 │
│  • process2.txt                 │
│  • requirements.docx            │
└─────────────────────────────────┘

📋 Batch Settings:
Template: BPMN Process
Quality: 0.8
Output: Individual files + Summary
```

### 2. Quality Analytics Dashboard

Track generation performance:

```
📊 Quality Analytics:
┌─────────────────────────────────┐
│  Session Statistics:            │
│  Diagrams Generated: 12         │
│  Average Quality: 0.83          │
│  Total Time: 8.5 minutes        │
│  Success Rate: 100%             │
└─────────────────────────────────┘

📈 Quality Trends:
Iteration 1: 0.65 → 0.78 → 0.85 ✅
Iteration 2: 0.70 → 0.82 → 0.89 ✅
```

### 3. Export and Integration

Multiple export formats available:

```
💾 Export Options:
┌─────────────────────────────────┐
│  BPMN Formats:                  │
│  ○ .bpmn (Camunda Modeler)     │
│  ○ .xml (Generic BPMN 2.0)     │
│  ○ .svg (Vector Graphics)      │
│                                 │
│  PlantUML Formats:              │
│  ○ .puml (PlantUML Source)     │
│  ○ .svg (Vector Graphics)      │
│  ○ .png (Raster Graphics)      │
└─────────────────────────────────┘
```

## Mobile and Responsive Design

### Mobile Usage

The web application is fully responsive:

**Features on Mobile**:
- Optimized input interfaces
- Touch-friendly controls
- Compressed diagram view
- Mobile-optimized exports

**Mobile Workflow**:
1. Open on mobile browser
2. Configure in sidebar (swipe from left)
3. Enter description (voice input supported)
4. Generate and review
5. Share or download directly

### Tablet Experience

Enhanced experience on tablets:

- Split-screen layout
- Larger diagram viewing
- Better editing experience
- Full desktop features

## Performance Optimization

### Speed Optimization

**Fast Generation Settings**:
```
Quality Target: 0.7 (vs 0.8+)
Max Iterations: 5 (vs 10+)
Template: Simple (vs Domain-specific)
```

**Network Optimization**:
- Local model deployment
- Caching enabled
- Compressed API requests

### Resource Management

**Memory Usage**:
- Automatic cleanup after generation
- Progressive loading of large PDFs
- Efficient diagram rendering

**Bandwidth**:
- Compressed API payloads
- SVG over raster graphics
- Lazy loading of components

## Troubleshooting

### Common Web Application Issues

#### **Connection Problems**
```
❌ Issue: "Cannot connect to AI provider"
✅ Solutions:
- Check internet connection
- Verify API key format
- Try alternative provider
- Check browser console for errors
```

#### **Diagram Display Issues**
```
❌ Issue: "Diagram not rendering"
✅ Solutions:
- Refresh page (Ctrl+F5)
- Clear browser cache
- Disable ad blockers
- Try different browser
```

#### **PDF Upload Failures**
```
❌ Issue: "PDF processing failed"
✅ Solutions:
- Check file size (<50MB)
- Verify PDF is not password-protected
- Try text extraction mode
- Use smaller file
```

### Performance Issues

#### **Slow Generation**
```
❌ Issue: Generation taking too long
✅ Solutions:
- Lower quality target
- Reduce max iterations
- Use simpler templates
- Try local AI provider
```

#### **Browser Memory Issues**
```
❌ Issue: Browser running out of memory
✅ Solutions:
- Close other tabs
- Refresh application
- Clear browser data
- Use smaller files
```

## Tips and Best Practices

### Writing for Web Interface

**Optimized Input**:
- Use clear, structured descriptions
- Include numbered steps
- Specify actors and decisions
- Add business rules explicitly

**Mobile-Friendly Input**:
- Use voice input for initial draft
- Edit and refine on larger screen
- Keep descriptions focused
- Use bullet points

### Quality vs Speed Balance

**For Quick Prototypes**:
```
Quality Target: 0.6-0.7
Max Iterations: 3-5
Template: Basic BPMN
```

**For Production Use**:
```
Quality Target: 0.8-0.9
Max Iterations: 8-12
Template: Domain-specific
```

### PDF Optimization

**Prepare PDFs for Best Results**:
- Use clear headings
- Structure with numbered sections
- Include process flow descriptions
- Add business rules explicitly

## Browser Security and Privacy

### Data Handling

**Local Processing**:
- Process descriptions handled locally when possible
- No data stored on servers without consent
- API keys encrypted in browser session

**Privacy Controls**:
- Clear session data option
- No tracking cookies
- Transparent data usage

### Security Features

**API Key Protection**:
- Keys stored in browser session only
- Never logged or transmitted unsecured
- Option to use environment variables

**Secure Communication**:
- HTTPS enforced for external APIs
- Encrypted API requests
- Secure session management

---

## Support and Resources

### Web Application Help

**In-App Help**:
- Contextual tooltips
- Interactive tutorials
- Example gallery
- FAQ section

**Video Resources**:
- Getting started guide
- Feature demonstrations
- Best practices tutorials
- Troubleshooting help

### Community and Support

**Online Resources**:
- GitHub documentation
- Community discussions
- Example processes
- Template library

**Professional Support**:
- Enterprise deployment assistance
- Custom template creation
- Training and consultation
- Priority technical support

---

*This guide covers all aspects of the GD_python Streamlit web application. For technical integration or API usage, refer to the technical documentation.*