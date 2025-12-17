"""
Seeding script for Supabase database with tourist safety test data
"""
from datetime import datetime, timedelta
from faker import Faker
import random
import logging
import asyncio
import json
from typing import List, Dict, Any

from app.database import get_supabase
from app.models.alert import AlertType, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)
fake = Faker('en_IN')  # Indian locale


# Indian cities with coordinates
CITIES = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Goa": {"lat": 15.2993, "lon": 74.1240},
    "Shillong": {"lat": 25.5788, "lon": 91.8933},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Kerala": {"lat": 10.8505, "lon": 76.2711},
    "Manali": {"lat": 32.2396, "lon": 77.1887},
    "Rishikesh": {"lat": 30.0869, "lon": 78.2676},
    "Udaipur": {"lat": 24.5854, "lon": 73.7125},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739}
}


async def seed_tourists(count: int = 100) -> List[Dict]:
    """Generate sample tourists in Supabase"""
    supabase = get_supabase()
    tourists = []
        
    for i in range(count):
        tourist = {
            "name": fake.name(),
            "contact": fake.phone_number()[:15],  # Ensure it fits in the field
            "email": fake.email() if random.choice([True, False]) else None,
            "trip_info": {
                "duration_days": random.randint(3, 14),
                "purpose": random.choice(["leisure", "business", "pilgrimage", "adventure"]),
                "group_size": random.randint(1, 6),
                "preferred_activities": random.sample([
                    "sightseeing", "photography", "trekking", "cultural_tours", 
                    "food_tours", "shopping", "religious_visits", "adventure_sports"
                ], k=random.randint(1, 4))
            },
            "emergency_contact": fake.phone_number()[:15],
            "safety_score": random.randint(60, 100),  # Most tourists start with good scores
            "age": random.randint(18, 75),
            "nationality": random.choice(["Indian", "American", "British", "German", "French", "Japanese", "Australian"]),
            "passport_number": fake.passport_number() if random.choice([True, False, False]) else None,  # 1/3 have passports
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        tourists.append(tourist)
    
    # Insert in batches for performance
    batch_size = 20
    for i in range(0, len(tourists), batch_size):
        batch = tourists[i:i+batch_size]
        result = supabase.table("tourists").insert(batch).execute()
        logger.info(f"Inserted {len(result.data)} tourists (batch {i//batch_size + 1})")
    
    # Fetch all inserted tourists
    result = supabase.table("tourists").select("*").execute()
    logger.info(f"Generated {len(result.data)} sample tourists")
    return result.data


async def seed_locations(tourists: List[Dict]) -> List[Dict]:
    """Generate location data for tourists in Supabase"""
    supabase = get_supabase()
    locations = []
    
    for tourist in tourists:
        # Each tourist gets 5-20 location points over the last few days
        num_locations = random.randint(5, 20)
        base_city = random.choice(list(CITIES.keys()))
        base_coords = CITIES[base_city]
        
        for i in range(num_locations):
            # Generate location within ~10km radius of base city
            lat_offset = random.uniform(-0.1, 0.1)  # ~11km at equator
            lon_offset = random.uniform(-0.1, 0.1)
            
            # Create timestamps over the past week
            hours_ago = random.randint(0, 24 * 7)  # Up to a week ago
            timestamp = datetime.utcnow() - timedelta(hours=hours_ago)
            
            location = {
                "tourist_id": tourist["id"],
                "latitude": base_coords["lat"] + lat_offset,
                "longitude": base_coords["lon"] + lon_offset,
                "altitude": random.uniform(0, 1000) if random.choice([True, False]) else None,
                "accuracy": random.uniform(5, 50),
                "speed": random.uniform(0, 20) if random.choice([True, False, False]) else None,
                "heading": random.uniform(0, 359) if random.choice([True, False, False]) else None,
                "timestamp": timestamp.isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            locations.append(location)
    
    # Insert in batches for performance
    batch_size = 50
    for i in range(0, len(locations), batch_size):
        batch = locations[i:i+batch_size]
        result = supabase.table("locations").insert(batch).execute()
        logger.info(f"Inserted {len(result.data)} locations (batch {i//batch_size + 1})")
    
    # Update tourists' last location
    for tourist in tourists:
        # Find the latest location for this tourist
        tourist_locations = [loc for loc in locations if loc["tourist_id"] == tourist["id"]]
        if tourist_locations:
            latest_location = max(tourist_locations, key=lambda x: x["timestamp"])
            supabase.table("tourists").update({
                "last_location_update": latest_location["timestamp"],
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", tourist["id"]).execute()
    
    logger.info(f"Generated {len(locations)} sample locations")
    return locations


async def seed_restricted_zones() -> List[Dict]:
    """Generate restricted zones in Supabase"""
    supabase = get_supabase()
    
    # Create zone templates for major cities
    zone_templates = [
        # Delhi military area
        {
            "name": "Delhi Military Zone",
            "description": "Restricted military area, no civilian access",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [77.2090, 28.6139],  # Center point of Delhi
                        [77.2290, 28.6139], 
                        [77.2290, 28.6339],
                        [77.2090, 28.6339],
                        [77.2090, 28.6139]
                    ]
                ]
            },
            "danger_level": 5,
            "buffer_zone_meters": 200
        },
        # Mumbai dangerous area
        {
            "name": "Mumbai Construction Site",
            "description": "Dangerous construction area with heavy machinery",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [72.8777, 19.0760],  # Center point of Mumbai
                        [72.8977, 19.0760],
                        [72.8977, 19.0960],
                        [72.8777, 19.0960],
                        [72.8777, 19.0760]
                    ]
                ]
            },
            "danger_level": 4,
            "buffer_zone_meters": 100
        },
        # Goa beach restricted area
        {
            "name": "Goa Protected Beach",
            "description": "Protected marine ecosystem, limited access",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [74.1240, 15.2993],  # Center point of Goa
                        [74.1440, 15.2993],
                        [74.1440, 15.3193],
                        [74.1240, 15.3193],
                        [74.1240, 15.2993]
                    ]
                ]
            },
            "danger_level": 3,
            "buffer_zone_meters": 50
        },
        # Shillong landslide risk area
        {
            "name": "Shillong Landslide Risk Zone",
            "description": "Area with high landslide risk during monsoon",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [91.8933, 25.5788],  # Center point of Shillong
                        [91.9133, 25.5788],
                        [91.9133, 25.5988],
                        [91.8933, 25.5988],
                        [91.8933, 25.5788]
                    ]
                ]
            },
            "danger_level": 4,
            "buffer_zone_meters": 150
        },
        # Jaipur private property
        {
            "name": "Jaipur Private Estate",
            "description": "Private property, no trespassing",
            "coordinates": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [75.7873, 26.9124],  # Center point of Jaipur
                        [75.8073, 26.9124],
                        [75.8073, 26.9324],
                        [75.7873, 26.9324],
                        [75.7873, 26.9124]
                    ]
                ]
            },
            "danger_level": 2,
            "buffer_zone_meters": 50
        }
    ]
    
    # Insert all zones
    result = supabase.table("restricted_zones").insert(zone_templates).execute()
    logger.info(f"Generated {len(result.data)} restricted zones")
    
    return result.data


async def seed_alerts(tourists: List[Dict], locations: List[Dict]) -> List[Dict]:
    """Generate sample alerts in Supabase"""
    supabase = get_supabase()
    alerts = []
    
    # Create a few panic alerts (10% of tourists)
    panic_tourists = random.sample(tourists, k=min(len(tourists) // 10, 10))
    
    for tourist in panic_tourists:
        # Find a random location for this tourist
        tourist_locations = [loc for loc in locations if loc["tourist_id"] == tourist["id"]]
        if not tourist_locations:
            continue
            
        location = random.choice(tourist_locations)
        
        alert = {
            "tourist_id": tourist["id"],
            "type": "panic",
            "severity": random.choice(["MEDIUM", "HIGH", "CRITICAL"]),
            "message": random.choice([
                "Help needed immediately!",
                "I don't feel safe here",
                "Medical emergency",
                "Being followed by suspicious person",
                "Lost and need assistance"
            ]),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "auto_generated": False,
            "acknowledged": random.choice([True, False]),
            "status": random.choice(["active", "resolved"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        alerts.append(alert)
    
    # Insert all alerts
    if alerts:
        result = supabase.table("alerts").insert(alerts).execute()
        logger.info(f"Generated {len(result.data)} sample alerts")
    else:
        logger.warning("No alerts were generated")
        result = {"data": []}
    
    return result.data


async def seed_database():
    """Main seeding function that populates all tables"""
    logger.info("Starting database seeding process...")
    
    try:
        # Check if we already have data
        supabase = get_supabase()
        existing_tourists = supabase.table("tourists").select("count", count="exact").execute()
        
        if existing_tourists.count > 0:
            logger.info(f"Database already contains {existing_tourists.count} tourists. Skipping seeding.")
            return
            
        # Generate data in correct order due to foreign keys
        tourists = await seed_tourists(100)  # Generate 100 tourists
        await asyncio.sleep(1)  # Small delay to ensure tourists are fully saved
        
        locations = await seed_locations(tourists)
        await asyncio.sleep(1)
        
        zones = await seed_restricted_zones()
        await asyncio.sleep(1)
        
        alerts = await seed_alerts(tourists, locations)
        
        logger.info("Database seeding completed successfully!")
        logger.info(f"Created: {len(tourists)} tourists, {len(locations)} locations, {len(zones)} zones, {len(alerts)} alerts")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise