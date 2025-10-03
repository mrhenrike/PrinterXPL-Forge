#!/usr/bin/env python3
"""
Simple PJL v2.0 Test
Basic functionality test for PJL v2.0
"""

import subprocess
import sys
import os

def create_simple_test_commands():
    """Create simple test commands"""
    
    commands = [
        # Basic info commands
        "status",
        "help",
        
        # Test system information commands
        "id",
        "version",
        "product",
        
        # Test help system
        "help filesystem",
        "help system",
        "help control",
        
        # Exit
        "exit"
    ]
    
    return commands

def run_simple_test(target="15.204.211.244"):
    """Run simple PJL v2.0 test"""
    
    print(f"Simple PJL v2.0 Test")
    print(f"Target: {target}")
    print("=" * 50)
    
    # Get simple test commands
    commands = create_simple_test_commands()
    
    # Create command file
    cmd_file = "simple_pjl_v2_test.txt"
    with open(cmd_file, "w") as f:
        for cmd in commands:
            f.write(cmd + "\n")
    
    print(f"Created simple test file with {len(commands)} commands")
    print("Testing basic PJL v2.0 functionality...")
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
        
        print("Starting simple PJL v2.0 test...")
        print("=" * 50)
        
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=60)
        
        print("\n" + "=" * 50)
        print("Simple PJL v2.0 test completed!")
        print(f"Exit code: {result.returncode}")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\nTest timed out after 60 seconds")
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
    """Main simple test function"""
    print("Simple PJL v2.0 Test")
    print("Testing basic PJL v2.0 functionality")
    print("=" * 50)
    
    # Run simple test
    return run_simple_test()

if __name__ == "__main__":
    sys.exit(main())
