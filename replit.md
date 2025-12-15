# TI-Monitoring

## Overview
TI-Monitoring is a German Telematikinfrastruktur (TI) monitoring application that tracks the availability and status of TI components. It fetches data from the gematik API and provides a web interface for viewing statistics, status information, and notifications.

## Project Structure
- `app.py` - Main Dash application entry point
- `mylibrary.py` - Core library with database operations and utility functions
- `cron.py` - Background job for fetching data from gematik API
- `config.yaml` - Application configuration
- `pages/` - Dash multi-page app pages (home, stats, notifications, admin)
- `assets/` - Static assets (CSS, JS, images)

## Tech Stack
- **Frontend**: Dash (Plotly) with custom CSS
- **Backend**: Flask (via Dash server)
- **Database**: PostgreSQL (originally designed for TimescaleDB, adapted for standard PostgreSQL)
- **Python Version**: 3.11

## Running the Application
The app runs on port 5000 with the workflow "TI-Monitoring":
```
python app.py
```

For production deployment:
```
gunicorn --bind=0.0.0.0:5000 --workers=2 app:server
```

## Environment Variables
Required environment variables (set via Replit Secrets):
- `POSTGRES_HOST` - Database host
- `POSTGRES_PORT` - Database port  
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `ENCRYPTION_KEY` - Fernet encryption key for sensitive data

## Database
The application uses PostgreSQL for storing:
- `measurements` - Time-series availability data
- `ci_metadata` - Configuration item metadata
- `users` - User accounts for OTP authentication
- `otp_codes` - One-time password codes
- `notification_profiles` - User notification settings

## Key Features
- Real-time TI component status monitoring
- Historical availability statistics
- Multi-user notification system with OTP authentication
- Support for 90+ notification channels via Apprise
- Admin dashboard for user management

## Notes
- The app was designed for TimescaleDB but has been adapted to work with standard PostgreSQL
- Data is fetched from the gematik API: https://ti-lage.prod.ccs.gematik.solutions/lageapi/v1/tilage/bu/PU
- The cron job (`cron.py`) should be run separately to populate data
