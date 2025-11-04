#!/usr/bin/env python3
"""
PythonAnywhere Deployment Script for PublicBridge
This script helps automate the deployment process to PythonAnywhere.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_pythonanywhere_wsgi():
    """Create PythonAnywhere WSGI configuration file."""
    wsgi_content = '''import os
import sys

# Add your project directory to the sys.path
project_home = u'/home/{username}/publicbridge'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'PublicBridge.pythonanywhere_config'
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['DEBUG'] = 'False'

# Import and configure Django
import django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''
    
    username = input("Enter your PythonAnywhere username: ")
    wsgi_content = wsgi_content.format(username=username)
    
    with open('pythonanywhere_wsgi.py', 'w') as f:
        f.write(wsgi_content)
    
    print("✅ Created pythonanywhere_wsgi.py")
    return username

def create_bash_script(username):
    """Create bash script for PythonAnywhere setup."""
    bash_content = f'''#!/bin/bash
# PythonAnywhere setup script for PublicBridge

echo "Setting up PublicBridge on PythonAnywhere..."

# Create virtual environment
echo "Creating virtual environment..."
mkvirtualenv --python=/usr/bin/python3.11 publicbridge

# Clone repository (replace with your GitHub URL)
echo "Cloning repository..."
cd /home/{username}/
git clone https://github.com/your-username/PublicBridge.git publicbridge

# Install requirements
echo "Installing requirements..."
cd /home/{username}/publicbridge
workon publicbridge
pip install -r requirements.txt

# Create static and media directories
echo "Creating directories..."
mkdir -p /home/{username}/publicbridge/staticfiles
mkdir -p /home/{username}/publicbridge/media

# Run migrations
echo "Running migrations..."
python manage.py migrate --settings=PublicBridge.pythonanywhere_config

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=PublicBridge.pythonanywhere_config

# Create superuser (optional)
echo "Creating superuser..."
python manage.py createsuperuser --settings=PublicBridge.pythonanywhere_config

echo "✅ Setup complete! Now configure the web app in PythonAnywhere dashboard."
echo "Don't forget to:"
echo "1. Set the virtualenv to: /home/{username}/.virtualenvs/publicbridge"
echo "2. Set the source code directory to: /home/{username}/publicbridge"
echo "3. Set the WSGI configuration file"
echo "4. Reload the web app"
'''
    
    with open('setup_pythonanywhere.sh', 'w') as f:
        f.write(bash_content)
    
    # Make script executable
    os.chmod('setup_pythonanywhere.sh', 0o755)
    print("✅ Created setup_pythonanywhere.sh")

def create_requirements_pythonanywhere():
    """Create PythonAnywhere-compatible requirements.txt"""
    # Read current requirements
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    # Remove problematic packages for PythonAnywhere
    filtered_requirements = []
    for line in requirements.split('\n'):
        line = line.strip()
        # Skip packages that might cause issues on PythonAnywhere
        if not any(skip in line.lower() for skip in ['psycopg2', 'daphne', 'channels-redis']):
            filtered_requirements.append(line)
    
    # Add PythonAnywhere-compatible packages
    pythonanywhere_requirements = '''
# PythonAnywhere-compatible requirements
django==4.2.7
djangorestframework==3.14.0
django-grappelli==3.0.8
django-crispy-forms==2.1
django-allauth==0.57.0
whitenoise==6.6.0
dj-database-url==2.1.0
mysqlclient==2.2.0  # For PythonAnywhere MySQL
requests==2.31.0
sqlparse==0.4.4
asgiref==3.7.2
Pillow==10.1.0
python-decouple==3.8
gunicorn==21.2.0
'''
    
    with open('requirements_pythonanywhere.txt', 'w') as f:
        f.write(pythonanywhere_requirements)
    
    print("✅ Created requirements_pythonanywhere.txt")

def main():
    """Main deployment function."""
    print("🚀 PythonAnywhere Deployment Setup for PublicBridge")
    print("=" * 50)
    
    # Get username
    username = create_pythonanywhere_wsgi()
    
    # Create setup scripts
    create_bash_script(username)
    create_requirements_pythonanywhere()
    
    print("\n🎉 Setup files created successfully!")
    print("\nNext steps:")
    print("1. Sign up at https://www.pythonanywhere.com")
    print("2. Upload setup_pythonanywhere.sh to your PythonAnywhere account")
    print("3. Run: bash setup_pythonanywhere.sh")
    print("4. Configure web app in PythonAnywhere dashboard")
    print("5. Update pythonanywhere_config.py with your database credentials")
    print("\nFor detailed instructions, see pythonanywhere_setup.md")

if __name__ == "__main__":
    main()