#!/usr/bin/env python3
"""
Test script to verify the infinite loop bug fix
This test ensures that the program exits correctly when loading commands from file
"""

import sys
import os
import subprocess
import time

def test_load_commands_with_exit():
    """Test that program exits correctly when loading commands with exit"""
    print("=" * 70)
    print("TEST 1: Load commands from file with exit command")
    print("=" * 70)
    
    # Create a temporary test file
    test_file = "test_temp_commands.txt"
    with open(test_file, 'w') as f:
        f.write("help\n")
        f.write("exit\n")
    
    try:
        # Run the program with timeout
        start_time = time.time()
        result = subprocess.run(
            ["python3", "printer-reaper.py", "test", "pjl", "-q", "-i", test_file],
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✓ Program exited in {execution_time:.2f} seconds")
        print(f"✓ Exit code: {result.returncode}")
        
        # Check if output contains the expected commands
        if "Executing: help" in result.stdout:
            print("✓ Command 'help' was executed")
        else:
            print("✗ Command 'help' was NOT executed")
            return False
        
        if "Executing: exit" in result.stdout:
            print("✓ Command 'exit' was executed")
        else:
            print("✗ Command 'exit' was NOT executed")
            return False
        
        # Check that there's no infinite loop (no repeated prompt)
        prompt_count = result.stdout.count(":/> ")
        if prompt_count > 10:
            print(f"✗ FAILED: Too many prompts ({prompt_count}), possible infinite loop")
            return False
        else:
            print(f"✓ No infinite loop detected (prompt count: {prompt_count})")
        
        print("\n✅ TEST 1 PASSED\n")
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ FAILED: Program timed out (infinite loop detected)")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_interactive_mode():
    """Test that interactive mode still works"""
    print("=" * 70)
    print("TEST 2: Interactive mode (without -i flag)")
    print("=" * 70)
    
    try:
        # Run the program in interactive mode with input
        start_time = time.time()
        result = subprocess.run(
            ["python3", "printer-reaper.py", "test", "pjl", "-q"],
            input="exit\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✓ Program exited in {execution_time:.2f} seconds")
        print(f"✓ Exit code: {result.returncode}")
        
        print("\n✅ TEST 2 PASSED\n")
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ FAILED: Program timed out in interactive mode")
        return False

def test_load_multiple_commands():
    """Test loading multiple commands from file"""
    print("=" * 70)
    print("TEST 3: Load multiple commands from file")
    print("=" * 70)
    
    # Create a test file with multiple commands
    test_file = "test_temp_multiple.txt"
    with open(test_file, 'w') as f:
        f.write("help\n")
        f.write("help exit\n")
        f.write("help open\n")
        f.write("exit\n")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            ["python3", "printer-reaper.py", "test", "pjl", "-q", "-i", test_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✓ Program exited in {execution_time:.2f} seconds")
        print(f"✓ Exit code: {result.returncode}")
        
        # Check if all commands were executed
        expected_commands = ["help", "help exit", "help open", "exit"]
        executed_count = 0
        for cmd in expected_commands:
            if f"Executing: {cmd}" in result.stdout:
                print(f"✓ Command '{cmd}' was executed")
                executed_count += 1
            else:
                print(f"✗ Command '{cmd}' was NOT executed")
        
        if executed_count == len(expected_commands):
            print(f"\n✓ All {executed_count} commands were executed")
        else:
            print(f"\n✗ Only {executed_count}/{len(expected_commands)} commands were executed")
            return False
        
        print("\n✅ TEST 3 PASSED\n")
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ FAILED: Program timed out with multiple commands")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("PrinterReaper Infinite Loop Bug Fix - Test Suite")
    print("=" * 70 + "\n")
    
    # Change to project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    results = []
    
    # Run tests
    results.append(("Load commands with exit", test_load_commands_with_exit()))
    results.append(("Interactive mode", test_interactive_mode()))
    results.append(("Load multiple commands", test_load_multiple_commands()))
    
    # Print summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 70)
    print(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! The infinite loop bug is fixed.\n")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED! Please review the failures.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

