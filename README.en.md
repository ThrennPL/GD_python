# UML/BPMN Diagram Generator & Validator with AI

An application for generating, visualizing, and validating UML (PlantUML) and BPMN (XML) diagrams based on process descriptions, using AI models (e.g., LLM). The project offers both a desktop version (PyQt5) and a web version (Streamlit), allowing you to select prompt templates, diagram types, validate process descriptions, and automatically verify PlantUML code. The app supports **two languages (English and Polish)**, with dedicated prompt templates for each, ensuring better generation results in the chosen language.

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
     streamlit run streamlit_app.py
     ```
   - **PyQt5:**  
     ```bash
     python main.py
     ```

---

## Features

  * Generate PlantUML or BPMN XML code from process descriptions
  * Select prompt template and diagram type (sequence, activity, class, component, state, use case, etc.)
  * Visualize PlantUML diagrams (SVG)
  * Automatic PlantUML code verification if SVG generation fails
  * AI-based process description validation
  * Conversation history with the AI model
  * Support for multiple AI models (local or via API, e.g., OpenAI, Gemini)
  * Download generated diagrams in PlantUML, SVG, XMI formats
  * Special options for BPMN diagrams (complexity level, validation rule, output format, domain)
  * Save queries and model responses to a database (mySQL, PostgreSQL)
  * **Two interface and prompt languages (English and Polish)**
  * Sample test prompts for the banking industry

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
  * Dependencies from `requirements.txt`
  * Java (for local PlantUML rendering)
  * `plantuml.jar` (download from PlantUML website)
  * PyQt5 (desktop version only)
  * `.env` configuration file (see above)

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
2.  **Configure template**: Choose the template type (PlantUML/XML) and a specific template.
3.  **Select diagram type**: Sequence, activity, class, etc.
4.  **Enter process description**: In the text field, enter a detailed description of the process you want to visualize.
5.  **Generate/Validate**: Click "Send query" or "Validate description".
6.  **Display Diagram**: The generated PlantUML diagram (SVG) or BPMN XML code will appear in the appropriate tabs.

---

## File Structure

  * `streamlit_app.py` - main Streamlit application
  * `main.py` - original PyQt5 application
  * `run_streamlit.bat` - Windows launch script for Streamlit version
  * Other Python files - helper modules
      * `translations_pl.py`, `translations_en.py` - interface translation files
      * `prompt_templates_pl.py`, `prompt_templates_en.py` - prompt template files for Polish and English

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

## TODO (development)

  * Work on prompt templates, especially for process validation (consider step-by-step).
  * XMI export for other diagram types will be available in future versions.
  * Develop an agent to assist users in creating comprehensive documentation.

---

## Sample Prompts

See the file `Prompty_bankowe.txt` for sample process descriptions for various UML/BPMN diagram types.
Check `Szablony_promptow.txt` for descriptions of dedicated prompt templates for diagram types.

---

## Screenshots

  * [GD 2025-06-14 Process description validation](https://github.com/user-attachments/assets/6bafbbb4-c6e7-4f62-b145-51623c20026e)
  * [GD 2025-06-14 Class Diagram](https://github.com/user-attachments/assets/a3082146-64d2-466b-b1d7-de33567c51eb)
  * [GD 2025-06-14 Component Diagram](https://github.com/user-attachments/assets/eb99c9a0-834b-4a84-9037-c2a32af755da)
  * [GD 2025-06-14 C4 Component Diagram](https://github.com/user-attachments/assets/168735ab-e2d8-4fcb-97d83f2a5b6c)
