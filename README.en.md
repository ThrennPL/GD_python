# UML/BPMN Diagram Generator and Validator with AI

Desktop application (PyQt5) for generating, visualizing, and verifying UML (PlantUML) and BPMN (XML) diagrams based on process descriptions, using AI models (e.g., LLM). Allows selection of prompt templates, diagram types, process description validation, and automatic PlantUML code verification.

## Features

- Generate PlantUML code or BPMN XML based on process descriptions
- Choose prompt templates and diagram types (sequence, activity, class, component, state, use case, etc.)
- Visualize PlantUML diagrams (SVG) in tabs
- Automatic PlantUML code verification in case of SVG generation errors
- AI-powered process description validation
- Conversation history with the model
- Support for multiple AI models (e.g., local or OpenAI API)
- Sample test prompts for the banking industry
- XMI export for PlantUML

## XMI Export

- XMI export is currently available **only for Class Diagrams**.
- The "Save XMI" button is active only when the active tab contains a class diagram.
- For other diagram types (e.g., sequence, activity), XMI export is not yet supported.

## Tab Management

- The application allows working with multiple diagrams in tabs.
- After switching tabs, the application automatically checks the diagram type and activates/deactivates the XMI export button.

## TODO

- Work on prompt templates, particularly for process correctness validation - considering step-by-step approach in this area.
- XMI export works only partially - after loading into Enterprise Architect there is no diagram but other elements remain.
- XMI export for other diagram types will be available in future versions.

## Requirements

- Python 3.8+
- PyQt5
- requests

## Installation

```bash
git clone https://github.com/ThrennPL/GD_python
cd your-project
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Project Structure

- `main.py` – main application file (GUI, logic)
- `prompt_templates.py` – AI prompt templates
- `plantuml_utils.py` – PlantUML utility functions (encoding, SVG retrieval, diagram type recognition)
- `input_validator.py` – function for AI-powered process description validation
- `plantuml_convert_to_xmi.py` – functions for converting PlantUML format to XMI for EA
- `Prompty_bankowe.txt` – sample process descriptions for testing

## Example Usage

1. Enter process description in the text field.
2. Select template type (PlantUML/XML) and prompt template.
3. Choose diagram type.
4. Click "Send" – AI model will generate diagram code.
5. Diagram will be displayed as SVG (or XML).
6. In case of errors, PlantUML code will be automatically verified by AI.
7. You can also check process description correctness through AI.

Use Case Diagram:
![Use Case Diagram](https://github.com/user-attachments/assets/bcac902f-0fe5-48b9-8088-968c597ffb62)

## Sample Prompts

See the [`Prompty_bankowe.txt`](Prompty_bankowe.txt) file – you'll find examples of process descriptions for various UML/BPMN diagram types.

## Screenshots

![GD 2025-06-11 Process Description Validation](https://github.com/user-attachments/assets/f2ea75e1-32a6-44b6-936e-8d4298231215)
![GD 2025-06-11 Component Diagram](https://github.com/user-attachments/assets/4f11ba4c-cf2e-42fc-9f5e-2af3ef2b0d99)

## Author

Grzegorz Majewski / ThrennPL
[https://www.linkedin.com/in/grzegorz-majewski-421306151/]

## License

MIT