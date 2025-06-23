# SafeWork Pro - Comprehensive Architecture Overview

## 🏗️ High-Level Architecture

SafeWork Pro is a **modular, containerized health management system** for Korean construction sites with the following architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│  FastAPI        │────▶│ PostgreSQL 15   │
│  (TypeScript)   │     │   Backend       │     │  with Korean    │
│  Port 3001      │     │  Port 8000      │     │     Locale      │
└─────────────────┘     └──────┬──────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Redis 7      │
                        │ Session Cache   │
                        └─────────────────┘
```

## 🔧 Technology Stack

- **Backend**: Python 3.11+ with FastAPI, SQLAlchemy ORM, Asyncio
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Radix UI
- **Database**: PostgreSQL 15 with Korean full-text search
- **Cache**: Redis 7 for session management
- **Deployment**: Docker containers with docker-compose
- **Testing**: Pytest (backend) + Vitest (frontend)
- **Monitoring**: Custom structured JSON logging

## 🎯 Key Architectural Decisions

### 1. **Application Factory Pattern**
- **File**: `src/app.py`
- **Pattern**: FastAPI app created via `create_app()` factory
- **Benefits**: Configurable instances, better testing, lifecycle management

### 2. **Layered Architecture** 
```
Handlers (API) → Services (Business Logic) → Repositories (Data) → Models (ORM)
```

### 3. **Async-First Design**
- All database operations use SQLAlchemy async sessions
- Non-blocking I/O throughout the stack
- Proper connection pooling and retry logic

## 📁 Directory Structure
```
src/
├── app.py              # FastAPI application factory
├── config/             # Database, settings configuration
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── handlers/           # FastAPI route handlers (API layer)
├── services/           # Business logic layer
├── repositories/       # Data access layer
├── middleware/         # Custom middleware (logging, performance)
├── utils/              # Utilities (logging, error handling)
└── components/         # React components (modular frontend)
```