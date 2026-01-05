# Render Health Check Setup

## Health Check Endpoints

Your PublicBridge application now has two health check endpoints:

1. **Primary endpoint**: `/health/` (defined in `PublicBridge/urls.py:32`)
2. **Secondary endpoint**: `/health-check/` (defined in `main/urls.py:7`)

Both endpoints return a simple "OK" response with HTTP 200 status.

## Setting Up Automatic Health Checks

To prevent your Render deployment from sleeping, you need to set up automatic health checks. Here are the recommended approaches:

### Option 1: UptimeRobot (Free)
1. Sign up at https://uptimerobot.com
2. Create a new monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://your-app.onrender.com/health/`
   - Monitoring Interval: 5 minutes (free tier)
3. Save the monitor

### Option 2: Cron-Job.org (Free)
1. Sign up at https://cron-job.org
2. Create a new cron job:
   - URL: `https://your-app.onrender.com/health/`
   - Schedule: Every 5 minutes
   - HTTP Method: GET
3. Save the job

### Option 3: GitHub Actions (Free)
Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Render Alive

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping health endpoint
        run: |
          curl -f https://your-app.onrender.com/health/ || exit 1
```

### Option 4: JavaScript Browser Extension
If you frequently visit the site, you can use a browser extension that automatically pings the endpoint.

## Configuration Notes

- **Interval**: Query every 5-10 minutes for optimal results
- **Timeout**: Render free tier sleeps after 15 minutes of inactivity
- **Response**: Both endpoints return simple "OK" or JSON response
- **Monitoring**: You can monitor both endpoints for redundancy

## Testing

Test your endpoints:
```bash
# Test primary endpoint
curl https://your-app.onrender.com/health/

# Test secondary endpoint  
curl https://your-app.onrender.com/health-check/
```

Expected responses:
- `/health/`: Plain text "OK"
- `/health-check/`: JSON `{"status": "healthy", "service": "PublicBridge"}`

## Deployment

The health check endpoints are already deployed with your application. Simply set up one of the monitoring solutions above to start keeping your Render deployment awake.