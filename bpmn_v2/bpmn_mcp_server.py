"""
Model Context Protocol Server dla BPMN Process Generation & Validation
Implementuje MCP server z automatyczną weryfikacją, iteracyjną poprawą i walidacją BPMN.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib
import tempfile
import copy

# MCP imports
try:
    from mcp import Server
    from mcp.server import NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest, 
        ListToolsResult,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Fallback for development
    class Server:
        def __init__(self, name: str, version: str): pass
        def list_tools(self): return lambda: None
        def call_tool(self): return lambda: None
    
    class CallToolResult:
        def __init__(self, content, isError=False):
            self.content = content
            self.isError = isError
    
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class ListToolsResult:
        def __init__(self, tools):
            self.tools = tools

# BPMN v2 imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'bpmn_v2'))

from structure_definition import BPMNDiagram, Process, ElementType, TaskType
from polish_dictionary import PolishToBPMNDictionary, ProcessAnalyzer, ContextType
from json_prompt_template import BPMNJSONSchema, PromptGenerator, ResponseValidator, AIPromptTemplate
from json_to_bpmn_generator import BPMNJSONConverter
from bpmn_v2.ai_integration import AIClientFactory, ResponseParser, AIResponse, AIProvider
from ai_config import get_default_config, AIConfig


class BPMNValidationIssue:
    """Reprezentuje problem z walidacją BPMN"""
    def __init__(self, severity: str, category: str, message: str, element_id: Optional[str] = None):
        self.severity = severity  # error, warning, suggestion
        self.category = category  # schema, logic, completeness, naming
        self.message = message
        self.element_id = element_id
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'severity': self.severity,
            'category': self.category,
            'message': self.message,
            'element_id': self.element_id,
            'timestamp': self.timestamp.isoformat()
        }


class BPMNIterativeValidator:
    """Zaawansowany walidator BPMN z sugestiami poprawek"""
    
    def __init__(self):
        self.response_validator = ResponseValidator()
        self.schema = BPMNJSONSchema.get_schema()
        
    def validate_comprehensive(self, bpmn_json: Dict) -> Tuple[bool, List[BPMNValidationIssue]]:
        """
        Przeprowadza kompleksową walidację BPMN
        
        Returns:
            Tuple (is_valid, list of issues)
        """
        issues = []
        
        # 1. Schema validation
        schema_issues = self._validate_schema(bpmn_json)
        issues.extend(schema_issues)
        
        # 2. Process logic validation
        logic_issues = self._validate_process_logic(bpmn_json)
        issues.extend(logic_issues)
        
        # 3. Completeness validation
        completeness_issues = self._validate_completeness(bpmn_json)
        issues.extend(completeness_issues)
        
        # 4. Naming and clarity validation
        clarity_issues = self._validate_naming_clarity(bpmn_json)
        issues.extend(clarity_issues)
        
        # 5. Best practices validation
        best_practice_issues = self._validate_best_practices(bpmn_json)
        issues.extend(best_practice_issues)
        
        # Check if there are blocking errors
        has_errors = any(issue.severity == 'error' for issue in issues)
        
        return not has_errors, issues
    
    def _validate_schema(self, bpmn_json: Dict) -> List[BPMNValidationIssue]:
        """Walidacja względem JSON Schema"""
        issues = []
        
        try:
            import jsonschema
            jsonschema.validate(bpmn_json, self.schema)
        except jsonschema.ValidationError as e:
            issues.append(BPMNValidationIssue(
                severity='error',
                category='schema',
                message=f"Schema validation error: {e.message}"
            ))
        except Exception as e:
            issues.append(BPMNValidationIssue(
                severity='error',
                category='schema', 
                message=f"Schema validation failed: {str(e)}"
            ))
        
        return issues
    
    def _validate_process_logic(self, bpmn_json: Dict) -> List[BPMNValidationIssue]:
        """Walidacja logiki procesu"""
        issues = []
        elements = bpmn_json.get('elements', [])
        flows = bpmn_json.get('flows', [])
        
        # Check start/end events
        start_events = [e for e in elements if e.get('type') == 'startEvent']
        end_events = [e for e in elements if e.get('type') == 'endEvent']
        
        if len(start_events) == 0:
            issues.append(BPMNValidationIssue(
                severity='error',
                category='logic',
                message="Process must have at least one start event"
            ))
        elif len(start_events) > 1:
            issues.append(BPMNValidationIssue(
                severity='warning',
                category='logic',
                message="Process has multiple start events - consider if this is intentional"
            ))
        
        if len(end_events) == 0:
            issues.append(BPMNValidationIssue(
                severity='error',
                category='logic',
                message="Process must have at least one end event"
            ))
        
        # Check flow connectivity
        element_ids = {e['id'] for e in elements}
        
        for flow in flows:
            source_id = flow.get('source')
            target_id = flow.get('target')
            
            if source_id not in element_ids:
                issues.append(BPMNValidationIssue(
                    severity='error',
                    category='logic',
                    message=f"Flow references unknown source element: {source_id}",
                    element_id=source_id
                ))
            
            if target_id not in element_ids:
                issues.append(BPMNValidationIssue(
                    severity='error',
                    category='logic',
                    message=f"Flow references unknown target element: {target_id}",
                    element_id=target_id
                ))
        
        # Check for orphaned elements (not connected to any flow)
        connected_elements = set()
        for flow in flows:
            connected_elements.add(flow.get('source'))
            connected_elements.add(flow.get('target'))
        
        for element in elements:
            if element['id'] not in connected_elements:
                # Start events don't need incoming flows, end events don't need outgoing flows
                if element.get('type') not in ['startEvent', 'endEvent']:
                    issues.append(BPMNValidationIssue(
                        severity='warning',
                        category='logic',
                        message=f"Element '{element['name']}' is not connected to any flow",
                        element_id=element['id']
                    ))
        
        return issues
    
    def _validate_completeness(self, bpmn_json: Dict) -> List[BPMNValidationIssue]:
        """Walidacja kompletności procesu"""
        issues = []
        
        # Check required fields
        if not bpmn_json.get('process_name'):
            issues.append(BPMNValidationIssue(
                severity='warning',
                category='completeness',
                message="Process should have a meaningful name"
            ))
        
        if not bpmn_json.get('description'):
            issues.append(BPMNValidationIssue(
                severity='suggestion',
                category='completeness',
                message="Consider adding process description for better documentation"
            ))
        
        # Check participants assignment
        elements = bpmn_json.get('elements', [])
        participants = bpmn_json.get('participants', [])
        participant_ids = {p['id'] for p in participants}
        
        for element in elements:
            participant = element.get('participant')
            if participant and participant not in participant_ids:
                issues.append(BPMNValidationIssue(
                    severity='error',
                    category='completeness',
                    message=f"Element '{element['name']}' references unknown participant: {participant}",
                    element_id=element['id']
                ))
        
        # Check if process has enough activities
        activities = [e for e in elements if e.get('type') in ['userTask', 'serviceTask', 'task']]
        if len(activities) < 1:
            issues.append(BPMNValidationIssue(
                severity='warning',
                category='completeness',
                message="Process should have at least one activity/task"
            ))
        
        return issues
    
    def _validate_naming_clarity(self, bpmn_json: Dict) -> List[BPMNValidationIssue]:
        """Walidacja jasności nazewnictwa"""
        issues = []
        
        elements = bpmn_json.get('elements', [])
        
        for element in elements:
            name = element.get('name', '')
            
            # Check for empty or generic names
            if not name or name.strip() == '':
                issues.append(BPMNValidationIssue(
                    severity='warning',
                    category='naming',
                    message=f"Element {element['id']} has empty name",
                    element_id=element['id']
                ))
            elif name.lower() in ['task', 'activity', 'process', 'step']:
                issues.append(BPMNValidationIssue(
                    severity='suggestion',
                    category='naming',
                    message=f"Element '{name}' has generic name - consider more descriptive name",
                    element_id=element['id']
                ))
            
            # Check name length
            if len(name) > 50:
                issues.append(BPMNValidationIssue(
                    severity='suggestion',
                    category='naming',
                    message=f"Element '{name}' has very long name - consider shortening",
                    element_id=element['id']
                ))
        
        return issues
    
    def _validate_best_practices(self, bpmn_json: Dict) -> List[BPMNValidationIssue]:
        """Walidacja zgodności z best practices"""
        issues = []
        
        elements = bpmn_json.get('elements', [])
        
        # Check for proper task types
        for element in elements:
            element_type = element.get('type')
            name = element.get('name', '')
            
            # Suggest specific task types based on name
            if element_type == 'task':  # generic task
                name_lower = name.lower()
                if any(word in name_lower for word in ['wprowadź', 'wybierz', 'potwierdź', 'autoryzuj']):
                    issues.append(BPMNValidationIssue(
                        severity='suggestion',
                        category='best_practices',
                        message=f"Task '{name}' sounds like user interaction - consider userTask type",
                        element_id=element['id']
                    ))
                elif any(word in name_lower for word in ['sprawdź', 'oblicz', 'wyślij', 'zapisz']):
                    issues.append(BPMNValidationIssue(
                        severity='suggestion',
                        category='best_practices',
                        message=f"Task '{name}' sounds like system action - consider serviceTask type",
                        element_id=element['id']
                    ))
        
        # Check process complexity
        if len(elements) > 15:
            issues.append(BPMNValidationIssue(
                severity='suggestion',
                category='best_practices',
                message="Process has many elements - consider breaking into sub-processes"
            ))
        
        return issues


class BPMNImprovementSuggester:
    """Generator sugestii poprawek BPMN"""
    
    def generate_improvement_prompt(self, original_text: str, bpmn_json: Dict, 
                                  issues: List[BPMNValidationIssue]) -> str:
        """
        Generuje prompt dla AI z prośbą o poprawki
        """
        
        # Group issues by category
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning'] 
        suggestions = [i for i in issues if i.severity == 'suggestion']
        
        prompt = f"""
ITERACYJNA POPRAWA PROCESU BPMN

Oryginalny opis procesu:
{original_text}

Aktualny proces BPMN (JSON):
{json.dumps(bpmn_json, indent=2, ensure_ascii=False)}

ZIDENTYFIKOWANE PROBLEMY:

"""
        
        if errors:
            prompt += "🚨 BŁĘDY (wymagają poprawy):\n"
            for i, error in enumerate(errors, 1):
                prompt += f"{i}. {error.message}\n"
            prompt += "\n"
        
        if warnings:
            prompt += "⚠️ OSTRZEŻENIA (zaleca się poprawę):\n"
            for i, warning in enumerate(warnings, 1):
                prompt += f"{i}. {warning.message}\n"
            prompt += "\n"
        
        if suggestions:
            prompt += "💡 SUGESTIE (opcjonalne ulepszenia):\n"
            for i, suggestion in enumerate(suggestions, 1):
                prompt += f"{i}. {suggestion.message}\n"
            prompt += "\n"
        
        prompt += """
ZADANIE:
Popraw powyższy proces BPMN, uwzględniając zidentyfikowane problemy. 

WYMAGANIA:
1. Zachowaj główną logikę procesu z oryginalnego opisu
2. Napraw wszystkie BŁĘDY
3. Uwzględnij OSTRZEŻENIA gdzie to możliwe  
4. Rozważ SUGESTIE jeśli poprawią klarowność procesu

Zwróć poprawiony proces w identycznym formacie JSON.
"""
        
        return prompt


class BPMNProcessMCP:
    """
    MCP Server dla zaawansowanego przetwarzania procesów BPMN
    z automatyczną walidacją i iteracyjną poprawą
    """
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        self.name = "bpmn-process-mcp"
        self.version = "2.0.0"
        self.server = Server(self.name, self.version) if MCP_AVAILABLE else None
        
        # BPMN v2 components
        self.polish_dict = PolishToBPMNDictionary()
        self.process_analyzer = ProcessAnalyzer()
        self.prompt_generator = PromptGenerator(AIPromptTemplate(
            context_type=ContextType.BANKING, 
            include_banking_context=True
        ))
        self.bpmn_converter = BPMNJSONConverter()
        
        # AI integration
        self.ai_config = ai_config or get_default_config()
        self.ai_client = AIClientFactory.create_client(self.ai_config)
        self.response_parser = ResponseParser()
        
        # Validation and improvement
        self.validator = BPMNIterativeValidator()
        self.improver = BPMNImprovementSuggester()
        
        # Process cache
        self.process_cache = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        if MCP_AVAILABLE and self.server:
            self._register_tools()
    
    def _register_tools(self):
        """Rejestruje narzędzia MCP"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(tools=[
                Tool(
                    name="generate_bpmn_process",
                    description="Generuje proces BPMN z polskiego opisu tekstowego",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "process_description": {
                                "type": "string",
                                "description": "Polski opis procesu biznesowego"
                            },
                            "process_name": {
                                "type": "string", 
                                "description": "Nazwa procesu",
                                "default": "Generated Process"
                            },
                            "context": {
                                "type": "string",
                                "description": "Kontekst biznesowy (banking, insurance, etc.)",
                                "default": "generic"
                            },
                            "validate_and_improve": {
                                "type": "boolean",
                                "description": "Czy automatycznie walidować i poprawiać proces",
                                "default": True
                            }
                        },
                        "required": ["process_description"]
                    }
                ),
                
                Tool(
                    name="validate_bpmn_process", 
                    description="Waliduje proces BPMN i zwraca sugestie poprawek",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bpmn_json": {
                                "type": "object",
                                "description": "Proces BPMN w formacie JSON"
                            },
                            "original_description": {
                                "type": "string",
                                "description": "Oryginalny opis procesu (opcjonalny)"
                            }
                        },
                        "required": ["bpmn_json"]
                    }
                ),
                
                Tool(
                    name="improve_bpmn_process",
                    description="Iteracyjnie poprawia proces BPMN na podstawie walidacji",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "bpmn_json": {
                                "type": "object",
                                "description": "Proces BPMN do poprawy"
                            },
                            "original_description": {
                                "type": "string",
                                "description": "Oryginalny opis procesu"
                            },
                            "max_iterations": {
                                "type": "integer",
                                "description": "Maksymalna liczba iteracji poprawek",
                                "default": 3
                            }
                        },
                        "required": ["bpmn_json", "original_description"]
                    }
                ),
                
                Tool(
                    name="generate_bpmn_xml",
                    description="Konwertuje proces BPMN JSON na XML",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bpmn_json": {
                                "type": "object", 
                                "description": "Proces BPMN w formacie JSON"
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Ścieżka pliku wyjściowego (opcjonalne)"
                            }
                        },
                        "required": ["bpmn_json"]
                    }
                ),
                
                Tool(
                    name="analyze_process_text",
                    description="Analizuje polski tekst i zwraca mapowane elementy BPMN",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "process_text": {
                                "type": "string",
                                "description": "Polski tekst do analizy"
                            },
                            "context": {
                                "type": "string", 
                                "description": "Kontekst biznesowy",
                                "default": "generic"
                            }
                        },
                        "required": ["process_text"]
                    }
                )
            ])
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            try:
                if request.params.name == "generate_bpmn_process":
                    return await self._handle_generate_process(request.params.arguments)
                elif request.params.name == "validate_bpmn_process":
                    return await self._handle_validate_process(request.params.arguments)
                elif request.params.name == "improve_bpmn_process":
                    return await self._handle_improve_process(request.params.arguments)
                elif request.params.name == "generate_bpmn_xml":
                    return await self._handle_generate_xml(request.params.arguments)
                elif request.params.name == "analyze_process_text":
                    return await self._handle_analyze_text(request.params.arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Unknown tool: {request.params.name}"
                        )],
                        isError=True
                    )
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Error: {str(e)}"
                    )],
                    isError=True
                )
    
    async def _handle_generate_process(self, args: Dict) -> CallToolResult:
        """Obsługuje generowanie procesu BPMN"""
        
        description = args.get("process_description")
        process_name = args.get("process_name", "Generated Process") 
        context = args.get("context", "generic")
        validate_and_improve = args.get("validate_and_improve", True)
        
        try:
            # Step 1: Analyze text
            analysis = self.process_analyzer.analyze_process_description(description)
            
            # Step 2: Generate AI prompt
            prompt = self.prompt_generator.generate_prompt(description)
            
            # Step 3: Get AI response
            ai_response = self.ai_client.generate_response(prompt)
            if not ai_response.success:
                raise Exception(f"AI error: {ai_response.error}")
            
            # Step 4: Parse JSON
            json_success, bpmn_json, parse_errors = self.response_parser.extract_json(ai_response)
            if not json_success:
                raise Exception(f"JSON parsing failed: {parse_errors}")
            
            # Step 5: Validate and improve if requested
            if validate_and_improve:
                bpmn_json = await self._iterative_improvement(description, bpmn_json)
            
            result = {
                "success": True,
                "process_name": process_name,
                "bpmn_json": bpmn_json,
                "analysis": analysis,
                "ai_usage": ai_response.usage,
                "timestamp": datetime.now().isoformat()
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }, indent=2, ensure_ascii=False)
                )],
                isError=True
            )
    
    async def _handle_validate_process(self, args: Dict) -> CallToolResult:
        """Obsługuje walidację procesu BPMN"""
        
        bpmn_json = args.get("bpmn_json")
        original_description = args.get("original_description", "")
        
        try:
            is_valid, issues = self.validator.validate_comprehensive(bpmn_json)
            
            result = {
                "is_valid": is_valid,
                "issues_count": len(issues),
                "errors": [i.to_dict() for i in issues if i.severity == 'error'],
                "warnings": [i.to_dict() for i in issues if i.severity == 'warning'],
                "suggestions": [i.to_dict() for i in issues if i.severity == 'suggestion'],
                "timestamp": datetime.now().isoformat()
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2, ensure_ascii=False)
                )],
                isError=True
            )
    
    async def _handle_improve_process(self, args: Dict) -> CallToolResult:
        """Obsługuje iteracyjną poprawę procesu"""
        
        bpmn_json = args.get("bpmn_json")
        original_description = args.get("original_description")
        max_iterations = args.get("max_iterations", 10)
        
        try:
            improved_json = await self._iterative_improvement(
                original_description, bpmn_json, max_iterations
            )
            
            result = {
                "success": True,
                "improved_process": improved_json,
                "timestamp": datetime.now().isoformat()
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2, ensure_ascii=False)
                )],
                isError=True
            )
    
    async def _handle_generate_xml(self, args: Dict) -> CallToolResult:
        """Obsługuje konwersję JSON → BPMN XML"""
        
        bpmn_json = args.get("bpmn_json")
        output_file = args.get("output_file")
        
        try:
            bpmn_xml = self.bpmn_converter.convert_json_to_bpmn(bpmn_json)
            
            result = {
                "success": True,
                "bpmn_xml": bpmn_xml,
                "xml_length": len(bpmn_xml),
                "timestamp": datetime.now().isoformat()
            }
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(bpmn_xml)
                result["output_file"] = output_file
            
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2, ensure_ascii=False)
                )],
                isError=True
            )
    
    async def _handle_analyze_text(self, args: Dict) -> CallToolResult:
        """Obsługuje analizę tekstu polskiego"""
        
        process_text = args.get("process_text")
        context = args.get("context", "generic")
        
        try:
            analysis = self.process_analyzer.analyze_process_description(process_text)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2, ensure_ascii=False)
                )],
                isError=True
            )
    
    async def _iterative_improvement(self, original_text: str, bpmn_json: Dict, 
                                   max_iterations: int = 10) -> Dict:
        """
        Iteracyjnie poprawia proces BPMN
        """
        current_json = copy.deepcopy(bpmn_json)
        iteration = 0
        
        while iteration < max_iterations:
            # Validate current version
            is_valid, issues = self.validator.validate_comprehensive(current_json)
            
            # If valid with only suggestions, we're done
            serious_issues = [i for i in issues if i.severity in ['error', 'warning']]
            if not serious_issues:
                self.logger.info(f"Process improved in {iteration} iterations")
                break
            
            # Generate improvement prompt
            improvement_prompt = self.improver.generate_improvement_prompt(
                original_text, current_json, issues
            )
            
            # Get improved version from AI
            ai_response = self.ai_client.generate_response(improvement_prompt)
            
            if not ai_response.success:
                self.logger.warning(f"AI improvement failed at iteration {iteration}: {ai_response.error}")
                break
            
            # Parse improved JSON
            json_success, improved_json, parse_errors = self.response_parser.extract_json(ai_response)
            
            if not json_success:
                self.logger.warning(f"JSON parsing failed at iteration {iteration}: {parse_errors}")
                break
            
            current_json = improved_json
            iteration += 1
            
            self.logger.info(f"Completed improvement iteration {iteration}")
        
        return current_json


async def main():
    """Główna funkcja uruchamiająca serwer MCP"""
    
    if not MCP_AVAILABLE:
        print("❌ MCP libraries not available. Install with: pip install mcp")
        return
    
    # Initialize server
    print("🚀 Starting BPMN Process MCP Server v2.0.0")
    
    try:
        server = BPMNProcessMCP()
        print(f"✅ Server initialized with AI: {server.ai_config.provider.value}")
        
        # Test AI connection
        if server.ai_client.test_connection():
            print("✅ AI connection test passed")
        else:
            print("⚠️ AI connection test failed")
        
        print("📋 Available tools:")
        print("  - generate_bpmn_process")
        print("  - validate_bpmn_process") 
        print("  - improve_bpmn_process")
        print("  - generate_bpmn_xml")
        print("  - analyze_process_text")
        
        print("\n🎯 Server ready for connections...")
        
        # Keep server running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())