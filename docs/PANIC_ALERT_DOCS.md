# 🚔 Panic Alert & Police Dashboard API

## Overview
The Smart Tourist Safety System now includes complete panic alert management with police dashboard integration. When tourists create panic alerts, they are automatically saved to the database and can be forwarded to police systems.

## API Endpoints

### 1. Create SOS/Panic Alert (Already Exists)
**Endpoint:** `POST /alerts/pressSOS`

**Purpose:** Create emergency SOS alert for tourist (automatically saved to database)

**Request:**
```json
{
  "tourist_id": 123,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "message": "Emergency SOS - immediate help needed!"
}
```

**Response:**
```json
{
  "id": 456,
  "tourist_id": 123,
  "type": "panic",
  "severity": "CRITICAL",
  "message": "🆘 EMERGENCY SOS: Emergency SOS - immediate help needed!",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "status": "active",
  "timestamp": "2025-09-27T10:30:00"
}
```

### 2. Send Panic Alert to Police Dashboard (NEW)
**Endpoint:** `POST /alerts/sendPanicToPoliceDashboard/{alert_id}`

**Purpose:** Forward existing panic/SOS alert to police dashboard

**Request:**
```bash
POST /alerts/sendPanicToPoliceDashboard/456
```

**Success Response:**
```json
{
  "success": true,
  "message": "Panic alert sent to police dashboard",
  "alert_id": 456,
  "police_status": 200
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Timeout connecting to police dashboard",
  "alert_id": 456
}
```

### 3. Get Panic Alerts Count (NEW)
**Endpoint:** `GET /alerts/panicAlertsCount`

**Purpose:** Get count of panic/SOS alerts from database with breakdown

**Response:**
```json
{
  "total_panic_alerts": 15,
  "breakdown": {
    "active": 5,
    "acknowledged": 8,
    "resolved": 2,
    "critical_severity": 12
  },
  "timestamp": "2025-09-27T10:30:00"
}
```

### 4. Get All Alerts (Already Exists)
**Endpoint:** `GET /alerts/getAlerts`

**Purpose:** Retrieve all alerts with filtering options

**Query Parameters:**
- `alert_type=panic` - Filter for panic alerts only
- `status=active` - Filter by status
- `severity=CRITICAL` - Filter by severity

**Example:**
```bash
GET /alerts/getAlerts?alert_type=panic&status=active
```

## Database Integration

### Automatic Saving
✅ **All panic alerts are automatically saved to database when created**
- Panic alerts saved to `alerts` table
- Tourist safety score automatically updated (-40 for SOS)
- Alert status tracking (active → acknowledged → resolved)

### Database Schema
```sql
-- Alerts table structure
alerts {
  id: bigint (primary key)
  tourist_id: bigint (foreign key)
  type: varchar ('panic', 'sos', etc.)
  severity: varchar ('CRITICAL', 'HIGH', etc.)
  message: text
  latitude: numeric
  longitude: numeric
  status: varchar ('active', 'acknowledged', 'resolved')
  acknowledged: boolean
  acknowledged_by: varchar
  timestamp: timestamp
}
```

## Police Dashboard Integration

### Data Sent to Police
```json
{
  "alert_id": 456,
  "emergency_type": "TOURIST_PANIC_SOS",
  "severity": "CRITICAL",
  "timestamp": "2025-09-27T10:30:00",
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "tourist": {
    "id": 123,
    "name": "John Doe",
    "contact": "+919876543210",
    "emergency_contact": "+919876543211"
  },
  "message": "Emergency SOS - immediate help needed!",
  "priority": "CRITICAL"
}
```

### Configuration
Set environment variable for police dashboard URL:
```bash
POLICE_DASHBOARD_URL=http://police-api.example.com/emergency
```

### Auto-Acknowledgment
When alert is successfully sent to police:
- Alert marked as `acknowledged = true`
- `acknowledged_by = "Police Dashboard"`
- `acknowledged_at` timestamp set

## Complete Workflow

### 1. Tourist Presses SOS
```bash
POST /alerts/pressSOS
```
- ✅ Alert created and saved to database
- ✅ Tourist safety score updated
- ✅ Alert gets unique ID for tracking

### 2. System Forwards to Police
```bash
POST /alerts/sendPanicToPoliceDashboard/{alert_id}
```
- ✅ Alert data sent to police dashboard
- ✅ Database updated with acknowledgment status
- ✅ Response indicates success/failure

### 3. Monitor Alert Counts
```bash
GET /alerts/panicAlertsCount
```
- ✅ Get real-time count from database
- ✅ Breakdown by status and severity
- ✅ Track system performance

### 4. Retrieve All Panic Alerts
```bash
GET /alerts/getAlerts?alert_type=panic
```
- ✅ Get all panic alerts from database
- ✅ Filter by status, severity, etc.
- ✅ Pagination support

## Error Handling

### Database Errors
- Invalid tourist ID → 404 Not Found
- Database connection issues → 500 Internal Server Error
- Data validation failures → 400 Bad Request

### Police Dashboard Errors
- Network timeout → success: false, timeout message
- Police API error → success: false, API error details
- Invalid alert type → 400 Bad Request (only panic/SOS allowed)

## Testing

Run the test script:
```bash
python test_panic_system.py
```

This will:
1. ✅ Register a test tourist
2. ✅ Create a panic alert (saved to database)
3. ✅ Get panic alerts count from database
4. ✅ Send alert to police dashboard
5. ✅ Verify database updates
6. ✅ Retrieve all panic alerts

## Usage Examples

### Create and Track Panic Alert
```python
import httpx

async def handle_emergency(tourist_id, lat, lon):
    async with httpx.AsyncClient() as client:
        # 1. Create panic alert (auto-saved to DB)
        panic_data = {
            "tourist_id": tourist_id,
            "latitude": lat,
            "longitude": lon,
            "message": "Tourist emergency!"
        }
        
        response = await client.post(
            "http://localhost:8000/alerts/pressSOS",
            json=panic_data
        )
        alert = response.json()
        alert_id = alert["id"]
        
        # 2. Send to police dashboard
        police_response = await client.post(
            f"http://localhost:8000/alerts/sendPanicToPoliceDashboard/{alert_id}"
        )
        
        # 3. Check current panic count
        count_response = await client.get(
            "http://localhost:8000/alerts/panicAlertsCount"
        )
        count_data = count_response.json()
        
        print(f"Alert {alert_id} created and sent to police!")
        print(f"Total panic alerts: {count_data['total_panic_alerts']}")
```

## Key Benefits

### For Development
- ✅ All panic alerts automatically saved to database
- ✅ No manual database operations needed
- ✅ Built-in error handling and validation
- ✅ RESTful API design

### For Operations
- ✅ Real-time panic alert counting
- ✅ Police dashboard integration ready
- ✅ Alert status tracking and history
- ✅ Comprehensive logging and monitoring

### For Emergency Response
- ✅ Immediate database persistence
- ✅ Automated police notifications
- ✅ Complete audit trail
- ✅ Multi-channel alert management

## Summary

The system now provides:
1. **Automatic Database Saving** - All panic alerts saved when created
2. **Police Dashboard API** - Forward alerts to law enforcement
3. **Real-time Counting** - Get panic alert statistics from database  
4. **Complete Integration** - Uses existing alert management system

All functionality works with the existing database schema and API structure!