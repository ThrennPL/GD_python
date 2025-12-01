import sys
sys.path.append('bpmn_v2')
from bpmn_compliance_validator import BPMNComplianceValidator
import xml.etree.ElementTree as ET

# Read the BPMN file
with open('Generated_Process_improved_20251127_181922.bpmn', 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Parse the XML
root = ET.fromstring(xml_content)

# Create validator
validator = BPMNComplianceValidator()

# Run validation
result = validator.validate(root)
print(f'BPMN Compliance Score: {result.score}/100')
print(f'Level: {result.level}')
print(f'Total Issues: {len(result.issues)}')

# Show critical issues
critical_issues = [issue for issue in result.issues if issue.severity == 'critical']
print(f'Critical Issues: {len(critical_issues)}')

# Show pool statistics
stats = result.statistics.get('process_statistics', {})
print(f'Participants: {stats.get("participants_count", "unknown")}')
print(f'Start Events: {stats.get("start_events", "unknown")}')
print(f'End Events: {stats.get("end_events", "unknown")}')

if critical_issues:
    print('\nFirst 5 critical issues:')
    for issue in critical_issues[:5]:
        print(f'  - {issue.element_id}: {issue.message}')

print('\nSummary:')
print('✅' if len(critical_issues) == 0 else '❌', f'Critical issues: {len(critical_issues)}')
if result.score >= 90:
    print('🎉 EXCELLENT BPMN compliance!')
elif result.score >= 70:
    print('✅ GOOD BPMN compliance')
elif result.score >= 50:
    print('⚠️  ACCEPTABLE BPMN compliance')
else:
    print('❌ POOR BPMN compliance - needs improvement')