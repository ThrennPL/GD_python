#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from complete_pipeline import BPMNv2Pipeline
from ai_integration import AIConfig, AIProvider
import json

# Create Gemini config with real API key
config = AIConfig(
    provider=AIProvider.GEMINI,
    model='models/gemini-2.0-flash',
    api_key='AIzaSyD3830DF1lqmwuGjsltt4MhBagLW8e8uoM',
    base_url='https://generativelanguage.googleapis.com/v1v1beta/chat/completions',
    temperature=0.7,
    max_tokens=4000,
    timeout=30
)

# Polish text from attachment - kredyt process
polish_text = """
**Opis procesu:**
Klient składa wniosek kredytowy wraz z dokumentami potwierdzającymi dochody. System automatycznie przeprowadza pre-scoring sprawdzając historię kredytową w BIK i wewnętrznych bazach banku. Jeśli scoring jest pozytywny, wniosek trafia do doradcy, który weryfikuje dokumenty i aktualizuje dane klienta.

Doradca przeprowadza wywiad kredytowy sprawdzając szczegóły finansowe i cel kredytu. Kompletny wniosek trafia do analityka kredytowego, który ocenia zdolność kredytową klienta kalkulując wskaźniki DTI (Debt-to-Income). 

W przypadku kwot powyżej 100 000 zł, wymagana jest dodatkowa akceptacja kierownika działu kredytów. Pozytywnie zweryfikowany wniosek trafia do komitetu kredytowego, który podejmuje ostateczną decyzję.

Po akceptacji klient otrzymuje ofertę kredytową z warunkami. Może ją zaakceptować, odrzucić lub negocjować warunki. Po podpisaniu umowy, środki są wypłacane na wskazany rachunek. Odrzucone wnioski są archiwizowane z uzasadnieniem decyzji.

**Uczestnicy:**
- Klient
- Doradca kredytowy
- Analityk kredytowy  
- Kierownik działu kredytów
- Komitet kredytowy
- System scoringowy
- BIK
- System core banking

**Regulacje:** Rekomendacja T, ustawa o kredycie konsumenckim, AML
"""

print('🏦 TEST PROCESU BANKOWEGO Z RZECZYWISTYM GEMINI')
print('='*60)

try:
    # Create pipeline
    pipeline = BPMNv2Pipeline(config)
    print('✅ Pipeline initialized with Gemini')
    
    # Generate BPMN using correct method
    result = pipeline.run_complete_pipeline(
        polish_text=polish_text,
        process_name='Proces Udzielania Kredytu Gotówkowego',
        context='banking'
    )
    
    if result['success']:
        print('\n🎉 SUKCES! BPMN wygenerowany z rzeczywistym AI!')
        print(f"📊 Confidence: {result['analysis']['confidence']}")
        print(f"🤖 Model: {result['ai_info']['model']}")
        print(f"💰 Tokens: {result['ai_info'].get('token_usage', 'N/A')}")
        print(f"📄 BPMN XML size: {len(result['bpmn_xml'])} chars")
        
        # Parse BPMN JSON for details
        bpmn_data = result['bpmn_json']
        print(f"👥 Participants: {len(bpmn_data.get('participants', []))}")
        print(f"🔧 Elements: {len(bpmn_data.get('elements', []))}")
        print(f"🔗 Flows: {len(bpmn_data.get('flows', []))}")
        
        # Save result for review
        with open('kredyt_gemini_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print('💾 Result saved to kredyt_gemini_result.json')
        
    else:
        print(f'❌ BPMN generation failed: {result.get("error", "Unknown error")}')
        
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()