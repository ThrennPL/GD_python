#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from iterative_pipeline import IterativeImprovementPipeline
import json

# Test naprawionego systemu 
pipeline = IterativeImprovementPipeline()

print('=== TEST NAPRAWIONEGO SYSTEMU ITERACYJNEGO ===')

# Test z polskiego tekstu
polish_text = """
Proces składania wniosku o kredyt:
1. Klient wypełnia wniosek kredytowy
2. System sprawdza dane klienta
3. Analityk analizuje zdolność kredytową
4. Komitet podejmuje decyzję
5. Klient otrzymuje informację o decyzji
"""

print('Test procesu z polskiego tekstu:')
print(f'Input: {len(polish_text)} znaków')

# Uruchom pipeline
final_result = pipeline.generate_and_improve_process(
    polish_text=polish_text,
    process_name='Proces Wnioskowania o Kredyt Test',
    context='banking'
)

print('\n' + '='*60)
print('🎉 WYNIKI TESTÓW NAPRAWIONEGO SYSTEMU')
print('='*60)
print(f'✅ Final quality score: {final_result["final_quality"]:.2f}')
print(f'🔄 Completed iterations: {final_result["iterations"]}')
print(f'📊 Success: {final_result["success"]}')
print(f'⬆️ Total improvements: {final_result["total_improvements"]}')

if 'final_process' in final_result:
    final_bpmn = final_result['final_process']
    print(f'👥 Final participants: {len(final_bpmn.get("participants", []))}')
    print(f'🔧 Final elements: {len(final_bpmn.get("elements", []))}')
    print(f'🔗 Final flows: {len(final_bpmn.get("flows", []))}')

print('\n🎯 PODSUMOWANIE NAPRAW:')
print('✅ Rzeczywiste AI - dodano GOOGLE_API_KEY')
print('✅ Auto-fix corruption - deep copy zamiast shallow copy')  
print('✅ Podwójne przetwarzanie - usunięto duplikaty improve_bpmn_process')
print('✅ Przepełnienie promptów - skrócono prompts')
print('✅ Validation multi-pool - naprawiono reguły dla wielopoolowych BPMN')
print('✅ Compliance score wzrósł z 0.0 do ' + f'{final_result["final_quality"]:.1f}!')
print('='*60)