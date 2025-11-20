# UML/BPMN Diagram Generator & Validator with AI

**Project Status**: ✅ **REORGANIZATION COMPLETED** (2025-11-20) - New professional structure + Smart PDF Analysis System

An application for generating, visualizing, and validating UML (PlantUML) and BPMN (XML) diagrams based on process descriptions, using AI models (e.g., LLM). The project offers both a desktop version (PyQt5) and a web version (Streamlit), allowing you to select prompt templates, diagram types, validate process descriptions, and automatically verify PlantUML code.

**🆕 Latest Features:**
- **🧠 Smart PDF Analysis System** - intelligent model capability detection and automatic method selection
- **📁 Reorganized structure** - professional code organization (src/, tests/, tools/, config/)
- **⚡ Real-time progress tracking** - live feedback during operations
- **🔄 Graceful fallback** - automatic method switching on errors

---

## Quick Start (for new users)

1. **Clone the repository:**
    ```bash
    git clone https://github.com/ThrennPL/GD_python
    cd GD_python
    ```
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Download `plantuml.jar`**  
   Download the file from [PlantUML Download](https://plantuml.com/download) and place it in the project directory.
4. **Check Java:**  
   Make sure Java is installed (run in terminal):
    ```bash
    java -version
    ```
5. **Create a `.env` file:**  
   Copy the configuration below into a `.env` file in the main project directory and fill in the required fields (e.g., `API_KEY` for Gemini/OpenAI, database details if you want to save history):
    ```
    PLANTUML_JAR_PATH=plantuml.jar
    PLANTUML_GENERATOR_TYPE=local
    API_URL=http://localhost:1234/v1/models
    #API_URL=https://api.openai.com/v1/models
    #API_URL=https://generativelanguage.googleapis.com/v1beta/models
    API_DEFAULT_MODEL=
    CHAT_URL=http://localhost:1234/v1/chat/completions
    #CHAT_URL=https://api.openai.com/v1/chat/completions
    #CHAT_URL=https://generativelanguage.googleapis.com/v1v1beta/chat/completions
    API_KEY=
    MODEL_PROVIDER=local
    #MODEL_PROVIDER=openai
    #MODEL_PROVIDER=gemini
    DB_PROVIDER=
    DB_HOST=
    DB_PORT=
    DB_NAME=
    DB_USER=
    DB_PASSWORD=
    ```
6. **Start a local AI server (e.g., LM Studio):**  
   If using a local model, start LM Studio and check if it's available at `http://localhost:1234`.
7. **Run the application:**
   - **Streamlit:**  
     ```bash
     streamlit run src/streamlit_app.py
     # or
     scripts/run_streamlit.bat
     ```
   - **PyQt5:**  
     ```bash
     python main.py
     ```

---

## Features

  * Generate PlantUML or BPMN XML code from process descriptions
  * **🆕 Smart PDF Analysis System** - intelligent model capability detection and automatic analysis method selection
  * Select prompt template and diagram type (sequence, activity, class, component, state, use case, etc.)
  * Visualize PlantUML diagrams (SVG)
  * **🆕 PlantUML Code Editing** - edit generated code directly in the application
  * Automatic PlantUML code verification if SVG generation fails
  * **🆕 Enhanced Error Verification** - more accurate detection of PlantUML syntax errors
  * **🆕 GUI Language Selection** - dynamic language switching during application use
  * AI-based process description validation
  * Conversation history with the AI model
  * Support for multiple AI models (local or via API, e.g., OpenAI, Gemini)
  * Download generated diagrams in PlantUML, SVG, XMI formats
  * Special options for BPMN diagrams (complexity level, validation rule, output format, domain)
  * Save queries and model responses to a database (mySQL, PostgreSQL)
  * **Two interface and prompt languages (English and Polish)**
  * Sample test prompts for the banking industry

---

## 🆕 Smart PDF Analysis System

**Advanced PDF analysis system with AI that automatically detects model capabilities and intelligently selects analysis method.**

### 🎯 Key Features:
- **Automatic model capability detection** - system checks if model supports direct PDF upload
- **Intelligent method selection** - based on file size and model capabilities
- **Real-time progress tracking** - live feedback during PDF analysis
- **Hierarchical fallback** - automatic switching between methods on errors
- **Smart method selection** - small files (Direct PDF, high quality), large files (Text Extraction, faster)

### 📊 Performance Metrics:
| Method | Time/MB | Quality | Business Elements |
|--------|---------|---------|-------------------|
| Direct PDF | 11.5s | High | 75% accuracy |
| Text Extraction | 3.6s | Medium | Basic |

### ⚙️ Configuration:
```env
# Smart PDF Analysis
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash
PDF_ANALYSIS_MODE=ai
PDF_DIRECT_THRESHOLD_MB=2.0
PDF_MAX_PAGES_TEXT=50
PDF_CHUNK_SIZE=4000
```

### 🚀 Usage:
1. **Automatic detection** - system checks model capabilities
2. **Smart selection** - chooses optimal method (Direct PDF ≤2MB, Text Extraction >2MB)
3. **Progress tracking** - real-time feedback on progress
4. **Graceful fallback** - automatic switching on errors
5. **Enhanced context** - enriched business context in prompts

### 🎯 Models Supporting Direct PDF:
- ✅ Gemini 2.0 Flash
- ✅ Gemini 1.5 Pro/Flash
- ❌ OpenAI models (fallback to text extraction)
- ❌ Local models (fallback to text extraction)

---

## 🆕 PlantUML Code Editing

**New functionality allowing direct editing of generated PlantUML code.**

### Capabilities:
- **Code editing** directly in the application via "PlantUML Code" button
- **Real-time preview** - instant diagram updates
- **Save changes** - ability to update diagram after editing
- **Intuitive UI** - convenient editor with syntax highlighting

### How to use:
1. **Generate diagram** using AI
2. **Click "PlantUML Code"** to open editor
3. **Edit code** directly in dialog window
4. **Click "Update diagram"** to apply changes
5. **Diagram will be automatically updated**

### Benefits:
- **Quick fixes** without AI regeneration
- **Fine-tuning** diagram details
- **Learn PlantUML syntax** through practice
- **Control over final result**

---

## XMI Export

XMI export is currently available **only for class, sequence, activity and component diagrams (Class Diagram, Sequence Diagram, Activity Diagram, Component Diagram)**. The "Save XMI" button (also in the context menu) is active only when the current tab contains a class, sequence, or activity diagram. For other diagram types (e.g., use case, component), XMI export is not yet supported. After importing into EA, elements may require manual arrangement.

---

## Tab Management (Desktop Version)

The desktop app allows working with multiple diagrams in tabs. When switching tabs, the app automatically checks the diagram type and activates/deactivates the XMI export button.

---

## SVG Diagram Generation

SVG diagrams can be generated in two ways, depending on the `plantuml_generator_type` setting:

  * **`plantuml_generator_type = local`**: SVG diagrams are generated locally using `plantuml.jar` and Java. Make sure both are available on your system.
  * **`plantuml_generator_type = www`**: SVG diagrams are generated using [www.plantuml.com](https://plantuml.com/).

---

## Requirements

  * Python 3.7+ (for Streamlit) or Python 3.8+ (for PyQt5)
  * Local AI server (e.g., LM Studio) running at `http://localhost:1234` (if using a local model)
  * Dependencies from `config/requirements.txt`
  * **🆕 Smart PDF Analysis:** 
    * PyPDF2, PyMuPDF (automatically installed)
    * Google Generative AI SDK (for Direct PDF upload)
    * Automatic model capability detection
  * Java (for local PlantUML rendering)
  * `plantuml.jar` (in `config/plantuml.jar`)
  * PyQt5 (desktop version only)
  * `.env` configuration file (copy in main directory + `config/.env`)

---

## FAQ / Common Issues

- **Missing Java or plantuml.jar:**  
  Make sure Java is installed (`java -version`) and `plantuml.jar` is in the project directory.
- **No connection to AI server:**  
  Check if LM Studio or another server is running and available at the specified address.
- **Missing API_KEY:**  
  For Gemini/OpenAI, you must provide your own API key in the `.env` file.
- **Database issues:**  
  If you want to save history to a database, configure the appropriate parameters in `.env` and ensure the database is available. See the dedicated connectors: `mysql_connector.py` and `PostgreSQL_connector.py` for required tables.

---

## Usage

1.  **Select AI model**: From the list of available models on the server.
2.  **🆕 Add PDF context**: (Optional) Upload a PDF file to enrich context.
3.  **Configure template**: Choose the template type (PlantUML/XML) and a specific template.
4.  **Select diagram type**: Sequence, activity, class, etc.
5.  **Enter process description**: In the text field, enter a detailed description of the process you want to visualize.
6.  **Generate/Validate**: Click "Send query" or "Validate description".
7.  **Display Diagram**: The generated PlantUML diagram (SVG) or BPMN XML code will appear in the appropriate tabs.
8.  **🆕 Edit code**: Click "PlantUML Code" to edit generated code directly in the application.

---

## 📁 New Project Structure

```
GD_python/
├── 📁 src/                     # Main application code
│   ├── main.py                 # PyQt5 application
│   ├── streamlit_app.py        # Streamlit application
│   ├── api_thread.py           # API communication
│   └── input_validator.py      # Input validation
├── 📁 tests/                   # All tests
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── system/                 # System tests
│   └── fixtures/               # Test data
├── 📁 tools/                   # Development tools
├── 📁 examples/                # Example diagrams
│   ├── activity/, class/, sequence/
│   └── generated/              # Generated files
├── 📁 config/                  # Configuration
│   ├── .env, requirements.txt
│   └── plantuml.jar
├── 📁 scripts/                 # Launch scripts
│   ├── run_streamlit.bat
│   └── run_tests.py
├── 📁 utils/                   # Utility modules
│   └── pdf/                    # **🆕 Smart PDF Analysis**
│       ├── ai_pdf_analyzer.py  # AI analysis engine
│       ├── pdf_processor.py    # Enhanced PDF processor
│       └── streamlit_pdf_integration.py
├── 📁 language/                # Translations
├── 📁 prompts/                 # Prompt templates
├── 📁 docs/                    # Documentation
├── main.py                     # PyQt5 entry point
└── streamlit_app.py            # Streamlit entry point
```

---

## 📈 Version History

### v3.0.0 - Project Reorganization (2025-11-20)
- ✅ **Complete structure reorganization** - professional organization in src/, tests/, tools/, config/
- ✅ **Smart PDF Analysis System** - intelligent model capability detection and automatic method selection
- ✅ **Real-time progress tracking** - user feedback during operations
- ✅ **Hierarchical fallback** - graceful degradation on errors
- ✅ **Enhanced testing** - full test structure (unit/integration/system)
- ✅ **Performance optimization** - 75% vs 0% accuracy analysis (Direct PDF vs Text Extraction)

### v2.x - Legacy Features
- PDF Integration
- PlantUML Code Editing  
- GUI Language Selection
- Enhanced Error Verification

### Planned features (v3.1+):
- Cache system for PDF analysis results
- Batch processing of multiple files
- User interface progress bars in GUI
- Model auto-selection

---

## 🔗 Useful Links

- **📚 Smart PDF System Documentation**: [`docs/SMART_PDF_SYSTEM_README.md`](docs/SMART_PDF_SYSTEM_README.md)
- **📁 Reorganization Documentation**: [`REORGANIZATION_README.md`](REORGANIZATION_README.md)
- **🧪 Test runner**: `python scripts/run_tests.py`
- **🛠️ Development tools**: `tools/` directory

---

## 🤝 Collaboration

Project is open for collaboration! If you have ideas for improvements or found bugs:

1. **Fork repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Run tests** (`python scripts/run_tests.py`)
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to branch** (`git push origin feature/amazing-feature`)
6. **Open Pull Request**

---

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**.

You can view the full license details here:
[https://creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

### What this means:

This license allows others to use, share, and build upon this work, but with the following key restrictions:

* **Attribution (BY)**: You must give appropriate credit to the original author (me) and provide a link to this license.
* **NonCommercial (NC)**: **You may not use this material for commercial purposes.** This is a core condition of the license.
* **ShareAlike (SA)**: If you remix, transform, or build upon this material, you must distribute your contributions under the **same license** (CC BY-NC-SA 4.0) as the original.

---

## 🧪 Testing

### Run all tests:
```bash
python scripts/run_tests.py
```

### Tests by category:
```bash
# Unit tests
python scripts/run_tests.py unit

# Integration tests  
python scripts/run_tests.py integration

# System tests
python scripts/run_tests.py system
```

### Specific test:
```bash
# Test Smart PDF System
python tests/system/test_smart_pdf_system.py

# Test intelligent selection
python tests/system/test_smart_selection.py

# PDF quality analysis
python tools/analyze_pdf_quality.py
```

### 📊 Test Status:
- ✅ **Smart PDF Analysis** - Comprehensive system tests
- ✅ **Model Capability Detection** - Auto PDF support detection
- ✅ **Progress Tracking** - Real-time user feedback
- ✅ **Fallback Mechanisms** - Graceful error handling
- ✅ **Performance Analysis** - Direct PDF vs Text Extraction

---

## TODO (development)

  * Work on prompt templates, especially for process validation (consider step-by-step approach).
  * XMI export for other diagram types will be available in future versions.
  * Develop an agent to assist users in creating comprehensive documentation.
  * Cache system for PDF analysis results
  * Batch processing of multiple files
  * User interface progress bars
  * Model auto-selection based on capabilities

---

## Sample Prompts

See the file `prompts/Prompty_bankowe.txt` for sample process descriptions for various UML/BPMN diagram types.
Check `prompts/Szablony_promptow.txt` for descriptions of dedicated prompt templates for diagram types.

Test file: `tests/fixtures/test_documents/Prompty.txt` - business process example ready for testing.

---

## Screenshots

  * [GD 2025-11-15 Process description validation](https://github.com/user-attachments/assets/5016fd0b-d3fd-48e9-ae34-6285e4ab57bd)
  * [GD 2025-11-15 Class Diagram](https://github.com/user-attachments/assets/87dd2e69-c36e-4e53-8a3f-a5ed2c14e398)
  * [GD 2025-06-14 Component Diagram](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-11-15 C4 Component Diagram](https://github.com/user-attachments/assets/c7ff4a33-aede-45cd-b168-3012db42cf89)

---

**Status**: ✅ **PRODUCTION READY v3.0.0** - Reorganization completed + Smart PDF Analysis System  
**Last Update**: 2025-11-20  
**Next Steps**: GUI progress bars, cache system, batch processing

