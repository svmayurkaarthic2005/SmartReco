# Templates Directory

## ⚠️ Notice: No HTML Templates - React Frontend Only

This directory is **empty** because SmartReco uses a **separate React frontend** for all UI.

The FastAPI backend serves **JSON-only API responses** with no server-side rendering.

## Architecture

**Backend (FastAPI):**
- JSON API at `/auth/*` endpoints
- No HTML templates
- No static file serving
- CORS enabled for React frontend

**Frontend (React - Separate Project):**
- Runs on `localhost:3000` (Create React App) or `localhost:5173` (Vite)
- Handles all UI rendering
- Calls backend API for data
- Stores JWT token in localStorage

## Current API Endpoints (JSON Only)

Use these endpoints from your React frontend:

### POST `/auth/register`
Register a new user account.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "name": "John Doe"
}
```

### POST `/auth/login`
Authenticate user and get JWT token.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "name": "John Doe"
}
```

**Error (401):**
```json
{
  "detail": "Invalid credentials"
}
```

### GET `/auth/me`
Get current user profile (requires Bearer token).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user",
  "created_at": "2026-08-04T10:30:00"
}
```

**Error (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

### POST `/auth/refresh`
Refresh access token (requires Bearer token).

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "name": "John Doe"
}
```

## React Frontend Integration

### Store Token After Login

```javascript
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ email, password })
});

const data = await response.json();

if (response.ok) {
  // Store token
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('user_id', data.user_id);
  localStorage.setItem('user_role', data.role);
  localStorage.setItem('user_name', data.name);
}
```

### Make Authenticated Requests

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.status === 401) {
  // Token expired, redirect to login
  localStorage.clear();
  navigate('/login');
}
```

## CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (React Create React App)
- `http://localhost:5173` (Vite)

Additional origins can be configured in `.env`:
```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Documentation

For complete API documentation:
- **OpenAPI/Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Auth Documentation**: See `AUTH_DOCUMENTATION.md` in project root
- **Quick Start**: See `AUTH_QUICKSTART.md` in project root

---

**Note:** If you need to use server-side rendering, you can re-enable templates by:
1. Uncommenting StaticFiles and Jinja2Templates in `app/main.py`
2. Adding template routes back to the application
3. Mounting the static directory

However, the recommended architecture is to use the React frontend for all UI.
