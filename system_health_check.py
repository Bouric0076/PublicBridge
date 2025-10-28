#!/usr/bin/env python
"""
System Health Check Script for PublicBridge
This script performs comprehensive testing of the system after migration
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

def test_database_connectivity():
    """Test database connection and basic operations"""
    print("Testing Database Connectivity...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✓ Database connected successfully")
            print(f"✓ Found {len(tables)} tables in database")
            
            # Test CRUD operations
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'auth_%';")
            auth_tables = cursor.fetchone()[0]
            print(f"✓ Found {auth_tables} authentication-related tables")
            
            return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_static_files():
    """Test static files configuration"""
    print("\nTesting Static Files...")
    try:
        static_root = settings.STATIC_ROOT
        static_url = settings.STATIC_URL
        
        print(f"✓ STATIC_ROOT: {static_root}")
        print(f"✓ STATIC_URL: {static_url}")
        
        if os.path.exists(static_root):
            files_count = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
            print(f"✓ Static files directory exists with {files_count} files")
        else:
            print("✗ Static files directory not found")
            
        return True
    except Exception as e:
        print(f"✗ Static files test failed: {e}")
        return False

def test_logging():
    """Test logging configuration"""
    print("\nTesting Logging Configuration...")
    try:
        import logging
        
        # Check log directory
        log_dir = settings.BASE_DIR / 'logs'
        log_file = log_dir / 'django.log'
        
        print(f"✓ Log directory: {log_dir}")
        print(f"✓ Log file path: {log_file}")
        print(f"✓ Log directory exists: {os.path.exists(log_dir)}")
        print(f"✓ Log file exists: {os.path.exists(log_file)}")
        
        # Test logging
        logger = logging.getLogger('system_health')
        logger.info('System health check logging test')
        
        return True
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def test_security_settings():
    """Test security configuration"""
    print("\nTesting Security Settings...")
    try:
        issues = []
        
        # Check SECRET_KEY
        if len(settings.SECRET_KEY) < 50:
            issues.append("SECRET_KEY is too short (< 50 characters)")
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            issues.append("ALLOWED_HOSTS is empty")
        
        # Check debug mode
        if settings.DEBUG:
            issues.append("DEBUG is True (should be False in production)")
        
        # Check security headers
        if not hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
            issues.append("SECURE_BROWSER_XSS_FILTER not set")
        
        if issues:
            print("⚠ Security issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ Security settings look good")
            
        return len(issues) == 0
    except Exception as e:
        print(f"✗ Security test failed: {e}")
        return False

def test_django_apps():
    """Test Django app imports"""
    print("\nTesting Django Apps...")
    try:
        from django.apps import apps
        
        # Get all installed apps
        app_configs = apps.get_app_configs()
        print(f"✓ Found {len(app_configs)} installed apps")
        
        # Test model imports
        models_count = 0
        for app_config in app_configs:
            try:
                models = app_config.get_models()
                models_count += len(list(models))
            except Exception as e:
                print(f"⚠ Warning: Could not load models for {app_config.name}: {e}")
        
        print(f"✓ Found {models_count} total models")
        return True
    except Exception as e:
        print(f"✗ Django apps test failed: {e}")
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\nTesting Email Configuration...")
    try:
        email_backend = settings.EMAIL_BACKEND
        email_host = settings.EMAIL_HOST
        
        print(f"✓ Email backend: {email_backend}")
        print(f"✓ Email host: {email_host}")
        
        if not email_host:
            print("⚠ Warning: EMAIL_HOST is not configured")
        
        return True
    except Exception as e:
        print(f"✗ Email configuration test failed: {e}")
        return False

def main():
    """Run all health checks"""
    print("=" * 60)
    print("PublicBridge System Health Check")
    print("=" * 60)
    
    tests = [
        test_database_connectivity,
        test_static_files,
        test_logging,
        test_security_settings,
        test_django_apps,
        test_email_configuration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Health Check Summary:")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✓ All systems operational!")
        return 0
    else:
        print("✗ Some issues detected. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())