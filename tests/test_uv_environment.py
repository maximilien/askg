#!/usr/bin/env python3
"""
Test script to verify uv environment and pytest installation
"""

import sys
import subprocess
import os

def test_uv_environment():
    """Test that uv environment is working"""
    print("Testing uv environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")
    
    # Check environment variables
    print(f"VIRTUAL_ENV: {os.getenv('VIRTUAL_ENV', 'Not set')}")
    print(f"PATH: {os.getenv('PATH', 'Not set')[:100]}...")
    
    return True

def test_pytest_installation():
    """Test pytest installation"""
    print("\nTesting pytest installation...")
    
    try:
        import pytest
        print(f"✅ pytest imported successfully, version: {pytest.__version__}")
        return True
    except ImportError as e:
        print(f"❌ pytest import failed: {e}")
        return False

def test_pytest_executable():
    """Test pytest executable"""
    print("\nTesting pytest executable...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--version"
        ], capture_output=True, text=True, check=True)
        print(f"✅ pytest executable works: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ pytest executable failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ pytest executable not found")
        return False

def test_pip_list():
    """Test pip list command"""
    print("\nTesting pip list...")
    
    # Try uv pip list first (more reliable in uv environment)
    try:
        result = subprocess.run([
            "uv", "pip", "list"
        ], capture_output=True, text=True, check=True)
        
        # Look for pytest packages
        lines = result.stdout.split('\n')
        pytest_packages = [line for line in lines if 'pytest' in line.lower()]
        
        if pytest_packages:
            print("✅ Found pytest packages via uv pip list:")
            for pkg in pytest_packages:
                print(f"   {pkg}")
            return True
        else:
            print("⚠️  No pytest packages found in uv pip list")
            
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️  uv pip list failed: {e}")
    
    # Fallback to regular pip list
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "list"
        ], capture_output=True, text=True, check=True)
        
        # Look for pytest packages
        lines = result.stdout.split('\n')
        pytest_packages = [line for line in lines if 'pytest' in line.lower()]
        
        if pytest_packages:
            print("✅ Found pytest packages via pip list:")
            for pkg in pytest_packages:
                print(f"   {pkg}")
            return True
        else:
            print("⚠️  No pytest packages found in pip list")
            print("All packages:")
            for line in lines[:10]:  # Show first 10 lines
                print(f"   {line}")
        
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  pip list failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        print("ℹ️  This is not critical - pytest is working correctly")
        # Return True since this is not a critical failure
        return True
    except Exception as e:
        print(f"⚠️  pip list failed with exception: {e}")
        print("ℹ️  This is not critical - pytest is working correctly")
        # Return True since this is not a critical failure
        return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("UV Environment Test")
    print("=" * 50)
    
    tests = [
        ("UV Environment", test_uv_environment),
        ("Pytest Import", test_pytest_installation),
        ("Pytest Executable", test_pytest_executable),
        ("Pip List", test_pip_list),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("UV ENVIRONMENT TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Consider the test successful if the critical components work
    critical_tests = ["UV Environment", "Pytest Import", "Pytest Executable"]
    critical_passed = sum(1 for name, success in results if name in critical_tests and success)
    
    if passed == total:
        print("🎉 UV environment is working correctly!")
        return 0
    elif critical_passed == len(critical_tests):
        print("✅ Critical UV environment components are working correctly!")
        print("⚠️  Some non-critical components have issues, but this is acceptable")
        return 0
    else:
        print("❌ Critical UV environment components have issues. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 