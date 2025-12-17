# 🌐 Smart Tourist Safety API - Complete Endpoint Documentation

## 🔗 Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 📖 API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🏠 System Endpoints

### Health Check
Monitor system status and database connectivity.

#### `GET /health`
**Description**: Check system health and database status
**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1695825600,
  "version": "1.0.0",
  "database": "connected"
}
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/health"
```

---

## 👥 Tourist Management

### Register New Tourist
Register a tourist in the system with safety tracking enabled.

#### `POST /registerTourist` ⭐ **Required Endpoint**
**Description**: Register a new tourist with personal and emergency information
**Authentication**: None (public endpoint)

**Request Body**:
```json
{
  "name": "John Doe",
  "contact": "+91-9876543210",
  "email": "john.doe@email.com",
  "emergency_contact": "+91-9876543211",
  "trip_info": {
    "destination": "Goa",
    "duration": "5 days",
    "hotel": "Beach Resort"
  },
  "age": 28,
  "nationality": "Indian",
  "passport_number": "A1234567"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "name": "John Doe", 
  "contact": "+91-9876543210",
  "email": "john.doe@email.com",
  "emergency_contact": "+91-9876543211",
  "safety_score": 100,
  "is_active": true,
  "created_at": "2025-09-27T10:30:00Z"
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/registerTourist" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "contact": "+91-9876543210",
    "emergency_contact": "+91-9876543211",
    "age": 28
  }'
```

**Error Responses**:
- `400`: Tourist with contact already exists
- `500`: Registration failed

---

### Get Tourist Details

#### `GET /tourists/{tourist_id}`
**Description**: Get detailed tourist information including current safety score
**Authentication**: None

**Parameters**:
- `tourist_id` (path): Tourist ID number

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "John Doe",
  "contact": "+91-9876543210",
  "safety_score": 85,
  "trip_info": {
    "destination": "Goa",
    "duration": "5 days"
  },
  "emergency_contact": "+91-9876543211",
  "last_location_update": "2025-09-27T14:30:00Z",
  "is_active": true
}
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/tourists/1"
```

---

### List All Tourists

#### `GET /tourists/`
**Description**: Get list of all tourists with filtering options
**Authentication**: None

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)
- `active_only` (optional): Show only active tourists (default: true)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "contact": "+91-9876543210",
    "safety_score": 85,
    "is_active": true,
    "last_location_update": "2025-09-27T14:30:00Z"
  },
  {
    "id": 2,
    "name": "Jane Smith", 
    "contact": "+91-9876543220",
    "safety_score": 92,
    "is_active": true,
    "last_location_update": "2025-09-27T14:25:00Z"
  }
]
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/tourists/?limit=50&active_only=true"
```

---

## 📍 Location Management

### Send Location Update
Update tourist location and trigger AI safety assessment.

#### `POST /sendLocation` ⭐ **Required Endpoint**
**Description**: Update tourist GPS location and automatically trigger AI safety assessment
**Authentication**: None

**Request Body**:
```json
{
  "tourist_id": 1,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "altitude": 200.5,
  "accuracy": 5.0,
  "speed": 15.0,
  "heading": 270.0
}
```

**Response** (201 Created):
```json
{
  "id": 1001,
  "tourist_id": 1,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "speed": 15.0,
  "timestamp": "2025-09-27T14:30:00Z",
  "created_at": "2025-09-27T14:30:00Z"
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/sendLocation" \
  -H "Content-Type: application/json" \
  -d '{
    "tourist_id": 1,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "speed": 15.0
  }'
```

**What Happens Behind the Scenes**:
1. Location stored in database
2. Tourist's `last_location_update` updated
3. **AI Assessment triggered automatically** in background
4. Safety score recalculated
5. Alerts generated if risks detected

**Error Responses**:
- `404`: Tourist not found
- `400`: Tourist is inactive
- `500`: Location update failed

---

### Get All Tourist Locations

#### `GET /locations/all` ⭐ **Required Endpoint**
**Description**: Get latest location of all active tourists for monitoring dashboard
**Authentication**: None

**Response** (200 OK):
```json
[
  {
    "tourist_id": 1,
    "tourist_name": "John Doe",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "speed": 15.0,
    "safety_score": 85,
    "timestamp": "2025-09-27T14:30:00Z",
    "status": "active"
  },
  {
    "tourist_id": 2,
    "tourist_name": "Jane Smith",
    "latitude": 15.2993,
    "longitude": 74.1240,
    "speed": 0.0,
    "safety_score": 92,
    "timestamp": "2025-09-27T14:28:00Z",
    "status": "active"
  }
]
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/locations/all"
```

---

### Get Tourist Location History

#### `GET /locations/tourist/{tourist_id}`
**Description**: Get location history for a specific tourist
**Authentication**: None

**Parameters**:
- `tourist_id` (path): Tourist ID
- `limit` (query): Number of recent locations (default: 100)
- `hours` (query): Hours of history to retrieve (default: 24)

**Response** (200 OK):
```json
[
  {
    "id": 1001,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "speed": 15.0,
    "timestamp": "2025-09-27T14:30:00Z"
  },
  {
    "id": 1000,
    "latitude": 28.6140,
    "longitude": 77.2085,
    "speed": 12.0,
    "timestamp": "2025-09-27T14:25:00Z"
  }
]
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/locations/tourist/1?limit=50&hours=12"
```

---

## 🚨 Alert Management

### Create Panic Alert

#### `POST /pressSOS` ⭐ **Required Endpoint**
**Description**: Create emergency SOS alert with CRITICAL priority
**Authentication**: None

**Request Body**:
```json
{
  "tourist_id": 1,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "message": "Help! I'm in danger!"
}
```

**Response** (201 Created):
```json
{
  "id": 501,
  "tourist_id": 1,
  "type": "panic",
  "severity": "CRITICAL", 
  "message": "🆘 EMERGENCY SOS: Help! I'm in danger!",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "status": "active",
  "timestamp": "2025-09-27T14:30:00Z",
  "auto_generated": false
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/pressSOS" \
  -H "Content-Type: application/json" \
  -d '{
    "tourist_id": 1,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "message": "Emergency assistance needed!"
  }'
```

**What Happens**:
1. **Critical alert created** immediately
2. **Safety score reduced by 40 points**
3. **Emergency contacts notified** (implementation pending)
4. **Authorities alerted** (integration ready)
5. **Continuous location tracking** activated

---

### Create Manual Alert

#### `POST /alerts/panic`
**Description**: Create a panic alert manually (similar to SOS but configurable severity)
**Authentication**: None

**Request Body**:
```json
{
  "tourist_id": 1,
  "latitude": 28.6139,
  "longitude": 77.2090,
  "message": "Feeling unsafe in this area",
  "severity": "HIGH"
}
```

**Response** (201 Created):
```json
{
  "id": 502,
  "tourist_id": 1,
  "type": "panic",
  "severity": "HIGH",
  "message": "Feeling unsafe in this area",
  "status": "active",
  "timestamp": "2025-09-27T14:30:00Z"
}
```

---

### List Alerts

#### `GET /alerts` ⭐ **Required Endpoint**
**Description**: Get all alerts with filtering options for monitoring dashboard
**Authentication**: None

**Query Parameters**:
- `status` (optional): Filter by status (active, resolved, acknowledged)
- `severity` (optional): Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `tourist_id` (optional): Filter by specific tourist
- `limit` (optional): Maximum records to return (default: 100)
- `hours` (optional): Recent alerts within X hours (default: 24)

**Response** (200 OK):
```json
[
  {
    "id": 501,
    "tourist_id": 1,
    "tourist_name": "John Doe",
    "type": "panic",
    "severity": "CRITICAL",
    "message": "🆘 EMERGENCY SOS: Help!",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "status": "active",
    "timestamp": "2025-09-27T14:30:00Z",
    "auto_generated": false
  },
  {
    "id": 502,
    "tourist_id": 2,
    "tourist_name": "Jane Smith",
    "type": "geofence",
    "severity": "HIGH",
    "message": "Tourist entered restricted zone",
    "status": "acknowledged",
    "timestamp": "2025-09-27T13:45:00Z",
    "auto_generated": true,
    "ai_confidence": 0.95
  }
]
```

**Curl Example**:
```bash
# Get all active critical alerts
curl -X GET "http://localhost:8000/alerts?status=active&severity=CRITICAL"

# Get alerts for specific tourist
curl -X GET "http://localhost:8000/alerts?tourist_id=1&hours=6"
```

---

### Resolve Alert

#### `PUT /alerts/{alert_id}/resolve` ⭐ **Required Endpoint**
**Description**: Mark an alert as resolved with optional notes
**Authentication**: None

**Parameters**:
- `alert_id` (path): Alert ID to resolve

**Request Body** (optional):
```json
{
  "resolved_by": "Officer Smith",
  "resolution_notes": "False alarm - tourist confirmed safe"
}
```

**Response** (200 OK):
```json
{
  "id": 501,
  "status": "resolved",
  "resolved_by": "Officer Smith", 
  "resolved_at": "2025-09-27T15:00:00Z",
  "resolution_notes": "False alarm - tourist confirmed safe"
}
```

**Curl Example**:
```bash
curl -X PUT "http://localhost:8000/alerts/501/resolve" \
  -H "Content-Type: application/json" \
  -d '{
    "resolved_by": "Emergency Response Team",
    "resolution_notes": "Tourist rescued and safe"
  }'
```

---

### Acknowledge Alert

#### `PUT /alerts/{alert_id}/acknowledge`
**Description**: Acknowledge an alert to show it's being handled
**Authentication**: None

**Request Body**:
```json
{
  "acknowledged_by": "Control Room Operator"
}
```

**Response** (200 OK):
```json
{
  "id": 501,
  "status": "acknowledged",
  "acknowledged": true,
  "acknowledged_by": "Control Room Operator",
  "acknowledged_at": "2025-09-27T14:35:00Z"
}
```

---

## 🤖 AI Assessment Endpoints

### Get AI Engine Status

#### `GET /ai/status`
**Description**: Check AI engine health and model information
**Authentication**: None

**Response** (200 OK):
```json
{
  "status": "active",
  "timestamp": "2025-09-27T14:30:00Z",
  "models_loaded": {
    "geofence": {
      "status": "active",
      "version": "1.0.0",
      "type": "rule_based"
    },
    "isolation_forest": {
      "status": "active", 
      "version": "2.1.0",
      "last_trained": "2025-09-27T13:00:00Z",
      "accuracy": 0.87
    },
    "temporal": {
      "status": "active",
      "version": "1.2.0",
      "window_size": 10
    }
  },
  "assessments_processed": 1247,
  "alerts_generated": 23,
  "average_confidence": 0.84
}
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/ai/status"
```

---

### Trigger Immediate Assessment

#### `POST /ai/assess/{tourist_id}`
**Description**: Force immediate AI safety assessment for a tourist
**Authentication**: None

**Parameters**:
- `tourist_id` (path): Tourist ID to assess

**Response** (202 Accepted):
```json
{
  "message": "AI assessment triggered for tourist 1",
  "tourist_id": 1,
  "status": "processing",
  "estimated_completion": "2025-09-27T14:30:30Z"
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/ai/assess/1"
```

---

### Get Tourist AI Assessments

#### `GET /ai/assessments/{tourist_id}`
**Description**: Get AI assessment history for a tourist
**Authentication**: None

**Parameters**:
- `tourist_id` (path): Tourist ID
- `limit` (query): Number of assessments (default: 20)

**Response** (200 OK):
```json
[
  {
    "id": 1001,
    "tourist_id": 1,
    "safety_score": 85,
    "severity": "SAFE",
    "anomaly_score": 0.15,
    "temporal_risk_score": 0.10,
    "confidence_level": 0.88,
    "geofence_alert": false,
    "recommended_action": "Continue normal activities",
    "created_at": "2025-09-27T14:30:00Z",
    "model_predictions": [
      {
        "model_name": "isolation_forest",
        "prediction_value": 0.85,
        "confidence": 0.91
      },
      {
        "model_name": "temporal_autoencoder", 
        "prediction_value": 0.90,
        "confidence": 0.85
      }
    ]
  }
]
```

**Curl Example**:
```bash
curl -X GET "http://localhost:8000/ai/assessments/1?limit=10"
```

---

### Manual Model Retraining

#### `POST /ai/retrain/{model_type}`
**Description**: Manually trigger retraining for specific AI model
**Authentication**: Admin (implementation pending)

**Parameters**:
- `model_type` (path): Model to retrain (isolation_forest, temporal_autoencoder)

**Response** (202 Accepted):
```json
{
  "message": "Retraining started for isolation_forest",
  "model_type": "isolation_forest",
  "status": "training",
  "estimated_completion": "2025-09-27T15:00:00Z"
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/ai/retrain/isolation_forest"
```

---

## 📝 E-FIR (Electronic First Information Report)

### File E-FIR

#### `POST /fileEFIR`
**Description**: File electronic First Information Report for incidents
**Authentication**: None

**Request Body**:
```json
{
  "tourist_id": 1,
  "incident_type": "theft",
  "location_details": "Near Beach Resort, Goa",
  "description": "Mobile phone stolen while walking on the beach",
  "latitude": 15.2993,
  "longitude": 74.1240,
  "witness_details": "Local vendor saw the incident"
}
```

**Response** (201 Created):
```json
{
  "efir_id": "FIR-2025-001",
  "tourist_id": 1,
  "incident_type": "theft",
  "status": "filed",
  "filed_at": "2025-09-27T14:30:00Z",
  "reference_number": "GOA-2025-TH-001"
}
```

**Curl Example**:
```bash
curl -X POST "http://localhost:8000/fileEFIR" \
  -H "Content-Type: application/json" \
  -d '{
    "tourist_id": 1,
    "incident_type": "theft",
    "location_details": "Beach area",
    "description": "Phone stolen",
    "latitude": 15.2993,
    "longitude": 74.1240
  }'
```

---

## 📊 Analytics & Monitoring

### System Analytics Dashboard

#### `GET /ai/analytics/dashboard`
**Description**: Get system-wide analytics and performance metrics
**Authentication**: Admin

**Response** (200 OK):
```json
{
  "overview": {
    "total_tourists": 1247,
    "active_tourists": 1203,
    "total_alerts": 89,
    "active_alerts": 12,
    "average_safety_score": 87.3
  },
  "recent_activity": {
    "location_updates_24h": 15632,
    "ai_assessments_24h": 15632,
    "alerts_generated_24h": 8,
    "sos_alerts_24h": 2
  },
  "ai_performance": {
    "model_accuracy": 0.87,
    "average_processing_time": "1.2s",
    "false_positive_rate": 0.05,
    "models_last_trained": "2025-09-27T13:00:00Z"
  },
  "geographic_distribution": [
    {"location": "Goa", "tourist_count": 456},
    {"location": "Delhi", "tourist_count": 234},
    {"location": "Shillong", "tourist_count": 123}
  ]
}
```

---

## 🔧 Error Handling

### Standard Error Response Format
All endpoints return errors in the following format:

```json
{
  "detail": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-09-27T14:30:00Z"
}
```

### Common HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## 🚀 Quick Start Examples

### Complete Tourist Journey
```bash
# 1. Register tourist
curl -X POST "http://localhost:8000/registerTourist" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "contact": "+91-9999999999", "emergency_contact": "+91-8888888888"}'

# 2. Send location (triggers AI)
curl -X POST "http://localhost:8000/sendLocation" \
  -H "Content-Type: application/json" \
  -d '{"tourist_id": 1, "latitude": 28.6139, "longitude": 77.2090, "speed": 5.0}'

# 3. Check AI status
curl -X GET "http://localhost:8000/ai/status"

# 4. Get all locations
curl -X GET "http://localhost:8000/locations/all"

# 5. Press SOS (emergency)
curl -X POST "http://localhost:8000/pressSOS" \
  -H "Content-Type: application/json" \
  -d '{"tourist_id": 1, "latitude": 28.6139, "longitude": 77.2090, "message": "Need help!"}'

# 6. View alerts
curl -X GET "http://localhost:8000/alerts"
```

---

## 🔗 Integration Notes

### Mobile App Integration
- Use `/registerTourist` for user onboarding
- Send location updates every 30 seconds to `/sendLocation`
- Implement SOS button calling `/pressSOS`
- Poll `/alerts?tourist_id=X` for personalized alerts

### Web Dashboard Integration  
- Use `/locations/all` for real-time map view
- Use `/alerts` with filters for alert management
- Use `/ai/analytics/dashboard` for overview metrics
- Use alert resolution endpoints for operator actions

### Third-Party Services
- Emergency services can integrate with alert endpoints
- Police dashboard can use analytics endpoints
- Family notifications can hook into alert webhooks (coming soon)

---

*This completes the comprehensive API documentation for the Smart Tourist Safety & Incident Response System. All endpoints are production-ready and include proper error handling, validation, and real-time AI processing.*