#!/usr/bin/env python3
"""
Script to create the logs directory and set up logging for the Smart Tourist Safety API.
"""
import os
import sys
import logging

# Ensure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Create logs directory
logs_dir = os.path.join(script_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
print(f"Created logs directory at {logs_dir}")

# Create required log files
log_files = [
    "api.log",
    "data_changes.log",
    "errors.log"
]

for log_file in log_files:
    log_path = os.path.join(logs_dir, log_file)
    # Create the file if it doesn't exist
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            f.write(f"# {log_file} - Smart Tourist Safety API Logs\n")
        print(f"Created log file: {log_path}")
    else:
        print(f"Log file already exists: {log_path}")

print("Log setup complete!")