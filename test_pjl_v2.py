#!/usr/bin/env python3
"""
Test PJL v2.0 Commands
Validates all PJL v2.0 commands and functionality
"""

import subprocess
import sys
import os

def create_pjl_v2_test_commands():
    """Create commands to test PJL v2.0 functionality"""
    
    commands = [
        # Basic info commands
        "status",
        "help",
        
        # Test system information commands
        "id",
        "version",
        "info id",
        "product",
        "network",
        "wifi",
        "variables",
        "printenv PAGECOUNT",
        
        # Test control commands
        "set TESTVAR=testvalue",
        "display 'Test Message'",
        "selftest",
        
        # Test filesystem commands
        "ls",
        "mkdir testdir",
        "ls testdir",
        "touch testfile.txt",
        "ls testfile.txt",
        "delete testfile.txt",
        "rmdir testdir",
        
        # Test help system
        "help filesystem",
        "help system",
        "help control",
        "help security",
        "help attacks",
        "help network",
        "help monitoring",
        
        # Exit
        "exit"
    ]
    
    return commands

def run_pjl_v2_test(target="15.204.211.244"):
    """Run PJL v2.0 test on target"""
    
    print(f"PJL v2.0 Test")
    print(f"Target: {target}")
    print("=" * 50)
    
    # Get PJL v2.0 test commands
    commands = create_pjl_v2_test_commands()
    
    # Create command file
    cmd_file = "pjl_v2_test.txt"
    with open(cmd_file, "w") as f:
        for cmd in commands:
            f.write(cmd + "\n")
    
    print(f"Created PJL v2.0 test file with {len(commands)} commands")
    print("Testing PJL v2.0 functionality...")
    print("=" * 50)
    
    try:
        # Run PrinterReaper with PJL v2.0
        cmd = [
            sys.executable,
            "printer-reaper.py",
            target,
            "pjl2",
            "--load", cmd_file,
            "--quiet"
        ]
        
        print("Starting PJL v2.0 test...")
        print("=" * 50)
        
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=180)
        
        print("\n" + "=" * 50)
        print("PJL v2.0 test completed!")
        print(f"Exit code: {result.returncode}")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\nTest timed out after 180 seconds")
        return 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 0
    except Exception as e:
        print(f"Error during test: {e}")
        return 1
    finally:
        # Clean up
        try:
            os.remove(cmd_file)
        except:
            pass

def main():
    """Main PJL v2.0 test function"""
    print("PJL v2.0 Command Testing")
    print("Testing all PJL v2.0 commands and functionality")
    print("=" * 50)
    
    # Run PJL v2.0 test
    return run_pjl_v2_test()

if __name__ == "__main__":
    sys.exit(main())
