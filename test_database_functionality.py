#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.contrib.sessions.models import Session
from django.contrib.admin.models import LogEntry

def test_database_tables():
    """Test that all expected database tables exist and are accessible."""
    print("Testing database functionality...")
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✓ Database connected successfully")
            print(f"✓ Found {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        # Test Django ORM functionality
        print("\nTesting Django ORM...")
        
        # Test user model
        user_count = User.objects.count()
        print(f"✓ User model accessible - {user_count} users")
        
        # Test content types
        content_type_count = ContentType.objects.count()
        print(f"✓ ContentType model accessible - {content_type_count} content types")
        
        # Test permissions
        permission_count = Permission.objects.count()
        print(f"✓ Permission model accessible - {permission_count} permissions")
        
        # Test sessions
        session_count = Session.objects.count()
        print(f"✓ Session model accessible - {session_count} sessions")
        
        # Test admin logs
        log_count = LogEntry.objects.count()
        print(f"✓ LogEntry model accessible - {log_count} admin logs")
        
        # Test creating a superuser (if none exists)
        if user_count == 0:
            print("\nCreating test superuser...")
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print("✓ Test superuser created (admin/admin123)")
        
        print("\n✅ All database functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database functionality test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_tables()
    sys.exit(0 if success else 1)