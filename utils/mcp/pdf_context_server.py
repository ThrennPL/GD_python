"""
Model Context Protocol Server dla zaawansowanego przetwarzania dokumentów PDF.
Implementuje pełny MCP server z obsługą semantic search i analizą kontekstu.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib
import tempfile

# MCP imports (zakładając użycie standardowej biblioteki MCP)
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
        ImageContent
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Fallback classes for development
    class Server:
        def __init__(self, name: str, version: str): pass
        def list_tools(self): return lambda: None
        def call_tool(self): return lambda: None

# PDF processing imports
from utils.pdf.pdf_processor import PDFProcessor, PDFDocument, ProcessContext

class AdvancedPDFContextServer:
    """
    Zaawansowany MCP server do przetwarzania kontekstu z dokumentów PDF.
    Oferuje inteligentną analizę dokumentów dla generowania diagramów.
    """
    
    def __init__(self):
        self.name = "pdf-context-mcp"
        self.version = "1.0.0"
        self.server = Server(self.name, self.version)
        self.pdf_processor = PDFProcessor()
        
        # Cache dla przetworzonych dokumentów
        self.document_cache = {}
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Rejestracja narzędzi
        self._register_tools()
    
    def _register_tools(self):
        """Rejestruje dostępne narzędzia MCP."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Zwraca listę dostępnych narzędzi."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="process_pdf",
                        description="Przetwarza plik PDF i ekstraktuje kontekst biznesowy",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Ścieżka do pliku PDF"
                                },
                                "use_cache": {
                                    "type": "boolean",
                                    "description": "Czy używać cache dla już przetworzonych plików",
                                    "default": True
                                }
                            },
                            "required": ["file_path"]
                        }
                    ),
                    Tool(
                        name="extract_context_for_diagram",
                        description="Ekstraktuje kontekst z PDF dostosowany do typu diagramu",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Ścieżka do pliku PDF"
                                },
                                "diagram_type": {
                                    "type": "string",
                                    "description": "Typ diagramu (sequence, activity, class, component)",
                                    "enum": ["sequence", "activity", "class", "component", "usecase", "bpmn"]
                                },
                                "focus_areas": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Obszary na których ma się skupić ekstrakcja (actors, processes, systems, decisions)"
                                }
                            },
                            "required": ["file_path", "diagram_type"]
                        }
                    ),
                    Tool(
                        name="search_pdf_content",
                        description="Wyszukuje semantyczne w treści dokumentu PDF",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Ścieżka do pliku PDF"
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Zapytanie semantyczne"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maksymalna liczba wyników",
                                    "default": 5
                                }
                            },
                            "required": ["file_path", "query"]
                        }
                    ),
                    Tool(
                        name="analyze_process_flow",
                        description="Analizuje przepływ procesu z dokumentu PDF",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Ścieżka do pliku PDF"
                                },
                                "process_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Słowa kluczowe procesu do znalezienia"
                                }
                            },
                            "required": ["file_path"]
                        }
                    ),
                    Tool(
                        name="enhance_prompt_with_context",
                        description="Wzbogaca prompt o kontekst z dokumentów PDF",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "original_prompt": {
                                    "type": "string",
                                    "description": "Oryginalny prompt do wzbogacenia"
                                },
                                "pdf_files": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Lista ścieżek do plików PDF"
                                },
                                "diagram_type": {
                                    "type": "string",
                                    "description": "Typ diagramu"
                                },
                                "enhancement_level": {
                                    "type": "string",
                                    "description": "Poziom wzbogacenia (basic, detailed, comprehensive)",
                                    "enum": ["basic", "detailed", "comprehensive"],
                                    "default": "detailed"
                                }
                            },
                            "required": ["original_prompt", "pdf_files", "diagram_type"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Obsługuje wywołania narzędzi."""
            
            try:
                if name == "process_pdf":
                    return await self._process_pdf(**arguments)
                elif name == "extract_context_for_diagram":
                    return await self._extract_context_for_diagram(**arguments)
                elif name == "search_pdf_content":
                    return await self._search_pdf_content(**arguments)
                elif name == "analyze_process_flow":
                    return await self._analyze_process_flow(**arguments)
                elif name == "enhance_prompt_with_context":
                    return await self._enhance_prompt_with_context(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                self.logger.error(f"Error calling tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )],
                    isError=True
                )
    
    async def _process_pdf(self, file_path: str, use_cache: bool = True) -> CallToolResult:
        """Przetwarza plik PDF i zwraca podstawowe informacje."""
        
        try:
            # Sprawdź czy plik istnieje
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Przetwórz PDF
            pdf_doc = self.pdf_processor.process_pdf(file_path, use_cache)
            
            # Przygotuj wynik
            result_data = {
                "file_path": pdf_doc.file_path,
                "title": pdf_doc.title,
                "total_pages": pdf_doc.total_pages,
                "processed_date": pdf_doc.processed_date,
                "content_preview": pdf_doc.text_content[:500] + "..." if len(pdf_doc.text_content) > 500 else pdf_doc.text_content,
                "metadata": pdf_doc.metadata
            }
            
            # Cache document
            self.document_cache[file_path] = pdf_doc
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    async def _extract_context_for_diagram(
        self, 
        file_path: str, 
        diagram_type: str, 
        focus_areas: Optional[List[str]] = None
    ) -> CallToolResult:
        """Ekstraktuje kontekst dostosowany do typu diagramu."""
        
        try:
            # Pobierz dokument (z cache lub przetwórz)
            if file_path in self.document_cache:
                pdf_doc = self.document_cache[file_path]
            else:
                pdf_doc = self.pdf_processor.process_pdf(file_path)
                self.document_cache[file_path] = pdf_doc
            
            # Analizuj kontekst procesu
            process_context = self.pdf_processor.analyze_process_context(pdf_doc.text_content)
            
            # Dostosuj do typu diagramu
            context_text = self.pdf_processor.get_context_for_diagram_type(pdf_doc, diagram_type)
            
            # Zastosuj filtrowanie obszarów
            if focus_areas:
                filtered_context = self._filter_context_by_areas(process_context, focus_areas)
                context_text += f"\n\n**FILTERED CONTEXT:**\n{json.dumps(filtered_context, indent=2, ensure_ascii=False)}"
            
            result_data = {
                "diagram_type": diagram_type,
                "context": context_text,
                "process_name": process_context.process_name,
                "actors_count": len(process_context.actors),
                "activities_count": len(process_context.activities),
                "systems_count": len(process_context.systems),
                "decisions_count": len(process_context.decisions)
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract context: {str(e)}")
    
    async def _search_pdf_content(
        self, 
        file_path: str, 
        query: str, 
        max_results: int = 5
    ) -> CallToolResult:
        """Wykonuje wyszukiwanie semantyczne w dokumencie."""
        
        try:
            # Pobierz dokument
            if file_path in self.document_cache:
                pdf_doc = self.document_cache[file_path]
            else:
                pdf_doc = self.pdf_processor.process_pdf(file_path)
                self.document_cache[file_path] = pdf_doc
            
            # Proste wyszukiwanie tekstowe (można rozwinąć o semantic search)
            lines = pdf_doc.text_content.split('\n')
            query_words = query.lower().split()
            
            matches = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                score = sum(1 for word in query_words if word in line_lower)
                
                if score > 0:
                    matches.append({
                        "line_number": i + 1,
                        "content": line.strip(),
                        "relevance_score": score / len(query_words),
                        "context": self._get_line_context(lines, i, 2)
                    })
            
            # Sortuj po relevance score
            matches = sorted(matches, key=lambda x: x['relevance_score'], reverse=True)[:max_results]
            
            result_data = {
                "query": query,
                "total_matches": len(matches),
                "matches": matches
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            raise Exception(f"Failed to search content: {str(e)}")
    
    async def _analyze_process_flow(
        self, 
        file_path: str, 
        process_keywords: Optional[List[str]] = None
    ) -> CallToolResult:
        """Analizuje przepływ procesu w dokumencie."""
        
        try:
            # Pobierz dokument
            if file_path in self.document_cache:
                pdf_doc = self.document_cache[file_path]
            else:
                pdf_doc = self.pdf_processor.process_pdf(file_path)
                self.document_cache[file_path] = pdf_doc
            
            # Analizuj kontekst
            process_context = self.pdf_processor.analyze_process_context(pdf_doc.text_content)
            
            # Znajdź sekwencje procesów
            flow_indicators = [
                "krok", "etap", "następnie", "później", "po tym",
                "step", "stage", "then", "next", "after", "following"
            ]
            
            lines = pdf_doc.text_content.split('\n')
            process_flow = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if any(indicator in line_lower for indicator in flow_indicators):
                    if len(line.strip()) > 10:  # Filtruj krótkie linie
                        process_flow.append({
                            "step_number": len(process_flow) + 1,
                            "line_number": i + 1,
                            "content": line.strip(),
                            "keywords_found": [kw for kw in (process_keywords or []) if kw.lower() in line_lower]
                        })
            
            result_data = {
                "process_name": process_context.process_name,
                "total_steps": len(process_flow),
                "actors": process_context.actors,
                "systems": process_context.systems,
                "process_flow": process_flow[:20],  # Limit do 20 kroków
                "summary": {
                    "actors_count": len(process_context.actors),
                    "activities_count": len(process_context.activities),
                    "decisions_count": len(process_context.decisions),
                    "systems_count": len(process_context.systems)
                }
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            raise Exception(f"Failed to analyze process flow: {str(e)}")
    
    async def _enhance_prompt_with_context(
        self,
        original_prompt: str,
        pdf_files: List[str],
        diagram_type: str,
        enhancement_level: str = "detailed"
    ) -> CallToolResult:
        """Wzbogaca prompt o kontekst z dokumentów PDF."""
        
        try:
            from utils.pdf.pdf_processor import enhance_prompt_with_pdf_context
            
            enhanced_prompt = enhance_prompt_with_pdf_context(
                original_prompt, 
                pdf_files, 
                diagram_type
            )
            
            # Dodatkowe dostosowanie na podstawie poziomu wzbogacenia
            if enhancement_level == "comprehensive":
                enhanced_prompt = await self._add_comprehensive_context(enhanced_prompt, pdf_files)
            elif enhancement_level == "basic":
                enhanced_prompt = await self._simplify_context(enhanced_prompt)
            
            result_data = {
                "original_length": len(original_prompt),
                "enhanced_length": len(enhanced_prompt),
                "enhancement_level": enhancement_level,
                "pdf_files_count": len(pdf_files),
                "enhanced_prompt": enhanced_prompt
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2, ensure_ascii=False)
                )]
            )
            
        except Exception as e:
            raise Exception(f"Failed to enhance prompt: {str(e)}")
    
    def _filter_context_by_areas(self, process_context: ProcessContext, focus_areas: List[str]) -> Dict:
        """Filtruje kontekst na podstawie wybranych obszarów."""
        
        filtered = {}
        
        if "actors" in focus_areas:
            filtered["actors"] = process_context.actors
        if "processes" in focus_areas or "activities" in focus_areas:
            filtered["activities"] = process_context.activities
        if "systems" in focus_areas:
            filtered["systems"] = process_context.systems
        if "decisions" in focus_areas:
            filtered["decisions"] = process_context.decisions
        if "rules" in focus_areas:
            filtered["business_rules"] = process_context.business_rules
        
        return filtered
    
    def _get_line_context(self, lines: List[str], line_index: int, context_size: int = 2) -> str:
        """Zwraca kontekst wokół danej linii."""
        
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        
        context_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_index else "    "
            context_lines.append(f"{prefix}{lines[i].strip()}")
        
        return '\n'.join(context_lines)
    
    async def _add_comprehensive_context(self, prompt: str, pdf_files: List[str]) -> str:
        """Dodaje szczegółowy kontekst do promptu."""
        
        comprehensive_additions = []
        
        for pdf_file in pdf_files:
            try:
                if pdf_file in self.document_cache:
                    pdf_doc = self.document_cache[pdf_file]
                else:
                    pdf_doc = self.pdf_processor.process_pdf(pdf_file)
                    self.document_cache[pdf_file] = pdf_doc
                
                # Dodaj szczegółowe metadane
                comprehensive_additions.append(f"""
**SZCZEGÓŁOWY KONTEKST Z {pdf_doc.title}:**
- Liczba stron: {pdf_doc.total_pages}
- Data przetwarzania: {pdf_doc.processed_date}
- Struktura dokumentu: {len(pdf_doc.structured_content.get('pages', []))} sekcji
""")
                
            except Exception as e:
                self.logger.warning(f"Could not add comprehensive context for {pdf_file}: {e}")
        
        if comprehensive_additions:
            return prompt + "\n\n" + "\n".join(comprehensive_additions)
        
        return prompt
    
    async def _simplify_context(self, prompt: str) -> str:
        """Upraszcza kontekst w prompcie."""
        
        # Usuń nadmiarowe szczegóły, zachowaj tylko kluczowe informacje
        lines = prompt.split('\n')
        simplified_lines = []
        
        skip_section = False
        for line in lines:
            if "SZCZEGÓŁOWY KONTEKST" in line or "DODATKOWE INFORMACJE" in line:
                skip_section = True
                continue
            elif line.startswith("**") and skip_section:
                skip_section = False
            
            if not skip_section:
                simplified_lines.append(line)
        
        return '\n'.join(simplified_lines)

# Funkcja do uruchamiania servera
async def run_pdf_context_server():
    """Uruchamia MCP server dla kontekstu PDF."""
    
    if not MCP_AVAILABLE:
        raise RuntimeError("MCP libraries not available. Install with: pip install mcp")
    
    server = AdvancedPDFContextServer()
    
    # Konfiguracja servera
    async with server.server.run(
        host="localhost",
        port=3001,
        options=InitializationOptions(
            experimental_capabilities={}
        )
    ):
        await server.server.wait_for_shutdown()

if __name__ == "__main__":
    # Przykład użycia
    asyncio.run(run_pdf_context_server())