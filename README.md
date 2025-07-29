# Job Application Tracker - Backend API

A FastAPI-based REST API for tracking job applications with comprehensive CRUD operations, filtering, and statistics.

## Features

- **CRUD Operations**: Create, Read, Update, Delete job applications
- **Advanced Filtering**: Filter by company, job title, and application status
- **Sorting & Pagination**: Sort by multiple fields with pagination support
- **Statistics**: Get summary statistics and status breakdown
- **Validation**: Comprehensive input validation with Pydantic
- **Error Handling**: Proper error responses and database rollback

## 🛠️ Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **SQLite** - Lightweight database (can be easily switched to PostgreSQL/MySQL)
- **Uvicorn** - ASGI server


## API Endpoints

### Job Applications

- `POST /api/v1/job-applications` - Create a new job application
- `GET /api/v1/job-applications` - List all job applications (with filtering & pagination)
- `GET /api/v1/job-applications/{id}` - Get a specific job application
- `PUT /api/v1/job-applications/{id}` - Update a job application
- `DELETE /api/v1/job-applications/{id}` - Delete a job application

### Statistics

- `GET /api/v1/job-applications/stats/summary` - Get summary statistics

## API Documentation

Once the server is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Database Schema

The application uses SQLite with the following main table:

### JobApplication
- `id` (Primary Key)
- `job_title` (Required)
- `company` (Required)
- `job_description`
- `location`
- `salary`
- `job_url`
- `date_applied` (Required)
- `date_job_posted`
- `application_status` (Default: "Applied")
- `interview_stage` (Default: "None")
- `notes`
- `created_at` (Auto-generated)
- `updated_at` (Auto-updated)
