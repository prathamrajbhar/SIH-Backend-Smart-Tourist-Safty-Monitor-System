"""
🚨 Alert Management System for Smart Tourist Safety

This service handles:
1. Real-time alert routing to police dashboard, family, and tourist app
2. Emergency notifications via multiple channels
3. Alert escalation based on severity levels
4. Integration with AI assessment results
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Alert, Tourist, AlertSeverity, AlertType
import json

logger = logging.getLogger(__name__)


class AlertManagementService:
    """
    🚨 Real-time Alert Management & Notification System
    
    Routes alerts to appropriate channels:
    - Police Dashboard (for CRITICAL/HIGH alerts)
    - Family Emergency Contacts (for CRITICAL alerts)
    - Tourist Mobile App (for all alerts)
    - E-FIR generation (for CRITICAL incidents)
    """
    
    def __init__(self):
        self.db_session: Optional[Session] = None
        self.notification_channels = {
            'police_dashboard': True,
            'family_sms': True,
            'tourist_app': True,
            'email_alerts': True
        }
        
    async def initialize(self):
        """Initialize alert management service."""
        try:
            self.db_session = SessionLocal()
            logger.info("🚨 Alert Management Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Alert Management Service: {e}")
            raise

    async def process_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Process and route alert to appropriate channels.
        
        Args:
            alert_id: Alert ID to process
            
        Returns:
            Processing status and actions taken
        """
        try:
            alert = self.db_session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            tourist = self.db_session.query(Tourist).filter(Tourist.id == alert.tourist_id).first()
            if not tourist:
                raise ValueError(f"Tourist {alert.tourist_id} not found")
            
            logger.info(f"🚨 Processing {alert.severity} alert for tourist {tourist.name}")
            
            processing_results = {
                'alert_id': alert_id,
                'severity': alert.severity,
                'actions_taken': [],
                'notifications_sent': [],
                'errors': []
            }
            
            # Route based on severity level
            if alert.severity == AlertSeverity.CRITICAL:
                await self._handle_critical_alert(alert, tourist, processing_results)
                
            elif alert.severity == AlertSeverity.HIGH:
                await self._handle_high_alert(alert, tourist, processing_results)
                
            elif alert.severity == AlertSeverity.MEDIUM:
                await self._handle_medium_alert(alert, tourist, processing_results)
                
            else:  # LOW severity
                await self._handle_low_alert(alert, tourist, processing_results)
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing alert {alert_id}: {e}")
            raise

    async def _handle_critical_alert(self, alert: Alert, tourist: Tourist, results: Dict[str, Any]):
        """Handle CRITICAL severity alerts - highest priority."""
        try:
            logger.critical(f"🆘 CRITICAL ALERT: {alert.message}")
            
            # 1. Immediate police dashboard notification
            await self._notify_police_dashboard(alert, tourist, "EMERGENCY")
            results['notifications_sent'].append('police_dashboard')
            
            # 2. Emergency SMS to family contacts
            await self._notify_emergency_contacts(alert, tourist, "SMS")
            results['notifications_sent'].append('family_sms')
            
            # 3. Emergency call to family contacts (if possible)
            await self._notify_emergency_contacts(alert, tourist, "CALL")
            results['notifications_sent'].append('family_call')
            
            # 4. Push notification to tourist app
            await self._notify_tourist_app(alert, tourist, urgent=True)
            results['notifications_sent'].append('tourist_app')
            
            # 5. Auto-generate E-FIR for police
            efir_result = await self._auto_generate_efir(alert, tourist)
            if efir_result['success']:
                results['actions_taken'].append('auto_efir_generated')
            
            # 6. Escalate to higher authorities after 15 minutes if not resolved
            asyncio.create_task(self._schedule_escalation(alert.id, delay_minutes=15))
            results['actions_taken'].append('escalation_scheduled')
            
        except Exception as e:
            logger.error(f"Error handling critical alert: {e}")
            results['errors'].append(f"Critical alert handling failed: {e}")

    async def _handle_high_alert(self, alert: Alert, tourist: Tourist, results: Dict[str, Any]):
        """Handle HIGH severity alerts."""
        try:
            logger.warning(f"⚠️ HIGH ALERT: {alert.message}")
            
            # 1. Police dashboard notification
            await self._notify_police_dashboard(alert, tourist, "HIGH_PRIORITY")
            results['notifications_sent'].append('police_dashboard')
            
            # 2. SMS to emergency contacts
            await self._notify_emergency_contacts(alert, tourist, "SMS")
            results['notifications_sent'].append('family_sms')
            
            # 3. Push notification to tourist app
            await self._notify_tourist_app(alert, tourist, urgent=True)
            results['notifications_sent'].append('tourist_app')
            
        except Exception as e:
            logger.error(f"Error handling high alert: {e}")
            results['errors'].append(f"High alert handling failed: {e}")

    async def _handle_medium_alert(self, alert: Alert, tourist: Tourist, results: Dict[str, Any]):
        """Handle MEDIUM severity alerts."""
        try:
            logger.info(f"📱 MEDIUM ALERT: {alert.message}")
            
            # 1. Tourist app notification
            await self._notify_tourist_app(alert, tourist, urgent=False)
            results['notifications_sent'].append('tourist_app')
            
            # 2. Email to emergency contacts (non-urgent)
            await self._notify_emergency_contacts(alert, tourist, "EMAIL")
            results['notifications_sent'].append('family_email')
            
        except Exception as e:
            logger.error(f"Error handling medium alert: {e}")
            results['errors'].append(f"Medium alert handling failed: {e}")

    async def _handle_low_alert(self, alert: Alert, tourist: Tourist, results: Dict[str, Any]):
        """Handle LOW severity alerts."""
        try:
            logger.info(f"ℹ️ LOW ALERT: {alert.message}")
            
            # 1. Tourist app notification only
            await self._notify_tourist_app(alert, tourist, urgent=False)
            results['notifications_sent'].append('tourist_app')
            
        except Exception as e:
            logger.error(f"Error handling low alert: {e}")
            results['errors'].append(f"Low alert handling failed: {e}")

    # ========================================================================
    # 📲 NOTIFICATION CHANNEL IMPLEMENTATIONS
    # ========================================================================

    async def _notify_police_dashboard(self, alert: Alert, tourist: Tourist, priority: str):
        """Send alert to police dashboard."""
        try:
            dashboard_payload = {
                'type': 'TOURIST_ALERT',
                'priority': priority,
                'alert_id': alert.id,
                'tourist_id': tourist.id,
                'tourist_name': tourist.name,
                'tourist_contact': tourist.contact,
                'message': alert.message,
                'location': {
                    'latitude': float(alert.latitude) if alert.latitude else None,
                    'longitude': float(alert.longitude) if alert.longitude else None
                },
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity
            }
            
            # TODO: Integrate with actual police dashboard API
            logger.info(f"🚔 Police Dashboard Alert: {json.dumps(dashboard_payload, indent=2)}")
            
            # Simulate API call
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Failed to notify police dashboard: {e}")

    async def _notify_emergency_contacts(self, alert: Alert, tourist: Tourist, method: str):
        """Send notifications to emergency contacts."""
        try:
            contact_info = {
                'emergency_contact': tourist.emergency_contact,
                'tourist_name': tourist.name,
                'alert_message': alert.message,
                'location': f"Lat: {alert.latitude}, Lon: {alert.longitude}" if alert.latitude else "Unknown",
                'timestamp': alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if method == "SMS":
                sms_message = (
                    f"🆘 EMERGENCY ALERT for {tourist.name}\\n"
                    f"Status: {alert.message}\\n"
                    f"Location: {contact_info['location']}\\n"
                    f"Time: {contact_info['timestamp']}\\n"
                    f"Please contact authorities if needed."
                )
                
                # TODO: Integrate with Twilio SMS API
                logger.info(f"📱 SMS Alert to {tourist.emergency_contact}: {sms_message}")
                
            elif method == "CALL":
                # TODO: Integrate with Twilio Voice API
                logger.info(f"📞 Voice Call Alert to {tourist.emergency_contact}")
                
            elif method == "EMAIL":
                # TODO: Integrate with email service
                logger.info(f"📧 Email Alert to emergency contacts")
            
            await asyncio.sleep(0.1)  # Simulate API call
            
        except Exception as e:
            logger.error(f"Failed to notify emergency contacts via {method}: {e}")

    async def _notify_tourist_app(self, alert: Alert, tourist: Tourist, urgent: bool = False):
        """Send push notification to tourist mobile app."""
        try:
            push_payload = {
                'type': 'SAFETY_ALERT',
                'title': '🚨 Safety Alert' if urgent else 'ℹ️ Safety Notice',
                'message': alert.message,
                'urgent': urgent,
                'alert_id': alert.id,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat(),
                'location': {
                    'latitude': float(alert.latitude) if alert.latitude else None,
                    'longitude': float(alert.longitude) if alert.longitude else None
                }
            }
            
            # TODO: Integrate with Firebase Cloud Messaging (FCM)
            logger.info(f"📲 Tourist App Push: {json.dumps(push_payload, indent=2)}")
            
            await asyncio.sleep(0.1)  # Simulate API call
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")

    async def _auto_generate_efir(self, alert: Alert, tourist: Tourist) -> Dict[str, Any]:
        """Auto-generate E-FIR for critical incidents."""
        try:
            efir_data = {
                'alert_id': alert.id,
                'incident_description': f"Emergency alert from tourist {tourist.name}: {alert.message}",
                'incident_location': f"Latitude: {alert.latitude}, Longitude: {alert.longitude}",
                'witnesses': "Tourist safety monitoring system",
                'evidence': f"AI-generated alert with severity: {alert.severity}",
                'police_station': "Smart Tourism Police Station",
                'officer_name': "AI System Auto-Generated"
            }
            
            # TODO: Call E-FIR API endpoint
            logger.info(f"⚖️ Auto-generated E-FIR for alert {alert.id}")
            
            return {'success': True, 'efir_data': efir_data}
            
        except Exception as e:
            logger.error(f"Failed to auto-generate E-FIR: {e}")
            return {'success': False, 'error': str(e)}

    async def _schedule_escalation(self, alert_id: int, delay_minutes: int = 15):
        """Schedule alert escalation if not resolved within time limit."""
        try:
            await asyncio.sleep(delay_minutes * 60)  # Convert to seconds
            
            # Check if alert is still active
            alert = self.db_session.query(Alert).filter(Alert.id == alert_id).first()
            if alert and alert.status == 'active':
                logger.warning(f"🚨 Escalating unresolved alert {alert_id} after {delay_minutes} minutes")
                
                # TODO: Escalate to higher authorities, additional notifications
                # For now, just log the escalation
                
        except Exception as e:
            logger.error(f"Error in alert escalation for alert {alert_id}: {e}")

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get real-time alert statistics."""
        try:
            stats = {
                'active_alerts': self.db_session.query(Alert).filter(Alert.status == 'active').count(),
                'critical_alerts': self.db_session.query(Alert).filter(
                    Alert.severity == AlertSeverity.CRITICAL, Alert.status == 'active'
                ).count(),
                'alerts_last_hour': self.db_session.query(Alert).filter(
                    Alert.timestamp >= datetime.utcnow() - timedelta(hours=1)
                ).count(),
                'notification_status': self.notification_channels
            }
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}


# Global alert management service instance
alert_management_service = AlertManagementService()