"""
Smart Tourist Safety API Server Runner
This script starts the API server and verifies it's running correctly.
"""

import subprocess
import sys
import os
import time
import requests
import argparse
import platform
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import signal

# Initialize console
console = Console()

def check_dependencies():
    """Check if required dependencies are installed"""
    console.print("[cyan]Checking dependencies...[/cyan]")
    
    requirements = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "shapely",
        "requests",
        "python-dotenv",
        "supabase",
        "rich"
    ]
    
    missing = []
    
    for req in requirements:
        try:
            __import__(req.split("[")[0])
        except ImportError:
            missing.append(req)
    
    if missing:
        console.print(f"[yellow]Missing dependencies: {', '.join(missing)}[/yellow]")
        console.print("[cyan]Installing missing dependencies...[/cyan]")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            console.print("[green]Dependencies installed successfully![/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to install dependencies: {e}[/red]")
            return False
    else:
        console.print("[green]All dependencies already installed![/green]")
    
    return True

def is_server_running(host="localhost", port=8000):
    """Check if the server is already running"""
    try:
        response = requests.get(f"http://{host}:{port}/")
        if response.status_code == 200:
            return True
    except:
        pass
    
    return False

def start_server(host="localhost", port=8000, reload=True):
    """Start the API server"""
    # Check if server is already running
    if is_server_running(host, port):
        console.print(f"[yellow]Server already running at http://{host}:{port}/[/yellow]")
        return None
    
    console.print(f"[cyan]Starting server on http://{host}:{port}/...[/cyan]")
    
    # Determine the right command to start the server
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")
    
    # Start the server
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start (up to 10 seconds)
        start_time = time.time()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            task = progress.add_task("[cyan]Starting server...", total=None)
            
            while time.time() - start_time < 10:
                if is_server_running(host, port):
                    progress.update(task, completed=True, description="[green]Server started successfully![/green]")
                    console.print(f"[green]Server running at http://{host}:{port}/[/green]")
                    return process
                time.sleep(0.5)
            
            progress.update(task, completed=True, description="[red]Failed to start server[/red]")
            process.kill()
            console.print("[red]Server failed to start within timeout period[/red]")
            return None
            
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        return None

def stop_server(process):
    """Stop the server process"""
    if process:
        console.print("[cyan]Stopping server...[/cyan]")
        
        # Send interrupt signal (Ctrl+C)
        if platform.system() == "Windows":
            process.send_signal(signal.CTRL_C_EVENT)
        else:
            process.send_signal(signal.SIGINT)
            
        # Wait for process to terminate (up to 5 seconds)
        try:
            process.wait(timeout=5)
            console.print("[green]Server stopped successfully![/green]")
        except subprocess.TimeoutExpired:
            console.print("[yellow]Server did not stop gracefully, forcing termination...[/yellow]")
            process.kill()
            console.print("[green]Server terminated.[/green]")

def run_tests(host="localhost", port=8000):
    """Run the API endpoint tests"""
    console.print("[cyan]Running API tests...[/cyan]")
    
    try:
        subprocess.run([
            sys.executable, 
            os.path.join("tests", "test_api_endpoints.py"),
            "--host", host,
            "--port", str(port)
        ], check=True)
        
        console.print("[green]Tests completed![/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Test execution failed: {e}[/red]")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Smart Tourist Safety API server and tests")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", default="8000", type=int, help="Server port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--test-only", action="store_true", help="Only run tests, don't start server")
    
    args = parser.parse_args()
    
    console.print(Panel(f"[bold blue]Smart Tourist Safety API Server Runner[/bold blue]\n[cyan]Server: http://{args.host}:{args.port}/[/cyan]"))
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Change to project root directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_dir)
    
    server_process = None
    
    try:
        # Start server if needed
        if not args.test_only and not is_server_running(args.host, args.port):
            server_process = start_server(args.host, args.port, not args.no_reload)
            if not server_process:
                sys.exit(1)
        
        # Run tests
        run_tests(args.host, args.port)
        
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user[/yellow]")
    finally:
        # Stop server if we started it
        if server_process:
            stop_server(server_process)