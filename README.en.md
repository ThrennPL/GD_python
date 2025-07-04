# UML/BPMN Diagram Generator and Verifier with AI

This application generates, visualizes, and verifies UML (PlantUML) and BPMN (XML) diagrams based on process descriptions, utilizing AI models (e.g., LLMs). The project offers both a desktop version (PyQt5) and a web version (Streamlit), allowing users to select prompt templates, diagram types, validate process descriptions, and automatically verify PlantUML code. The application supports **two language versions (English and Polish)**, with dedicated prompt templates for each, ensuring better generation results in the chosen language.

## Features

  * Generates PlantUML code or BPMN XML based on process description.
  * Selectable prompt templates and diagram types (sequence, activity, class, component, state, use case, etc.).
  * Visualization of PlantUML diagrams (SVG).
  * Automatic PlantUML code verification in case of SVG generation errors.
  * AI-powered validation of process descriptions.
  * AI model conversation history.
  * Support for multiple AI models (local or via API, e.g., OpenAI, Gemini).
  * Download generated diagrams in PlantUML, SVG, and XMI formats.
  * Special options for BPMN diagrams (complexity level, validation rule, output format, domain).
  * **Two language versions for the interface and prompts (English and Polish).**
  * Example test prompts for the banking industry.

## XMI Export

XMI export is currently available **only for Class Diagrams**. The "Save XMI" button is active only when the active tab contains a Class Diagram. XMI export is not yet supported for other diagram types (e.g., sequence, activity). Please note that only elements, not the diagram itself, may appear when loaded into Enterprise Architect.

## Tab Support (for Desktop Version)

The desktop application allows working with multiple diagrams in separate tabs. When switching tabs, the application automatically checks the diagram type and activates/deactivates the XMI export button accordingly.

## SVG Diagram Generation

SVG diagrams can be generated in two ways, depending on the `plantuml_generator_type` setting:

  * **`plantuml_generator_type = local`**: SVG diagrams are generated locally using `plantuml.jar` and Java. Ensure both are available on your system.
  * **`plantuml_generator_type = www`**: SVG diagrams are generated using the [www.plantuml.com](https://plantuml.com/) website.

## Requirements

  * Python 3.7+ (for Streamlit) or Python 3.8+ (for PyQt5)
  * Local AI server (e.g., LM Studio) running on port `http://localhost:1234`
  * Dependencies from `requirements.txt`
  * Java (for local PlantUML rendering)
  * `plantuml.jar` (downloadable from the PlantUML website)
  * PyQt5 (for desktop version only)
  * `requests`

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/ThrennPL/GD_python
    cd your-project
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ensure your local AI server is running on `http://localhost:1234`.

## Configuration (`.env`)

Example configuration in the `.env` file:

```
PLANTUML_JAR_PATH=plantuml.jar
PLANTUML_GENERATOR_TYPE=local
API_URL=http://localhost:1234/v1/models
CHAT_URL=http://localhost:1234/v1/chat/completions
API_KEY=
API_DEFAULT_MODEL=models/gemini-2.0-flash
MODEL_PROVIDER=gemini  # or "local", "openai"
```

## Running the Application

### Streamlit Version

  * **Method 1: Directly**
    ```bash
    streamlit run streamlit_app.py
    ```
  * **Method 2: Batch script (Windows)**
    ```bash
    run_streamlit.bat
    ```

### PyQt5 Version

```bash
python main.py
```

## Usage

1.  **Select AI Model**: Choose from the list of available models on your server.
2.  **Configure Template**: Select the template type (PlantUML/XML) and a specific template.
3.  **Choose Diagram Type**: Sequence, activity, class, etc.
4.  **Enter Process Description**: In the text field, provide a detailed description of the process you want to visualize.
5.  **Generate/Validate**: Click the "Send Query" or "Validate Description" button.
6.  **Display Diagram**: The generated PlantUML diagram (SVG) or BPMN XML code will appear in the respective tabs.

## File Structure

  * `streamlit_app.py` - Main Streamlit application
  * `main.py` - Original PyQt5 application
  * `run_streamlit.bat` - Launch script (Windows) for the Streamlit version
  * Other Python files - Auxiliary modules (unchanged)
      * `translations_pl.py`, `translations_en.py` - Files with interface translations
      * `prompt_templates_pl.py`, `prompt_templates_en.py` - Files with prompt templates for Polish and English languages

## TODO (Development)

  * Work on prompt templates, especially regarding process correctness checks (consider step-by-step validation).
  * XMI export for other diagram types will be available in future versions.

## Example Prompts

See the `Prompty_bankowe.txt` file – you'll find examples of process descriptions for various UML/BPMN diagram types.
Refer to the `Szablony_promptow.txt` file – it contains descriptions of how individual prompt templates dedicated to diagram types work.

## Screenshots

  * [GD 2025-06-14 Process Description Validation](https://github.com/user-attachments/assets/6bafbbb4-c6e7-4f62-b145-51623c20026e)
  * [GD 2025-06-14 Class Diagram](https://github.com/user-attachments/assets/a3082146-64d2-466b-b1d7-de33567c51eb)
  * [GD 2025-06-14 Component Diagram](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-06-14 C4 Component Diagram](https://github.com/user-attachments/assets/168735ab-e2d8-4fcb-97d83f2a5b6c)
