#!/usr/bin/env python
"""
Database Migration Script - MySQL to SQLite
This script handles the migration from MySQL to SQLite database.
"""

import os
import sys
import django
from django.core.management import call_command
from django.db import connection
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_django():
    """Initialize Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
    django.setup()

def check_sqlite_connection():
    """Test SQLite database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"SQLite connection successful. Found {len(tables)} tables.")
            return True
    except Exception as e:
        logger.error(f"SQLite connection failed: {e}")
        return False

def migrate_database():
    """Perform database migration"""
    logger.info("Starting database migration to SQLite...")
    
    try:
        # Run migrations
        logger.info("Running Django migrations...")
        call_command('makemigrations')
        call_command('migrate')
        
        # Create superuser if it doesn't exist
        logger.info("Creating superuser if needed...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            logger.info("Creating default superuser...")
            User.objects.create_superuser(
                username='admin',
                email='admin@publicbridge.com',
                password='admin123'
            )
            logger.info("Default superuser created (username: admin, password: admin123)")
        
        logger.info("Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

def verify_database():
    """Verify database integrity and functionality"""
    logger.info("Verifying database integrity...")
    
    try:
        # Check if all required tables exist
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            required_tables = [
                'auth_user', 'users_user', 'django_session',
                'django_admin_log', 'django_content_type',
                'django_migrations', 'django_site'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False
            else:
                logger.info("All required tables found.")
                
        # Test basic CRUD operations
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Test user creation
        test_user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test user retrieval
        retrieved_user = User.objects.get(username='test_user')
        
        if retrieved_user.email == 'test@example.com':
            logger.info("Database CRUD operations working correctly.")
            
            # Clean up test data
            test_user.delete()
            
            return True
        else:
            logger.error("Database CRUD operations failed.")
            return False
            
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

def main():
    """Main migration process"""
    logger.info("=== SQLite Database Migration Tool ===")
    
    try:
        # Setup Django
        setup_django()
        
        # Test SQLite connection
        if not check_sqlite_connection():
            logger.error("SQLite connection test failed.")
            sys.exit(1)
        
        # Perform migration
        if not migrate_database():
            logger.error("Database migration failed.")
            sys.exit(1)
        
        # Verify database
        if not verify_database():
            logger.error("Database verification failed.")
            sys.exit(1)
        
        logger.info("=== Migration completed successfully! ===")
        logger.info("You can now run the development server with: python manage.py runserver")
        
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()