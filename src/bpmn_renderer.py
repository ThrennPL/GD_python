"""
BPMN Renderer dla Streamlit - komponent do wyświetlania diagramów BPMN w przeglądarce
"""
import streamlit as st
import base64
from typing import Optional

def render_bpmn_diagram(bpmn_xml: str, height: int = 600, width: Optional[int] = None) -> None:
    """
    Renderuje diagram BPMN w Streamlit używając BPMN.js
    
    Args:
        bpmn_xml: XML procesu BPMN
        height: wysokość kontenera w pikselach
        width: szerokość kontenera w pikselach (domyślnie None = 100%)
    """
    if not bpmn_xml or not bpmn_xml.strip():
        st.error("Brak danych BPMN do wyświetlenia")
        return
    
    # Encode BPMN XML for safe embedding
    bpmn_encoded = base64.b64encode(bpmn_xml.encode('utf-8')).decode('utf-8')
    
    # HTML with BPMN.js viewer
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>BPMN Diagram</title>
        <script src="https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-navigated-viewer.development.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
                background: #f8f9fa;
            }}
            #canvas {{
                width: 100%;
                height: {height - 80}px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .error {{
                color: #dc3545;
                background: #f8d7da;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #f5c6cb;
                margin: 10px 0;
            }}
            .warning {{
                color: #856404;
                background: #fff3cd;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #ffeaa7;
                margin: 5px 0;
                font-size: 12px;
            }}
            .controls {{
                margin-bottom: 15px;
                text-align: center;
                background: white;
                padding: 10px;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .btn {{
                background: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                margin: 0 5px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 13px;
                transition: background 0.2s;
            }}
            .btn:hover {{
                background: #0056b3;
            }}
            .btn:active {{
                background: #004085;
            }}
            #status {{
                margin-top: 10px;
                font-size: 12px;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="warning">
            ⚠️ Diagram może zawierać niepoprawne połączenia między procesami. 
            BPMN v2 wymaga message flows między różnymi poolami.
        </div>
        
        <div class="controls">
            <button class="btn" onclick="zoomIn()">🔍+ Przybliż</button>
            <button class="btn" onclick="zoomOut()">🔍- Oddal</button>
            <button class="btn" onclick="zoomFit()">📐 Dopasuj</button>
            <button class="btn" onclick="zoomReset()">🏠 Reset</button>
            <button class="btn" onclick="downloadSVG()">💾 Pobierz SVG</button>
            <div id="status">Ładowanie diagramu...</div>
        </div>
        <div id="canvas"></div>
        
        <script>
            // Initialize BPMN viewer
            const viewer = new BpmnJS({{
                container: '#canvas'
            }});
            
            // Global viewer reference for controls
            window.bpmnViewer = viewer;
            
            // Status updates
            function updateStatus(message, isError = false) {{
                const status = document.getElementById('status');
                status.textContent = message;
                status.style.color = isError ? '#dc3545' : '#6c757d';
            }}
            
            // Decode and load BPMN
            const bpmnXML = atob('{bpmn_encoded}');
            
            async function loadDiagram() {{
                try {{
                    updateStatus('Ładowanie diagramu BPMN...');
                    
                    const result = await viewer.importXML(bpmnXML);
                    
                    // Check for warnings (cross-process flows, etc.)
                    if (result.warnings && result.warnings.length > 0) {{
                        console.warn('BPMN warnings:', result.warnings);
                        updateStatus(`Diagram załadowany z ostrzeżeniami ({{result.warnings.length}})`);
                    }} else {{
                        updateStatus('Diagram załadowany pomyślnie');
                    }}
                    
                    // Fit diagram to container
                    const canvas = viewer.get('canvas');
                    canvas.zoom('fit-viewport', 'auto');
                    
                    console.log('BPMN diagram loaded successfully');
                }} catch (err) {{
                    console.error('Error loading BPMN diagram:', err);
                    updateStatus('Błąd ładowania diagramu', true);
                    
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error';
                    errorDiv.innerHTML = `
                        <strong>Błąd ładowania diagramu BPMN:</strong><br>
                        ${{err.message || 'Nieznany błąd'}}<br>
                        <small>Sprawdź konsole przeglądarki dla szczegółów.</small>
                    `;
                    document.getElementById('canvas').appendChild(errorDiv);
                }}
            }}
            
            // Control functions
            function zoomIn() {{
                const canvas = window.bpmnViewer.get('canvas');
                const currentZoom = canvas.zoom();
                canvas.zoom(Math.min(currentZoom + 0.2, 3.0));
                updateStatus(`Zoom: ${{Math.round(canvas.zoom() * 100)}}%`);
            }}
            
            function zoomOut() {{
                const canvas = window.bpmnViewer.get('canvas');
                const currentZoom = canvas.zoom();
                canvas.zoom(Math.max(currentZoom - 0.2, 0.2));
                updateStatus(`Zoom: ${{Math.round(canvas.zoom() * 100)}}%`);
            }}
            
            function zoomFit() {{
                const canvas = window.bpmnViewer.get('canvas');
                canvas.zoom('fit-viewport', 'auto');
                updateStatus('Dopasowano do okna');
            }}
            
            function zoomReset() {{
                const canvas = window.bpmnViewer.get('canvas');
                canvas.zoom(1.0);
                updateStatus('Zoom: 100%');
            }}
            
            function downloadSVG() {{
                try {{
                    const canvas = window.bpmnViewer.get('canvas');
                    canvas.saveSVG({{ format: true }}).then(function(result) {{
                        const svgBlob = new Blob([result.svg], {{type: 'image/svg+xml'}});
                        const url = URL.createObjectURL(svgBlob);
                        
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = 'bpmn_diagram.svg';
                        link.click();
                        
                        URL.revokeObjectURL(url);
                        updateStatus('SVG pobrano');
                    }});
                }} catch (err) {{
                    updateStatus('Błąd pobierania SVG', true);
                }}
            }}
            
            // Load diagram on page load
            loadDiagram();
        </script>
    </body>
    </html>
    """
    
    # Display in Streamlit - pass width as int or None
    st.components.v1.html(html_content, height=height, width=width)


def render_bpmn_preview(bpmn_xml: str, show_xml: bool = True) -> None:
    """
    Renderuje podgląd BPMN z opcją wyświetlenia XML
    
    Args:
        bpmn_xml: XML procesu BPMN
        show_xml: czy pokazać XML w expander
    """
    
    st.subheader("📊 Diagram BPMN")
    
    if not bpmn_xml or not bpmn_xml.strip():
        st.warning("Brak wygenerowanego diagramu BPMN")
        return
    
    # Main diagram
    render_bpmn_diagram(bpmn_xml, height=500)
    
    # Optional XML view
    if show_xml:
        with st.expander("🔍 Podgląd BPMN XML", expanded=False):
            st.code(bpmn_xml, language="xml")
    
    # Download button
    st.download_button(
        label="📥 Pobierz BPMN XML",
        data=bpmn_xml,
        file_name=f"bpmn_process_{st.session_state.get('timestamp', 'export')}.bpmn",
        mime="application/xml",
        help="Pobierz diagram BPMN jako plik XML"
    )


def create_bpmn_viewer_component() -> str:
    """
    Tworzy standalone komponent BPMN viewer do użycia w innych miejscach
    
    Returns:
        HTML string z kompletnym viewer BPMN
    """
    return """
    <div id="bpmn-container" style="height: 400px; border: 1px solid #ccc;"></div>
    <script src="https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-navigated-viewer.development.js"></script>
    <script>
        function loadBPMNDiagram(xmlString) {
            const viewer = new BpmnJS({
                container: '#bpmn-container'
            });
            
            viewer.importXML(xmlString).then(() => {
                const canvas = viewer.get('canvas');
                canvas.zoom('fit-viewport', 'auto');
            }).catch(err => {
                console.error('Error loading BPMN:', err);
            });
        }
    </script>
    """


# Test function
def test_bpmn_renderer():
    """Test function z przykładowym BPMN"""
    sample_bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" 
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" 
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI" 
                  id="Definitions_1" 
                  targetNamespace="http://example.org/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>SequenceFlow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:userTask id="UserTask_1" name="User Task">
      <bpmn:incoming>SequenceFlow_1</bpmn:incoming>
      <bpmn:outgoing>SequenceFlow_2</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>SequenceFlow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="SequenceFlow_1" sourceRef="StartEvent_1" targetRef="UserTask_1"/>
    <bpmn:sequenceFlow id="SequenceFlow_2" sourceRef="UserTask_1" targetRef="EndEvent_1"/>
  </bpmn:process>
</bpmn:definitions>"""
    
    st.title("🧪 Test BPMN Renderer")
    render_bpmn_preview(sample_bpmn)


if __name__ == "__main__":
    test_bpmn_renderer()