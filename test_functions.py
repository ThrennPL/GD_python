#!/usr/bin/env python
# Test script for Streamlit app

try:
    print("Testing imports...")
    from streamlit_app import get_complexity_level, get_validation_rule, get_output_format, get_domain
    print("✓ Core functions imported successfully")
    
    print("\nTesting functions...")
    print(f"Complexity (medium): {get_complexity_level('medium')}")
    print(f"Validation (syntax): {get_validation_rule('syntax')}")
    print(f"Output format (clean): {get_output_format('clean')}")
    print(f"Domain (bankowość): {get_domain('bankowość')}")
    
    print("\n✓ All tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
