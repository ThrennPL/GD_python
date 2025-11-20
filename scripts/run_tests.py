#!/usr/bin/env python3
"""
Test runner for GD_python project.
Uruchamia testy w reorganizowanej strukturze katalogów.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Uruchamia wszystkie testy."""
    project_root = Path(__file__).parent
    
    print("🧪 RUNNING TESTS FOR GD_PYTHON")
    print("=" * 50)
    
    # Test categories
    test_categories = {
        "Unit Tests": "tests/unit",
        "Integration Tests": "tests/integration", 
        "System Tests": "tests/system"
    }
    
    total_passed = 0
    total_failed = 0
    
    for category, path in test_categories.items():
        print(f"\n📁 {category}")
        print("-" * 30)
        
        test_dir = project_root / path
        if not test_dir.exists():
            print(f"   ⚠️ Directory {path} not found")
            continue
            
        test_files = list(test_dir.glob("test_*.py"))
        
        if not test_files:
            print(f"   ⚠️ No test files found in {path}")
            continue
            
        for test_file in test_files:
            print(f"   🔍 Running {test_file.name}...")
            
            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {test_file.name} - PASSED")
                    total_passed += 1
                else:
                    print(f"   ❌ {test_file.name} - FAILED")
                    print(f"      Error: {result.stderr}")
                    total_failed += 1
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏰ {test_file.name} - TIMEOUT")
                total_failed += 1
            except Exception as e:
                print(f"   💥 {test_file.name} - ERROR: {e}")
                total_failed += 1
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"📊 TEST SUMMARY:")
    print(f"   ✅ Passed: {total_passed}")
    print(f"   ❌ Failed: {total_failed}")
    print(f"   📈 Total: {total_passed + total_failed}")
    
    if total_failed == 0:
        print(f"   🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"   ⚠️ {total_failed} tests failed")
        return 1

def run_specific_test(test_name):
    """Uruchamia konkretny test."""
    project_root = Path(__file__).parent
    
    # Szukaj test file
    for test_dir in ["tests/unit", "tests/integration", "tests/system"]:
        test_path = project_root / test_dir / f"{test_name}.py"
        if test_path.exists():
            print(f"🔍 Running {test_path}...")
            subprocess.run([sys.executable, str(test_path)], cwd=project_root)
            return
    
    print(f"❌ Test {test_name} not found")
    print(f"Available tests:")
    
    for test_dir in ["tests/unit", "tests/integration", "tests/system"]:
        test_path = project_root / test_dir
        if test_path.exists():
            for test_file in test_path.glob("test_*.py"):
                print(f"   - {test_file.stem}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        if not test_name.startswith("test_"):
            test_name = f"test_{test_name}"
        run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_tests()
        sys.exit(exit_code)