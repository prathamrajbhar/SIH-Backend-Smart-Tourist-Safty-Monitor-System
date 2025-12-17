"""
Model classes for the Smart Tourist Safety System
"""
from app.models.alert import Alert, AlertType, AlertStatus, AlertSeverity
from app.models.tourist import Tourist
from app.models.location import Location
from app.models.zone import RestrictedZone, SafeZone, ZoneType

__all__ = [
    'Alert', 'AlertType', 'AlertStatus', 'AlertSeverity',
    'Tourist',
    'Location',
    'RestrictedZone', 'SafeZone', 'ZoneType'
]