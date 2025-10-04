#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper v2.4.0 - Comprehensive QA Testing
===============================================
Complete functionality and integration testing
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    print("[QA] PrinterReaper v2.4.0 - Comprehensive Testing")
    print("="*70)
    
    # Test 1: Module Imports
    print("\n[TEST 1] Module Imports")
    print("-"*70)
    
    modules_to_test = [
        ('core.printer', 'Base printer class'),
        ('core.capabilities', 'Capability detection'),
        ('core.discovery', 'Network discovery'),
        ('core.osdetect', 'OS detection'),
        ('modules.pjl', 'PJL module'),
        ('modules.ps', 'PostScript module'),
        ('modules.pcl', 'PCL module'),
        ('protocols.raw', 'RAW protocol'),
        ('protocols.lpd', 'LPD protocol'),
        ('protocols.ipp', 'IPP protocol'),
        ('protocols.smb', 'SMB protocol'),
        ('payloads', 'Payload system'),
        ('utils.helper', 'Helper utilities'),
        ('utils.codebook', 'Error codebook'),
        ('utils.fuzzer', 'Fuzzer'),
        ('utils.operators', 'PS operators'),
    ]
    
    for module_name, description in modules_to_test:
        results['total'] += 1
        try:
            __import__(module_name)
            print(f"  [PASS] {module_name:25s} - {description}")
            results['passed'] += 1
        except Exception as e:
            print(f"  [FAIL] {module_name:25s} - {e}")
            results['failed'] += 1
            results['errors'].append({'test': f'Import {module_name}', 'error': str(e)})
    
    # Test 2: Version Check
    print("\n[TEST 2] Version Information")
    print("-"*70)
    
    tests = [
        ('Version import', lambda: __import__('version')),
        ('Version string', lambda: __import__('version').get_version()),
        ('Version tuple', lambda: __import__('version').get_version_info()),
    ]
    
    for test_name, test_func in tests:
        results['total'] += 1
        try:
            result = test_func()
            print(f"  [PASS] {test_name:25s} - {result}")
            results['passed'] += 1
        except Exception as e:
            print(f"  [FAIL] {test_name:25s} - {e}")
            results['failed'] += 1
            results['errors'].append({'test': test_name, 'error': str(e)})
    
    # Test 3: Payload System
    print("\n[TEST 3] Payload System")
    print("-"*70)
    
    try:
        from payloads import list_payloads, load_payload
        
        results['total'] += 1
        payloads = list_payloads()
        print(f"  [PASS] List payloads - Found {len(payloads)} payloads")
        print(f"         Payloads: {', '.join(payloads)}")
        results['passed'] += 1
        
        # Test loading each payload
        for payload_name in ['banner.ps', 'loop.ps', 'erase.ps', 'storm.ps', 'exfil.ps']:
            results['total'] += 1
            try:
                if payload_name == 'banner.ps':
                    content = load_payload(payload_name, {'msg': 'TEST'})
                    assert 'TEST' in content
                elif payload_name == 'storm.ps':
                    content = load_payload(payload_name, {'count': '10'})
                    assert '10' in content
                elif payload_name == 'exfil.ps':
                    content = load_payload(payload_name, {'file': '/etc/passwd'})
                    assert '/etc/passwd' in content
                else:
                    content = load_payload(payload_name)
                
                print(f"  [PASS] Load {payload_name:15s} - {len(content)} bytes")
                results['passed'] += 1
            except Exception as e:
                print(f"  [FAIL] Load {payload_name:15s} - {e}")
                results['failed'] += 1
                results['errors'].append({'test': f'Load {payload_name}', 'error': str(e)})
    
    except Exception as e:
        print(f"  [FAIL] Payload system - {e}")
        results['errors'].append({'test': 'Payload system', 'error': str(e)})
    
    # Test 4: Operators Database
    print("\n[TEST 4] PostScript Operators Database")
    print("-"*70)
    
    try:
        from utils.operators import operators
        
        results['total'] += 1
        ops = operators()
        categories = len(ops.oplist)
        total_ops = sum(len(v) for v in ops.oplist.values())
        
        print(f"  [PASS] Operators loaded - {categories} categories, {total_ops} operators")
        results['passed'] += 1
        
        # Test first category
        results['total'] += 1
        first_category = list(ops.oplist.keys())[0]
        first_ops = ops.oplist[first_category]
        print(f"  [PASS] Category '{first_category}' - {len(first_ops)} operators")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  [FAIL] Operators - {e}")
        results['failed'] += 1
        results['errors'].append({'test': 'Operators database', 'error': str(e)})
    
    # Test 5: Protocol Classes
    print("\n[TEST 5] Network Protocol Classes")
    print("-"*70)
    
    protocol_tests = [
        ('RAW', 'protocols.raw', 'RAWProtocol', 9100),
        ('LPD', 'protocols.lpd', 'LPDProtocol', 515),
        ('IPP', 'protocols.ipp', 'IPPProtocol', 631),
        ('SMB', 'protocols.smb', 'SMBProtocol', 445),
    ]
    
    for proto_name, module_name, class_name, port in protocol_tests:
        results['total'] += 1
        try:
            module = __import__(module_name, fromlist=[class_name])
            proto_class = getattr(module, class_name)
            instance = proto_class('localhost', port, timeout=1)
            print(f"  [PASS] {proto_name:4s} Protocol - Port {port}, class {class_name}")
            results['passed'] += 1
        except Exception as e:
            print(f"  [FAIL] {proto_name:4s} Protocol - {e}")
            results['failed'] += 1
            results['errors'].append({'test': f'{proto_name} Protocol', 'error': str(e)})
    
    # Test 6: Fuzzer
    print("\n[TEST 6] Fuzzer System")
    print("-"*70)
    
    try:
        from utils.fuzzer import fuzzer
        
        f = fuzzer()
        
        results['total'] += 1
        paths = f.fuzz_paths()
        print(f"  [PASS] fuzz_paths() - {len(paths)} paths generated")
        results['passed'] += 1
        
        results['total'] += 1
        names = f.fuzz_names()
        print(f"  [PASS] fuzz_names() - {len(names)} names generated")
        results['passed'] += 1
        
        results['total'] += 1
        data = f.fuzz_data('small')
        print(f"  [PASS] fuzz_data() - {len(data)} bytes generated")
        results['passed'] += 1
        
        results['total'] += 1
        vectors = f.fuzz_traversal_vectors()
        print(f"  [PASS] fuzz_traversal_vectors() - {len(vectors)} vectors")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  [FAIL] Fuzzer - {e}")
        results['failed'] += 1
        results['errors'].append({'test': 'Fuzzer', 'error': str(e)})
    
    # Test 7: Codebook
    print("\n[TEST 7] Error Codebook")
    print("-"*70)
    
    try:
        from utils.codebook import codebook
        
        cb = codebook()
        
        results['total'] += 1
        assert len(cb.codelist) > 0
        print(f"  [PASS] Codebook loaded - {len(cb.codelist)} error codes")
        results['passed'] += 1
        
        results['total'] += 1
        errors = list(cb.get_errors('10001'))
        assert len(errors) > 0
        print(f"  [PASS] Error lookup - Code 10001: {errors[0]}")
        results['passed'] += 1
        
    except Exception as e:
        print(f"  [FAIL] Codebook - {e}")
        results['failed'] += 1
        results['errors'].append({'test': 'Codebook', 'error': str(e)})
    
    # Final Report
    print("\n" + "="*70)
    print("COMPREHENSIVE QA REPORT")
    print("="*70)
    print(f"\nTotal Tests: {results['total']}")
    print(f"[PASS] Passed: {results['passed']}")
    print(f"[FAIL] Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/results['total']*100) if results['total'] > 0 else 0:.1f}%")
    
    if results['errors']:
        print("\n" + "="*70)
        print(f"ERRORS FOUND: {len(results['errors'])}")
        print("="*70)
        for i, error in enumerate(results['errors'], 1):
            print(f"\n{i}. {error['test']}")
            print(f"   Error: {error['error']}")
    else:
        print("\n[SUCCESS] ALL TESTS PASSED!")
    
    return results

if __name__ == "__main__":
    results = run_comprehensive_tests()
    sys.exit(0 if results['failed'] == 0 else 1)

