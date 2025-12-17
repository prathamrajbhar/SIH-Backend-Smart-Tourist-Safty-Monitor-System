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
            tourist = Tourist(
                name=fake.name(),
                contact=fake.phone_number()[:15],  # Ensure it fits in the field
                email=fake.email() if random.choice([True, False]) else None,
                trip_info={
                    "duration_days": random.randint(3, 14),
                    "purpose": random.choice(["leisure", "business", "pilgrimage", "adventure"]),
                    "group_size": random.randint(1, 6),
                    "preferred_activities": random.sample([
                        "sightseeing", "photography", "trekking", "cultural_tours", 
                        "food_tours", "shopping", "religious_visits", "adventure_sports"
                    ], k=random.randint(1, 4))
                },
                emergency_contact=fake.phone_number()[:15],
                safety_score=random.randint(60, 100),  # Most tourists start with good scores
                age=random.randint(18, 75),
                nationality=random.choice(["Indian", "American", "British", "German", "French", "Japanese", "Australian"]),
                passport_number=fake.passport_number() if random.choice([True, False, False]) else None,  # 1/3 have passports
                is_active=True
            )
            tourists.append(tourist)
        
        self.db.add_all(tourists)
        self.db.commit()
        
        # Refresh to get IDs
        for tourist in tourists:
            self.db.refresh(tourist)
        
        logger.info(f"Generated {len(tourists)} sample tourists")
        return tourists

    async def generate_locations(self, tourists: List[Tourist]) -> List[Location]:
        """
        Generate location data for tourists.
        """
        locations = []
        
        for tourist in tourists:
            # Each tourist gets 5-20 location points over the last few days
            num_locations = random.randint(5, 20)
            base_city = random.choice(list(self.CITIES.keys()))
            base_coords = self.CITIES[base_city]
            
            for i in range(num_locations):
                # Generate location within ~10km radius of base city
                lat_offset = random.uniform(-0.1, 0.1)  # ~11km at equator
                lon_offset = random.uniform(-0.1, 0.1)
                
                location = Location(
                    tourist_id=tourist.id,
                    latitude=base_coords["lat"] + lat_offset,
                    longitude=base_coords["lon"] + lon_offset,
                    altitude=random.uniform(0, 1000) if random.choice([True, False]) else None,
                    accuracy=random.uniform(5, 50),
                    speed=random.uniform(0, 60) if random.choice([True, False]) else None,
                    heading=random.uniform(0, 360) if random.choice([True, False]) else None,
                    timestamp=datetime.utcnow() - timedelta(
                        hours=random.uniform(0, 72)  # Within last 3 days
                    )
                )
                locations.append(location)
            
            # Update tourist's last location update
            tourist.last_location_update = max(
                [loc.timestamp for loc in locations if loc.tourist_id == tourist.id]
            )
        
        self.db.add_all(locations)
        self.db.commit()
        
        logger.info(f"Generated {len(locations)} location records")
        return locations

    async def generate_safe_zones(self) -> List[SafeZone]:
        """
        Generate safe zones in major tourist areas.
        """
        safe_zones = []
        
        safe_zone_templates = [
            {
                "name": "Red Fort Tourist Area",
                "city": "Delhi",
                "coordinates": {"coordinates": [[[77.2395, 28.6562], [77.2405, 28.6562], [77.2405, 28.6572], [77.2395, 28.6572], [77.2395, 28.6562]]]},
                "zone_type": ZoneType.TOURIST_AREA,
                "description": "Historic Red Fort and surrounding tourist facilities"
            },
            {
                "name": "Gateway of India Area",
                "city": "Mumbai", 
                "coordinates": {"coordinates": [[[72.8342, 18.9220], [72.8352, 18.9220], [72.8352, 18.9230], [72.8342, 18.9230], [72.8342, 18.9220]]]},
                "zone_type": ZoneType.TOURIST_AREA,
                "description": "Gateway of India and Colaba tourist district"
            },
            {
                "name": "Baga Beach Safe Zone",
                "city": "Goa",
                "coordinates": {"coordinates": [[[73.7519, 15.5557], [73.7529, 15.5557], [73.7529, 15.5567], [73.7519, 15.5567], [73.7519, 15.5557]]]},
                "zone_type": ZoneType.TOURIST_AREA,
                "description": "Popular beach area with lifeguards and police presence"
            },
            {
                "name": "Police Khyndailad",
                "city": "Shillong",
                "coordinates": {"coordinates": [[[91.8863, 25.5788], [91.8873, 25.5788], [91.8873, 25.5798], [91.8863, 25.5798], [91.8863, 25.5788]]]},
                "zone_type": ZoneType.POLICE_STATION,
                "description": "Main police station area"
            },
            {
                "name": "AIIMS Delhi",
                "city": "Delhi",
                "coordinates": {"coordinates": [[[77.2075, 28.5665], [77.2085, 28.5665], [77.2085, 28.5675], [77.2075, 28.5675], [77.2075, 28.5665]]]},
                "zone_type": ZoneType.HOSPITAL,
                "description": "Major hospital complex"
            }
        ]
        
        for template in safe_zone_templates:
            safe_zone = SafeZone(**template)
            safe_zones.append(safe_zone)
        
        self.db.add_all(safe_zones)
        self.db.commit()
        
        logger.info(f"Generated {len(safe_zones)} safe zones")
        return safe_zones

    async def generate_restricted_zones(self) -> List[RestrictedZone]:
        """
        Generate restricted/dangerous zones.
        """
        restricted_zones = []
        
        restricted_zone_templates = [
            {
                "name": "Delhi Military Cantonment",
                "city": "Delhi",
                "coordinates": {"coordinates": [[[77.1800, 28.5800], [77.1850, 28.5800], [77.1850, 28.5850], [77.1800, 28.5850], [77.1800, 28.5800]]]},
                "zone_type": RestrictedZoneType.MILITARY,
                "description": "Military area - civilian access restricted",
                "danger_level": 4
            },
            {
                "name": "Mumbai Industrial Zone",
                "city": "Mumbai",
                "coordinates": {"coordinates": [[[72.8500, 19.0500], [72.8550, 19.0500], [72.8550, 19.0550], [72.8500, 19.0550], [72.8500, 19.0500]]]},
                "zone_type": RestrictedZoneType.DANGEROUS,
                "description": "Industrial area with chemical plants - avoid after dark",
                "danger_level": 3
            },
            {
                "name": "Goa Cliff Area",
                "city": "Goa",
                "coordinates": {"coordinates": [[[73.7400, 15.5400], [73.7450, 15.5400], [73.7450, 15.5450], [73.7400, 15.5450], [73.7400, 15.5400]]]},
                "zone_type": RestrictedZoneType.NATURAL_HAZARD,
                "description": "Dangerous cliff area - frequent accidents",
                "danger_level": 5
            },
            {
                "name": "Shillong Forest Reserve",
                "city": "Shillong", 
                "coordinates": {"coordinates": [[[91.8500, 25.5500], [91.8600, 25.5500], [91.8600, 25.5600], [91.8500, 25.5600], [91.8500, 25.5500]]]},
                "zone_type": RestrictedZoneType.RESTRICTED,
                "description": "Protected forest area - permits required",
                "danger_level": 2
            },
            {
                "name": "Construction Zone - Ring Road",
                "city": "Delhi",
                "coordinates": {"coordinates": [[[77.2200, 28.6200], [77.2250, 28.6200], [77.2250, 28.6250], [77.2200, 28.6250], [77.2200, 28.6200]]]},
                "zone_type": RestrictedZoneType.CONSTRUCTION,
                "description": "Major road construction - heavy machinery operating",
                "danger_level": 3
            },
            {
                "name": "Private Port Area",
                "city": "Mumbai",
                "coordinates": {"coordinates": [[[72.8400, 18.9400], [72.8450, 18.9400], [72.8450, 18.9450], [72.8400, 18.9450], [72.8400, 18.9400]]]},
                "zone_type": RestrictedZoneType.PRIVATE,
                "description": "Private port facility - no public access",
                "danger_level": 2
            },
            {
                "name": "Landslide Prone Area",
                "city": "Shillong",
                "coordinates": {"coordinates": [[[91.8700, 25.5700], [91.8750, 25.5700], [91.8750, 25.5750], [91.8700, 25.5750], [91.8700, 25.5700]]]},
                "zone_type": RestrictedZoneType.NATURAL_HAZARD,
                "description": "Area prone to landslides during monsoon",
                "danger_level": 4
            }
        ]
        
        for template in restricted_zone_templates:
            restricted_zone = RestrictedZone(**template)
            restricted_zones.append(restricted_zone)
        
        self.db.add_all(restricted_zones)
        self.db.commit()
        
        logger.info(f"Generated {len(restricted_zones)} restricted zones")
        return restricted_zones

    async def generate_sample_alerts(self, tourists: List[Tourist]) -> List[Alert]:
        """
        Generate some sample alerts for demonstration.
        """
        alerts = []
        
        # Select some tourists for alerts
        alert_tourists = random.sample(tourists, min(15, len(tourists)))
        
        for tourist in alert_tourists:
            # Generate 1-3 alerts per selected tourist
            num_alerts = random.randint(1, 3)
            
            for _ in range(num_alerts):
                alert_type = random.choice(list(AlertType))
                
                # Set severity based on type
                if alert_type in [AlertType.PANIC, AlertType.SOS]:
                    severity = AlertSeverity.CRITICAL
                elif alert_type in [AlertType.GEOFENCE, AlertType.LOW_SAFETY_SCORE]:
                    severity = random.choice([AlertSeverity.HIGH, AlertSeverity.MEDIUM])
                else:
                    severity = random.choice([AlertSeverity.LOW, AlertSeverity.MEDIUM])
                
                # Generate appropriate message
                messages = {
                    AlertType.PANIC: "Emergency panic button activated!",
                    AlertType.SOS: "SOS signal received from tourist",
                    AlertType.GEOFENCE: "Tourist entered restricted area",
                    AlertType.ANOMALY: "Unusual movement pattern detected",
                    AlertType.TEMPORAL: "Tourist inactive for extended period",
                    AlertType.LOW_SAFETY_SCORE: "Safety score dropped below threshold",
                    AlertType.MANUAL: "Manual alert created by operator"
                }
                
                alert = Alert(
                    tourist_id=tourist.id,
                    type=alert_type,
                    severity=severity,
                    message=messages.get(alert_type, "Alert triggered"),
                    description=fake.text(max_nb_chars=200),
                    latitude=random.uniform(15, 32) if random.choice([True, False]) else None,
                    longitude=random.uniform(72, 92) if random.choice([True, False]) else None,
                    auto_generated=alert_type in [AlertType.GEOFENCE, AlertType.ANOMALY, AlertType.TEMPORAL, AlertType.LOW_SAFETY_SCORE],
                    timestamp=datetime.utcnow() - timedelta(hours=random.uniform(0, 48)),
                    status=random.choice([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]),
                    ai_confidence=random.uniform(0.7, 0.99) if alert_type in [AlertType.ANOMALY, AlertType.TEMPORAL] else None
                )
                
                # For resolved alerts, add resolution info
                if alert.status == AlertStatus.RESOLVED:
                    alert.resolved_at = alert.timestamp + timedelta(hours=random.uniform(1, 24))
                    alert.resolved_by = random.choice(["System", "Operator1", "Operator2", "Police"])
                    alert.resolution_notes = "Alert resolved successfully"
                
                # For acknowledged alerts, add acknowledgment info
                if alert.status == AlertStatus.ACKNOWLEDGED:
                    alert.acknowledged = True
                    alert.acknowledged_at = alert.timestamp + timedelta(minutes=random.uniform(5, 60))
                    alert.acknowledged_by = random.choice(["Operator1", "Operator2", "Police"])
                
                alerts.append(alert)
        
        self.db.add_all(alerts)
        self.db.commit()
        
        logger.info(f"Generated {len(alerts)} sample alerts")
        return alerts


async def seed_database(db: Session):
    """
    Main function to seed the database with demo data.
    """
    try:
        generator = SeedDataGenerator(db)
        
        # Check if data already exists
        existing_tourists = db.query(Tourist).count()
        if existing_tourists > 0:
            logger.info(f"Database already has {existing_tourists} tourists. Skipping seed data generation.")
            return
        
        logger.info("Starting database seeding...")
        
        # Generate sample data
        tourists = await generator.generate_tourists(100)
        locations = await generator.generate_locations(tourists)
        safe_zones = await generator.generate_safe_zones()
        restricted_zones = await generator.generate_restricted_zones()
        alerts = await generator.generate_sample_alerts(tourists)
        
        logger.info("Database seeding completed successfully!")
        logger.info(f"Created: {len(tourists)} tourists, {len(locations)} locations, "
                   f"{len(safe_zones)} safe zones, {len(restricted_zones)} restricted zones, "
                   f"{len(alerts)} alerts")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise