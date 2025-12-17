# 🚀 Smart Tourist Safety System - API Documentation

## 📋 Overview

This documentation provides comprehensive information about all API endpoints available in the Smart Tourist Safety System. This system provides real-time tourist safety monitoring with AI-powered risk assessment.

**Base URL:** `http://localhost:8000`  
**API Version:** 3.0.0  
**Documentation:** `/docs` (Swagger UI)  
**Database:** Supabase (Cloud PostgreSQL)

## 📝 **IMPORTANT: Actual Working Endpoints**

Based on live server testing, here are the **confirmed working endpoints**:

### ✅ **Core Tourist Management**
- `POST /registerTourist` - Register new tourist ✅ **Required Endpoint**
- `GET /tourists/{tourist_id}` - Get tourist details with activity

### ✅ **Location & Safety**
- `POST /sendLocation` - Send location & trigger AI assessment ✅ **Required Endpoint**

### ✅ **Emergency & Alerts**
- `POST /pressSOS` - Emergency SOS alert ✅ **Required Endpoint**
- `GET /getAlerts` - Get all alerts with filtering ✅ **Required Endpoint**
- `PUT /resolveAlert/{alert_id}` - Resolve an alert

### ✅ **Incident Reporting**
- `POST /fileEFIR` - File electronic incident report ✅ **Required Endpoint**

### ✅ **AI & Monitoring**
- `GET /ai/training/status` - AI training status
- `GET /ai/data/stats` - System data statistics
- `POST /ai/training/force` - Force AI training

### ✅ **System**
- `GET /` - Root endpoint with API info

---

## 🏗️ API Architecture

The API is built with:
- **Framework:** FastAPI (Python)
- **Database:** Supabase (Cloud PostgreSQL)
- **Authentication:** None (Development mode)
- **AI Processing:** Real-time background processing
- **Deployment:** Single server application

**Key Features:**
- Real-time location tracking with AI assessment
- Emergency SOS system with automatic notifications
- E-FIR (Electronic First Information Report) filing
- Continuous AI model training (60-second intervals)

---

## 🔐 Authentication & Headers

Currently, the API operates without authentication for development purposes.

**Required Headers:**
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 👥 Tourist Management API

### Register Tourist
**`POST /tourists/registerTourist`** ✅ **Required Endpoint**

Register a new tourist in the system.

**Request Body:**
```json
{
  "name": "John Doe",
  "contact": "+919876543210",
  "email": "john.doe@example.com",
  "emergency_contact": "+911234567890",
  "age": 28,
  "nationality": "Indian",
  "passport_number": "ABC123456",
  "trip_info": {
    "destination": "Goa",
    "duration": "7 days",
    "hotel": "Beach Resort"
  }
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "John Doe",
  "contact": "+919876543210",
  "email": "john.doe@example.com",
  "trip_info": {
    "destination": "Goa",
    "duration": "7 days",
    "hotel": "Beach Resort"
  },
  "emergency_contact": "+911234567890",
  "safety_score": 100,
  "age": 28,
  "nationality": "Indian",
  "passport_number": "ABC123456",
  "is_active": true,
  "last_location_update": null,
  "created_at": "2025-09-27T10:30:00Z",
  "updated_at": "2025-09-27T10:30:00Z"
}
```

### Get Tourist Details
**`GET /tourists/{tourist_id}`**

Retrieve detailed information about a specific tourist.

**Response (200):**
```json
{
  "id": 1,
  "name": "John Doe",
  "contact": "+919876543210",
  "safety_score": 85,
  "trip_info": {...},
  "emergency_contact": "+911234567890",
  "is_active": true,
  "last_location_update": "2025-09-27T12:15:00Z"
}
```

### List All Tourists
**`GET /tourists/`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Update Tourist
**`PUT /tourists/{tourist_id}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Deactivate Tourist
**`DELETE /tourists/{tourist_id}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

---

## 📍 Location Management API

### Send Location Update
**`POST /locations/sendLocation`** ✅ **Required Endpoint**

Send tourist's current location and trigger AI safety assessment.

**Request Body:**
```json
{
  "tourist_id": 1,
  "latitude": 15.4909,
  "longitude": 73.8278,
  "altitude": 10.5,
  "accuracy": 5.0,
  "speed": 2.5,
  "heading": 180.0,
  "timestamp": "2025-09-27T12:30:00Z"
}
```

**Response (201):**
```json
{
  "id": 123,
  "tourist_id": 1,
  "latitude": 15.4909,
  "longitude": 73.8278,
  "altitude": 10.5,
  "accuracy": 5.0,
  "speed": 2.5,
  "heading": 180.0,
  "timestamp": "2025-09-27T12:30:00Z",
  "created_at": "2025-09-27T12:30:00Z"
}
```

### Get All Tourist Locations
**`GET /locations/all`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Get Tourist Location History  
**`GET /locations/tourist/{tourist_id}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Get Latest Location
**`GET /locations/latest/{tourist_id}`** ❌ **Not Available**  

This endpoint is not currently implemented in the active server.

> **Note:** Location data is available through the tourist details endpoint (`GET /tourists/{tourist_id}`) which includes recent locations in the response.

---

## 🚨 Alert Management API

### Press SOS
**`POST /alerts/pressSOS`** ✅ **Required Endpoint**

Create an emergency SOS alert.

**Request Body:**
```json
{
  "tourist_id": 1,
  "latitude": 15.4909,
  "longitude": 73.8278,
  "message": "Emergency! Need immediate help!"
}
```

**Response (201):**
```json
{
  "id": 456,
  "tourist_id": 1,
  "type": "panic",
  "severity": "CRITICAL",
  "message": "🆘 EMERGENCY SOS: Emergency! Need immediate help!",
  "latitude": 15.4909,
  "longitude": 73.8278,
  "auto_generated": false,
  "acknowledged": false,
  "timestamp": "2025-09-27T12:35:00Z",
  "status": "active"
}
```

### Get Alerts
**`GET /alerts/getAlerts`** ✅ **Required Endpoint**

Retrieve alerts with filtering options.

**Query Parameters:**
- `status` (string, default="active"): Filter by status (active, acknowledged, resolved)
- `severity` (string): Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `alert_type` (string): Filter by type (panic, geofence, anomaly, temporal)
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=100): Maximum records to return

**Response (200):**
```json
[
  {
    "id": 456,
    "tourist_id": 1,
    "tourist_name": "John Doe",
    "type": "panic",
    "severity": "CRITICAL",
    "message": "🆘 EMERGENCY SOS: Emergency! Need immediate help!",
    "timestamp": "2025-09-27T12:35:00Z",
    "status": "active",
    "latitude": 15.4909,
    "longitude": 73.8278
  }
]
```

### Create Geofence Alert
**`POST /alerts/geofence`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Get Specific Alert
**`GET /alerts/{alert_id}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Resolve Alert  
**`PUT /resolveAlert/{alert_id}`** ✅ **Available**

Mark an alert as resolved.

**Query Parameters:**
- `resolution_notes` (string): Notes about the resolution

**Response (200):**
```json
{
  "success": true,
  "message": "Alert resolved successfully",
  "alert_id": 73,
  "resolved_at": "2025-09-27T13:00:00Z"
}
```

### Acknowledge Alert
**`PUT /alerts/{alert_id}/acknowledge`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Forward Panic Alert
**`POST /alerts/forwardAlert/{alert_id}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Get Panic Alerts Count
**`GET /alerts/panicAlertsCount`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

---

## 🧠 AI Assessment API

### Get AI Training Status
**`GET /ai/training/status`** ✅ **Available**

Get current status of AI models and training information.

**Response (200):**
```json
{
  "is_training": false,
  "last_training": "2025-09-27T12:00:00Z",
  "next_training": "2025-09-27T12:01:00Z", 
  "training_count": 12,
  "models_trained": ["isolation_forest", "temporal_analysis", "geofence_classifier"],
  "training_interval": "60 seconds",
  "status": "active"
}
```

### Get AI Data Statistics
**`GET /ai/data/stats`** ✅ **Available**

Get statistics about data available for AI training.

**Response (200):**
```json
{
  "total_locations": 651,
  "total_tourists": 38,
  "total_alerts": 32,
  "recent_locations_1h": 1,
  "recent_alerts_1h": 2,
  "data_freshness": "real-time",
  "last_updated": "2025-09-27T12:45:00Z"
}
```

### Force AI Training
**`POST /ai/training/force`** ✅ **Available**

Trigger immediate AI training cycle.

**Response (200):**
```json
{
  "message": "Manual training cycle initiated",
  "status": "initiated", 
  "next_scheduled": "2025-09-27T12:46:00Z"
}
```

### Other AI Endpoints ❌ **Not Available**

The following AI endpoints mentioned in other documentation are not currently implemented:
- `POST /ai/initialize`
- `GET /ai/status` 
- `POST /ai/assess/{tourist_id}`
- `GET /ai/assessment/{tourist_id}`
- `GET /ai/predictions/{assessment_id}`

---

## 📋 E-FIR Management API

### File E-FIR
**`POST /efir/fileEFIR`** ✅ **Required Endpoint**

File an electronic First Information Report.

**Request Body:**
```json
{
  "alert_id": 456,
  "incident_description": "Tourist reported missing in restricted area",
  "incident_location": "Baga Beach, Goa",
  "witnesses": "Local fishermen saw tourist around 2 PM",
  "evidence": "CCTV footage from nearby shop",
  "police_station": "Calangute Police Station",
  "officer_name": "Inspector Sharma"
}
```

**Response (201):**
```json
{
  "id": "EFIR-2025-09-27-000456",
  "alert_id": 456,
  "tourist_id": 1,
  "incident_description": "Tourist reported missing in restricted area",
  "incident_location": "Baga Beach, Goa",
  "witnesses": "Local fishermen saw tourist around 2 PM",
  "evidence": "CCTV footage from nearby shop",
  "police_station": "Calangute Police Station",
  "officer_name": "Inspector Sharma",
  "status": "FILED",
  "filed_at": "2025-09-27T13:00:00Z",
  "fir_number": "EFIR-2025-09-27-000456"
}
```

### Get E-FIR by Number
**`GET /efir/efir/{fir_number}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

### Get E-FIRs by Status
**`GET /efir/efirs/status/{status_filter}`** ❌ **Not Available**

This endpoint is not currently implemented in the active server.

---

## 🎯 Frontend Dashboard API ❌ **Not Available**

The frontend dashboard endpoints mentioned in other documentation are not currently implemented in the active server:

- `GET /frontend/dashboard/stats`
- `GET /frontend/tourists/cards`
- `GET /frontend/locations/cards`
- `GET /frontend/alerts/cards`
- `GET /frontend/safety/map`
- `GET /frontend/system/health`

**Alternative:** Use the available endpoints like `GET /ai/data/stats` for system statistics and `GET /tourists/{id}` for tourist information.

---

## 📊 Main Application Endpoints

### Root Endpoint
**`GET /`** ✅ **Available**

API information and health status.

**Response (200):**
```json
{
  "status": "healthy",
  "message": "Smart Tourist Safety System is operational",
  "version": "3.0.0",
  "database": "connected",
  "timestamp": "2025-09-27T13:20:00Z"
}
```

### Health Check
**`GET /health`** ❌ **Not Available**

This endpoint is not currently implemented in the active server. Use the root endpoint (`GET /`) for health status.

---

## 📝 Data Models

### Tourist Model
```json
{
  "id": 1,
  "name": "John Doe",
  "contact": "+919876543210",
  "email": "john@example.com",
  "trip_info": {},
  "emergency_contact": "+911234567890",
  "safety_score": 100,
  "age": 28,
  "nationality": "Indian",
  "passport_number": "ABC123456",
  "is_active": true,
  "last_location_update": "2025-09-27T12:00:00Z",
  "created_at": "2025-09-27T10:00:00Z",
  "updated_at": "2025-09-27T12:00:00Z"
}
```

### Location Model
```json
{
  "id": 123,
  "tourist_id": 1,
  "latitude": 15.4909,
  "longitude": 73.8278,
  "altitude": 10.5,
  "accuracy": 5.0,
  "speed": 2.5,
  "heading": 180.0,
  "timestamp": "2025-09-27T12:30:00Z",
  "created_at": "2025-09-27T12:30:00Z"
}
```

### Alert Model
```json
{
  "id": 456,
  "tourist_id": 1,
  "type": "panic",
  "severity": "CRITICAL",
  "message": "Emergency message",
  "description": "Detailed description",
  "latitude": 15.4909,
  "longitude": 73.8278,
  "ai_confidence": 0.95,
  "auto_generated": false,
  "acknowledged": false,
  "acknowledged_by": null,
  "acknowledged_at": null,
  "resolved_by": null,
  "resolved_at": null,
  "resolution_notes": null,
  "timestamp": "2025-09-27T12:35:00Z",
  "status": "active"
}
```

---

## 🔧 Enums & Constants

### Alert Types
- `panic` - Emergency SOS alert
- `geofence` - Geofence violation
- `anomaly` - AI-detected anomaly
- `temporal` - Time-based risk
- `low_safety_score` - Low safety score alert
- `sos` - SOS button press
- `manual` - Manually created

### Alert Severity
- `LOW` - Minor concern
- `MEDIUM` - Moderate risk
- `HIGH` - High risk
- `CRITICAL` - Emergency situation

### Alert Status
- `active` - Alert is active
- `acknowledged` - Alert acknowledged
- `resolved` - Alert resolved
- `false_alarm` - False alarm

---

## 🚀 Usage Examples

### Frontend Integration

#### 1. Tourist Registration Flow
```javascript
// Register a new tourist
const response = await fetch('/tourists/registerTourist', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'Jane Smith',
    contact: '+919876543210',
    emergency_contact: '+911234567890',
    trip_info: {
      destination: 'Goa',
      duration: '5 days'
    }
  })
});
const tourist = await response.json();
console.log('Tourist registered:', tourist.id);
```

#### 2. Send Location Update
```javascript
// Send GPS location
await fetch('/locations/sendLocation', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tourist_id: touristId,
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
    accuracy: position.coords.accuracy
  })
});
```

#### 3. Emergency SOS
```javascript
// Trigger emergency alert
const sosResponse = await fetch('/alerts/pressSOS', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tourist_id: touristId,
    latitude: currentLat,
    longitude: currentLng,
    message: 'Emergency assistance needed!'
  })
});
const alert = await sosResponse.json();
```

#### 4. Dashboard Data
```javascript
// Get dashboard statistics
const stats = await fetch('/frontend/dashboard/stats');
const dashboardData = await stats.json();

// Get active alerts
const alerts = await fetch('/alerts/getAlerts?status=active&limit=50');
const activeAlerts = await alerts.json();
```

---

## ⚠️ Error Handling

All endpoints return standard HTTP status codes:

- **200** - OK
- **201** - Created
- **204** - No Content
- **400** - Bad Request
- **404** - Not Found
- **500** - Internal Server Error
- **503** - Service Unavailable

**Error Response Format:**
```json
{
  "detail": "Tourist not found"
}
```

**Validation Error Format:**
```json
{
  "detail": [
    {
      "loc": ["body", "latitude"],
      "msg": "ensure this value is greater than or equal to -90",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": -90}
    }
  ]
}
```

---

## 🔄 Real-time Features

The system includes real-time capabilities:

1. **Location Tracking** - GPS updates trigger AI assessment
2. **Alert Generation** - Automatic alerts based on AI analysis
3. **Emergency Response** - Immediate SOS processing
4. **Dashboard Updates** - Live statistics and monitoring

---

## 🗄️ Database Integration

The API uses PostgreSQL with Supabase as the database backend:

**Connection:** Supabase Cloud Database  
**ORM:** SQLAlchemy  
**Migrations:** Automatic table creation on startup

---

## 📱 Mobile App Integration

**Required Endpoints for Mobile App:**
- `POST /tourists/registerTourist` - User registration
- `POST /locations/sendLocation` - GPS tracking
- `POST /alerts/pressSOS` - Emergency button
- `GET /alerts/getAlerts` - View alerts
- `POST /efir/fileEFIR` - File incident report

**Recommended Flow:**
1. User registers → calls `/registerTourist`
2. App sends location updates → calls `/sendLocation` every 30 seconds
3. Emergency button → calls `/pressSOS`
4. View incidents → calls `/getAlerts`

---

## 🖥️ Web Dashboard Integration

**Required Endpoints for Web Dashboard:**
- `GET /frontend/dashboard/stats` - Main statistics
- `GET /frontend/tourists/cards` - Tourist management
- `GET /frontend/alerts/cards` - Alert monitoring
- `GET /frontend/locations/cards` - Location tracking
- `GET /ai/status` - AI system status

---

## 📧 Support & Contact

For API support and questions:
- **Documentation:** `/docs` (Swagger UI)
- **Health Check:** `/health`
- **Version Info:** `/`

---

## 🏗️ System Architecture Notes

### Current Active Server
The system is currently running from **`main.py`** (root level) which implements direct FastAPI endpoints without routers. This provides **12 working endpoints** as documented above.

### Alternative Router-Based Structure
There is an alternative implementation in **`app/main.py`** that uses FastAPI routers and would provide endpoints under `/api/` prefix. However, this structure is **NOT currently active**.

**To switch to router-based structure:** Run `app/main.py` instead of root `main.py`

### Database Architecture
- **Database:** Supabase (Cloud PostgreSQL) - **NOT local PostgreSQL**
- **Connection:** Direct Supabase client integration
- **Configuration:** Environment variables for Supabase URL and API keys

### AI Engine Status
- **Training Interval:** 60 seconds
- **Models:** Isolation Forest, LSTM Autoencoder, LightGBM
- **Real-time Processing:** Location updates trigger AI assessment
- **Safety Scoring:** 0-100 scale with automatic alerts

---

*Last Updated: September 27, 2025*  
*API Version: 3.0.0*  
*Database: Supabase Cloud PostgreSQL*