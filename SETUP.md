# 🚀 Quick Setup Guide

## Smart Tourist Safety & Incident Response System

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Environment File
Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres.tqenqwfuywighainnujh:[YOUR_DB_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

# Supabase Configuration  
SUPABASE_URL=https://tqenqwfuywighainnujh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxZW5xd2Z1eXdpZ2hhaW5udWpoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyMDg5NTgsImV4cCI6MjA3Mzc4NDk1OH0.qztg3ZGxTCGZwDjIKlnvHtdGODdMxPxy2ntQg6GkHAs
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRxZW5xd2Z1eXdpZ2hhaW5udWpoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODIwODk1OCwiZXhwIjoyMDczNzg0OTU4fQ._Z6Fk7qOP1D72rZrJwYt6_A3oMZPf5GZEF8xJ_BTKhg

# Application Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
```

**⚠️ Important**: Replace `[YOUR_DB_PASSWORD]` with your actual Supabase database password.

### Step 3: Initialize Database
```bash
python init_db.py
```

### Step 4: Start the Application
```bash
python run.py
```

### Step 5: Access the API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health  
- **AI Status**: http://localhost:8000/api/v1/ai/status

### 🧪 Quick Test

#### Register a Tourist:
```bash
curl -X POST "http://localhost:8000/api/v1/tourists/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "contact": "+91-9876543210", 
    "emergency_contact": "+91-9876543211",
    "age": 25
  }'
```

#### Update Location (triggers AI):
```bash
curl -X POST "http://localhost:8000/api/v1/locations/update" \
  -H "Content-Type: application/json" \
  -d '{
    "tourist_id": 1,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "speed": 5.0
  }'
```

### 🤖 AI Features Active
- **Continuous Model Training**: Every hour
- **Real-time Safety Assessment**: Every location update  
- **Anomaly Detection**: Isolation Forest + Temporal Analysis
- **Dynamic Safety Scoring**: 0-100 scale
- **Automatic Alerts**: Based on AI predictions

### 📊 Monitor the System
- Check AI status: `GET /api/v1/ai/status`
- View analytics: `GET /api/v1/ai/analytics/dashboard`
- Force retraining: `POST /api/v1/ai/retrain/isolation_forest`

---

**🎯 Your AI-powered tourist safety system is now running!**