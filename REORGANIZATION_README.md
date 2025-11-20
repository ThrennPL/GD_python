# GD_python - Reorganized Project Structure

## 📁 New Project Structure

```
GD_python/
├── 📁 src/                          # Main application code
│   ├── main.py                     # PyQt5 GUI application
│   ├── streamlit_app.py            # Streamlit web application
│   ├── api_thread.py               # API communication
│   └── input_validator.py          # Input validation
│
├── 📁 tests/                       # All test files
│   ├── 📁 unit/                    # Unit tests
│   │   ├── test_functions.py
│   │   ├── test_plantuml_utils.py
│   │   └── test_streamlit.py
│   ├── 📁 integration/             # Integration tests  
│   │   ├── test_pdf_integration.py
│   │   ├── test_ai_pdf_system.py
│   │   └── test_plantuml_to_xmi.py
│   ├── 📁 system/                  # System tests
│   │   ├── test_smart_pdf_system.py
│   │   ├── test_smart_selection.py
│   │   ├── test_pdf_capabilities.py
│   │   └── test_direct_pdf.py
│   └── 📁 fixtures/                # Test data
│       └── test_documents/
│
├── 📁 tools/                       # Development tools
│   ├── analyze_pdf_quality.py
│   ├── debug_ai_calls.py
│   ├── demo_ai_pdf_system.py
│   ├── create_test_pdf.py
│   └── test_real_ai_call.py
│
├── 📁 examples/                    # Example diagrams
│   ├── 📁 activity/               # Activity diagrams
│   ├── 📁 class/                  # Class diagrams  
│   ├── 📁 sequence/               # Sequence diagrams
│   └── 📁 generated/              # Generated output files
│
├── 📁 logs/                       # Log files
├── 📁 cache/                      # Application cache
├── 📁 config/                     # Configuration files
│   ├── .env                       # Environment variables
│   ├── requirements.txt           # Python dependencies
│   └── plantuml.jar               # PlantUML JAR
│
├── 📁 scripts/                    # Utility scripts
│   ├── run_streamlit.bat          # Start Streamlit app
│   └── run_tests.py               # Test runner
│
├── 📁 utils/                      # Utility modules (unchanged)
├── 📁 language/                   # Translations (unchanged)
├── 📁 prompts/                    # AI prompts (unchanged) 
├── 📁 docs/                       # Documentation
│
├── main.py                        # Entry point for PyQt5 app
├── streamlit_app.py               # Entry point for Streamlit
└── .env                          # Environment config (copy)
```

## 🚀 Running the Application

### PyQt5 Desktop Application
```bash
python main.py
```

### Streamlit Web Application  
```bash
# Option 1: Direct
streamlit run src/streamlit_app.py

# Option 2: Using script
scripts/run_streamlit.bat

# Option 3: Via entry point
python streamlit_app.py
```

## 🧪 Running Tests

### All Tests
```bash
python scripts/run_tests.py
```

### Specific Test Category
```bash
# Unit tests
python scripts/run_tests.py unit

# Integration tests  
python scripts/run_tests.py integration

# System tests
python scripts/run_tests.py system
```

### Individual Test
```bash
# Example: Smart PDF system test
python scripts/run_tests.py smart_pdf_system

# Direct execution
python tests/system/test_smart_pdf_system.py
```

## 🛠️ Development Tools

### PDF Analysis Tools
```bash
# Analyze PDF quality comparison
python tools/analyze_pdf_quality.py

# Debug AI calls
python tools/debug_ai_calls.py

# Demo PDF system
python tools/demo_ai_pdf_system.py
```

### Test Tools
```bash
# Create test PDF
python tools/create_test_pdf.py

# Test real AI calls
python tools/test_real_ai_call.py
```

## ⚙️ Configuration

### Environment Variables
The main `.env` file is in the project root, with a copy in `config/` for organization.

Key settings:
```env
# PDF Analysis
PDF_ANALYSIS_MODEL=models/gemini-2.0-flash
PDF_ANALYSIS_MODE=ai
PDF_DIRECT_THRESHOLD_MB=2.0

# PlantUML  
PLANTUML_JAR_PATH=config/plantuml.jar

# API Configuration
API_URL=https://generativelanguage.googleapis.com/v1beta/models
API_DEFAULT_MODEL=models/gemini-2.0-flash
```

### Dependencies
Install from requirements:
```bash
pip install -r config/requirements.txt
```

## 📊 Benefits of Reorganization

### ✅ **Before Issues Fixed:**
- ❌ Tests scattered in root directory
- ❌ Config files mixed with source code  
- ❌ Example files cluttering main directory
- ❌ No clear separation of concerns
- ❌ Development tools mixed with application

### ✅ **After Reorganization:**
- ✅ Clean separation: src/, tests/, tools/, config/
- ✅ Logical grouping: unit/integration/system tests
- ✅ Examples organized by diagram type
- ✅ Clear entry points for different interfaces
- ✅ Professional project structure
- ✅ Easy maintenance and navigation

## 🔄 Migration Notes

### Path Updates
All import paths have been updated to work with the new structure:
- `src/` files use `sys.path.insert(0, parent_dir)` 
- `tests/` use appropriate relative paths
- `tools/` maintain access to utils/

### Backward Compatibility
- Main entry points (`main.py`, `streamlit_app.py`) remain in root
- `.env` copied to root for easy access
- All functionality preserved

### File Movements
| Old Location | New Location | Type |
|--------------|--------------|------|
| `main.py` | `src/main.py` | Source |
| `test_*.py` | `tests/*/test_*.py` | Tests |
| `*.puml` | `examples/*/` | Examples |
| `*.log` | `logs/` | Logs |
| `.env` | `config/.env` | Config |

## 📚 Next Steps

1. **Test the reorganized structure** ✅
2. **Update CI/CD pipelines** (if any)
3. **Update documentation references**  
4. **Consider adding pytest configuration**
5. **Add pre-commit hooks**

---

**Status**: ✅ **REORGANIZATION COMPLETE**  
**Date**: 2025-11-20  
**Version**: 3.0.0 (Reorganized)