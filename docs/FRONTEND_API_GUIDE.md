# 🎨 Frontend Developer API Guide

Complete guide for frontend developers to integrate with the Smart Tourist Safety System API.

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Real-time Features](#real-time-features)
5. [Dashboard APIs](#dashboard-apis)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)

---

## 🚀 Quick Start

### Base URL
```
Production: https://api.smart-tourism.com
Development: http://localhost:8000
```

### API Prefix
All new endpoints use the `/api/v1` prefix:
```
GET /api/v1/frontend/dashboard/stats
POST /api/v1/tourists/register
WebSocket: /api/v1/realtime/ws
```

### Required Headers
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 🔐 Authentication

Currently, the API is open for development. In production, include:

```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

---

## 🎯 Core Endpoints

### 1. Dashboard Statistics
Get overview stats for dashboard cards.

```http
GET /api/v1/frontend/dashboard/stats
```

**Response:**
```json
{
  "total_tourists": 1250,
  "active_tourists": 890,
  "active_alerts": 15,
  "critical_alerts": 3,
  "avg_safety_score": 87.5,
  "min_safety_score": 45,
  "max_safety_score": 100,
  "recent_location_updates": 156,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 2. Tourist Cards (Paginated)
Get tourist cards for list/grid views with search and filters.

```http
GET /api/v1/frontend/tourists/cards?page=1&size=20&status_filter=active&search=john
```

**Parameters:**
- `page`: Page number (1-based)
- `size`: Items per page (1-100)
- `status_filter`: `active` | `inactive` | `critical`
- `search`: Search by name or contact

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "name": "John Doe",
      "contact": "+91-9876543210",
      "safety_score": 95,
      "status": "safe",
      "last_location": {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timestamp": "2024-01-15T10:25:00Z"
      },
      "recent_alerts_count": 0,
      "is_active": true,
      "last_seen": "2024-01-15T10:25:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "size": 20,
  "pages": 63
}
```

### 3. Active Alerts
Get currently active alerts for monitoring.

```http
GET /api/v1/frontend/alerts/active?limit=50&severity=CRITICAL
```

**Response:**
```json
[
  {
    "id": 456,
    "tourist_id": 123,
    "tourist_name": "John Doe",
    "type": "PANIC",
    "severity": "CRITICAL",
    "message": "🆘 EMERGENCY SOS: Help needed urgently!",
    "location": {
      "latitude": 28.6139,
      "longitude": 77.2090,
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "auto_generated": false,
    "acknowledged": false
  }
]
```

### 4. Safety Map Data
Get data for map visualization with optional bounds filtering.

```http
GET /api/v1/frontend/map/safety-data?bounds=28.5,77.0,28.7,77.4
```

**Response:**
```json
{
  "tourist_locations": [
    {
      "tourist_id": 123,
      "name": "John Doe",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "safety_score": 95,
      "status": "safe",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "alert_locations": [
    {
      "alert_id": 456,
      "tourist_name": "Jane Smith",
      "latitude": 28.6200,
      "longitude": 77.2100,
      "severity": "HIGH",
      "type": "GEOFENCE",
      "message": "Entered restricted area",
      "timestamp": "2024-01-15T10:25:00Z"
    }
  ],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 5. Tourist Timeline
Get comprehensive timeline for a specific tourist.

```http
GET /api/v1/frontend/tourist/123/timeline?hours=24
```

**Response:**
```json
{
  "tourist_id": 123,
  "tourist_name": "John Doe",
  "timeline": [
    {
      "type": "location",
      "timestamp": "2024-01-15T09:00:00Z",
      "data": {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "speed": 5.2,
        "accuracy": 10.0
      }
    },
    {
      "type": "alert",
      "timestamp": "2024-01-15T09:30:00Z",
      "data": {
        "id": 456,
        "type": "GEOFENCE",
        "severity": "MEDIUM",
        "message": "Approached restricted area",
        "status": "RESOLVED"
      }
    },
    {
      "type": "ai_assessment",
      "timestamp": "2024-01-15T09:32:00Z",
      "data": {
        "safety_score": 85,
        "severity": "WARNING",
        "confidence": 0.87,
        "geofence_alert": false,
        "anomaly_score": 0.15
      }
    }
  ],
  "summary": {
    "total_events": 25,
    "locations": 20,
    "alerts": 3,
    "ai_assessments": 2,
    "time_range_hours": 24
  }
}
```

---

## ⚡ Real-time Features

### WebSocket Connection
Connect to real-time updates for live dashboards.

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws');

ws.onopen = function() {
    console.log('Connected to real-time updates');
    
    // Subscribe to specific channels
    ws.send(JSON.stringify({
        type: 'subscribe',
        data: {
            channels: ['alerts', 'locations'],
            tourist_ids: [123, 456], // Optional: specific tourists
            filters: {
                severity: 'CRITICAL' // Optional: filter by severity
            }
        }
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'new_alert':
            handleNewAlert(message.data);
            break;
        case 'location_update':
            updateTouristPosition(message.data);
            break;
        case 'heartbeat':
            console.log('Connection alive');
            break;
    }
};
```

### Available Channels
- `alerts`: New alerts and alert status changes
- `locations`: Tourist location updates
- `assessments`: AI safety assessments
- `system`: System status and heartbeat messages
- `all`: Subscribe to all channels

### Live Data Endpoints
For polling-based implementations:

```http
# Get active alerts (updates every 30 seconds)
GET /api/v1/realtime/live/active-alerts

# Get tourist positions (updates every 15 seconds)
GET /api/v1/realtime/live/tourist-positions

# Get system metrics (updates every minute)
GET /api/v1/realtime/live/system-metrics
```

---

## 📊 Dashboard APIs

### Analytics and Trends
```http
GET /api/v1/frontend/analytics/trends?days=7
```

### Alert Statistics
```http
GET /api/v1/frontend/alerts/stats?days=30
```

### System Health
```http
GET /api/v1/frontend/system/health
```

---

## ❌ Error Handling

### Standard Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "tourist_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 💻 Code Examples

### React Dashboard Component
```javascript
import React, { useState, useEffect } from 'react';

function Dashboard() {
    const [stats, setStats] = useState(null);
    const [alerts, setAlerts] = useState([]);
    
    useEffect(() => {
        // Fetch dashboard stats
        fetch('/api/v1/frontend/dashboard/stats')
            .then(response => response.json())
            .then(data => setStats(data));
        
        // Fetch active alerts
        fetch('/api/v1/frontend/alerts/active?limit=10')
            .then(response => response.json())
            .then(data => setAlerts(data));
    }, []);
    
    return (
        <div className="dashboard">
            {stats && (
                <div className="stats-grid">
                    <StatCard title="Total Tourists" value={stats.total_tourists} />
                    <StatCard title="Active Alerts" value={stats.active_alerts} />
                    <StatCard title="Avg Safety Score" value={stats.avg_safety_score} />
                </div>
            )}
            
            <AlertsList alerts={alerts} />
        </div>
    );
}
```

### Vue.js Real-time Map
```javascript
<template>
  <div id="map"></div>
</template>

<script>
export default {
  data() {
    return {
      map: null,
      markers: {},
      ws: null
    }
  },
  
  mounted() {
    this.initMap();
    this.connectWebSocket();
  },
  
  methods: {
    initMap() {
      this.map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: { lat: 28.6139, lng: 77.2090 }
      });
      
      // Load initial positions
      this.loadTouristPositions();
    },
    
    connectWebSocket() {
      this.ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws');
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'location_update') {
          this.updateMarker(message.data);
        }
      };
    },
    
    async loadTouristPositions() {
      const response = await fetch('/api/v1/realtime/live/tourist-positions');
      const data = await response.json();
      
      data.positions.forEach(position => {
        this.createMarker(position);
      });
    },
    
    updateMarker(data) {
      const marker = this.markers[data.tourist_id];
      if (marker) {
        marker.setPosition({
          lat: data.latitude,
          lng: data.longitude
        });
      } else {
        this.createMarker(data);
      }
    }
  }
}
</script>
```

### Angular Service
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TouristService {
  private baseUrl = '/api/v1';
  private ws: WebSocket | null = null;
  
  // Real-time data streams
  public alerts$ = new BehaviorSubject([]);
  public tourists$ = new BehaviorSubject([]);
  
  constructor(private http: HttpClient) {
    this.initWebSocket();
  }
  
  getDashboardStats(): Observable<any> {
    return this.http.get(`${this.baseUrl}/frontend/dashboard/stats`);
  }
  
  getTouristCards(page: number = 1, size: number = 20, filters: any = {}): Observable<any> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
      ...filters
    });
    
    return this.http.get(`${this.baseUrl}/frontend/tourists/cards?${params}`);
  }
  
  private initWebSocket() {
    this.ws = new WebSocket('ws://localhost:8000/api/v1/realtime/ws');
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch(message.type) {
        case 'new_alert':
          const currentAlerts = this.alerts$.value;
          this.alerts$.next([message.data, ...currentAlerts]);
          break;
          
        case 'location_update':
          // Update tourist position in the stream
          this.updateTouristPosition(message.data);
          break;
      }
    };
  }
  
  private updateTouristPosition(data: any) {
    const tourists = this.tourists$.value;
    const index = tourists.findIndex(t => t.tourist_id === data.tourist_id);
    
    if (index >= 0) {
      tourists[index] = { ...tourists[index], ...data };
      this.tourists$.next([...tourists]);
    }
  }
}
```

---

## 🔧 Development Tips

### 1. Pagination Best Practices
- Always use pagination for list endpoints
- Limit page size to max 100 items
- Include total count for UI pagination controls

### 2. Real-time Updates
- Use WebSocket for live dashboards
- Implement fallback polling for critical data
- Handle reconnection gracefully

### 3. Error Handling
- Always check HTTP status codes
- Display user-friendly error messages
- Implement retry logic for failed requests

### 4. Performance
- Cache dashboard stats for 60 seconds
- Use debouncing for search inputs
- Implement virtual scrolling for large lists

### 5. Security
- Validate all user inputs
- Sanitize data before display
- Use HTTPS in production

---

## 📞 Support

For technical support or questions:
- Email: dev-support@smart-tourism.com
- Slack: #frontend-api-support
- Documentation: https://docs.smart-tourism.com

---

## 📋 Changelog

### v2.1.0 (Latest)
- Added real-time WebSocket support
- New frontend-specific endpoints
- Enhanced pagination and filtering
- Tourist timeline API

### v2.0.0
- Complete API redesign
- Standardized response formats
- Added comprehensive error handling

### v1.0.0
- Initial API release
- Basic CRUD operations
- Legacy endpoint support
