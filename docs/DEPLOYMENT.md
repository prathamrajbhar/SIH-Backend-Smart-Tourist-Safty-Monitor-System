# 🚀 Deployment Guide - Smart Tourist Safety System

## Quick Deployment Options

### 🏃‍♂️ Option 1: Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables in .env file
DATABASE_URL=postgresql://postgres.tqenqwfuywighainnujh:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://tqenqwfuywighainnujh.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# 3. Initialize database
python init_db.py

# 4. Start server
python run.py
```

### 🐳 Option 2: Docker (Recommended)
```bash
# 1. Build and run with Docker Compose
docker-compose up --build -d

# 2. Check status
docker-compose logs -f api

# 3. Access API
curl http://localhost:8000/health
```

### ☸️ Option 3: Kubernetes (Production)
```bash
# 1. Update secrets in k8s-deployment.yaml
# 2. Deploy to cluster
kubectl apply -f k8s-deployment.yaml

# 3. Check deployment
kubectl get pods
kubectl get services
```

---

## 🌐 API Endpoints

### Required Endpoints (✅ All Implemented)
- `POST /registerTourist` - Register new tourist
- `POST /sendLocation` - Update location + trigger AI assessment
- `POST /pressSOS` - Create emergency SOS alert  
- `POST /fileEFIR` - File electronic FIR
- `GET /getAlerts` - Get all alerts with filtering

### Additional Endpoints
- `GET /health` - System health check
- `GET /docs` - Interactive API documentation
- `GET /api/v1/ai/status` - AI engine status
- `GET /api/v1/ai/analytics/dashboard` - AI analytics

---

## 🤖 AI Engine Features

### ✅ Hybrid AI Pipeline Active
1. **Rule-based Geofencing** - Instant alerts for restricted zones
2. **Isolation Forest** - Anomaly detection for unusual behavior  
3. **Temporal Analysis** - Sequential pattern recognition
4. **Safety Scoring** - Dynamic 0-100 safety score calculation

### 🔄 Continuous Learning
- Models retrain every hour with fresh Supabase data
- Real-time assessment on every location update
- Background processing for optimal performance
- Model versioning and performance tracking

---

## 🚨 Alert Management

### Alert Routing by Severity
- **CRITICAL** → Police + Family (SMS/Call) + Tourist App + Auto E-FIR
- **HIGH** → Police + Family (SMS) + Tourist App
- **MEDIUM** → Tourist App + Family (Email)
- **LOW** → Tourist App only

### Notification Channels
- 🚔 Police Dashboard (real-time)
- 📱 Family Emergency Contacts (SMS/Call via Twilio)
- 📲 Tourist Mobile App (Push notifications via FCM)
- ⚖️ Auto E-FIR generation for critical incidents

---

## 📊 Testing & Monitoring

### Run Comprehensive Tests
```bash
cd tests
python comprehensive_test.py
```

### Health Monitoring
```bash
# API Health
curl http://localhost:8000/health

# AI Status  
curl http://localhost:8000/api/v1/ai/status

# Alert Statistics
curl http://localhost:8000/api/v1/ai/analytics/dashboard
```

---

## 🔧 Configuration

### Environment Variables
```env
# Database (Required)
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Optional
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key
```

### AI Configuration
```python
# In ai_engine.py
retrain_interval = 3600  # 1 hour
min_data_points = 25     # Min for training
safety_thresholds = {
    'safe': 80,      # > 80 = Safe
    'warning': 50,   # 50-80 = Warning  
    'critical': 50   # < 50 = Critical
}
```

---

## 📈 Scaling for Production

### Performance Optimization
- Use Redis for caching AI results
- Enable database connection pooling
- Deploy with Gunicorn + multiple workers
- Use background job queue (Celery) for AI training

### Infrastructure Scaling
```bash
# Scale with Docker Compose
docker-compose up --scale api=3

# Scale with Kubernetes
kubectl scale deployment tourist-safety-api --replicas=5
```

### Monitoring Stack
- **Prometheus** - Metrics collection
- **Grafana** - Dashboard and visualization  
- **ELK Stack** - Logging and analysis
- **Jaeger** - Distributed tracing

---

## ✅ Production Checklist

### Security
- [ ] Update all secret keys
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure rate limiting
- [ ] Set up firewall rules
- [ ] Enable audit logging

### Performance  
- [ ] Configure database connection pooling
- [ ] Enable Redis caching
- [ ] Set up CDN for static assets
- [ ] Configure load balancing
- [ ] Enable compression

### Monitoring
- [ ] Set up health checks
- [ ] Configure alerting (PagerDuty/Slack)
- [ ] Enable application monitoring
- [ ] Set up log aggregation
- [ ] Configure backup strategy

---

## 🎯 Success Metrics

### API Performance
- Response time < 200ms for most endpoints
- 99.9% uptime
- Error rate < 0.1%

### AI Engine Performance  
- Assessment time < 500ms per location
- Model accuracy > 85%
- False positive rate < 5%

### Alert System Performance
- Critical alerts processed < 10 seconds
- SMS delivery rate > 95%
- Push notification delivery > 98%

---

**🚀 Your Smart Tourist Safety System is production-ready!**

For support: Check `/docs` endpoint or review logs at `/health`