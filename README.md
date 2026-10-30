# Event & Movie Ticket Booking System

A FastAPI-based backend application for managing movie and event bookings, venues, screens, seats, showtimes, payments, and ticket QR-code downloads.

## Technologies Used

- Python 3.14
- FastAPI
- MySQL 8.0
- SQLAlchemy (Async)
- Alembic
- JWT Authentication
- Redis integration
- Pydantic
- QR Code Generation
- Uvicorn

## Main Features

### Authentication and Authorization
- User registration and login
- JWT-based authentication
- Role-based access control
- Roles: Admin, Organizer, Customer, Staff
- Current-user profile endpoint
- Organizer approval and staff creation

### Venue and Event Management
- Venue management
- Screen management
- Seat management
- Event creation and management
- Showtime scheduling and management

### Booking Management
- Ticket booking
- Customer booking history
- Seat booking validation
- Booking references
- QR-code generation
- QR-code image download

### Payment Management
- Mock payment creation
- Successful and failed payment processing
- Payment status retrieval

### Refund Management
- Refund request creation
- Mock refund processing
- Refund status retrieval

## Project Structure

```text
Event_Movie_Ticket_Booking_System/
│
├── alembic/
│   └── versions/
│
├── app/
│   ├── auth/
│   ├── jobs/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── websockets/
│   ├── database.py
│   └── main.py
│
├── static/
├── tickets/
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Event_Movie_Ticket_Booking_System
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

Configure your MySQL database URL, JWT secret key, and Redis connection URL.

Never upload your actual `.env` file or credentials to GitHub.

### 6. Create the MySQL database

```sql
CREATE DATABASE event_movie_booking_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 7. Run database migrations

```powershell
alembic upgrade head
```

### 8. Start the application

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

## API Documentation

After starting the application, open:

**Swagger UI:**

http://127.0.0.1:8002/docs

**OpenAPI JSON:**

http://127.0.0.1:8002/openapi.json

## Main API Modules

| Module | Main Endpoints |
|---|---|
| Authentication | `/auth/register`, `/auth/login`, `/auth/me` |
| Admin | `/admin/organizers/{user_id}/approve`, `/admin/staff` |
| Venues | `/venues` |
| Screens | `/screens` |
| Seats | `/seats` |
| Events | `/events` |
| Showtimes | `/showtimes` |
| Bookings | `/bookings/` |
| Payments | `/payments/` |
| Refunds | `/refunds/` |

## Database Migrations

Alembic is used to manage database schema changes and migrations.

```powershell
alembic current
alembic history
alembic upgrade head
```

## Payment and Ticket Notes

- Payment processing uses a mock payment workflow.
- Refund processing uses a mock refund workflow.
- QR codes are generated as PNG images.
- QR images can be downloaded through the booking QR-code endpoint.
- Email notifications currently include terminal preview functionality.

## Testing

The following application checks were performed:

- FastAPI application startup
- Swagger documentation
- Root endpoint
- Admin login and JWT authorization
- Current-user endpoint
- Event and showtime retrieval
- Seat retrieval
- Customer booking history
- QR-code image download
- Refund retrieval
- Existing successful and failed mock-payment records

## Important Notes

- MySQL must be configured before starting the application.
- Redis must be configured for Redis-dependent seat-locking functionality.
- Configure all required environment variables before running the application.
- Do not commit passwords, JWT secrets, or other sensitive credentials.

## Project

**Event & Movie Ticket Booking System**

Backend API developed using FastAPI, Python, MySQL, SQLAlchemy, and Alembic.
