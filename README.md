# ChargeMate AI Backend

## Overview

ChargeMate AI is an AI-powered EV charging station management backend built with FastAPI, SQLAlchemy, Alembic, and PostgreSQL.

The system provides EV driver management, charging simulation, AI-based demand forecasting, fault detection, and automated recommendations.

---

## Tech Stack

- FastAPI
- Python
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL (Neon Database)
- Pydantic
- Uvicorn
- Scikit-learn (AI evaluation metrics)

---

## Project Modules

### Authentication
- User login
- Token-based authentication
- Role-based access control

### Driver Management
- Create driver
- View drivers
- Update driver
- Delete driver
- Vehicle management
- Favorite charging stations

### Simulation Management
- Create simulation scenarios
- Store initial and current states
- Manage charging scenarios

### AI Module

#### Demand Forecasting
Features:
- Predicted demand calculation
- Demand level classification
- Evaluation metrics:
  - MAE
  - RMSE

#### Fault Detection
Features:
- Fault type detection
- Severity classification
- Confidence scoring
- Evaluation metrics:
  - Precision
  - Recall
  - F1 Score
  - False positives

### AI Recommendations

Automatically generates recommendations:

- High demand:
  - Load balancing suggestions

- High severity fault:
  - Maintenance alerts

---

## API Documentation

Swagger UI:
