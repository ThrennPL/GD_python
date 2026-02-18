import xml.etree.ElementTree as ET
import xml.dom.minidom
import uuid
from datetime import datetime
import re
import os
from typing import Dict, List, Optional, Tuple
from logger_utils import log_debug, log_info, log_error, log_exception, log_warning, setup_logger
from utils.plantuml.plantuml_component_parser import PlantUMLComponentParser

setup_logger('xmi_component_generator.log')

class LayoutManager:
    """Oblicza rozmieszczenie pakietów, komponentów i notatek na diagramie."""

    def __init__(self, generator, log_callback):
        self.generator = generator
        self.log = log_callback
        self.parsed = generator.parsed_data

        self.package_nodes: Dict[str, Dict[str, object]] = {}
        self.root_packages: List[str] = []
        self.root_components: List[str] = []
        self.root_interfaces: List[str] = []

        self.measurements: Dict[str, Dict[str, object]] = {}
        self.positions: Dict[str, str] = {}
        self.output_packages: List[Dict[str, object]] = []
        self.output_elements: List[Dict[str, object]] = []
        self.placed_parser_ids: set[str] = set()

        self.max_right = 0
        self.min_top: Optional[int] = None
        self.max_bottom = 0

        # Konfiguracja layoutu
        self.padding_x = 40
        self.padding_y = 30
        self.header_height = 50
        self.min_package_width = 480
        self.min_package_height = 260
        self.package_spacing = 60
        self.component_spacing_x = 30
        self.component_spacing_y = 25
        self.max_components_per_row = 3

        self.root_start_x = 100
        self.root_start_y = 120
        self.root_vertical_spacing = 80
        self.column_spacing = 220
        self.max_packages_per_column = 4
        self.external_offset_x = 200
        self.external_spacing_y = 40

    def layout(self) -> Dict[str, List[Dict[str, object]]]:
        self._build_nodes()

        if not self.package_nodes:
            self.log("Brak pakietów do rozmieszczenia")

        for parser_id in list(self.package_nodes.keys()):
            self._measure_package(parser_id)

        self._place_top_packages()
        self._place_external_elements()
        self._place_notes()

        return {
            'packages': self.output_packages,
            'elements': self.output_elements,
            'positions': self.positions
        }

    def _build_nodes(self) -> None:
        packages = self.parsed.get('packages', {})

        for pkg_id, pkg_data in packages.items():
            display_id = self.generator.package_display_ids.get(pkg_id)
            xmi_id = display_id or self.generator.parser_id_to_xmi_id.get(pkg_id)
            if not xmi_id:
                log_warning(f"Pominięto pakiet {pkg_id}: brak identyfikatora XMI")
                continue
            package_kind = pkg_data.get('package_kind')
            if pkg_data.get('type') == 'c4_boundary':
                display_class = 'Boundary'
            elif package_kind == 'frame':
                display_class = 'Boundary'
            elif display_id:
                display_class = 'Component'
            else:
                display_class = 'Package'
            node = {
                'parser_id': pkg_id,
                'xmi_id': xmi_id,
                'name': pkg_data.get('name', 'Unnamed Package'),
                'type': pkg_data.get('type', 'package'),
                'package_kind': package_kind,
                'display_class': display_class,
                'parent': pkg_data.get('parent_package'),
                'children': [],
                'components': [],
                'interfaces': []
            }
            self.package_nodes[pkg_id] = node

        for node in self.package_nodes.values():
            parent_id = node['parent']
            if parent_id and parent_id in self.package_nodes:
                self.package_nodes[parent_id]['children'].append(node['parser_id'])
            else:
                self.root_packages.append(node['parser_id'])

        components = self.parsed.get('components', {})
        for comp_id, comp_data in components.items():
            package_id = comp_data.get('package')
            if package_id and package_id in self.package_nodes:
                self.package_nodes[package_id]['components'].append(comp_id)
            else:
                self.root_components.append(comp_id)

        interfaces = self.parsed.get('interfaces', {})
        for interface_id, interface_data in interfaces.items():
            package_id = interface_data.get('package')
            if package_id and package_id in self.package_nodes:
                self.package_nodes[package_id]['interfaces'].append(interface_id)
            else:
                self.root_interfaces.append(interface_id)

    def _measure_package(self, parser_id: str) -> Dict[str, object]:
        if parser_id in self.measurements:
            return self.measurements[parser_id]

        node = self.package_nodes.get(parser_id)
        if not node:
            return {}

        child_measurements = []
        for child_id in node['children']:
            child_measurements.append(self._measure_package(child_id))

        component_entries: List[Dict[str, object]] = []
        for comp_id in node['components']:
            entry = self._create_element_entry(comp_id, 'component')
            if entry:
                component_entries.append(entry)

        for interface_id in node['interfaces']:
            entry = self._create_element_entry(interface_id, 'interface')
            if entry:
                component_entries.append(entry)

        component_entries.sort(key=lambda item: item['name'])

        measurement = self._compute_container_measurement(node, child_measurements, component_entries)
        self.measurements[parser_id] = measurement
        return measurement

    def _create_element_entry(self, parser_id: str, element_source: str) -> Optional[Dict[str, object]]:
        if element_source == 'component':
            data = self.parsed['components'].get(parser_id)
            if not data:
                return None
            name = data.get('name', 'Component')
            element_type = data.get('type', 'component').lower()
            if 'actor' in element_type:
                kind = 'actor'
            elif element_type == 'interface':
                kind = 'interface'
            else:
                kind = 'component'
        elif element_source == 'interface':
            data = self.parsed['interfaces'].get(parser_id)
            if not data:
                return None
            name = data.get('name', 'Interface')
            kind = 'interface'
        else:
            return None

        xmi_id = self.generator.parser_id_to_xmi_id.get(parser_id)
        if not xmi_id:
            return None

        width, height = self._compute_element_size(name, kind)
        return {
            'parser_id': parser_id,
            'xmi_id': xmi_id,
            'name': name,
            'kind': kind,
            'width': width,
            'height': height
        }

    def _compute_element_size(self, name: str, kind: str) -> Tuple[int, int]:
        length = len(name)
        if kind == 'interface':
            base_width, base_height = 150, 60
        elif kind == 'actor':
            base_width, base_height = 110, 120
        else:
            base_width, base_height = 170, 70

        width = max(base_width, min(base_width + length * 7, base_width * 2))
        return width, base_height

    def _compute_container_measurement(
        self,
        node: Dict[str, object],
        child_measurements: List[Dict[str, object]],
        component_entries: List[Dict[str, object]]
    ) -> Dict[str, object]:
        node_name = node['name']
        xmi_id = node['xmi_id']

        valid_children = [child for child in child_measurements if child]
        max_child_width = max((child['width'] for child in valid_children), default=0)

        rows = self._group_components(component_entries)

        row_infos = []
        max_component_width = 0
        total_component_height = 0

        for row in rows:
            row_width = sum(entry['width'] for entry in row)
            row_spacing = self.component_spacing_x * (len(row) - 1) if len(row) > 1 else 0
            total_width = row_width + row_spacing
            row_height = max(entry['height'] for entry in row)
            row_infos.append({
                'entries': row,
                'width': total_width,
                'height': row_height
            })
            max_component_width = max(max_component_width, total_width)
            total_component_height += row_height

        if row_infos:
            total_component_height += self.component_spacing_y * (len(row_infos) - 1)

        inner_width = max(max_child_width, max_component_width, self.min_package_width - 2 * self.padding_x)
        package_width = inner_width + 2 * self.padding_x

        current_y = self.header_height + self.padding_y
        child_positions = []

        for child in valid_children:
            offset_x = self.padding_x + max(0, (inner_width - child['width']) / 2)
            child_positions.append({
                'parser_id': child['parser_id'],
                'x_offset': offset_x,
                'y_offset': current_y
            })
            current_y += child['height'] + self.package_spacing

        if valid_children and row_infos:
            current_y += self.package_spacing

        component_positions = []
        for idx, row in enumerate(row_infos):
            row_offset_x = self.padding_x + max(0, (inner_width - row['width']) / 2)
            comp_left = row_offset_x
            row_height = row['height']
            for entry in row['entries']:
                offset_y = current_y + max(0, (row_height - entry['height']) / 2)
                component_positions.append({
                    'parser_id': entry['parser_id'],
                    'x_offset': comp_left,
                    'y_offset': offset_y,
                    'width': entry['width'],
                    'height': entry['height'],
                    'kind': entry['kind'],
                    'name': entry['name']
                })
                comp_left += entry['width'] + self.component_spacing_x

            current_y += row_height
            if idx < len(row_infos) - 1:
                current_y += self.component_spacing_y

        total_height = max(current_y + self.padding_y, self.min_package_height)

        measurement = {
            'parser_id': node['parser_id'],
            'width': package_width,
            'height': total_height,
            'child_positions': child_positions,
            'component_positions': component_positions,
            'name': node_name,
            'xmi_id': xmi_id,
            'package_type': node['type']
        }

        self.log(
            f"Analiza pakietu '{node_name}' (ID: {xmi_id}), szerokość: {int(package_width)}, wysokość: {int(total_height)}"
        )
        return measurement

    def _group_components(self, entries: List[Dict[str, object]]) -> List[List[Dict[str, object]]]:
        if not entries:
            return []

        rows: List[List[Dict[str, object]]] = []
        row: List[Dict[str, object]] = []
        for entry in entries:
            row.append(entry)
            if len(row) >= self.max_components_per_row:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return rows

    def _place_top_packages(self) -> None:
        if not self.root_packages:
            return

        current_x = self.root_start_x
        current_y = self.root_start_y
        column_width = 0
        packages_in_column = 0

        for parser_id in self.root_packages:
            measurement = self.measurements.get(parser_id)
            if not measurement:
                continue

            if packages_in_column >= self.max_packages_per_column:
                current_x += column_width + self.column_spacing
                current_y = self.root_start_y
                packages_in_column = 0
                column_width = 0

            self._place_package(parser_id, current_x, current_y)
            column_width = max(column_width, measurement['width'])
            current_y += measurement['height'] + self.root_vertical_spacing
            packages_in_column += 1

    def _place_package(self, parser_id: str, left: float, top: float) -> None:
        measurement = self.measurements.get(parser_id)
        node = self.package_nodes.get(parser_id)
        if not measurement or not node:
            return

        width = measurement['width']
        height = measurement['height']
        right = left + width
        bottom = top + height

        geometry = self._format_geometry(left, top, width, height)
        self.positions[node['xmi_id']] = geometry
        self.output_packages.append({
            'parser_id': parser_id,
            'xmi_id': node['xmi_id'],
            'geometry': geometry,
            'name': node['name'],
            'package_type': node['type'],
            'element_class': node.get('display_class', 'Component')
        })

        self.max_right = max(self.max_right, int(right))
        self.max_bottom = max(self.max_bottom, int(bottom))
        if self.min_top is None:
            self.min_top = int(top)
        else:
            self.min_top = min(self.min_top, int(top))

        self.log(
            f"Pakiet '{node['name']}' (ID: {node['xmi_id']}): Left={int(left)}, Top={int(top)}, Right={int(right)}, Bottom={int(bottom)}"
        )

        for child in measurement['child_positions']:
            child_left = left + child['x_offset']
            child_top = top + child['y_offset']
            self._place_package(child['parser_id'], child_left, child_top)

        for component in measurement['component_positions']:
            self._place_element_within_package(component, left, top)

    def _place_element_within_package(self, component: Dict[str, object], parent_left: float, parent_top: float) -> None:
        parser_id = component['parser_id']
        xmi_id = self.generator.parser_id_to_xmi_id.get(parser_id)
        if not xmi_id:
            return

        left = parent_left + component['x_offset']
        top = parent_top + component['y_offset']
        width = component['width']
        height = component['height']
        geometry = self._format_geometry(left, top, width, height)

        self.positions[xmi_id] = geometry
        self.output_elements.append({
            'parser_id': parser_id,
            'xmi_id': xmi_id,
            'geometry': geometry,
            'kind': component['kind']
        })
        self.placed_parser_ids.add(parser_id)

        self.max_right = max(self.max_right, int(left + width))
        self.max_bottom = max(self.max_bottom, int(top + height))
        if self.min_top is None:
            self.min_top = int(top)
        else:
            self.min_top = min(self.min_top, int(top))

        self.log(
            f"  - Element (ID: {xmi_id}): Left={int(left)}, Top={int(top)}, Right={int(left + width)}, Bottom={int(top + height)}"
        )

    def _place_external_elements(self) -> None:
        entries: List[Dict[str, object]] = []

        for comp_id in self.root_components:
            if comp_id in self.placed_parser_ids:
                continue
            entry = self._create_element_entry(comp_id, 'component')
            if entry:
                entries.append(entry)
                self.placed_parser_ids.add(comp_id)

        for interface_id in self.root_interfaces:
            if interface_id in self.placed_parser_ids:
                continue
            entry = self._create_element_entry(interface_id, 'interface')
            if entry:
                entries.append(entry)
                self.placed_parser_ids.add(interface_id)

        entries.sort(key=lambda item: item['name'])

        if not entries:
            return

        current_x = self.max_right + self.external_offset_x if self.max_right else self.root_start_x
        current_y = self.min_top if self.min_top is not None else self.root_start_y

        for entry in entries:
            xmi_id = entry['xmi_id']
            if not xmi_id:
                continue

            geometry = self._format_geometry(current_x, current_y, entry['width'], entry['height'])
            self.positions[xmi_id] = geometry
            self.output_elements.append({
                'parser_id': entry['parser_id'],
                'xmi_id': xmi_id,
                'geometry': geometry,
                'kind': entry['kind']
            })

            self.log(
                f"Element zewnętrzny '{entry['name']}' (ID: {xmi_id}): Left={int(current_x)}, Top={int(current_y)}"
            )

            current_y += entry['height'] + self.external_spacing_y
            self.max_right = max(self.max_right, int(current_x + entry['width']))
            self.max_bottom = max(self.max_bottom, int(current_y))
            if self.min_top is None:
                self.min_top = int(current_y)

    def _place_notes(self) -> None:
        for note in self.parsed.get('notes', []):
            parser_id = note.get('id')
            if not parser_id or parser_id in self.placed_parser_ids:
                continue

            xmi_id = self.generator.parser_id_to_xmi_id.get(parser_id)
            if not xmi_id:
                continue

            content = note.get('content', '')
            width, height = self._compute_note_size(content)
            position = note.get('position', 'right')
            target_parser_id = note.get('target_id')

            left, top = self._calculate_note_coordinates(target_parser_id, position, width, height)
            geometry = self._format_geometry(left, top, width, height)

            self.positions[xmi_id] = geometry
            self.output_elements.append({
                'parser_id': parser_id,
                'xmi_id': xmi_id,
                'geometry': geometry,
                'kind': 'note'
            })
            self.placed_parser_ids.add(parser_id)

            self.log(
                f"Notatka '{content[:20]}' (ID: {xmi_id}): Left={int(left)}, Top={int(top)}"
            )

    def _compute_note_size(self, content: str) -> Tuple[int, int]:
        lines = content.split('\n') if content else ['']
        longest = max(len(line) for line in lines)
        width = max(220, min(220 + longest * 5, 400))
        height = max(100, 60 + (len(lines) - 1) * 20)
        return width, height

    def _calculate_note_coordinates(
        self,
        target_parser_id: Optional[str],
        position: str,
        width: int,
        height: int
    ) -> Tuple[int, int]:
        if target_parser_id:
            target_xmi_id = self.generator.parser_id_to_xmi_id.get(target_parser_id)
            target_geometry = self.positions.get(target_xmi_id)
            if target_geometry:
                coords = self._parse_geometry(target_geometry)
                left, top = self._position_relative_to(coords, position, width, height)
                self.max_right = max(self.max_right, int(left + width))
                self.max_bottom = max(self.max_bottom, int(top + height))
                if self.min_top is None:
                    self.min_top = int(top)
                else:
                    self.min_top = min(self.min_top, int(top))
                return left, top

        left = self.max_right + self.external_offset_x if self.max_right else self.root_start_x
        top = self.max_bottom + self.external_spacing_y
        self.max_right = max(self.max_right, int(left + width))
        self.max_bottom = max(self.max_bottom, int(top + height))
        if self.min_top is None:
            self.min_top = int(top)
        else:
            self.min_top = min(self.min_top, int(top))
        return left, top

    def _position_relative_to(self, coords: Dict[str, int], position: str, width: int, height: int) -> Tuple[int, int]:
        if position == 'left':
            left = coords['left'] - width - 40
            top = coords['top']
        elif position == 'top':
            left = coords['left']
            top = coords['top'] - height - 40
        elif position == 'bottom':
            left = coords['left']
            top = coords['bottom'] + 40
        else:  # default right
            left = coords['right'] + 40
            top = coords['top']
        return left, top

    def _parse_geometry(self, geometry: str) -> Dict[str, int]:
        coords = {}
        for part in geometry.split(';'):
            if not part:
                continue
            if '=' not in part:
                continue
            key, value = part.split('=')
            coords[key.lower()] = int(round(float(value)))
        return {
            'left': coords.get('left', 0),
            'top': coords.get('top', 0),
            'right': coords.get('right', 0),
            'bottom': coords.get('bottom', 0)
        }

    def _format_geometry(self, left: float, top: float, width: float, height: float) -> str:
        l = int(round(left))
        t = int(round(top))
        r = int(round(left + width))
        b = int(round(top + height))
        return f"Left={l};Top={t};Right={r};Bottom={b};"

class XMIComponentGenerator:
    """
    Generator XMI dla diagramów komponentów UML/C4.
    Generuje w pełni funkcjonalny diagram komponentów w formacie XMI (dla Enterprise Architect)
    na podstawie danych z parsera PlantUML.
    """
    
    def __init__(self, author: str = "XMI Generator", debug_options: dict = None):
        self.author = author
        # Ustaw domyślne opcje debugowania
        self.debug_options = {
            'positioning': False,     # Debugowanie pozycji elementów
            'elements': False,        # Lista elementów diagramu
            'processing': False,      # Śledzenie przetwarzania elementów
            'relationships': False,   # Szczegóły tworzenia relacji
            'xml': False              # Debugowanie struktury XML
        }
        # Nadpisz domyślne opcje tymi przekazanymi w parametrze
        if debug_options:
            self.debug_options.update(debug_options)
        
        self._reset_state()
        self.ns = {
            'uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi': 'http://schema.omg.org/spec/XMI/2.1'
        }
        self.stereotype_guid_map = {
            'service': 'EAID_E8EB7F24_9586_429a_A543_5B9AA9CB786B',
            'controller': 'EAID_3F786850_E47F_11D2_ABF0_00A0C90FFFC3',
            'gateway': 'EAID_C4F252E8_E947_11D2_ABF1_00A0C90FFFC8',
            'utility': 'EAID_D8C0A0A0_E947_11D2_ABF2_00A0C90FFFC9',
            'facade': 'EAID_F0C034E0_E947_11D2_ABF3_00A0C90FFFCA',
            'repository': 'EAID_F1C0F34E_F947_11D2_ABF4_00A0C90FFFCC',
            'database': 'EAID_DB9EAC10_E947_11D2_ABF5_00A0C90FFFD0'
        }

        self._register_namespaces()
        
    def _reset_state(self):
        """Resetuje stan generatora przed każdym nowym diagramem."""
        self.id_map = {}  # Mapa ID elementów XML
        self.parser_id_to_xmi_id = {}  # Mapa ID parsera do ID XMI
        self.package_display_ids = {}  # Mapa pakietów na element wizualny
        self.relationships = []  # Lista relacji
        self.diagram_objects = []  # Lista obiektów diagramu
        self.package_id = None  # ID głównego pakietu
        self.diagram_id = None  # ID diagramu
        self.root_package_id = None  # ID pakietu głównego
        self.added_to_diagram = set()
    
    def _register_namespaces(self):
        """Rejestruje przestrzenie nazw XML."""
        ET.register_namespace('xmi', self.ns['xmi'])
        ET.register_namespace('uml', self.ns['uml'])
        ET.register_namespace('thecustomprofile', 'http://www.sparxsystems.com/profiles/thecustomprofile/1.0')
        ET.register_namespace('SOMF', 'http://www.sparxsystems.com/profiles/SOMF/1.0')
        ET.register_namespace('StandardProfileL2', 'http://www.sparxsystems.com/profiles/StandardProfileL2/1.0')
    
    def _generate_ea_id(self, prefix: str = "EAID") -> str:
        """Generuje unikalny identyfikator w stylu EA."""
        return f"{prefix}_{str(uuid.uuid4()).upper().replace('-', '_')}"
    
    def generate_component_diagram(self, diagram_name: str, parsed_data: dict) -> str:
        """
        Główna metoda generująca całą strukturę XMI dla diagramu komponentów.
        
        Args:
            diagram_name: Nazwa diagramu
            parsed_data: Dane wygenerowane przez parser PlantUML
            
        Returns:
            str: Dokument XMI jako string
        """
        self._reset_state()
        self.parsed_data = parsed_data
        
        # Generowanie unikalnych identyfikatorów dla głównych elementów
        self.diagram_id = self._generate_ea_id("EAID")
        self.package_id = self._generate_ea_id("EAPK")
        
        # Utworzenie podstawowej struktury dokumentu
        root = self._create_document_root()
        model = self._create_uml_model(root)
        package = self._create_diagram_package(model, diagram_name)
        
        # Przetwarzanie elementów diagramu
        self._process_components(package, parsed_data['components'])
        self._process_interfaces(package, parsed_data['interfaces'])
        self._process_packages(package, parsed_data['packages'])
        
        # Przetwarzanie relacji
        self._process_relationships(package, parsed_data['relationships'])
        
        # Przetwarzanie notatek
        self._process_notes(package, parsed_data['notes'])
        
        # Weryfikacja spójności diagramu
        self._verify_diagram_consistency()
        
        # Dodanie rozszerzeń specyficznych dla EA
        self._create_ea_extensions(root, diagram_name)

        # Dodaj odniesienia do stereotypów po utworzeniu wszystkich elementów
        self._add_stereotype_references(root)
        
        # Zwróć sformatowany XML
        return self._format_xml(root)
    
    def _add_stereotype_references(self, root: ET.Element):
        """Dodaje odniesienia stereotypów do komponentów."""
        if not hasattr(self, 'component_stereotypes') or not self.component_stereotypes:
            return
        
        # Utwórz sekcję dla odniesień do stereotypów
        stereotype_refs = ET.SubElement(root, 'stereotypeApplications')
        
        for component_id, stereotype in self.component_stereotypes.items():
            element_def = self.id_map.get(component_id)
            element_xmi_type = element_def.get('xmi:type') if element_def is not None else ''

            if stereotype == 'service':
                ET.SubElement(stereotype_refs, 'serviceApplication', {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': 'StandardProfileL2:Service',
                    'base_Component': component_id
                })
            elif stereotype == 'repository':
                ET.SubElement(stereotype_refs, 'repositoryApplication', {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': 'SOMF:repository',
                    'base_Class': component_id
                })
            elif stereotype in ['controller', 'gateway', 'utility', 'facade', 'database']:
                base_attr = 'base_Component'
                if element_xmi_type == 'uml:Interface':
                    base_attr = 'base_Interface'
                app_attrs = {
                    'xmi:id': self._generate_ea_id("EAID"),
                    'xmi:type': f'thecustomprofile:{stereotype}'
                }
                app_attrs[base_attr] = component_id
                ET.SubElement(stereotype_refs, f'{stereotype}Application', app_attrs)

    def _create_document_root(self) -> ET.Element:
        """Tworzy główny element dokumentu XMI."""
        root = ET.Element(f'{{{self.ns["xmi"]}}}XMI', {'xmi:version': '2.1'})

        root.set('xmlns:thecustomprofile', 'http://www.sparxsystems.com/profiles/thecustomprofile/1.0')
        root.set('xmlns:SOMF', 'http://www.sparxsystems.com/profiles/SOMF/1.0')
        root.set('xmlns:StandardProfileL2', 'http://www.sparxsystems.com/profiles/StandardProfileL2/1.0')
        
        # Dodaj dokumentację o eksporterze
        ET.SubElement(root, f'{{{self.ns["xmi"]}}}Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5', 
            'exporterID': '1560'
        })
        
        return root
    
    def _create_uml_model(self, root: ET.Element) -> ET.Element:
        """Tworzy element modelu UML."""
        return ET.SubElement(root, ET.QName(self.ns['uml'], 'Model'), {
            'xmi:type': 'uml:Model', 'name': 'EA_Model', 'visibility': 'public'
        })
    
    def _create_diagram_package(self, model: ET.Element, diagram_name: str) -> ET.Element:
        """Tworzy główny pakiet diagramu."""
        root_package_id = self._generate_ea_id("EAPK")
        root_package = ET.SubElement(model, 'packagedElement', {
            'xmi:type': 'uml:Package', 
            'xmi:id': root_package_id, 
            'name': diagram_name, 
            'visibility': 'public'
        })
        
        # Dodaj atrybut "ea_localid" kluczowy dla EA
        root_package.set('ea_localid', self._get_local_id(root_package_id))
        
        self.root_package_id = root_package_id
        self.package_id = root_package_id
        
        return root_package
    
    def _process_components(self, parent_element, components):
        """Przetwarza komponenty z parsera PlantUML."""
        # Najpierw grupujemy komponenty według ich pakietów
        components_by_package = {}
        for component_id, component_data in components.items():
            package_id = component_data.get('package')
            if package_id:
                if package_id not in components_by_package:
                    components_by_package[package_id] = []
                components_by_package[package_id].append((component_id, component_data))
        
        # Przetwarzamy komponenty, które nie są przypisane do żadnego pakietu
        for component_id, component_data in components.items():
            component_package = component_data.get('package')
            
            # Tylko przetwarzaj komponenty bez pakietu w tym momencie
            if component_package:
                continue
                
            component_type = component_data.get('type', 'component')
            component_name = component_data.get('name', 'Unnamed')
            c4_type = component_data.get('c4_type', '')
            parser_id = component_data.get('id')
            
            # Utwórz element komponentu
            diagram_element_type = 'Component'
            if component_type == 'c4_element':
                # Specjalna obsługa elementów C4
                xmi_id = self._add_c4_element(parent_element, component_data)
            else:
                # Standardowy komponent UML lub inny element wspierany przez parser
                xmi_id, diagram_element_type = self._add_component(parent_element, component_data)
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': diagram_element_type,
                'name': component_name,
                'c4_type': c4_type
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono komponent '{component_name}' ({component_type})")
                log_debug(f"🔄 Przetworzono komponent '{component_name}' ({component_type})")
        
        # Komponenty w pakietach będą dodawane później w _process_package


    def _add_component(self, parent_element, component_data):
        """Dodaje komponent lub inny wspierany element UML do modelu."""
        component_id = self._generate_ea_id("EAID")
        component_name = component_data.get('name', 'Unnamed')
        component_alias = component_data.get('alias')
        component_stereotype = component_data.get('stereotype', '')
        component_type = (component_data.get('type') or 'component').lower()

        if 'actor' in component_type:
            uml_type = 'uml:Actor'
            diagram_element_type = 'Actor'
        elif component_stereotype == 'gateway':
            uml_type = 'uml:Interface'
            diagram_element_type = 'Interface'
        else:
            uml_type = 'uml:Component'
            diagram_element_type = 'Component'

        element = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': uml_type,
            'xmi:id': component_id,
            'name': component_name,
            'visibility': 'public'
        })

        if component_alias:
            element.set('alias', component_alias)

        self.id_map[component_id] = element

        if component_stereotype:
            if not hasattr(self, 'component_stereotypes'):
                self.component_stereotypes = {}
            self.component_stereotypes[component_id] = component_stereotype

        return component_id, diagram_element_type

    def _create_layer_visual_component(self, parent_element, package_data):
        """Tworzy komponent wizualny reprezentujący warstwę."""
        component_name = package_data.get('name', 'Unnamed Layer')
        component_alias = package_data.get('alias')
        stereotype = package_data.get('stereotype') or 'layer'

        component_data = {
            'name': component_name,
            'alias': component_alias,
            'stereotype': stereotype,
            'type': 'layer_component'
        }

        component_id, diagram_type = self._add_component(parent_element, component_data)

        self.diagram_objects.append({
            'id': component_id,
            'type': diagram_type,
            'name': component_name,
            'is_layer_visual': True
        })

        return component_id

    def _create_frame_boundary_component(self, parent_element, package_data):
        """Tworzy element Boundary dla obramowania frame, używany wyłącznie wizualnie."""
        boundary_name = package_data.get('name', 'Frame Boundary')
        boundary_alias = package_data.get('alias')

        boundary = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': 'uml:Component',
            'xmi:id': self._generate_ea_id("EAID"),
            'name': boundary_name,
            'visibility': 'public'
        })

        boundary_id = boundary.get('xmi:id')

        if boundary_alias:
            boundary.set('alias', boundary_alias)

        ET.SubElement(boundary, 'stereotype', {'name': 'Boundary'})

        self.id_map[boundary_id] = boundary

        self.diagram_objects.append({
            'id': boundary_id,
            'type': 'Boundary',
            'name': boundary_name,
            'is_frame_boundary': True
        })

        return boundary_id
    
    def _add_c4_element(self, parent_element, component_data):
        """Dodaje element C4 (Person, System, Container, Component) do modelu."""
        c4_id = self._generate_ea_id("EAID")
        c4_name = component_data.get('name', 'Unnamed')
        c4_type = component_data.get('c4_type', '')
        c4_technology = component_data.get('technology', '')
        c4_description = component_data.get('description', '')
        c4_package = component_data.get('package')
        
        # Określ element nadrzędny
        parent = parent_element
        if c4_package and c4_package in self.id_map:
            parent = self.id_map[c4_package]
        
        # Mapuj typ C4 na odpowiedni typ UML
        uml_type = 'uml:Component'  # domyślnie
        if 'person' in c4_type:
            uml_type = 'uml:Actor'
        elif 'system' in c4_type:
            uml_type = 'uml:Component'
        
        # Utwórz element C4
        c4_element = ET.SubElement(parent, 'packagedElement', {
            'xmi:type': uml_type,
            'xmi:id': c4_id,
            'name': c4_name,
            'visibility': 'public'
        })
        
        # Dodaj stereotyp odpowiadający typowi C4
        stereotype = c4_type.replace('_', ' ').title()
        ET.SubElement(c4_element, 'stereotype', {'name': stereotype})
        
        # Dodaj technologię jako taggedValue
        if c4_technology:
            tech_tag = ET.SubElement(c4_element, 'taggedValue', {'name': 'technology'})
            tech_tag.text = c4_technology
        
        # Dodaj opis jako taggedValue
        if c4_description:
            desc_tag = ET.SubElement(c4_element, 'taggedValue', {'name': 'description'})
            desc_tag.text = c4_description
        
        # Zapisz referencję do ID
        self.id_map[c4_id] = c4_element
        
        return c4_id
    
    def _process_interfaces(self, parent_element, interfaces):
        """Przetwarza interfejsy z parsera PlantUML."""
        for interface_id, interface_data in interfaces.items():
            interface_name = interface_data.get('name', 'Unnamed')
            interface_alias = interface_data.get('alias')
            interface_package = interface_data.get('package')
            interface_stereotype = (interface_data.get('stereotype') or '').lower()
            parser_id = interface_data.get('id')
            
            # Określ element nadrzędny
            parent = parent_element
            if interface_package and interface_package in self.id_map:
                parent = self.id_map[interface_package]
            
            # Utwórz element interfejsu
            xmi_id = self._generate_ea_id("EAID")
            interface = ET.SubElement(parent, 'packagedElement', {
                'xmi:type': 'uml:Interface',
                'xmi:id': xmi_id,
                'name': interface_name,
                'visibility': 'public'
            })
            
            # Dodaj alias jeśli istnieje
            if interface_alias:
                interface.set('alias', interface_alias)

            if interface_stereotype:
                stereotype_guid = self.stereotype_guid_map.get(interface_stereotype)
                interface.set('stereotype', interface_stereotype)
                if stereotype_guid:
                    interface.set('stereotypeGUID', stereotype_guid)
                if not hasattr(self, 'component_stereotypes'):
                    self.component_stereotypes = {}
                self.component_stereotypes[xmi_id] = interface_stereotype
            
            # Zapisz referencję do ID
            self.id_map[xmi_id] = interface
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Interface',
                'name': interface_name
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono interfejs '{interface_name}'")
                log_debug(f"🔄 Przetworzono interfejs '{interface_name}'")
    
    def _process_packages(self, parent_element, packages):
        """Przetwarza pakiety z parsera PlantUML."""
        # Najpierw przetwarzaj pakiety najwyższego poziomu
        top_level_packages = [pkg_id for pkg_id, pkg_data in packages.items() 
                            if not pkg_data.get('parent_package')]
        
        # Przetwórz pakiety najwyższego poziomu
        for pkg_id in top_level_packages:
            self._process_package(parent_element, pkg_id, packages)
            
        # Po przetworzeniu pakietów, dodaj komponenty do ich pakietów
        self._add_components_to_packages()
    
    def _add_components_to_packages(self):
        """Dodaje komponenty do ich odpowiednich pakietów."""
        for component_id, component_data in self.parsed_data['components'].items():
            package_id = component_data.get('package')
            
            # Pomijamy komponenty bez pakietu (zostały już przetworzone wcześniej)
            if not package_id:
                continue
                
            # Pobierz XMI ID pakietu
            package_xmi_id = self.parser_id_to_xmi_id.get(package_id)
            if not package_xmi_id or package_xmi_id not in self.id_map:
                continue
                
            # Pobierz element pakietu
            package_element = self.id_map[package_xmi_id]
            
            component_type = component_data.get('type', 'component')
            component_name = component_data.get('name', 'Unnamed')
            c4_type = component_data.get('c4_type', '')
            parser_id = component_data.get('id')
            
            # Utwórz element komponentu wewnątrz pakietu
            diagram_element_type = 'Component'
            if component_type == 'c4_element':
                xmi_id = self._add_c4_element(package_element, component_data)
            else:
                xmi_id, diagram_element_type = self._add_component(package_element, component_data)
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': diagram_element_type,
                'name': component_name,
                'c4_type': c4_type
            })
            
            if self.debug_options.get('processing', False):
                print(f"🔄 Przetworzono komponent '{component_name}' ({component_type}) w pakiecie '{package_element.get('name')}'")
                log_debug(f"🔄 Przetworzono komponent '{component_name}' ({component_type}) w pakiecie '{package_element.get('name')}'")


    def _process_package(self, parent_element, package_id, all_packages):
        """Rekurencyjnie przetwarza pakiet i jego zawartość."""
        package_data = all_packages[package_id]
        package_name = package_data.get('name', 'Unnamed')
        package_alias = package_data.get('alias')
        package_type = package_data.get('type', 'package')
        parser_id = package_data.get('id')
        
        # Utwórz element pakietu
        xmi_id = self._generate_ea_id("EAID")
        
        # Wybierz odpowiedni typ UML w zależności od typu pakietu
        uml_type = 'uml:Package'
        if package_type == 'c4_boundary':
            # C4 Boundary to też pakiet, ale ze stereotypem
            uml_type = 'uml:Package'
            
        package = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': uml_type,
            'xmi:id': xmi_id,
            'name': package_name,
            'visibility': 'public'
        })
        
        # Dodaj stereotyp dla granicy C4
        if package_type == 'c4_boundary':
            c4_type = package_data.get('c4_type', 'boundary')
            stereotype = c4_type.replace('_', ' ').title()
            ET.SubElement(package, 'stereotype', {'name': stereotype})
        
        # Dodaj alias jeśli istnieje
        if package_alias:
            package.set('alias', package_alias)
        
        # Zapisz referencję do ID
        self.id_map[xmi_id] = package
        
        # Zapisz mapowanie ID
        if parser_id:
            self.parser_id_to_xmi_id[parser_id] = xmi_id
        
        # Dodaj do listy obiektów diagramu (strukturalnych)
        self.diagram_objects.append({
            'id': xmi_id,
            'type': 'Package' if package_type == 'package' else 'Boundary',
            'name': package_name,
            'c4_type': package_data.get('c4_type', '')
        })
        
        if self.debug_options.get('processing', False):
            print(f"📦 Przetworzono pakiet '{package_name}' ({package_type})")
            log_debug(f"📦 Przetworzono pakiet '{package_name}' ({package_type})")

        package_kind = package_data.get('package_kind')

        # Utwórz element wizualny reprezentujący obramowanie frame jako Boundary
        if package_kind == 'frame':
            boundary_id = self._create_frame_boundary_component(parent_element, package_data)
            if boundary_id:
                self.package_display_ids[parser_id] = boundary_id
        # Utwórz element wizualny reprezentujący warstwę jako komponent (dla wewnętrznych pakietów)
        elif package_type != 'c4_boundary' and package_data.get('parent_package'):
            layer_component_id = self._create_layer_visual_component(parent_element, package_data)
            if layer_component_id:
                self.package_display_ids[parser_id] = layer_component_id
        
        # Rekurencyjnie przetwarzaj pakiety-dzieci
        children_packages = [
            child_id for child_id, child_data in all_packages.items()
            if child_data.get('parent_package') == package_id
        ]
        
        for child_id in children_packages:
            self._process_package(package, child_id, all_packages)
    
    def _process_relationships(self, parent_element, relationships):
        """Przetwarza relacje między elementami."""
        # Dodaj pełne debugowanie
        log_debug(f"Rozpoczynam przetwarzanie {len(relationships)} relacji")
        
        # Utwórz mapowania dla aliasów
        alias_to_id = {}
        name_to_id = {}
        
        # Mapowanie dla komponentów
        for comp_id, comp_data in self.parsed_data['components'].items():
            if 'alias' in comp_data and comp_data['alias']:
                alias_to_id[comp_data['alias']] = comp_id
            if 'name' in comp_data and comp_data['name']:
                name_to_id[comp_data['name']] = comp_id
                # Dodaj warianty nazw bez cudzysłowów
                clean_name = comp_data['name'].strip('"[]')
                if clean_name != comp_data['name']:
                    name_to_id[clean_name] = comp_id
        
        # KRYTYCZNA ZMIANA: Dodaj debugowanie mapowań
        log_debug(f"Mapowanie nazw elementów: {name_to_id}")
        log_debug(f"Mapowanie aliasów elementów: {alias_to_id}")
        
        # Przetwarzanie relacji
        for relation in relationships:
            relation_id = relation.get('id')
            relation_type = relation.get('type', 'relationship')
            source_id = None
            target_id = None
            source_xmi_id = None
            target_xmi_id = None
            
            # Pobierz identyfikatory źródła i celu relacji
            source_ref = relation.get('source')
            target_ref = relation.get('target')
            
            # KRYTYCZNA ZMIANA: Dodaj więcej szczegółów do logowania
            log_debug(f"Przetwarzanie relacji: {source_ref} -> {target_ref} (ID: {relation_id})")
            log_debug(f"  Relacja typu: {relation_type}")
            
            # 1. Sprawdź bezpośrednie ID z relacji (POPRAWKA: wyraźnie przypisz source_id/target_id)
            if 'source_id' in relation and relation['source_id']:
                source_id = relation['source_id']
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Bezpośrednie source_id: {source_id} -> xmi_id: {source_xmi_id}")
            
            if 'target_id' in relation and relation['target_id']:
                target_id = relation['target_id']
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Bezpośrednie target_id: {target_id} -> xmi_id: {target_xmi_id}")
            
            # NOWA POPRAWKA: Szukaj dokładnych nazw w surowej postaci
            if not source_id and source_ref in self.parsed_data['components']:
                source_id = source_ref
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source jako bezpośredni ID komponentu: {source_id} -> {source_xmi_id}")
                
            if not target_id and target_ref in self.parsed_data['components']:
                target_id = target_ref
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target jako bezpośredni ID komponentu: {target_id} -> {target_xmi_id}")
            
            # 2. Szukaj przez alias (POPRAWKA: dodaj debugowanie)
            if not source_id and source_ref in alias_to_id:
                source_id = alias_to_id[source_ref]
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source przez alias: {source_ref} -> {source_id} -> xmi_id: {source_xmi_id}")
                
            if not target_id and target_ref in alias_to_id:
                target_id = alias_to_id[target_ref]
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target przez alias: {target_ref} -> {target_id} -> xmi_id: {target_xmi_id}")
            
            # 3. Szukaj przez nazwę (POPRAWKA: dodaj debugowanie)
            if not source_id and source_ref in name_to_id:
                source_id = name_to_id[source_ref]
                source_xmi_id = self.parser_id_to_xmi_id.get(source_id)
                log_debug(f"  Znaleziono source przez nazwę: {source_ref} -> {source_id} -> xmi_id: {source_xmi_id}")
                
            if not target_id and target_ref in name_to_id:
                target_id = name_to_id[target_ref]
                target_xmi_id = self.parser_id_to_xmi_id.get(target_id)
                log_debug(f"  Znaleziono target przez nazwę: {target_ref} -> {target_id} -> xmi_id: {target_xmi_id}")
            
            # Jeśli nadal nie znaleziono obu końców relacji, pomijamy ją
            if not source_xmi_id or not target_xmi_id:
                log_warning(f"Nie udało się znaleźć elementów relacji: {source_ref} -> {target_ref}")
                if not source_xmi_id:
                    log_warning(f"  Nie znaleziono elementu źródłowego: {source_ref}")
                if not target_xmi_id:
                    log_warning(f"  Nie znaleziono elementu docelowego: {target_ref}")
                continue
            
            # Utwórz relację (pozostała część funkcji bez zmian)
            label = relation.get('label', '')
            relation_style = relation.get('relation_type', '-->')
            
            if relation_type == 'c4_relationship':
                xmi_id = self._add_c4_relationship(parent_element, source_xmi_id, target_xmi_id, relation)
            else:
                xmi_id = self._add_relationship(parent_element, source_xmi_id, target_xmi_id, label, relation_style)
            
            # Zapisz mapowanie ID
            if relation_id:
                self.parser_id_to_xmi_id[relation_id] = xmi_id
            
            # Dodaj do listy relacji
            self.relationships.append({
                'id': xmi_id,
                'source_id': source_xmi_id,
                'target_id': target_xmi_id,
                'label': label,
                'type': relation_type
            })
            
            log_debug(f"  ✅ Dodano relację: {source_ref} ({source_xmi_id}) -> {target_ref} ({target_xmi_id})")
    
    def _add_relationship(self, parent_element, source_id, target_id, label, style):
        """Dodaje standardową relację UML do modelu."""
        relationship_id = self._generate_ea_id("EAID")
        
        # Określ typ relacji na podstawie stylu
        if style == '-->' or style == '->':
            # Standardowa zależność
            dependency = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Dependency',
                'xmi:id': relationship_id,
                'supplier': target_id,
                'client': source_id,
                'visibility': 'public'
            })
            
            if label:
                dependency.set('name', label)
            
            self.id_map[relationship_id] = dependency
        elif style == '--|>' or style == '-|>':
            # Generalizacja
            generalization = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Generalization',
                'xmi:id': relationship_id,
                'general': target_id,
                'specific': source_id,
                'visibility': 'public'
            })
            
            if label:
                generalization.set('name', label)
            
            self.id_map[relationship_id] = generalization
        else:
            # Inne typy relacji jako zależności ze stereotypem
            dependency = ET.SubElement(parent_element, 'packagedElement', {
                'xmi:type': 'uml:Dependency',
                'xmi:id': relationship_id,
                'supplier': target_id,
                'client': source_id,
                'visibility': 'public'
            })
            
            if label:
                dependency.set('name', label)
            
            # Dodaj stereotyp na podstawie stylu
            if style == '<-->' or style == '<->':
                ET.SubElement(dependency, 'stereotype', {'name': 'bidirectional'})
            elif style == '..>' or style == '.>':
                ET.SubElement(dependency, 'stereotype', {'name': 'use'})
            elif style == '*--' or style == '*-':
                ET.SubElement(dependency, 'stereotype', {'name': 'composition'})
            elif style == 'o--' or style == 'o-':
                ET.SubElement(dependency, 'stereotype', {'name': 'aggregation'})
            
            self.id_map[relationship_id] = dependency
        
        return relationship_id
    
    def _add_c4_relationship(self, parent_element, source_id, target_id, relation_data):
        """Dodaje relację C4 do modelu."""
        relationship_id = self._generate_ea_id("EAID")
        
        # C4 relacje są implementowane jako zależności ze stereotypem
        dependency = ET.SubElement(parent_element, 'packagedElement', {
            'xmi:type': 'uml:Dependency',
            'xmi:id': relationship_id,
            'supplier': target_id,
            'client': source_id,
            'visibility': 'public'
        })
        
        # Dodaj etykietę
        label = relation_data.get('label', '')
        if label:
            dependency.set('name', label)
        
        # Dodaj stereotyp "C4"
        ET.SubElement(dependency, 'stereotype', {'name': 'C4'})
        
        # Dodaj technologię jako taggedValue
        technology = relation_data.get('technology', '')
        if technology:
            tech_tag = ET.SubElement(dependency, 'taggedValue', {'name': 'technology'})
            tech_tag.text = technology
        
        # Dodaj kierunek jako taggedValue
        direction = relation_data.get('direction', '')
        if direction:
            dir_tag = ET.SubElement(dependency, 'taggedValue', {'name': 'direction'})
            dir_tag.text = direction
        
        self.id_map[relationship_id] = dependency
        
        return relationship_id
    
    def _process_notes(self, parent_element, notes):
        """Przetwarza notatki z parsera PlantUML."""
        for note in notes:
            note_content = note.get('content', '')
            note_position = note.get('position', 'right')
            note_target_id = note.get('target_id')
            parser_id = note.get('id')
            
            # Sprawdź, czy mamy mapowanie ID z parsera na XMI
            target_xmi_id = None
            if note_target_id:
                target_xmi_id = self.parser_id_to_xmi_id.get(note_target_id)
            
            # Utwórz element komentarza
            xmi_id = self._generate_ea_id("EAID")
            comment = ET.SubElement(parent_element, 'ownedComment', {
                'xmi:type': 'uml:Comment',
                'xmi:id': xmi_id,
                'visibility': 'public'
            })
            
            # Dodaj treść komentarza
            body = ET.SubElement(comment, 'body')
            body.text = note_content
            
            # Powiąż komentarz z elementem docelowym
            if target_xmi_id:
                ET.SubElement(comment, 'annotatedElement', {'xmi:idref': target_xmi_id})
            
            # Zapisz referencję do ID
            self.id_map[xmi_id] = comment
            
            # Zapisz mapowanie ID
            if parser_id:
                self.parser_id_to_xmi_id[parser_id] = xmi_id
            
            # Dodaj do listy obiektów diagramu
            self.diagram_objects.append({
                'id': xmi_id,
                'type': 'Note',
                'name': note_content[:30] + ('...' if len(note_content) > 30 else ''),
                'position': note_position,
                'target_id': target_xmi_id
            })
            
            if self.debug_options.get('processing', False):
                print(f"📝 Przetworzono notatkę: {note_content[:30]}...")
                log_debug(f"📝 Przetworzono notatkę: {note_content[:30]}...")
    
    def _verify_diagram_consistency(self):
        """Weryfikuje spójność wygenerowanego diagramu."""
        # Sprawdź relacje bez elementów źródłowych lub docelowych
        for relation in self.relationships:
            source_id = relation['source_id']
            target_id = relation['target_id']
            
            if source_id not in self.id_map:
                log_warning(f"Relacja {relation['id']} ma nieistniejący element źródłowy: {source_id}")
            
            if target_id not in self.id_map:
                log_warning(f"Relacja {relation['id']} ma nieistniejący element docelowy: {target_id}")
    
    def _create_ea_extensions(self, root: ET.Element, diagram_name: str):
        """Dodaje rozszerzenia specyficzne dla Enterprise Architect."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. Dodaj sekcję profili (NOWA)
        self._create_profiles_section(root)
        
        # 2. Dodaj pozostałe sekcje
        extension = ET.SubElement(root, ET.QName(self.ns['xmi'], 'Extension'), {
            'extender': 'Enterprise Architect', 'extenderID': '6.5'
        })
        
        # POPRAWIONA KOLEJNOŚĆ:
        self._create_elements_section(extension, diagram_name, current_time)
        self._create_diagrams_section(extension, diagram_name, current_time)  
        self._create_connectors_section(extension) 
        
        # Debug - pokaż listę obiektów diagramu
        self._debug_diagram_objects()
    
    def _create_profiles_section(self, root: ET.Element):
        """Tworzy sekcję z profilami UML dla stereotypów."""
        # Twórz sekcję profili
        profiles = ET.SubElement(root, 'profiles')
        
        # 1. Standardowy profil L2 (dla stereotypu service)
        std_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_D8F4E180_BED4_4e61_B22D_45F371A2009C',
            'profiletype': 'uml2',
            'name': 'StandardProfileL2',
            'metamodelReference': 'uml2metamodel'
        })
    
        # Dodaj element Service
        service_element = ET.SubElement(std_profile, 'packagedElement', {
            'xmi:type': 'uml:Stereotype',
            'xmi:id': 'EAID_E8EB7F24_9586_429a_A543_5B9AA9CB786B',
            'name': 'Service',
            'visibility': 'public'
        })
        
        # 2. Profil niestandardowy (dla pozostałych stereotypów)
        custom_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_EC27B841_1486_494e_B760_1860478BF8F5',
            'profiletype': 'ea_uml2',
            'name': 'thecustomprofile',
            'metamodelReference': 'uml2metamodel'
        })
        
        # Dodaj definicje stereotypów
        stereotype_definitions = {
            'controller': 'EAID_3F786850_E47F_11D2_ABF0_00A0C90FFFC3',
            'gateway': 'EAID_C4F252E8_E947_11D2_ABF1_00A0C90FFFC8',
            'utility': 'EAID_D8C0A0A0_E947_11D2_ABF2_00A0C90FFFC9',
            'facade': 'EAID_F0C034E0_E947_11D2_ABF3_00A0C90FFFCA',
            'repository': 'EAID_08C0A0A0_E947_11D2_ABF4_00A0C90FFFCB',
            'database': 'EAID_DB9EAC10_E947_11D2_ABF5_00A0C90FFFD0'
        }
        
        for stereotype_name, stereotype_id in stereotype_definitions.items():
            stereotype_element = ET.SubElement(custom_profile, 'packagedElement', {
                'xmi:type': 'uml:Stereotype',
                'xmi:id': stereotype_id,
                'name': stereotype_name,
                'visibility': 'public'
            })
        
        # 3. Profil SOMF (dla stereotypu repository)
        somf_profile = ET.SubElement(profiles, 'uml:Profile', {
            'xmi:version': '2.1',
            'xmlns:uml': 'http://schema.omg.org/spec/UML/2.1',
            'xmi:id': 'EAPK_A3DDA574_A47C_4d73_9C42_F7EA2C5ACD8D',
            'profiletype': 'uml2',
            'name': 'SOMF',
            'metamodelReference': 'uml2metamodel'
        })
        
        repository_element = ET.SubElement(somf_profile, 'packagedElement', {
            'xmi:type': 'uml:Stereotype',
            'xmi:id': 'EAID_F1C0F34E_F947_11D2_ABF4_00A0C90FFFCC',
            'name': 'repository',
            'visibility': 'public'
        })

    def _create_elements_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję elements z definicjami elementów dla EA."""
        elements = ET.SubElement(extension, 'elements')
        
        # Dodaj główny pakiet
        package_element = ET.SubElement(elements, 'element', {
            'xmi:idref': self.package_id,
            'xmi:type': 'uml:Package',
            'name': diagram_name,
            'scope': 'public'
        })
        
        # Dodaj model dla pakietu
        ET.SubElement(package_element, 'model', {
            'package2': f"EAID_{self.package_id.split('_')[1]}", 
            'package': "EAPK_25CB1803_12A5_47b7_BF59_0C80F57AA528",  # Stała wartość
            'tpos': '0',
            'ea_localid': self._get_local_id(self.package_id),
            'ea_eleType': 'package'
        })
        
        # Dodaj properties dla pakietu
        ET.SubElement(package_element, 'properties', {
            'isSpecification': 'false',
            'sType': 'Package',
            'nType': '7',
            'scope': 'public'
        })
        
        # Dodaj project info
        ET.SubElement(package_element, 'project', {
            'author': self.author,
            'version': '1.0',
            'phase': '1.0',
            'created': current_time,
            'modified': current_time
        })
        
        # Zbuduj mapowanie pakiet -> komponenty dla sekcji element
        package_to_components = {}
        
        # Dodaj elementy diagramu
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id')
                obj_type = obj.get('type', 'Component')
                obj_name = obj.get('name', '')
                
                if obj_id in self.id_map:
                    # Znajdź element pakietu, w którym znajduje się ten komponent
                    parent_pkg = None
                    
                    # Sprawdź, czy to komponent przypisany do pakietu
                    for component_id, component_data in self.parsed_data['components'].items():
                        if self.parser_id_to_xmi_id.get(component_id) == obj_id:
                            package_id = component_data.get('package')
                            if package_id:
                                parent_pkg = self.parser_id_to_xmi_id.get(package_id)
                                # Dodaj do mapowania
                                if parent_pkg not in package_to_components:
                                    package_to_components[parent_pkg] = []
                                package_to_components[parent_pkg].append(obj_id)
                                break
                    
                    element = ET.SubElement(elements, 'element', {
                        'xmi:idref': obj_id,
                        'xmi:type': f"uml:{obj_type}",
                        'name': obj_name,
                        'scope': 'public'
                    })
                    
                    # Dodaj model dla elementu - wskazując na pakiet, jeśli istnieje
                    model_attrs = {
                        'tpos': '0',
                        'ea_localid': self._get_local_id(obj_id),
                        'ea_eleType': 'element'
                    }
                    
                    # Ustaw pakiet nadrzędny dla komponentu (w sekcji elements)
                    if parent_pkg:
                        model_attrs['package'] = parent_pkg
                    else:
                        model_attrs['package'] = self.package_id
                    
                    ET.SubElement(element, 'model', model_attrs)
                    
                    # Dodaj properties dla elementu
                    properties_attrs = {
                        'isSpecification': 'false',
                        'sType': obj_type,
                        'nType': self._get_ntype_for_element_type(obj_type),
                        'scope': 'public'
                    }

                    if obj_type in ('Component', 'Interface') and hasattr(self, 'component_stereotypes'):
                        stereotype = self.component_stereotypes.get(obj_id)
                        if stereotype:
                            guid = self._get_stereotype_guid(stereotype)
                            properties_attrs['stereotype'] = stereotype
                            if guid:
                                properties_attrs['stereotypeGUID'] = guid
                                element.set('stereotypeGUID', guid)
                            element.set('stereotype', stereotype)

                    ET.SubElement(element, 'properties', properties_attrs)
                    
                    # Dodaj informację o pakiecie w extendedProperties
                    if parent_pkg:
                        # Znajdź nazwę pakietu
                        pkg_name = ""
                        for pkg_id, pkg_data in self.parsed_data['packages'].items():
                            if self.parser_id_to_xmi_id.get(pkg_id) == parent_pkg:
                                pkg_name = pkg_data.get('name', '')
                                break
                        
                        if pkg_name:
                            extended = ET.SubElement(element, 'extendedProperties')
                            extended.set('package_name', pkg_name)
    
    def _get_ntype_for_element_type(self, element_type):
        """Zwraca odpowiedni nType dla danego typu elementu w EA."""
        ntype_map = {
            'Component': '4',
            'Interface': '5',
            'Package': '7',
            'Boundary': '10',
            'Note': '19',
            'Actor': '1'
        }
        return ntype_map.get(element_type, '4')  # Domyślnie Component

    def _get_stereotype_guid(self, stereotype: str) -> Optional[str]:
        """Zwraca GUID stereotypu wykorzystywany przez EA."""
        return self.stereotype_guid_map.get(stereotype)

    def _map_kind_to_element_class(self, kind: str) -> str:
        mapping = {
            'interface': 'Interface',
            'actor': 'Actor',
            'note': 'Note'
        }
        return mapping.get(kind, 'Component')
    
    def _create_connectors_section(self, extension: ET.Element):
        """Tworzy sekcję connectors z definicjami relacji dla EA."""
        connectors = ET.SubElement(extension, 'connectors')
        
        if self.debug_options.get('relationships', False):
            print(f"Tworzenie sekcji connectors dla {len(self.relationships)} relacji")
            log_debug(f"Tworzenie sekcji connectors dla {len(self.relationships)} relacji")
        
        added_connectors = 0
        
        for i, relation in enumerate(self.relationships):
            relation_id = relation['id']
            source_id = relation['source_id']
            target_id = relation['target_id']
            label = relation['label']
            relation_type = relation['type']
            
            # Upewnij się, że elementy źródłowe i docelowe istnieją
            if source_id not in self.id_map or target_id not in self.id_map:
                if self.debug_options.get('relationships', False):
                    log_warning(f"Pomijam relację {relation_id}: brak elementów w id_map")
                continue
            
            connector = ET.SubElement(connectors, 'connector', {
                'xmi:idref': relation_id
            })
            
            # SOURCE (element źródłowy)
            source = ET.SubElement(connector, 'source', {
                'xmi:idref': source_id
            })
            
            # Dodaj model dla źródła
            source_element = self.id_map[source_id]
            source_name = source_element.get('name', '')
            source_type = self._get_element_type(source_element)
            
            ET.SubElement(source, 'model', {
                'ea_localid': self._get_local_id(source_id),
                'type': source_type,
                'name': source_name
            })
            
            # Dodaj role i pozostałe atrybuty
            ET.SubElement(source, 'role', {'visibility': 'Public'})
            ET.SubElement(source, 'type', {'aggregation': 'none'})
            ET.SubElement(source, 'constraints')
            ET.SubElement(source, 'modifiers', {'isNavigable': 'false'})
            
            # TARGET (element docelowy)
            target = ET.SubElement(connector, 'target', {
                'xmi:idref': target_id
            })
            
            # Dodaj model dla celu
            target_element = self.id_map[target_id]
            target_name = target_element.get('name', '')
            target_type = self._get_element_type(target_element)
            
            ET.SubElement(target, 'model', {
                'ea_localid': self._get_local_id(target_id),
                'type': target_type,
                'name': target_name
            })
            
            # Dodaj role i pozostałe atrybuty
            ET.SubElement(target, 'role', {'visibility': 'Public'})
            ET.SubElement(target, 'type', {'aggregation': 'none'})
            ET.SubElement(target, 'constraints')
            ET.SubElement(target, 'modifiers', {'isNavigable': 'true'})
            
            # PROPERTIES (właściwości relacji)
            ea_type = self._get_connector_type(relation_type)
            properties_attrs = {
                'ea_type': ea_type,
                'direction': 'Source -> Destination'
            }
            
            if label:
                properties_attrs['name'] = label
            
            ET.SubElement(connector, 'properties', properties_attrs)
            
            # Dodaj dokumentację
            ET.SubElement(connector, 'documentation')
            
            # Dodaj appearance - wygląd relacji
            ET.SubElement(connector, 'appearance', {
                'linemode': '1',
                'linecolor': '-1',
                'linewidth': '1',
                'seqno': str(i),
                'headStyle': '0',
                'lineStyle': '0'
            })

            added_connectors += 1

        if self.debug_options.get('relationships', False):
            print(f"Dodano {added_connectors} connectors z {len(self.relationships)} relacji")
            log_debug(f"Dodano {added_connectors} connectors z {len(self.relationships)} relacji")

    
    def _get_connector_type(self, relation_type):
        """Zwraca typ konektora EA na podstawie typu relacji."""
        connector_types = {
            'c4_relationship': 'Dependency',
            'relationship': 'Dependency',
            'dependency': 'Dependency',
            'generalization': 'Generalization',
            'realization': 'Realisation',
            'composition': 'Composition',
            'aggregation': 'Aggregation'
        }
        return connector_types.get(relation_type, 'Dependency')
    
    def _get_element_type(self, element):
        """Zwraca typ elementu EA na podstawie elementu XML."""
        element_type = element.get('xmi:type', '')
        
        if element_type == 'uml:Component':
            return 'Component'
        elif element_type == 'uml:Interface':
            return 'Interface'
        elif element_type == 'uml:Package':
            return 'Package'
        elif element_type == 'uml:Actor':
            return 'Actor'
        elif element_type == 'uml:Comment':
            return 'Note'
        else:
            return 'Class'  # Domyślny typ
    
    def _create_diagrams_section(self, extension: ET.Element, diagram_name: str, current_time: str):
        """Tworzy sekcję diagrams z definicją diagramu dla EA."""
        component_seq = 100
        diagrams = ET.SubElement(extension, 'diagrams')
        diagram = ET.SubElement(diagrams, 'diagram', {
            'xmi:id': self.diagram_id,
            'name': diagram_name,
            'type': 'Component',
            'diagramType': 'ComponentDiagram'
        })
        
        # Model diagramu
        ET.SubElement(diagram, 'model', {
            'package': self.package_id,
            'localID': self._get_local_id(self.diagram_id),
            'owner': self.package_id
        })
        
        # Properties diagramu
        ET.SubElement(diagram, 'properties', {
            'name': diagram_name,
            'type': 'Component'
        })
        
        # Project info
        ET.SubElement(diagram, 'project', {
            'author': self.author,
            'version': '1.0',
            'created': current_time,
            'modified': current_time
        })
        
        # Style diagramu
        ET.SubElement(diagram, 'style1', {'value': (
            'ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;'
            'Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;'
            'ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=795;DocSize.cy=1134;'
            'ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;'
            'VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;'
            'HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;'
            'HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;'
            'ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;'
            'ShowShape=1;'
        )})
        
        # Dodaj flagę diagnostyczną
        enable_position_diagnostics = True
        position_log = []
        
        def log_position_info(message):
            """Funkcja pomocnicza do logowania informacji o pozycjach elementów"""
            if enable_position_diagnostics:
                position_log.append(message)
                if self.debug_options.get('positioning', False):
                    print(f"📊 {message}")
                    log_debug(f"📊 {message}")
        
        log_position_info(f"Rozpoczęto rozmieszczanie elementów dla diagramu '{diagram_name}'")

        elements = ET.SubElement(diagram, 'elements')

        title_id = self._generate_ea_id("EAID")
        title_position = "Left=100;Top=20;Right=900;Bottom=70;"

        ET.SubElement(elements, 'element', {
            'subject': title_id,
            'seqno': "1",
            'geometry': title_position,
            'style': "DUID=unique_id;BorderColor=-1;BorderWidth=0;BackColor=-1;",
            'elementclass': 'Text'
        })

        self.added_to_diagram = set()

        layout_manager = LayoutManager(self, log_position_info)
        layout_data = layout_manager.layout()

        diagram_obj_map = {
            obj['id']: obj for obj in self.diagram_objects if isinstance(obj, dict) and obj.get('id')
        }

        boundary_ids = {obj_id for obj_id, info in diagram_obj_map.items() if info.get('is_frame_boundary')}
        layer_visual_ids = {obj_id for obj_id, info in diagram_obj_map.items() if info.get('is_layer_visual')}

        boundary_seq = 900000
        layer_seq = 200000
        package_seq = 500000
        for pkg in layout_data['packages']:
            xmi_id = pkg.get('xmi_id')
            if not xmi_id:
                continue

            package_name = pkg.get('name', 'Package')
            package_type = pkg.get('package_type', 'package')
            element_class = pkg.get('element_class') or ('Boundary' if package_type == 'c4_boundary' else 'Package')
            if element_class == 'Component':
                style = self._get_layer_style(package_name) + 'stereotype=layer;'
            elif element_class == 'Boundary':
                style = 'DUID=unique_id;BorderColor=-1;BorderWidth=2;BackColor=-1;'
            elif element_class == 'Package':
                style = self._get_layer_style(package_name)
            else:
                style = self._get_layer_style(package_name)

            if element_class == 'Boundary' or xmi_id in boundary_ids:
                seqno = str(boundary_seq)
                boundary_seq += 1
            elif xmi_id in layer_visual_ids:
                seqno = str(layer_seq)
                layer_seq += 1
            else:
                seqno = str(package_seq)
                package_seq += 1

            ET.SubElement(elements, 'element', {
                'subject': xmi_id,
                'seqno': seqno,
                'geometry': pkg.get('geometry', ''),
                'style': style,
                'elementclass': element_class
            })

            self.added_to_diagram.add(xmi_id)

        component_seq = 100
        for element in layout_data['elements']:
            xmi_id = element.get('xmi_id')
            if not xmi_id or xmi_id in self.added_to_diagram:
                continue

            geometry = element.get('geometry', '')
            parser_id = element.get('parser_id')
            kind = element.get('kind', 'component')

            obj_info = diagram_obj_map.get(xmi_id, {})
            element_class = obj_info.get('type') or self._map_kind_to_element_class(kind)

            style = "DUID=unique_id;"
            if element_class in ['Component', 'Interface']:
                comp_data = self.parsed_data['components'].get(parser_id, {})
                stereotype_style = self._get_stereotype_style(comp_data.get('stereotype', ''))
                if stereotype_style:
                    style += stereotype_style
            elif element_class == 'Note':
                style += "BorderColor=-1;BorderWidth=1;BackColor=-1;"
            elif element_class == 'Actor':
                style += "BorderColor=-1;BorderWidth=1;"

            ET.SubElement(elements, 'element', {
                'subject': xmi_id,
                'seqno': str(component_seq),
                'geometry': geometry,
                'style': style,
                'elementclass': element_class
            })

            self.added_to_diagram.add(xmi_id)
            component_seq += 1

        log_position_info("\nPODSUMOWANIE DIAGNOSTYKI")
        log_position_info(f"Pakiety umieszczone na diagramie: {len(layout_data['packages'])}")
        log_position_info(f"Elementy umieszczone na diagramie: {len(layout_data['elements'])}")

        if enable_position_diagnostics:
            try:
                log_file_name = f"position_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file_name, 'w', encoding='utf-8') as f:
                    f.write(f"Diagnostyka pozycji elementów dla diagramu '{diagram_name}'\n")
                    f.write(f"Data wygenerowania: {current_time}\n\n")
                    for log_entry in position_log:
                        f.write(f"{log_entry}\n")
                print(f"\nZapisano diagnostykę pozycji do pliku: {log_file_name}")
                log_info(f"Zapisano diagnostykę pozycji do pliku: {log_file_name}")
            except Exception as e:
                print(f"Błąd podczas zapisywania pliku diagnostycznego: {e}")
                log_error(f"Błąd podczas zapisywania pliku diagnostycznego: {e}")

        diagramlinks = ET.SubElement(diagram, 'diagramlinks')
        diagramlinks = ET.SubElement(diagram, 'diagramlinks')
        
        log_position_info(f"Przetwarzanie {len(self.relationships)} relacji dla diagramlinks")
        added_links = 0

        for relation in self.relationships:
            relation_id = relation['id']
            source_id = relation['source_id']
            target_id = relation['target_id']
            
            # Pomiń relacje bez prawidłowych ID źródła lub celu
            if source_id not in self.id_map or target_id not in self.id_map:
                log_position_info(f"  Pomijam relację {relation_id}: brak elementów w id_map")
                continue
            
            # KRYTYCZNA POPRAWKA: Sprawdź czy oba końce relacji są na diagramie
            if source_id not in self.added_to_diagram or target_id not in self.added_to_diagram:
                log_position_info(f"  Pomijam relację {relation_id}: elementy nie są na diagramie")
                continue
            
            # Generuj unikalny linkID dla diagramlink
            link_uuid = f"DCLINK_{uuid.uuid4().hex[:8].upper()}"
            
            diagramlink = ET.SubElement(diagramlinks, 'diagramlink', {
                'connectorID': relation_id,
                'start': source_id,
                'end': target_id,
                'linkID': link_uuid,
                'hidden': '0',
                'geometry': 'EDGE=1;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path=;'
            })
            
            added_links += 1
            log_position_info(f"  ✅ Dodano diagramlink: {source_id} -> {target_id}")

        log_position_info(f"Dodano {added_links} relacji do diagramu z {len(self.relationships)} istniejących")
        log_debug(f"self.added_to_diagram zawiera {len(self.added_to_diagram)} elementów")
        for elem_id in self.added_to_diagram:
            log_debug(f"  - {elem_id}")
    
    def _get_stereotype_style(self, stereotype):
        """Zwraca styl dla danego stereotypu."""
        if not stereotype:
            return ""
        
        # Stereotyp musi być jawnie podany w stylu
        style = f"stereotype={stereotype};"
        
        # Dodaj również kolor na podstawie stereotypu
        if stereotype == 'controller':
            style += "BackColor=-1249301;"
        elif stereotype == 'service':
            style += "BackColor=-3342357;"
        elif stereotype == 'repository':
            style += "BackColor=-1120106;"
        elif stereotype == 'facade':
            style += "BackColor=-6357;"
        elif stereotype == 'utility':
            style += "BackColor=-8355732;"
        elif stereotype == 'gateway':
            style += "BackColor=-16711681;"
        elif stereotype == 'database':
            style += "BackColor=-13421824;"
        
        return style

    def _get_layer_style(self, layer_name):
        """Zwraca styl dla pakietu warstwy z odpowiednim kolorem tła."""
        # Zamiast sztywno przypisanych kolorów, generuj kolor na podstawie nazwy
        name_hash = hash(layer_name) % 6  # Używamy tylko 6 podstawowych kolorów
        
        layer_colors = [
            "BackColor=-1249281;",  # Jasnoniebieski
            "BackColor=-3342337;",  # Jasnozielony
            "BackColor=-1120086;",  # Jasnopomarańczowy
            "BackColor=-6337;",     # Jasnofioletowy
            "BackColor=-5111808;",  # Czerwonawy
            "BackColor=-8355712;"   # Szary
        ]
        
        base_style = "DUID=unique_id;BorderColor=-1;BorderWidth=1;"
        return base_style + layer_colors[name_hash]

    def _get_local_id(self, obj_id):
        """Generuje lokalny identyfikator dla Enterprise Architect na podstawie ID elementu."""
        if not hasattr(self, '_local_id_counter'):
            self._local_id_counter = 1
        
        if not hasattr(self, '_local_id_map'):
            self._local_id_map = {}
        
        if obj_id not in self._local_id_map:
            self._local_id_map[obj_id] = str(self._local_id_counter)
            self._local_id_counter += 1
        
        return self._local_id_map[obj_id]
    
    def _debug_diagram_objects(self):
        """Wyświetla informacje o elementach dodanych do diagramu."""
        if not self.debug_options.get('elements', False):
            return
            
        print(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        log_debug(f"\n--- Elementy diagramu ({len(self.diagram_objects)}) ---")
        
        for obj in self.diagram_objects:
            if isinstance(obj, dict):
                obj_id = obj.get('id', 'brak ID')
                obj_type = obj.get('type', 'nieznany typ')
                obj_name = obj.get('name', '')
                print(f" - {obj_type}: {obj_name} ({obj_id[-6:]})")
                log_debug(f" - {obj_type}: {obj_name} ({obj_id[-6:]})")
            else:
                print(f" - {obj}")
                log_debug(f" - {obj}")
    
    def _format_xml(self, root: ET.Element) -> str:
        """Poprawia nagłówek i formatuje XML do czytelnej postaci."""
        # Zastosuj sanityzację do całego drzewa XML rekurencyjnie
        self._sanitize_tree(root)
        
        xml_string = ET.tostring(root, encoding='unicode', method='xml', xml_declaration=True)
        xml_string_fixed = xml_string.replace("<?xml version='1.0' encoding='unicode'?>", '<?xml version="1.0" encoding="UTF-8"?>')
        dom = xml.dom.minidom.parseString(xml_string_fixed)
        return dom.toprettyxml(indent="  ")
    
    def _sanitize_tree(self, element):
        """Sanityzuje wszystkie atrybuty w całym drzewie XML rekurencyjnie."""
        # Sanityzuj atrybuty bieżącego elementu
        for key, value in list(element.attrib.items()):
            if value is None:
                element.attrib[key] = ""
            elif isinstance(value, bool):
                element.attrib[key] = 'true' if value else 'false'
        
        # Sanityzuj wszystkie elementy potomne
        for child in element:
            self._sanitize_tree(child)

# --- Przykład użycia ---
if __name__ == '__main__':
    import argparse
    import os
    from utils.plantuml.plantuml_component_parser import PlantUMLComponentParser
    from datetime import datetime
    
    setup_logger('xmi_component_generator.log')
    
    # Utworzenie parsera argumentów z bezpośrednią obsługą plików PlantUML
    parser = argparse.ArgumentParser(description='Generator XMI dla diagramów komponentów')
    parser.add_argument('input_file', nargs='?', default='Diagram komponentów_20250726_085243.puml',
                        help='Plik wejściowy z kodem PlantUML')
    parser.add_argument('--output', '-o', 
                        help='Plik wyjściowy XMI (domyślnie: diagram_komponentow_[timestamp].xmi)')
    
    # Opcje parsowania PlantUML
    parser.add_argument('--parse-debug', '-pd', action='store_true', 
                        help='Włącz debugowanie parsowania')
    parser.add_argument('--parse-relationships', '-pr', action='store_true', 
                        help='Włącz debugowanie relacji w parserze')
    parser.add_argument('--parse-structure', '-ps', action='store_true', 
                        help='Włącz debugowanie struktury w parserze')
    parser.add_argument('--parse-packages', '-pp', action='store_true', 
                        help='Włącz debugowanie pakietów w parserze')
    parser.add_argument('--parse-c4', '-pc4', action='store_true',
                        help='Włącz debugowanie elementów C4 w parserze')
    
    # Opcje generowania XMI
    parser.add_argument('--debug-positioning', '-dp', action='store_true', 
                        help='Włącz debugowanie pozycjonowania elementów')
    parser.add_argument('--debug-elements', '-de', action='store_true', 
                        help='Pokaż listę elementów diagramu')
    parser.add_argument('--debug-processing', '-dpr', action='store_true', 
                        help='Włącz szczegółowe śledzenie przetwarzania elementów')
    parser.add_argument('--debug-relationships', '-dr', action='store_true', 
                        help='Pokaż szczegóły tworzenia relacji')
    parser.add_argument('--debug-xml', '-dx', action='store_true', 
                        help='Włącz debugowanie struktury XML')
    parser.add_argument('--author', '-a', default='XMI Generator', 
                        help='Autor diagramu')
    
    # Parsowanie argumentów
    args = parser.parse_args()
    
    # Konfiguracja opcji debugowania parsera PlantUML
    parse_debug_options = {
        'parsing': args.parse_debug,
        'relationships': args.parse_relationships,
        'structure': args.parse_structure,
        'packages': args.parse_packages,
        'c4': args.parse_c4
    }
    
    # Konfiguracja opcji debugowania generatora XMI
    xmi_debug_options = {
        'positioning': args.debug_positioning,
        'elements': args.debug_elements,
        'processing': args.debug_processing,
        'relationships': args.debug_relationships,
        'xml': args.debug_xml
    }
    
    # Ustawienie nazwy pliku wyjściowego
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_file = args.output
    else:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        output_file = f'{base_name}_{timestamp}.xmi'
    
    try:
        print(f"Wczytywanie pliku PlantUML: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            plantuml_code = f.read()
            
        # Parsowanie diagramu PlantUML
        print("Parsowanie diagramu komponentów PlantUML...")
        parser = PlantUMLComponentParser(plantuml_code, parse_debug_options)
        parsed_data = parser.parse()
        
        # Generowanie XMI
        print("Generowanie XMI...")
        generator = XMIComponentGenerator(author=args.author, debug_options=xmi_debug_options)
        
        # Użyj tytułu diagramu jako nazwy, jeśli istnieje
        diagram_name = parsed_data.get('title', '') or os.path.splitext(os.path.basename(args.input_file))[0]
        xmi_content = generator.generate_component_diagram(diagram_name, parsed_data)
        
        # Zapisz XMI do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xmi_content)
        
        # Wyświetl statystyki
        components_count = len(parsed_data['components'])
        interfaces_count = len(parsed_data['interfaces'])
        packages_count = len(parsed_data['packages'])
        relationships_count = len(parsed_data['relationships'])
        
        print("\n=== Podsumowanie ===")
        log_info("=== Podsumowanie ===")
        print(f"Diagram komponentów: {diagram_name}")
        log_info(f"Diagram komponentów: {diagram_name}")
        print(f"Komponenty: {components_count}")
        log_info(f"Komponenty: {components_count}")
        print(f"Interfejsy: {interfaces_count}")
        log_info(f"Interfejsy: {interfaces_count}")
        print(f"Pakiety: {packages_count}")
        log_info(f"Pakiety: {packages_count}")
        print(f"Relacje: {relationships_count}")
        log_info(f"Relacje: {relationships_count}")
        
        if parsed_data.get('is_c4_diagram'):
            print("Wykryto elementy notacji C4")
            log_info("Wykryto elementy notacji C4")
        
        print(f"\nWygenerowano plik XMI: {output_file}")
        log_info(f"Wygenerowano plik XMI: {output_file}")
        
    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {args.input_file}")
        log_error(f"Nie znaleziono pliku: {args.input_file}")
        print("Podaj poprawną ścieżkę do pliku PlantUML.")
        log_info("Podaj poprawną ścieżkę do pliku PlantUML.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        log_exception(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
