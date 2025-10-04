#!/usr/bin/env python3
"""
PrinterReaper v2.4.0 - Automated Test Runner
============================================
Comprehensive testing suite for all modules and functions
"""

import sys
import os
import json
import subprocess
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestRunner:
    def __init__(self):
        self.results = []
        self.errors = []
        self.start_time = None
    
    def test(self, name, func):
        """Run a test and record result"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print('='*60)
        
        try:
            start = time.time()
            result = func()
            elapsed = time.time() - start
            
            self.results.append({
                'name': name,
                'status': 'PASS',
                'time': elapsed,
                'result': result
            })
            print(f"[PASS] ({elapsed:.2f}s)")
            return True
            
        except Exception as e:
            self.errors.append({
                'name': name,
                'error': str(e),
                'type': type(e).__name__
            })
            self.results.append({
                'name': name,
                'status': 'FAIL',
                'error': str(e)
            })
            print(f"[FAIL] {e}")
            return False
    
    def test_import_modules(self):
        """Test all module imports"""
        print("\n[TEST] Testing Module Imports...")
        
        # Test core modules
        self.test("Import core.printer", lambda: __import__('core.printer'))
        self.test("Import core.capabilities", lambda: __import__('core.capabilities'))
        self.test("Import core.discovery", lambda: __import__('core.discovery'))
        self.test("Import core.osdetect", lambda: __import__('core.osdetect'))
        
        # Test language modules
        self.test("Import modules.pjl", lambda: __import__('modules.pjl'))
        self.test("Import modules.ps", lambda: __import__('modules.ps'))
        self.test("Import modules.pcl", lambda: __import__('modules.pcl'))
        
        # Test utils
        self.test("Import utils.helper", lambda: __import__('utils.helper'))
        self.test("Import utils.codebook", lambda: __import__('utils.codebook'))
        self.test("Import utils.fuzzer", lambda: __import__('utils.fuzzer'))
        self.test("Import utils.operators", lambda: __import__('utils.operators'))
        
        # Test protocols
        self.test("Import protocols.raw", lambda: __import__('protocols.raw'))
        self.test("Import protocols.lpd", lambda: __import__('protocols.lpd'))
        self.test("Import protocols.ipp", lambda: __import__('protocols.ipp'))
        self.test("Import protocols.smb", lambda: __import__('protocols.smb'))
        
        # Test payloads
        self.test("Import payloads", lambda: __import__('payloads'))
    
    def test_version(self):
        """Test version information"""
        print("\n[TEST] Testing Version Information...")
        
        from version import get_version, get_version_string, __version__
        
        self.test("Get version", lambda: get_version())
        self.test("Get version string", lambda: get_version_string())
        self.test("Check version is 2.4.0", lambda: assert_equal(__version__, "2.4.0"))
    
    def test_osdetect(self):
        """Test OS detection"""
        print("\n[TEST] Testing OS Detection...")
        
        from core.osdetect import get_os
        
        def test_os():
            os_type = get_os()
            assert os_type in ('linux', 'windows', 'wsl', 'darwin', 'bsd', 'unsupported')
            return os_type
        
        self.test("OS Detection", test_os)
        self.test("OS Detection Cache", test_os)  # Should use cached value
    
    def test_protocols(self):
        """Test protocol implementations"""
        print("\n[TEST] Testing Network Protocols...")
        
        # Test RAW
        def test_raw():
            from protocols.raw import RAWProtocol
            proto = RAWProtocol('localhost', 9100, timeout=1)
            return proto
        
        # Test LPD
        def test_lpd():
            from protocols.lpd import LPDProtocol
            proto = LPDProtocol('localhost', 515, timeout=1)
            return proto
        
        # Test IPP
        def test_ipp():
            from protocols.ipp import IPPProtocol
            proto = IPPProtocol('localhost', 631, timeout=1)
            return proto
        
        # Test SMB
        def test_smb():
            from protocols.smb import SMBProtocol
            proto = SMBProtocol('localhost', 445, timeout=1)
            return proto
        
        self.test("RAW Protocol Instantiation", test_raw)
        self.test("LPD Protocol Instantiation", test_lpd)
        self.test("IPP Protocol Instantiation", test_ipp)
        self.test("SMB Protocol Instantiation", test_smb)
    
    def test_payloads(self):
        """Test payload system"""
        print("\n[TEST] Testing Payload System...")
        
        from payloads import list_payloads, load_payload
        
        def test_list():
            payloads = list_payloads()
            assert len(payloads) >= 5
            return payloads
        
        def test_load_banner():
            payload = load_payload('banner.ps', {'msg': 'TEST'})
            assert 'TEST' in payload
            return payload
        
        def test_load_storm():
            payload = load_payload('storm.ps', {'count': '10'})
            assert '10' in payload
            return payload
        
        self.test("List Payloads", test_list)
        self.test("Load banner.ps", test_load_banner)
        self.test("Load storm.ps", test_load_storm)
    
    def test_operators(self):
        """Test PostScript operators database"""
        print("\n[TEST] Testing PostScript Operators...")
        
        from utils.operators import operators
        
        def test_ops():
            ops = operators()
            assert len(ops.oplist) > 0
            assert 'File Operators' in str(ops.oplist) or '10. File Operators' in str(ops.oplist)
            return len(ops.oplist)
        
        self.test("Operators Database", test_ops)
    
    def generate_report(self):
        """Generate QA test report"""
        print("\n" + "="*60)
        print("QA TEST REPORT")
        print("="*60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        total = len(self.results)
        
        print(f"\nTests Run: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        
        if self.errors:
            print("\n" + "="*60)
            print("ERRORS FOUND:")
            print("="*60)
            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. {error['name']}")
                print(f"   Type: {error['type']}")
                print(f"   Error: {error['error']}")
        else:
            print("\n[SUCCESS] NO ERRORS FOUND!")
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': self.errors,
            'results': self.results
        }
    
    def run_all(self):
        """Run all tests"""
        self.start_time = datetime.now()
        
        print("[QA] PrinterReaper v2.4.0 - QA Test Suite")
        print("="*60)
        print(f"Start Time: {self.start_time}")
        print("="*60)
        
        self.test_import_modules()
        self.test_version()
        self.test_osdetect()
        self.test_protocols()
        self.test_payloads()
        self.test_operators()
        
        report = self.generate_report()
        
        end_time = datetime.now()
        elapsed = (end_time - self.start_time).total_seconds()
        
        print(f"\nEnd Time: {end_time}")
        print(f"Total Elapsed: {elapsed:.2f}s")
        
        return report


def assert_equal(a, b):
    """Helper assertion"""
    if a != b:
        raise AssertionError(f"Expected {b}, got {a}")
    return True


if __name__ == "__main__":
    runner = TestRunner()
    report = runner.run_all()
    
    # Save report
    report_file = f"tests/qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n[INFO] Report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if report['failed'] == 0 else 1)

