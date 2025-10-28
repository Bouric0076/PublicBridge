import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings_secure')

import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

# Import models
from reports.models import Report, ReportComment, AnonymousReport
from disaster_reporting.models import DisasterReport, DisasterAgency
from users.models import User

# Import utilities
from utils.error_handlers import ErrorHandler
from utils.nlp_utils import analyze_text

# Test Configuration
pytestmark = pytest.mark.django_db

class TestReportModel(TestCase):
    """Test cases for Report model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.report_data = {
            'user': self.user,
            'title': 'Test Report',
            'description': 'This is a test report description',
            'category': 'Infrastructure',
            'urgency': 'high',
            'email': 'test@example.com'
        }
    
    def test_report_creation(self):
        """Test report creation with valid data."""
        report = Report.objects.create(**self.report_data)
        
        self.assertEqual(report.title, 'Test Report')
        self.assertEqual(report.category, 'Infrastructure')
        self.assertEqual(report.status, 'pending')
        self.assertIsNotNone(report.uuid)
        self.assertEqual(report.user, self.user)
    
    def test_report_nlp_analysis(self):
        """Test NLP analysis functionality."""
        report = Report.objects.create(**self.report_data)
        
        # Mock the NLP analysis
        with patch('utils.nlp_utils.analyze_text') as mock_analyze:
            mock_analyze.return_value = {
                'sentiment': 'positive',
                'keywords': ['test', 'report', 'infrastructure'],
                'category': 'Infrastructure',
                'urgency_score': 0.8
            }
            
            result = report.analyze_report()
            
            self.assertEqual(result['sentiment'], 'positive')
            self.assertIn('test', result['keywords'])
            self.assertEqual(result['category'], 'Infrastructure')
            self.assertEqual(result['urgency_score'], 0.8)
    
    def test_report_status_update(self):
        """Test report status update functionality."""
        report = Report.objects.create(**self.report_data)
        
        # Update status
        report.update_status('in_progress', 'Started working on the issue')
        
        self.assertEqual(report.status, 'in_progress')
        self.assertEqual(report.status_history[-1]['status'], 'in_progress')
        self.assertEqual(report.status_history[-1]['note'], 'Started working on the issue')
    
    def test_report_resolution(self):
        """Test report resolution functionality."""
        report = Report.objects.create(**self.report_data)
        
        report.resolve_report('Issue has been resolved successfully')
        
        self.assertEqual(report.status, 'resolved')
        self.assertEqual(report.status_history[-1]['status'], 'resolved')
        self.assertEqual(report.status_history[-1]['note'], 'Issue has been resolved successfully')
    
    def test_report_string_representation(self):
        """Test string representation of report."""
        report = Report.objects.create(**self.report_data)
        
        self.assertEqual(str(report), f'Test Report ({report.uuid})')

class TestAnonymousReportModel(TestCase):
    """Test cases for AnonymousReport model."""
    
    def setUp(self):
        self.anonymous_data = {
            'title': 'Anonymous Test Report',
            'description': 'This is an anonymous test report',
            'category': 'Safety',
            'urgency': 'medium',
            'email': 'anonymous@example.com'
        }
    
    def test_anonymous_report_creation(self):
        """Test anonymous report creation."""
        report = AnonymousReport.objects.create(**self.anonymous_data)
        
        self.assertEqual(report.title, 'Anonymous Test Report')
        self.assertEqual(report.category, 'Safety')
        self.assertEqual(report.status, 'pending')
        self.assertIsNotNone(report.uuid)
    
    def test_anonymous_report_email_handling(self):
        """Test email handling for anonymous reports."""
        report = AnonymousReport.objects.create(**self.anonymous_data)
        
        # Email should be stored but user should be None
        self.assertEqual(report.email, 'anonymous@example.com')

class TestDisasterReportModel(TestCase):
    """Test cases for DisasterReport model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='disasteruser',
            email='disaster@example.com',
            password='testpass123'
        )
        
        self.agency = DisasterAgency.objects.create(
            name='Test Emergency Services',
            category='Emergency',
            contact_email='emergency@test.com',
            phone_number='1234567890',
            latitude=40.7128,
            longitude=-74.0060,
            is_active=True
        )
        
        self.disaster_data = {
            'user': self.user,
            'category': 'Fire',
            'description': 'Fire emergency in downtown area',
            'latitude': 40.7130,
            'longitude': -74.0065,
            'address': '123 Main St, New York, NY',
            'assigned_agency': self.agency
        }
    
    def test_disaster_report_creation(self):
        """Test disaster report creation."""
        report = DisasterReport.objects.create(**self.disaster_data)
        
        self.assertEqual(report.category, 'Fire')
        self.assertEqual(report.status, 'pending')
        self.assertEqual(report.assigned_agency, self.agency)
        self.assertEqual(report.user, self.user)
    
    def test_disaster_report_auto_assignment(self):
        """Test automatic agency assignment."""
        # Create another agency closer to the report location
        closer_agency = DisasterAgency.objects.create(
            name='Closer Emergency Services',
            category='Emergency',
            contact_email='closer@test.com',
            phone_number='0987654321',
            latitude=40.7131,  # Closer to report location
            longitude=-74.0064,
            is_active=True
        )
        
        report = DisasterReport.objects.create(
            user=self.user,
            category='Fire',
            'description': 'Fire emergency',
            'latitude': 40.7130,
            'longitude': -74.0065
        )
        
        # Should be assigned to the closer agency
        self.assertEqual(report.assigned_agency, closer_agency)
    
    def test_disaster_report_archiving(self):
        """Test disaster report archiving."""
        report = DisasterReport.objects.create(**self.disaster_data)
        
        report.archive()
        
        self.assertTrue(report.is_archived)
        self.assertEqual(report.status, 'archived')
    
    def test_haversine_distance_calculation(self):
        """Test distance calculation between coordinates."""
        lat1, lon1 = 40.7128, -74.0060
        lat2, lon2 = 40.7130, -74.0065
        
        distance = DisasterReport.haversine_distance(lat1, lon1, lat2, lon2)
        
        # Distance should be positive and reasonable (in meters)
        self.assertGreater(distance, 0)
        self.assertLess(distance, 1000)  # Less than 1km
    
    def test_address_from_coordinates(self):
        """Test reverse geocoding."""
        # Mock the geocoding service
        with patch('geopy.geocoders.Nominatim.reverse') as mock_reverse:
            mock_reverse.return_value.address = '123 Test St, Test City, TS 12345'
            
            address = DisasterReport.get_address_from_coordinates(40.7128, -74.0060)
            
            self.assertEqual(address, '123 Test St, Test City, TS 12345')

class TestDisasterAgencyModel(TestCase):
    """Test cases for DisasterAgency model."""
    
    def setUp(self):
        self.agency_data = {
            'name': 'Test Emergency Services',
            'category': 'Emergency',
            'contact_email': 'emergency@test.com',
            'phone_number': '1234567890',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'is_active': True
        }
    
    def test_agency_creation(self):
        """Test disaster agency creation."""
        agency = DisasterAgency.objects.create(**self.agency_data)
        
        self.assertEqual(agency.name, 'Test Emergency Services')
        self.assertEqual(agency.category, 'Emergency')
        self.assertTrue(agency.is_active)
        self.assertIsNotNone(agency.last_seen)
    
    def test_agency_status_update(self):
        """Test agency status update."""
        agency = DisasterAgency.objects.create(**self.agency_data)
        
        agency.update_status(is_active=False)
        
        self.assertFalse(agency.is_active)
        self.assertIsNotNone(agency.last_seen)
    
    def test_agency_string_representation(self):
        """Test string representation of agency."""
        agency = DisasterAgency.objects.create(**self.agency_data)
        
        self.assertEqual(str(agency), 'Test Emergency Services')

class TestErrorHandling(TestCase):
    """Test cases for error handling utilities."""
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()
        
        self.assertIsNotNone(handler)
        self.assertTrue(hasattr(handler, 'log_error'))
        self.assertTrue(hasattr(handler, 'log_warning'))
        self.assertTrue(hasattr(handler, 'log_info'))
    
    def test_error_logging(self):
        """Test error logging functionality."""
        handler = ErrorHandler()
        
        # Test logging an error
        with patch('logging.error') as mock_log:
            handler.log_error("Test error", "test_module", {"context": "test"})
            mock_log.assert_called_once()
    
    def test_exception_decorator(self):
        """Test exception handling decorator."""
        from utils.error_handlers import handle_exceptions
        
        @handle_exceptions
        def failing_function():
            raise ValueError("Test error")
        
        # Should not raise exception, but log it
        result = failing_function()
        self.assertIsNone(result)  # Returns None on exception

class TestNLPUtils(TestCase):
    """Test cases for NLP utilities."""
    
    def test_analyze_text_basic(self):
        """Test basic text analysis."""
        text = "This is a test report about a pothole that needs immediate attention."
        
        result = analyze_text(text)
        
        self.assertIn('sentiment', result)
        self.assertIn('keywords', result)
        self.assertIn('category', result)
        self.assertIn('urgency_score', result)
        
        # Check data types
        self.assertIsInstance(result['sentiment'], str)
        self.assertIsInstance(result['keywords'], list)
        self.assertIsInstance(result['category'], str)
        self.assertIsInstance(result['urgency_score'], float)
    
    def test_analyze_text_empty(self):
        """Test text analysis with empty input."""
        result = analyze_text("")
        
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertEqual(result['keywords'], [])
        self.assertEqual(result['category'], 'Other')
        self.assertEqual(result['urgency_score'], 0.5)
    
    def test_analyze_text_urgency_detection(self):
        """Test urgency detection in text."""
        urgent_text = "URGENT! Medical emergency! Someone needs immediate help!"
        
        result = analyze_text(urgent_text)
        
        # Should detect high urgency
        self.assertGreater(result['urgency_score'], 0.7)
    
    def test_analyze_text_category_detection(self):
        """Test category detection in text."""
        infrastructure_text = "There's a large pothole on Main Street that needs to be fixed."
        
        result = analyze_text(infrastructure_text)
        
        # Should detect infrastructure category
        self.assertEqual(result['category'], 'Infrastructure')

# API Tests
class TestAPIEndpoints(TestCase):
    """Test cases for API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass123'
        )
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        
        # This would require the actual registration endpoint URL
        # response = self.client.post('/api/auth/register/', registration_data)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_user_login(self):
        """Test user login endpoint."""
        login_data = {
            'username': 'apiuser',
            'password': 'testpass123'
        }
        
        # This would require the actual login endpoint URL
        # response = self.client.post('/api/auth/login/', login_data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertIn('token', response.data)
    
    def test_report_submission(self):
        """Test report submission endpoint."""
        report_data = {
            'title': 'API Test Report',
            'description': 'Testing API submission',
            'category': 'Infrastructure',
            'urgency': 'medium',
            'email': 'api@example.com'
        }
        
        # This would require the actual report submission endpoint URL
        # self.client.force_authenticate(user=self.user)
        # response = self.client.post('/api/reports/', report_data)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)

# Performance Tests
class TestPerformance(TestCase):
    """Performance test cases."""
    
    def test_report_creation_performance(self):
        """Test performance of creating multiple reports."""
        import time
        
        start_time = time.time()
        
        # Create 100 reports
        for i in range(100):
            Report.objects.create(
                title=f'Performance Test Report {i}',
                description=f'This is performance test report number {i}',
                category='Infrastructure',
                urgency='medium',
                email='perf@test.com'
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should create 100 reports in less than 5 seconds
        self.assertLess(execution_time, 5.0)
        
        print(f"Created 100 reports in {execution_time:.2f} seconds")
    
    def test_report_query_performance(self):
        """Test performance of querying reports."""
        import time
        
        # Create test data
        for i in range(50):
            Report.objects.create(
                title=f'Query Test Report {i}',
                description=f'Query test report {i}',
                category='Infrastructure',
                urgency='high',
                email='query@test.com'
            )
        
        start_time = time.time()
        
        # Query reports
        reports = Report.objects.filter(
            category='Infrastructure',
            urgency='high'
        ).order_by('-created_at')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should query reports in less than 0.1 seconds
        self.assertLess(execution_time, 0.1)
        
        self.assertEqual(reports.count(), 50)
        print(f"Queried reports in {execution_time:.4f} seconds")

# Security Tests
class TestSecurity(TestCase):
    """Security test cases."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='securityuser',
            email='security@example.com',
            password='testpass123'
        )
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE reports_report; --"
        
        # This should not cause any SQL injection
        report = Report.objects.create(
            title=malicious_input,
            description='Test description',
            category='Infrastructure',
            urgency='medium',
            email='safe@example.com'
        )
        
        # Verify report was created safely
        self.assertEqual(report.title, malicious_input)
        
        # Verify no tables were dropped
        self.assertTrue(Report.objects.filter(title=malicious_input).exists())
    
    def test_xss_prevention(self):
        """Test XSS prevention."""
        xss_input = '<script>alert("XSS")</script>'
        
        # This should be safely stored
        report = Report.objects.create(
            title='XSS Test',
            description=xss_input,
            category='Infrastructure',
            urgency='medium',
            email='xss@example.com'
        )
        
        # Verify report was created safely
        self.assertEqual(report.description, xss_input)
        
        # In a real application, this would be escaped in templates
        self.assertTrue(Report.objects.filter(description=xss_input).exists())
    
    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints."""
        # This would require actual protected endpoints
        # response = self.client.get('/protected/endpoint/')
        # self.assertEqual(response.status_code, 302)  # Redirect to login
        pass