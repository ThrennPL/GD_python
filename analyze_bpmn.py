import xml.etree.ElementTree as ET

# Read and parse BPMN
with open('Generated_Process_improved_20251127_181922.bpmn', 'r', encoding='utf-8') as f:
    root = ET.fromstring(f.read())

# Count elements by pool
pools = {}
for process in root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}process'):
    process_id = process.get('id', '')
    pool_name = process_id.replace('process_', '')
    
    # Count different types
    start_events = len(process.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}startEvent'))
    intermediate_catch = len(process.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}intermediateCatchEvent'))
    end_events = len(process.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}endEvent'))
    activities = len(process.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}userTask')) + len(process.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}serviceTask'))
    
    pools[pool_name] = {
        'start_events': start_events,
        'intermediate_catch': intermediate_catch, 
        'end_events': end_events,
        'activities': activities,
        'has_start_or_intermediate': start_events > 0 or intermediate_catch > 0
    }

# Count Message Flows
message_flows = len(root.findall('.//{http://www.omg.org/spec/BPMN/20100524/MODEL}messageFlow'))

print('=== ANALIZA STRUKTURY BPMN ===')
print(f'Message Flows: {message_flows}')
print()

compliant_pools = 0
total_pools = 0

for pool, stats in pools.items():
    total_pools += 1
    has_start = stats['has_start_or_intermediate']
    has_end = stats['end_events'] > 0
    has_activities = stats['activities'] > 0
    
    status = '✅' if (has_start and has_end) or not has_activities else '❌'
    if (has_start and has_end) or not has_activities:
        compliant_pools += 1
    
    print(f'{status} Pool: {pool}')
    print(f'   Start Events: {stats["start_events"]}')
    print(f'   Intermediate Catch Events: {stats["intermediate_catch"]}')
    print(f'   End Events: {stats["end_events"]}')
    print(f'   Activities: {stats["activities"]}')
    
    if has_activities and not has_start:
        print('   ⚠️  Pool ma aktywności ale brak Start/Intermediate Catch Event')
    elif has_activities and not has_end:
        print('   ⚠️  Pool ma aktywności ale brak End Event')
    elif has_activities and has_start and has_end:
        print('   ✅ Pool kompletny!')
    elif not has_activities:
        print('   ℹ️  Pool pusty')
    print()

print(f'=== PODSUMOWANIE ===')
print(f'Pools zgodne ze standardem BPMN: {compliant_pools}/{total_pools}')
compliance_percentage = (compliant_pools / total_pools) * 100 if total_pools > 0 else 0
print(f'Compliance: {compliance_percentage:.0f}%')

if compliance_percentage == 100:
    print('🎉 DOSKONALE! Wszystkie poole są zgodne ze standardem BPMN 2.0!')
elif compliance_percentage >= 80:
    print('✅ BARDZO DOBRZE! Większość poolów jest zgodna ze standardem')
elif compliance_percentage >= 60:
    print('⚠️  ŚREDNIO - potrzebne są jeszcze poprawki')
else:
    print('❌ ŹLEE - diagram wymaga znacznych poprawek')