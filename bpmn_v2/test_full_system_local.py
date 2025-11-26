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

print('\nWYNIK FINALNY:')
print(f'Final score: {final_result["final_quality_score"]:.1f}')
print(f'Completed iterations: {final_result["completed_iterations"]}')
print(f'Reason for stopping: {final_result["termination_reason"]}')

if 'final_bpmn' in final_result:
    final_bpmn = final_result['final_bpmn']
    print(f'Final participants: {len(final_bpmn.get("participants", []))}')
    print(f'Final elements: {len(final_bpmn.get("elements", []))}')
    print(f'Final flows: {len(final_bpmn.get("flows", []))}')

print('\nWYNIK FINALNY:')
print(f'Final score: {final_result["final_quality_score"]:.1f}')
print(f'Completed iterations: {final_result["completed_iterations"]}')
print(f'Reason for stopping: {final_result["termination_reason"]}')

if 'final_bpmn' in final_result:
    final_bpmn = final_result['final_bpmn']
    print(f'Final participants: {len(final_bpmn.get("participants", []))}')
    print(f'Final elements: {len(final_bpmn.get("elements", []))}')
    print(f'Final flows: {len(final_bpmn.get("flows", []))}')