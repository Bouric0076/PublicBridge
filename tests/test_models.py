import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from reports.models import Report, ReportComment, AnonymousReport
from disaster_reporting.models import DisasterReport, DisasterAgency
import json
from datetime import datetime, timedelta

User = get_user_model()

class TestReportModel(TestCase):
    """Test cases for Report model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='citizen'
        )
        self.report = Report.objects.create(
            user_contact=self.user,
            title='Test Report',
            description='This is a test report',
            urgency='medium',
            email='test@example.com',
            category='infrastructure',
            priority='medium',
            status='pending'
        )
    
    def test_report_creation(self):
        """Test report creation with valid data."""
        self.assertEqual(self.report.title, 'Test Report')
        self.assertEqual(self.report.status, 'pending')
        self.assertIsNotNone(self.report.created_at)
    
    def test_report_status_update(self):
        """Test report status update functionality."""
        old_status = self.report.status
        self.report.update_status('in_progress', self.user)
        self.assertEqual(self.report.status, 'in_progress')
        self.assertIn(old_status, self.report.status_history)
    
    def test_report_string_representation(self):
        """Test report string representation."""
        expected = f"{self.report.title} - {self.report.status}"
        self.assertEqual(str(self.report), expected)

class TestDisasterReportModel(TestCase):
    """Test cases for DisasterReport model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='citizen'
        )
        self.agency = DisasterAgency.objects.create(
            name='Test Fire Department',
            category='fire_department',
            contact_email='fire@test.com',
            phone_number='1234567890',
            latitude=40.7128,
            longitude=-74.0060,
            is_active=True
        )
        self.disaster_report = DisasterReport.objects.create(
            user=self.user,
            category='fire',
            description='Fire emergency test',
            latitude=40.7128,
            longitude=-74.0060,
            status='pending'
        )
    
    def test_disaster_report_creation(self):
        """Test disaster report creation."""
        self.assertEqual(self.disaster_report.category, 'fire')
        self.assertEqual(self.disaster_report.status, 'pending')
        self.assertIsNotNone(self.disaster_report.address)
    
    def test_nearest_agency_assignment(self):
        """Test automatic assignment of nearest agency."""
        self.assertEqual(self.disaster_report.assigned_agency, self.agency)
    
    def test_haversine_distance_calculation(self):
        """Test distance calculation between coordinates."""
        distance = self.disaster_report.haversine_distance(
            40.7128, -74.0060, 40.7589, -73.9851
        )
        self.assertGreater(distance, 0)

class TestAPIEndpoints(TestCase):
    """Test cases for API endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='citizen'
        )
        self.report = Report.objects.create(
            user_contact=self.user,
            title='Test API Report',
            description='API test report',
            urgency='high',
            email='test@example.com',
            category='safety',
            priority='high',
            status='pending'
        )
    
    def test_report_list_api(self):
        """Test report list API endpoint."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, 200)
    
    def test_report_detail_api(self):
        """Test report detail API endpoint."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/api/reports/{self.report.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.report.title)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints."""
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, 403)

class TestUserAuthentication(TestCase):
    """Test cases for user authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'citizen'
        }
    
    def test_user_registration(self):
        """Test user registration process."""
        response = self.client.post('/users/register/', self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_user_login(self):
        """Test user login functionality."""
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/users/login/', login_data)
        self.assertEqual(response.status_code, 302)
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/users/login/', login_data)
        self.assertEqual(response.status_code, 200)  # Stays on login page

class TestReportFiltering(TestCase):
    """Test cases for report filtering and search."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='citizen'
        )
        # Create multiple reports with different statuses
        for i in range(5):
            Report.objects.create(
                user_contact=self.user,
                title=f'Test Report {i}',
                description=f'Description {i}',
                urgency='medium',
                email='test@example.com',
                category='infrastructure',
                priority='medium',
                status='pending' if i % 2 == 0 else 'resolved'
            )
    
    def test_filter_by_status(self):
        """Test filtering reports by status."""
        pending_reports = Report.objects.filter(status='pending')
        self.assertEqual(pending_reports.count(), 3)
        
        resolved_reports = Report.objects.filter(status='resolved')
        self.assertEqual(resolved_reports.count(), 2)
    
    def test_filter_by_category(self):
        """Test filtering reports by category."""
        infrastructure_reports = Report.objects.filter(category='infrastructure')
        self.assertEqual(infrastructure_reports.count(), 5)
    
    def test_search_by_title(self):
        """Test searching reports by title."""
        results = Report.objects.filter(title__icontains='Report 1')
        self.assertEqual(results.count(), 1)

class TestAnonymousReporting(TestCase):
    """Test cases for anonymous reporting."""
    
    def setUp(self):
        self.client = Client()
        self.anonymous_data = {
            'title': 'Anonymous Test Report',
            'category': 'safety',
            'description': 'This is an anonymous test report',
            'contact_info': 'anonymous@example.com'
        }
    
    def test_anonymous_report_creation(self):
        """Test creation of anonymous report."""
        response = self.client.post('/reports/anonymous/submit/', self.anonymous_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AnonymousReport.objects.filter(title='Anonymous Test Report').exists())
    
    def test_anonymous_report_review(self):
        """Test review process for anonymous reports."""
        anonymous_report = AnonymousReport.objects.create(**self.anonymous_data)
        self.assertEqual(anonymous_report.review_status, 'pending')
        
        # Simulate review
        anonymous_report.review_status = 'approved'
        anonymous_report.save()
        
        self.assertEqual(anonymous_report.review_status, 'approved')

@pytest.mark.django_db
class TestPerformance(TestCase):
    """Performance tests for critical operations."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='citizen'
        )
    
    def test_report_creation_performance(self):
        """Test report creation performance."""
        start_time = datetime.now()
        
        for i in range(100):
            Report.objects.create(
                user_contact=self.user,
                title=f'Performance Test {i}',
                description=f'Description {i}',
                urgency='medium',
                email='test@example.com',
                category='infrastructure',
                priority='medium',
                status='pending'
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should create 100 reports in less than 10 seconds
        self.assertLess(duration, 10.0)
    
    def test_report_query_performance(self):
        """Test report query performance."""
        # Create test data
        for i in range(1000):
            Report.objects.create(
                user_contact=self.user,
                title=f'Query Test {i}',
                description=f'Description {i}',
                urgency='medium',
                email='test@example.com',
                category='infrastructure',
                priority='medium',
                status='pending'
            )
        
        start_time = datetime.now()
        reports = Report.objects.filter(status='pending')[:50]
        list(reports)  # Force evaluation
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Should query 50 reports in less than 0.1 seconds
        self.assertLess(duration, 0.1)