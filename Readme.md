# 🛡️ GuardianX – Safety API Platform

**Tagline**: *Built for safety. Designed for freedom.*

GuardianX is a secure, scalable backend system built with **FastAPI**, designed to power a real-time personal safety app. It supports **OTP-based authentication**, **user registration**, **real-time SOS tracking**, **incident reporting**, and **ally-based location tracking**. The backend integrates **Redis caching** and **Redis-based circuit breakers** for high availability and low latency. The system is deployed serverlessly on **AWS Lambda** using **Docker images stored in ECR**, triggered via **API Gateway**, and managed using **Terraform**.

---

## 🕐️ Architecture

**Core Stack:**

* **Backend**: FastAPI (ASGI)
* **Deployment**: AWS Lambda + API Gateway
* **Container**: AWS ECR (Docker)
* **Infrastructure as Code**: Terraform
* **Database**: DynamoDB (users, sos_events, incidents, otp_requests)
* **Cache & Circuit Breaker**: Redis Cloud
* **Email**: SMTP (Gmail)
* **Auth**: JWT + Refresh Tokens
* **Geolocation**: Google Maps API (proxied)
* **Monitoring**: CloudWatch + SNS Alerts

> **Note:** For *production*, it is recommended to use **Amazon SES** instead of Gmail SMTP for higher throughput and reliability.

**Flow:**

1. User signs up → backend stores profile in DynamoDB
2. User requests OTP → email OTP sent via Gmail SMTP
3. OTP verified → JWT + refresh token issued
4. User triggers SOS → location + timestamp stored in `sos_events`
5. Allies receive email alerts and can track real-time location
6. Redis caching speeds up repeated GET requests
7. Redis circuit breakers prevent cascading failures from unhealthy services
8. Optional: location heartbeat + incident reporting

---

## 🖼️ Architecture Diagram

### 🧱 Layered System Design (Infrastructure + Functional Flow)

**SVG Version (for zoomable detail):**

![GuardianX Architecture Diagram SVG](Untitled-2025-07-29-0656.svg)

---

## 🚀 How to Clone and Run Locally

```bash
git clone https://github.com/anishsamantaray/GuardianX-backend.git
cd guardianx-backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### 🥚 Run with Uvicorn

```bash
uvicorn app.main:app --reload
```

---

## 🔐 Required Environment Variables

Create a `.env` file:

```env
# AWS
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# SMTP
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

# JWT
JWT_SECRET_KEY=supersecurekey
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_MINUTES=10080

# Redis
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_PASSWORD=your_redis_password

# Google Maps
GOOGLE_MAPS_API_KEY=your_maps_key
```

---

## 🐳 Docker + ECR + Lambda Deployment

### 1. Build Docker Image

```bash
docker build -t guardianx-fastapi .
```

### 2. Push to ECR

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
docker tag guardianx-fastapi:latest <ecr-url>/guardianx-fastapi:latest
docker push <ecr-url>/guardianx-fastapi:latest
```

### 3. Deploy Using Terraform

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

### 4. API Gateway Endpoint

Terraform will output the live HTTP endpoint linked to Lambda.

---


## 📊 Logging & Monitoring (CloudWatch)

All Lambda invocations emit structured JSON logs for observability.

### Example Log Structure

```
{
  "level": "INFO",
  "timestamp": "2025-01-22T10:33:12Z",
  "route": "/sos/trigger",
  "email": "user@example.com",
  "lat": 12.9182,
  "lng": 77.6421,
  "message": "SOS event recorded"
}
```

SNS Alerts configured for:

* Lambda failures
* DynamoDB throttling
* Circuit breaker OPEN state
* High API latency

---

## 🚢 Deployment Strategy & Versioning


GuardianX uses a modern CI/CD-friendly deployment workflow:

### Versioning

* Each Docker image is versioned using semantic tags (`v1.0.0`, `v1.1.0`, etc.)
* Lambda uses **image digest pinning** for reliable rollbacks
* Terraform automatically updates Lambda to the latest pushed image

### Deployment Flow

1. Build Docker image locally or through CI
2. Tag with version + `latest`
3. Push to Amazon ECR
4. Terraform applies infra updates
5. Lambda pulls the new container image
6. CloudWatch monitors runtime behaviour

Blue-green / canary deployment support can be added later via Lambda traffic shifting.

---

## 📦 DynamoDB Tables

| Table          | Partition Key | Sort Key  | Purpose                |
| -------------- | ------------- | --------- | ---------------------- |
| `users`        | email         | –         | User registration info |
| `otp_requests` | email         | –         | OTP storage + TTL      |
| `sos_events`   | email         | timestamp | SOS trigger logs       |
| `incidents`    | incident_id   | –         | Reported incidents     |

---

## 📙 API Endpoints Overview

### Authentication (Public)

| Method | Endpoint              | Description                  |
| ------ | --------------------- | ---------------------------- |
| POST   | `/user/signup`        | Register a new user          |
| POST   | `/user/send-otp`      | Send OTP to registered email |
| POST   | `/user/verify-otp`    | Verify OTP, issue tokens     |
| POST   | `/user/logout`        | Invalidate refresh token     |
| GET    | `/user/refresh-token` | Issue new access token       |

---

### User (Protected)

| Method | Endpoint                   | Description                         |
| ------ | -------------------------- | ----------------------------------- |
| GET    | `/user/profile`            | Get current user profile            |
| PATCH  | `/user/editprofile`        | Update current user profile         |
| POST   | `/user/upload-profile-pic` | Get presigned URL for profile image |
| GET    | `/user/suggestions`        | Search users by name/email          |

---

### Allies (Protected)

| Method | Endpoint                    | Description                  |
| ------ | --------------------------- | ---------------------------- |
| POST   | `/allies/request`           | Send ally request            |
| POST   | `/allies/respond`           | Accept / reject ally request |
| GET    | `/allies/requests/received` | Pending incoming requests    |
| GET    | `/allies/requests/sent`     | Pending outgoing requests    |
| GET    | `/allies`                   | List accepted allies         |

---

### SOS (Protected)

| Method | Endpoint         | Description              |
| ------ | ---------------- | ------------------------ |
| POST   | `/sos/trigger`   | Trigger SOS event        |
| POST   | `/sos/heartbeat` | Update live SOS location |
| POST   | `/sos/end`       | End SOS session          |

---

### Incidents (Protected)

| Method | Endpoint                  | Description                 |
| ------ | ------------------------- | --------------------------- |
| POST   | `/incident/report`        | Report a safety incident    |
| GET    | `/incident/history`       | List current user incidents |
| GET    | `/incident/{incident_id}` | Get incident details        |

---

### Maps

| Method | Endpoint                   | Auth      | Description             |
| ------ | -------------------------- | --------- | ----------------------- |
| GET    | `/maps/autocomplete`       | Protected | Address autocomplete    |
| GET    | `/maps/details`            | Protected | Place details from ID   |
| GET    | `/maps/reverse-geocode`    | Protected | Coordinates to address  |
| GET    | `/maps/distance-from-home` | Protected | Distance from user home |

---
## 📌 Redis Integration

### Caching

* Write-through caching for read-heavy endpoints
* TTL-based invalidation
* Reduced DynamoDB read load

### Circuit Breakers

* Redis-backed state machine
* Prevents cascading failures
* States: `closed → open → half-open`
* Automatic recovery after cooldown

---

## 🔖 Roadmap (Next Features)

* [ ] Push notifications (SNS)
* [ ] Admin dashboard (React + Map integration)
* [ ] Ally system with mutual request & live tracking
* [ ] Zone-based geofencing and risk prediction
* [ ] Upload media (image/audio) for incidents
* [ ] Chatbot integration (LLM-powered)
* [ ] Redis Pub/Sub for live updates
* [ ] Mobile App using React Native

---

## 🧠 Credits

Built by **Anish Samantaray** using FastAPI, AWS Lambda, DynamoDB, and Redis for GuardianX – a modern safety and incident reporting platform.

---

## 🔖 License

MIT – Free to use, modify, and deploy.
