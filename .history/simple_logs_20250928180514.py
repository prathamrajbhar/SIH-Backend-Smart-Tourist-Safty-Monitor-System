#!/usr/bin/env python
"""
Simple log viewer utility for Smart Tourist Safety System.
"""
import sys
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Simple log viewer for Tourist Safety System")
    parser.add_argument("-n", "--lines", type=int, default=20, help="Number of lines to show (default: 20)")
    parser.add_argument("-f", "--file", default="logs/api.log", help="Log file to view (default: logs/api.log)")
    return parser.parse_args()

def view_logs(file_path, num_lines):
    """Display the last n lines of a log file"""
    try:
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print("SMART TOURIST SAFETY SYSTEM - LOG VIEWER")
        print(f"Showing last {num_lines} lines from {file_path}")
        print("=" * 80)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: Log file '{file_path}' not found!")
            return
        
        # Read lines with the appropriate encoding
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        # Get the last n lines
        last_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
        
        # Print the lines
        for line in last_lines:
            print(line.rstrip())
            
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    args = parse_args()
    view_logs(args.file, args.lines)