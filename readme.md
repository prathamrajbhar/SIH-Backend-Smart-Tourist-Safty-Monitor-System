# Smart Tourist Safety & Incident Response System

A FastAPI-based backend system for monitoring tourist safety with **continuous AI/ML model training** and **real-time risk assessment**.

## 🌟 Key Features

- **Real-time Tourist Tracking**: GPS-based location monitoring
- **Continuous AI Learning**: Models retrain automatically with new data from Supabase
- **Multi-Model AI Assessment**: Isolation Forest + Temporal Analysis + Geofencing
- **Dynamic Safety Scoring**: Real-time safety score calculation (0-100)
- **Automated Alert System**: Panic alerts, geofence violations, AI-detected anomalies
- **Live Database Integration**: No mock data - uses real Supabase data
- **RESTful APIs**: Complete REST API with automatic documentation

## 🏗️ Architecture

### AI Engine Components
1. **Isolation Forest**: Unsupervised anomaly detection for unusual movement patterns
2. **Temporal Analysis**: Sequential pattern recognition for behavior changes  
3. **Geofencing**: Rule-based safe/restricted zone detection
4. **Safety Scoring**: Hybrid scoring system combining all models
5. **Continuous Learning**: Models retrain every hour with fresh data

### Data Flow
```
Tourist Location Update → Database → AI Assessment → Safety Score Update → Alerts (if needed)
                                ↓
                        Background AI Training (every hour)
```

## 🚀 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Supabase
Update `.env` file with your Supabase credentials:
```env
DATABASE_URL=postgresql://postgres.tqenqwfuywighainnujh:[YOUR_DB_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://tqenqwfuywighainnujh.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Start the Application
```bash
python run.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Tourist Management
- `POST /api/v1/tourists/register` - Register new tourist
- `GET /api/v1/tourists/{id}` - Get tourist details
- `PUT /api/v1/tourists/{id}` - Update tourist info

### Location Tracking
- `POST /api/v1/locations/update` - Update tourist location (triggers AI assessment)
- `GET /api/v1/locations/all` - Get all tourist locations
- `GET /api/v1/locations/tourist/{id}` - Get tourist location history

### Alert Management  
- `POST /api/v1/alerts/panic` - Create panic alert
- `POST /api/v1/alerts/geofence` - Create geofence alert
- `GET /api/v1/alerts` - List alerts (with filters)
- `PUT /api/v1/alerts/{id}/resolve` - Resolve alert

### AI Assessment (New!)
- `GET /api/v1/ai/status` - Get AI engine status and model info
- `POST /api/v1/ai/assess/{tourist_id}` - Trigger immediate AI assessment
- `GET /api/v1/ai/assessment/{tourist_id}` - Get tourist AI assessments
- `POST /api/v1/ai/retrain/{model_type}` - Trigger model retraining
  - **NEW**: `POST /api/v1/ai/retrain/force_all` - Force immediate retraining of all models
- `GET /api/v1/ai/training/status` - **NEW**: Get detailed training status and schedule
- `GET /api/v1/ai/data/stats` - **NEW**: Get real-time data statistics
- `GET /api/v1/ai/analytics/dashboard` - AI analytics dashboard

## 🤖 AI Engine Details

### Continuous Learning Process
1. **Data Collection**: Fetches location, alert, and tourist data from Supabase **every minute**
2. **Feature Engineering**: Calculates movement patterns, anomaly indicators
3. **Model Training**: Retrains models **every 60 seconds** with new data
4. **Real-time Assessment**: Processes each location update immediately (**every 15 seconds**)
5. **Performance Tracking**: Monitors model accuracy and confidence

### Training Schedule
- **🔄 Model Retraining**: Every 60 seconds (1 minute)
- **⚡ Real-time Processing**: Every 15 seconds
- **📊 Data Fetching**: Continuous with 1-minute intervals
- **🚀 Force Training**: Available on-demand via API

### AI Models

#### 1. Isolation Forest (Anomaly Detection)
- **Purpose**: Detect unusual movement patterns
- **Features**: distance_per_minute, inactivity_duration, speed_variance, etc.
- **Output**: Anomaly score (0-1, higher = more anomalous)
- **Retraining**: Every hour with last 7 days of data

#### 2. Temporal Analysis
- **Purpose**: Identify behavior pattern changes over time
- **Features**: Movement consistency, time regularity, location patterns
- **Output**: Temporal risk score (0-1)
- **Retraining**: Every hour with sequential location data

#### 3. Geofencing (Rule-based)
- **Purpose**: Immediate alerts for restricted areas
- **Input**: GPS coordinates vs. predefined zones
- **Output**: Binary (safe/restricted) + zone information
- **Updates**: Real-time, no training needed

### Safety Score Calculation
```
Base Score: 100
- Panic Alert: -40
- Restricted Zone: -30  
- AI Anomaly: -25 (max)
- Temporal Risk: -20 (max)
- Inactivity: -5 per hour

Final Score: max(0, min(100, calculated_score))
```

### Severity Levels
- **SAFE** (80-100): Green zone, no action needed
- **WARNING** (50-79): Yellow zone, monitor closely  
- **CRITICAL** (0-49): Red zone, immediate intervention

## 📊 Real-time Processing

### Location Update Flow
1. Tourist sends GPS coordinates
2. Location stored in Supabase
3. AI assessment triggered automatically
4. Safety score calculated and updated
5. Alerts created if score < 50
6. Response sent to client

### Background Tasks
- **AI Model Retraining**: Every 60 seconds (1 minute)
- **Real-time Assessments**: Every 15 seconds
- **Data Health Checks**: Every 60 seconds

## 🔧 Configuration

### AI Settings (in ai_engine.py)
```python
retrain_interval = 60        # 60 seconds (1 minute)
min_data_points = 10         # Minimum for training (reduced for faster iteration)
feature_columns = [
    'distance_per_minute',
    'inactivity_duration', 
    'deviation_from_route',
    'speed_variance',
    'location_density'
]
```

### Database Settings (in config.py)
```python
database_pool_size = 10
database_max_overflow = 20
database_pool_timeout = 30
```

## 📈 Monitoring & Analytics

### AI Dashboard Metrics
- Total assessments processed
- Safety score distribution  
- Model performance metrics
- Alert frequency by type
- Training history and accuracy

### Health Monitoring
- Database connection status
- AI model status and versions
- API response times
- Error rates and logs

## 🚨 Alert System

### Automatic Alerts
- **Panic Button**: Immediate CRITICAL alert
- **Geofence Violation**: HIGH severity when entering restricted zones
- **AI Anomaly**: AUTO-generated when AI detects unusual patterns
- **Low Safety Score**: When score drops below 50

### Alert Workflow
1. Alert created (manual or automatic)
2. Severity assigned (LOW/MEDIUM/HIGH/CRITICAL)
3. Notification sent (API response)
4. Status tracking (ACTIVE → ACKNOWLEDGED → RESOLVED)

## 🔒 Security Features

- Environment variable configuration
- Database connection pooling
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration for web/mobile apps
- Request logging and monitoring

## 🧪 Testing the System

### 1. Register a Tourist
```bash
curl -X POST "http://localhost:8000/api/v1/tourists/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "contact": "+91-9876543210",
    "emergency_contact": "+91-9876543211",
    "age": 30
  }'
```

### 2. Update Location (triggers AI assessment)
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

### 3. Test AI Training (1-minute intervals)
```bash
python test_ai_training.py
```

This will:
- Monitor AI training every 60 seconds
- Show real-time training status
- Generate test data for model training
- Verify force training functionality

### 4. Check Training Status
```bash
curl "http://localhost:8000/api/v1/ai/training/status"
```

### 5. Force Immediate Training
```bash
curl -X POST "http://localhost:8000/api/v1/ai/retrain/force_all"
```

## 🛠️ Development

### Project Structure
```
app/
├── models/          # Database models
├── schemas/         # Pydantic models  
├── api/            # API routes
├── services/       # Business logic
│   ├── ai_engine.py    # Main AI engine
│   └── safety.py      # Safety calculations
└── main.py         # FastAPI app
```

### Adding New AI Models
1. Extend `AIEngineService` class
2. Add model training method
3. Update prediction pipeline
4. Add to API endpoints

## 🎯 Production Deployment

### Environment Variables
```env
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=your_production_db_url
SECRET_KEY=your_secret_key
```

### Scaling Considerations
- Use Redis for caching AI model results
- Deploy with Gunicorn + multiple workers
- Use background job queue (Celery) for training
- Monitor with Prometheus/Grafana

## 📝 License

This project is part of Smart India Hackathon 2025.

---

## 🆘 Support

For issues or questions:
1. Check the `/docs` endpoint for API documentation
2. Monitor `/health` endpoint for system status  
3. Review logs for error details
4. Use `/ai/status` to check AI engine health

**Happy Coding! 🚀**