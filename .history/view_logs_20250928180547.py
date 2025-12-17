#!/usr/bin/env python
"""
Log viewer utility for Smart Tourist Safety System.
Displays clean, focused logs from the application.
"""
import os
import sys
import argparse
import re
from datetime import datetime
import time
from typing import List, Dict, Any, Optional
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored terminal output
colorama.init()

# ANSI color codes
COLORS = {
    "RESET": Style.RESET_ALL,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED + Style.BRIGHT,
    "DEBUG": Fore.CYAN,
    "REQUEST": Fore.BLUE,
    "RESPONSE": Fore.MAGENTA,
    "TIME": Fore.WHITE + Style.DIM,
    "HIGHLIGHT": Fore.WHITE + Style.BRIGHT
}

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Clean log viewer for Smart Tourist Safety System")
    parser.add_argument("--file", "-f", default="logs/api.log", help="Log file to view (default: logs/api.log)")
    parser.add_argument("--lines", "-n", type=int, default=50, help="Number of lines to show (default: 50)")
    parser.add_argument("--follow", "-F", action="store_true", help="Follow log output (like tail -f)")
    parser.add_argument("--filter", "-g", help="Filter logs by text pattern")
    parser.add_argument("--level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Filter logs by minimum level")
    parser.add_argument("--requests-only", "-r", action="store_true", help="Show only request/response logs")
    parser.add_argument("--errors-only", "-e", action="store_true", help="Show only error logs")
    return parser.parse_args()

def tail_file(filename: str, num_lines: int) -> List[str]:
    """Get the last n lines from a file"""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            return lines[-num_lines:] if len(lines) > num_lines else lines
    except FileNotFoundError:
        print(f"{COLORS['ERROR']}Error: Log file '{filename}' not found{COLORS['RESET']}")
        sys.exit(1)

def follow_file(filename: str):
    """Generator that yields new lines in a file as they are added (like tail -f)"""
    try:
        with open(filename, 'r') as file:
            # Go to the end of the file
            file.seek(0, 2)
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1)  # Sleep briefly
                    continue
                yield line
    except FileNotFoundError:
        print(f"{COLORS['ERROR']}Error: Log file '{filename}' not found{COLORS['RESET']}")
        sys.exit(1)

def format_log_line(line: str, filter_pattern: Optional[str] = None) -> str:
    """Format a log line with colors and highlighting"""
    # Extract components with regex
    match = re.match(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s* \| ([^|]+) \| (.+)', 
        line.strip()
    )
    
    if not match:
        # Return unformatted if it doesn't match expected format
        return line.strip()
    
    timestamp, level, component, message = match.groups()
    
    # Color based on level
    level_color = COLORS.get(level, COLORS["RESET"])
    
    # Format timestamp
    formatted_timestamp = f"{COLORS['TIME']}{timestamp}{COLORS['RESET']}"
    
    # Format level
    formatted_level = f"{level_color}{level.ljust(7)}{COLORS['RESET']}"
    
    # Format component
    formatted_component = f"{component}"
    
    # Format message with potential highlights
    formatted_message = message
    
    # Highlight request IDs, status codes, and HTTP methods
    formatted_message = re.sub(r'(\b[0-9a-f]{8}\b)', f"{COLORS['HIGHLIGHT']}\\1{COLORS['RESET']}", formatted_message)
    formatted_message = re.sub(r'\b(GET|POST|PUT|DELETE|PATCH)\b', f"{Fore.BLUE}\\1{COLORS['RESET']}", formatted_message)
    formatted_message = re.sub(r'\b([2-5]\d\d)\b', lambda m: status_code_color(m.group(1)), formatted_message)
    
    # Highlight special symbols
    formatted_message = formatted_message.replace('→', f"{COLORS['REQUEST']}→{COLORS['RESET']}")
    formatted_message = formatted_message.replace('←', f"{COLORS['RESPONSE']}←{COLORS['RESET']}")
    formatted_message = formatted_message.replace('!', f"{COLORS['ERROR']}!{COLORS['RESET']}")
    
    # If filter pattern exists, highlight it
    if filter_pattern:
        pattern = re.compile(f'({re.escape(filter_pattern)})', re.IGNORECASE)
        formatted_message = pattern.sub(f"{Fore.YELLOW + Style.BRIGHT}\\1{COLORS['RESET']}", formatted_message)
    
    return f"{formatted_timestamp} | {formatted_level} | {formatted_component.ljust(20)} | {formatted_message}"

def status_code_color(status_code: str) -> str:
    """Return colored status code based on its value"""
    code = int(status_code)
    if code >= 500:
        return f"{COLORS['ERROR']}{status_code}{COLORS['RESET']}"
    elif code >= 400:
        return f"{COLORS['WARNING']}{status_code}{COLORS['RESET']}"
    elif code >= 300:
        return f"{Fore.CYAN}{status_code}{COLORS['RESET']}"
    else:
        return f"{COLORS['INFO']}{status_code}{COLORS['RESET']}"

def should_show_line(line: str, args: argparse.Namespace) -> bool:
    """Determine if a line should be displayed based on filters"""
    # Filter by minimum log level
    if args.level:
        level_match = re.search(r'\| (\w+)\s* \|', line)
        if level_match:
            log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            line_level = level_match.group(1).strip()
            if line_level in log_levels:
                if log_levels.index(line_level) < log_levels.index(args.level):
                    return False
    
    # Filter by requests only
    if args.requests_only and not (('→' in line) or ('←' in line)):
        return False
    
    # Filter by errors only
    if args.errors_only and not (('ERROR' in line) or ('WARNING' in line) or ('CRITICAL' in line)):
        return False
    
    # Filter by text pattern
    if args.filter and args.filter.lower() not in line.lower():
        return False
    
    return True

def display_logs(args: argparse.Namespace):
    """Display logs according to command line arguments"""
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{COLORS['HIGHLIGHT']}=== Smart Tourist Safety System Log Viewer ==={COLORS['RESET']}")
    print(f"File: {args.file}   Lines: {args.lines}   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.filter:
        print(f"Filter: {COLORS['HIGHLIGHT']}{args.filter}{COLORS['RESET']}")
    print("=" * 80)
    
    if args.follow:
        # First show the tail
        lines = tail_file(args.file, args.lines)
        for line in lines:
            if should_show_line(line, args):
                print(format_log_line(line, args.filter))
        
        # Then follow the file
        print(f"\n{COLORS['HIGHLIGHT']}--- Following log updates (Ctrl+C to exit) ---{COLORS['RESET']}")
        try:
            for line in follow_file(args.file):
                if should_show_line(line, args):
                    print(format_log_line(line, args.filter))
        except KeyboardInterrupt:
            print(f"\n{COLORS['HIGHLIGHT']}Log viewing stopped.{COLORS['RESET']}")
    else:
        # Just show the tail
        lines = tail_file(args.file, args.lines)
        for line in lines:
            if should_show_line(line, args):
                print(format_log_line(line, args.filter))

if __name__ == "__main__":
    args = parse_arguments()
    display_logs(args)