"""
Smart Tourist Safety API Testing Script
This script tests all API endpoints of the Smart Tourist Safety System
"""

import requests
import json
from datetime import datetime
import time
import random
import sys
import logging
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_test.log"),
        logging.StreamHandler()
    ]
)

# Initialize console
console = Console()

# Base URL for API
BASE_URL = "http://localhost:8000"

# Test data
TEST_TOURIST = {
    "name": "Test Tourist",
    "contact": f"+9199{random.randint(10000000, 99999999)}",  # Random contact to avoid duplicates
    "email": f"test{random.randint(1000, 9999)}@example.com",
    "trip_info": {
        "duration": "5 days",
        "destination": "Delhi",
        "purpose": "Tourism",
        "starting_date": "2025-09-28"
    },
    "emergency_contact": "+911234567890",
    "age": 30,
    "nationality": "Indian"
}

# Test locations (Delhi landmarks)
TEST_LOCATIONS = [
    {"latitude": 28.6139, "longitude": 77.2090, "name": "India Gate"},
    {"latitude": 28.5535, "longitude": 77.2588, "name": "Humayun's Tomb"},
    {"latitude": 28.6562, "longitude": 77.2410, "name": "Red Fort"},
    {"latitude": 28.6129, "longitude": 77.2295, "name": "Jama Masjid"}
]

# Test alert data
TEST_ALERT = {
    "message": "Test alert from API testing script",
    "description": "This is a test alert created by the API testing script"
}

# Test E-FIR data
TEST_EFIR = {
    "incident_type": "theft",
    "description": "Test e-FIR from API testing script",
    "location": "India Gate, Delhi",
    "incident_datetime": datetime.now().isoformat(),
    "additional_info": {
        "items_lost": ["wallet", "mobile phone"],
        "estimated_value": 15000
    }
}

class APITester:
    """Class to test API endpoints"""
    
    def __init__(self):
        self.tourist_id = None
        self.location_id = None
        self.alert_id = None
        self.efir_id = None
        self.results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "endpoints": {}
        }

    def log_result(self, endpoint, success, status_code=None, response=None, error=None):
        """Log the result of a test"""
        result = "PASS" if success else "FAIL"
        self.results["total"] += 1
        if success:
            self.results["passed"] += 1
            logging.info(f"{result}: {endpoint} - Status: {status_code}")
        else:
            self.results["failed"] += 1
            logging.error(f"{result}: {endpoint} - Status: {status_code} - Error: {error}")
        
        self.results["endpoints"][endpoint] = {
            "success": success,
            "status_code": status_code,
            "response": response,
            "error": error
        }

    def test_root_endpoint(self):
        """Test the root endpoint"""
        endpoint = "/"
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_register_tourist(self):
        """Test registering a tourist"""
        endpoint = "/registerTourist"
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=TEST_TOURIST)
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            
            if success:
                self.tourist_id = response.json().get("id")
                console.print(f"[green]Created test tourist with ID: {self.tourist_id}[/green]")
            
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_get_tourist(self):
        """Test getting tourist details"""
        if not self.tourist_id:
            self.log_result("/tourists/{id}", False, error="No tourist ID available")
            return False, None
            
        endpoint = f"/tourists/{self.tourist_id}"
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_send_location(self):
        """Test sending location"""
        if not self.tourist_id:
            self.log_result("/sendLocation", False, error="No tourist ID available")
            return False, None
            
        endpoint = "/sendLocation"
        location = random.choice(TEST_LOCATIONS)
        location_data = {
            "tourist_id": self.tourist_id,
            "latitude": location["latitude"],
            "longitude": location["longitude"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=location_data)
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            
            if success:
                self.location_id = response.json().get("id")
                console.print(f"[green]Sent location update for {location['name']} with ID: {self.location_id}[/green]")
                
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_press_sos(self):
        """Test pressing SOS button"""
        if not self.tourist_id:
            self.log_result("/pressSOS", False, error="No tourist ID available")
            return False, None
            
        endpoint = "/pressSOS"
        location = random.choice(TEST_LOCATIONS)
        sos_data = {
            "tourist_id": self.tourist_id,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "message": "Test SOS alert"
        }
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=sos_data)
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            
            if success:
                self.alert_id = response.json().get("id")
                console.print(f"[green]Created SOS alert with ID: {self.alert_id}[/green]")
                
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_get_alerts(self):
        """Test getting alerts"""
        endpoint = "/getAlerts"
        
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_resolve_alert(self):
        """Test resolving an alert"""
        if not self.alert_id:
            self.log_result("/resolveAlert/{id}", False, error="No alert ID available")
            return False, None
            
        endpoint = f"/resolveAlert/{self.alert_id}"
        
        try:
            response = requests.put(
                f"{BASE_URL}{endpoint}", 
                json={"resolution_notes": "Resolved by API test script"}
            )
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_file_efir(self):
        """Test filing an E-FIR"""
        if not self.tourist_id:
            self.log_result("/fileEFIR", False, error="No tourist ID available")
            return False, None
            
        endpoint = "/fileEFIR"
        
        efir_data = {
            "tourist_id": self.tourist_id,
            **TEST_EFIR
        }
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=efir_data)
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            
            if success:
                self.efir_id = response.json().get("id")
                console.print(f"[green]Filed E-FIR with ID: {self.efir_id}[/green]")
                
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_ai_training_status(self):
        """Test getting AI training status"""
        endpoint = "/api/v1/ai/training/status"
        
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_ai_data_stats(self):
        """Test getting AI data statistics"""
        endpoint = "/api/v1/ai/data/stats"
        
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def test_force_ai_training(self):
        """Test forcing AI training"""
        endpoint = "/api/v1/ai/training/force"
        
        try:
            response = requests.post(f"{BASE_URL}{endpoint}")
            success = 200 <= response.status_code < 300
            self.log_result(endpoint, success, response.status_code, response.json())
            return success, response
        except Exception as e:
            self.log_result(endpoint, False, error=str(e))
            return False, None

    def run_all_tests(self):
        """Run all tests"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            # Test basic endpoints
            task = progress.add_task("[cyan]Testing root endpoint...", total=None)
            self.test_root_endpoint()
            progress.update(task, completed=True, description="[green]Root endpoint tested[/green]")
            
            # Test required endpoints
            task = progress.add_task("[cyan]Testing tourist registration...", total=None)
            self.test_register_tourist()
            progress.update(task, completed=True, description="[green]Tourist registration tested[/green]")
            
            task = progress.add_task("[cyan]Testing get tourist details...", total=None)
            self.test_get_tourist()
            progress.update(task, completed=True, description="[green]Get tourist details tested[/green]")
            
            task = progress.add_task("[cyan]Testing send location...", total=None)
            self.test_send_location()
            progress.update(task, completed=True, description="[green]Send location tested[/green]")
            
            # Wait a bit for AI processing to complete
            time.sleep(2)
            
            task = progress.add_task("[cyan]Testing SOS alert...", total=None)
            self.test_press_sos()
            progress.update(task, completed=True, description="[green]SOS alert tested[/green]")
            
            task = progress.add_task("[cyan]Testing get alerts...", total=None)
            self.test_get_alerts()
            progress.update(task, completed=True, description="[green]Get alerts tested[/green]")
            
            task = progress.add_task("[cyan]Testing resolve alert...", total=None)
            self.test_resolve_alert()
            progress.update(task, completed=True, description="[green]Resolve alert tested[/green]")
            
            task = progress.add_task("[cyan]Testing file E-FIR...", total=None)
            self.test_file_efir()
            progress.update(task, completed=True, description="[green]E-FIR filing tested[/green]")
            
            # Test AI endpoints
            task = progress.add_task("[cyan]Testing AI training status...", total=None)
            self.test_ai_training_status()
            progress.update(task, completed=True, description="[green]AI training status tested[/green]")
            
            task = progress.add_task("[cyan]Testing AI data stats...", total=None)
            self.test_ai_data_stats()
            progress.update(task, completed=True, description="[green]AI data stats tested[/green]")
            
            task = progress.add_task("[cyan]Testing force AI training...", total=None)
            self.test_force_ai_training()
            progress.update(task, completed=True, description="[green]Force AI training tested[/green]")

    def print_summary(self):
        """Print test summary"""
        console.print("\n")
        console.print(Panel(f"[bold]API TEST SUMMARY[/bold]", expand=False))
        
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Total Tests")
        summary_table.add_column("Passed", style="green")
        summary_table.add_column("Failed", style="red")
        summary_table.add_column("Success Rate")
        
        success_rate = (self.results["passed"] / self.results["total"]) * 100 if self.results["total"] > 0 else 0
        summary_table.add_row(
            str(self.results["total"]),
            str(self.results["passed"]),
            str(self.results["failed"]),
            f"{success_rate:.1f}%"
        )
        
        console.print(summary_table)
        
        # Details table
        console.print("\n")
        console.print("[bold]Endpoint Details:[/bold]")
        
        details_table = Table(show_header=True, header_style="bold blue")
        details_table.add_column("Endpoint")
        details_table.add_column("Status")
        details_table.add_column("Status Code")
        
        for endpoint, result in self.results["endpoints"].items():
            status = "[green]PASS[/green]" if result["success"] else "[red]FAIL[/red]"
            status_code = str(result["status_code"]) if result["status_code"] else "-"
            details_table.add_row(endpoint, status, status_code)
            
        console.print(details_table)
        
        # Save results to file
        with open("api_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": self.results["total"],
                    "passed": self.results["passed"],
                    "failed": self.results["failed"],
                    "success_rate": success_rate
                },
                "endpoints": {k: {
                    "success": v["success"], 
                    "status_code": v["status_code"],
                    "error": v["error"]
                } for k, v in self.results["endpoints"].items()}
            }, f, indent=4)
        
        console.print(f"\nResults saved to [cyan]api_test_results.json[/cyan]")
        
        # Report to console
        if self.results["failed"] > 0:
            console.print("\n[bold red]❌ Some tests failed. See details above.[/bold red]")
        else:
            console.print("\n[bold green]✅ All tests passed![/bold green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Smart Tourist Safety API endpoints")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", default="8000", help="API port (default: 8000)")
    
    args = parser.parse_args()
    BASE_URL = f"http://{args.host}:{args.port}"
    
    console.print(Panel(f"[bold blue]Smart Tourist Safety API Tester[/bold blue]\n[cyan]Testing API at: {BASE_URL}[/cyan]"))
    
    tester = APITester()
    tester.run_all_tests()
    tester.print_summary()