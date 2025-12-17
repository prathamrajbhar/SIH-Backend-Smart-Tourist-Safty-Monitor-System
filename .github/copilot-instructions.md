# 🚨 Prompt: Smart Tourist Safety & Incident Response System (Supabase + FastAPI + AI/ML)

## 🎯 Goal

Develop a **Smart Tourist Safety & Incident Response System** with:

1. **Backend APIs** → FastAPI + Supabase (DB + Auth + Storage)
2. **AI/ML Safety Layer** → Hybrid pipeline (Rule-based + ML + Deep Learning)

The system must track tourists, detect risks, trigger alerts, and compute a **real-time safety score**.

---

## 🖥️ 1. Backend Setup

* **Framework:** FastAPI
* **Database & Auth:** Supabase (Postgres + Auth)
* **ORM/Client:** Supabase Python SDK (no direct SQLAlchemy ORM)
* **Run with:** Uvicorn
* **Provide:** `requirements.txt`

Example `requirements.txt`:

```txt
fastapi
uvicorn
supabase
pydantic
python-dotenv
```

Enable **CORS** for mobile + web dashboards.
Add Swagger docs at `/docs`.
Seed database with **demo tourists, locations, and restricted zones** on startup.

---

## 🗄️ 2. Database Schema (Supabase)

### `tourists`

| Column               | Type        | Notes               |
| -------------------- | ----------- | ------------------- |
| id                   | bigint PK   | Auto                |
| name                 | varchar     | required            |
| contact              | varchar     | unique              |
| email                | varchar     | optional            |
| trip_info            | jsonb       | default {}          |
| emergency_contact    | varchar     | required            |
| safety_score         | integer     | default 100 (0–100) |
| is_active            | boolean     | default true        |
| last_location_update | timestamptz | nullable            |
| created_at           | timestamptz | default now()       |

### `locations`

| Column     | Type                    | Notes         |
| ---------- | ----------------------- | ------------- |
| id         | bigint PK               | Auto          |
| tourist_id | bigint FK → tourists.id |               |
| latitude   | numeric (-90 to 90)     |               |
| longitude  | numeric (-180 to 180)   |               |
| altitude   | numeric                 | optional      |
| speed      | numeric                 | optional      |
| timestamp  | timestamptz             | default now() |

### `alerts`

| Column     | Type        | Notes                         |
| ---------- | ----------- | ----------------------------- |
| id         | bigint PK   | Auto                          |
| tourist_id | bigint FK   |                               |
| type       | varchar     | panic, geofence, anomaly, sos |
| severity   | varchar     | LOW, MEDIUM, HIGH, CRITICAL   |
| message    | text        | required                      |
| latitude   | numeric     | optional                      |
| longitude  | numeric     | optional                      |
| status     | varchar     | active, resolved              |
| timestamp  | timestamptz | default now()                 |

### `restricted_zones`

| Column             | Type            | Notes           |
| ------------------ | --------------- | --------------- |
| id                 | bigint PK       | Auto            |
| name               | varchar         | required        |
| description        | text            | optional        |
| coordinates        | jsonb           | GeoJSON polygon |
| danger_level       | int (1–5)       |                 |
| buffer_zone_meters | int default 100 |                 |

---

## 📡 3. API Endpoints

### Tourist Management

* `POST /tourists/register` → Register tourist
* `GET /tourists/{id}` → Get tourist details (safety score, contacts)

### Location Management

* `POST /locations/update` → Tourist sends current GPS

  ```json
  { "tourist_id": 1, "latitude": 28.61, "longitude": 77.23 }
  ```
* `GET /locations/all` → Get latest location of all tourists

### Alerts

* `POST /alerts/panic` → Panic alert
* `POST /alerts/geofence` → Geofence alert
* `GET /alerts` → Get all active alerts
* `PUT /alerts/{id}/resolve` → Resolve alert

---

## 📊 4. Safety Score Rules

* Panic button → `-40`
* Enter risky zone → `-20`
* Stay safe 1 hour → `+10`
* Range: `0–100`

Update **`tourists.safety_score`** in Supabase DB.

---

## 🤖 5. AI/ML Hybrid Layer

### 1. **Rule-Based Geo-fencing**

* Check if location ∈ `restricted_zones` → instant alert

### 2. **Unsupervised Anomaly Detection (Isolation Forest)**

* Features: `[distance_per_min, inactivity_duration, deviation_from_route, speed]`
* Output: anomaly score

### 3. **Temporal Modeling (LSTM/GRU Autoencoder)**

* Input: sequential movement (sliding window)
* Output: temporal risk score

### 4. **Future: Supervised Classification (LightGBM/XGBoost)**

* Learn severity from real labeled incidents

### 5. **Alert Fusion**

* Fuse results → compute final **Safety Score (0–100)**

  * > 80 → Safe
  * 50–80 → Warning
  * <50 → Critical (alert police & family)

---

## 🧪 6. Dataset & Demo

* Generate **100 dummy tourists** with random trips (Delhi, Goa, Shillong, etc.)
* Insert **5–10 restricted zones** as polygons
* Store in Supabase for testing

---

## 🔐 7. Supabase Config

* **URL:** `https://tqenqwfuywighainnujh.supabase.co`
* **anon key:**

  ```
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
* **service_role key:**

  ```
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```

Use **service role key** for backend server (trusted).
Use **anon key** for frontend apps (untrusted).

---

## ✅ Expected Workflow

1. Tourist sends GPS → API stores in Supabase
2. Backend calls AI/ML pipeline → compute anomaly/safety score
3. Alerts generated if needed
4. Supabase DB updated with results
5. Dashboard + Mobile App fetch via REST

---
