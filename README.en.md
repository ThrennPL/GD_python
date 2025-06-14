# UML/BPMN Diagram Generator and Validator with AI

Desktop application (PyQt5) for generating, visualizing, and verifying UML (PlantUML) and BPMN (XML) diagrams based on process descriptions, using AI models (e.g., LLM). Allows selection of prompt templates, diagram types, process description validation, and automatic PlantUML code verification.

## Features

- Process Description Validation:
Users can validate their process descriptions before generating diagrams, ensuring input quality.

- Diagram Generation:
The application generates PlantUML code for various UML diagram types based on user input and selected prompt templates.

- Multiple Tabs:
Users can work with multiple diagrams simultaneously, each in its own tab.

- Automatic Diagram Type Recognition:
The system recognizes the type of diagram (e.g., class, sequence) and enables relevant export options.

- Export Options:
PlantUML: Save the generated PlantUML code.
SVG: Generate and save SVG images locally using plantuml.jar and Java.
XMI: Export class diagrams to XMI format for use in Enterprise Architect.

- Prompt Templates:
Easily extendable prompt templates for different diagram types.

- File Naming with Timestamp:
Exported files include the current date and time in their names for easy versioning.

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
- Java (for local PlantUML rendering)
- plantuml.jar (download from https://plantuml.com/download)

Install dependencies:
pip install -r requirements.txt

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

1. Enter a process description.
2. Select a diagram type and prompt template.
3. Click "Validate" to check the description.
4. Click "Generate Diagram" to create and display the diagram.
5. Use the export buttons to save the diagram in the desired format.


## Notes
- SVG Generation:
The application does not use plantuml.com for SVG rendering. Instead, it uses a local plantuml.jar and Java, ensuring privacy and offline capability.

- Error Handling:
The application provides clear error messages for missing dependencies, invalid input, or export issues.

- Extensibility:
You can add new prompt templates by placing files in the prompt_templates/ directory and registering them in the code.

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
