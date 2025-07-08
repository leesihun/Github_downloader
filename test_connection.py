#!/usr/bin/env python3
"""
Test script to verify MobaXterm-like SSH connection
"""
from run_ETX import run_remote_etx

if __name__ == "__main__":
    print("Testing MobaXterm-like SSH connection...")
    print("This will run a simple test to verify the connection works.")
    print("=" * 50)
    
    # Test with basic commands first
    run_remote_etx()
    
    print("=" * 50)
    print("Test completed!") 