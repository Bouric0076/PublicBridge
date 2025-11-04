# PythonAnywhere Free Django Deployment Guide

## Overview
PythonAnywhere offers **completely free Django hosting** without requiring credit card information. This guide will help you deploy PublicBridge on PythonAnywhere.

## Prerequisites
- PythonAnywhere account (free)
- GitHub repository with your code
- Basic understanding of Django

## Step-by-Step Deployment Process

### 1. Create PythonAnywhere Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Sign up for a **Beginner account** (completely free)
3. No credit card required

### 2. Prepare Your Code
1. Push your code to GitHub
2. Update settings to use `pythonanywhere_config.py`

### 3. Configure Web App
1. Go to "Web" tab in PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.11
5. Choose "Django" as framework

### 4. Upload Your Code
```bash
# In PythonAnywhere Bash console:
git clone https://github.com/your-username/PublicBridge.git
cd PublicBridge
```

### 5. Install Dependencies
```bash
# In PythonAnywhere Bash console:
pip3.11 install --user -r requirements.txt
```

### 6. Configure Settings
1. Edit `/var/www/your-username_pythonanywhere_com_wsgi.py`
2. Update paths to match your project structure
3. Use settings from `pythonanywhere_config.py`

### 7. Database Setup
1. Go to "Databases" tab
2. Create MySQL database (free)
3. Run migrations:
```bash
python manage.py migrate
```

### 8. Static Files
```bash
python manage.py collectstatic
```

### 9. Reload Web App
1. Go to "Web" tab
2. Click "Reload" to apply changes

## Free Tier Limitations
- **CPU time**: 100 seconds per day
- **Storage**: 512MB
- **Bandwidth**: 1GB per month
- **Domain**: your-username.pythonanywhere.com
- **Database**: MySQL (limited size)

## Advantages
- ✅ No credit card required
- ✅ Django-optimized hosting
- ✅ Easy deployment process
- ✅ Built-in MySQL database
- ✅ Python shell access
- ✅ Scheduled tasks support

## Common Issues & Solutions

### Static Files Not Loading
- Ensure `collectstatic` was run
- Check STATIC_ROOT path in settings
- Verify web app configuration

### Database Connection Errors
- Check database credentials in settings
- Ensure database was created in "Databases" tab
- Verify MySQL service is running

### Import Errors
- Install missing packages via pip
- Check Python version compatibility
- Verify virtual environment activation

## Next Steps
1. Test your deployed application
2. Monitor resource usage
3. Consider upgrading if you need more resources
4. Set up custom domain (requires paid plan)

## Support
- PythonAnywhere forums: [https://www.pythonanywhere.com/forums/](https://www.pythonanywhere.com/forums/)
- Django documentation: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)