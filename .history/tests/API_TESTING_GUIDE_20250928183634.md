# Smart Tourist Safety System - API Testing Guide

## API Endpoints

### Core Tourist Management
- `POST /registerTourist` - Register new tourist
  - Required fields: `name`, `contact`, `emergency_contact`
  - Optional fields: `email`, `trip_info`, `age`, `nationality`, `passport_number`

- `GET /tourists/{tourist_id}` - Get tourist details with activity

### Location & Safety
- `POST /sendLocation` - Send location & trigger AI assessment
  - Required fields: `tourist_id`, `latitude`, `longitude`
  - Optional fields: `altitude`, `accuracy`, `speed`, `heading`, `timestamp`

### Emergency & Alerts
- `POST /pressSOS` - Emergency SOS alert
  - Required fields: `tourist_id`, `latitude`, `longitude`
  - Optional fields: `message`, `description`

- `GET /getAlerts` - Get all alerts with filtering
  - Query parameters: `tourist_id`, `status`, `type`, `severity`

- `PUT /resolveAlert/{alert_id}` - Resolve an alert
  - Optional fields: `resolved_by`, `resolution_notes`

### Incident Reporting
- `POST /fileEFIR` - File electronic incident report
  - Required fields: `tourist_id`, `incident_type`, `description`, `location`
  - Optional fields: `incident_datetime`, `additional_info`

### AI & Monitoring
- `GET /api/v1/ai/training/status` - AI training status
- `GET /api/v1/ai/data/stats` - System data statistics
- `POST /api/v1/ai/training/force` - Force AI training

### System
- `GET /` - Root endpoint with API info

## Testing Instructions

1. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```
   python -m uvicorn app.main:app --reload
   ```

3. **Run the Test Suite**
   ```
   python tests/test_api_endpoints.py
   ```

4. **Run Server and Tests Combined**
   ```
   python tests/run_api_server_and_test.py
   ```

5. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Expected Test Results

When running the test script, you should see a summary of tests run against all endpoints. All required endpoints should pass with appropriate status codes.

The test script:
1. Registers a test tourist
2. Sends location updates
3. Creates SOS alerts
4. Gets and resolves alerts
5. Tests E-FIR filing
6. Tests AI endpoints

## Common Issues and Solutions

1. **Server Not Starting**
   - Check if port 8000 is already in use
   - Verify database connection
   - Check for errors in the console output

2. **Database Connection Errors**
   - Ensure Supabase credentials are correct in config
   - Check that Supabase server is running

3. **Missing Dependencies**
   - Run `pip install -r requirements.txt` to install all dependencies

4. **Test Failures**
   - Check the API response for detailed error messages
   - Verify the request body format matches the API requirements