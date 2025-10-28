import json
import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from reports.models import Report
from reports.tasks import (
    process_ai_analysis,
    process_batch_ai_analysis,
    cleanup_old_ai_analysis,
    check_ai_gateway_health,
    process_pending_ai_analysis
)


class AIIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.report = Report.objects.create(
            title="Test Report",
            description="This is a test report for AI analysis",
            location="Test Location",
            user=self.user,
            status='pending'
        )

    def test_ai_gateway_settings(self):
        """Test that AI Gateway settings are properly configured"""
        self.assertIsNotNone(settings.AI_GATEWAY_URL)
        self.assertIsNotNone(settings.AI_GATEWAY_TIMEOUT)
        self.assertIsNotNone(settings.AI_GATEWAY_MAX_RETRIES)
        self.assertIsNotNone(settings.AI_GATEWAY_RETRY_DELAY)
        
        self.assertEqual(settings.AI_GATEWAY_URL, 'http://localhost:8001')
        self.assertEqual(settings.AI_GATEWAY_TIMEOUT, 30)
        self.assertEqual(settings.AI_GATEWAY_MAX_RETRIES, 3)
        self.assertEqual(settings.AI_GATEWAY_RETRY_DELAY, 60)

    def test_report_model_ai_fields(self):
        """Test that Report model has AI Gateway integration fields"""
        # Test that all AI fields exist
        self.assertTrue(hasattr(self.report, 'ai_urgency_score'))
        self.assertTrue(hasattr(self.report, 'ai_confidence_scores'))
        self.assertTrue(hasattr(self.report, 'ai_explanation'))
        self.assertTrue(hasattr(self.report, 'ai_processing_time'))
        self.assertTrue(hasattr(self.report, 'ai_model_version'))
        self.assertTrue(hasattr(self.report, 'ai_analysis_status'))
        self.assertTrue(hasattr(self.report, 'ai_analysis_error'))

        # Test default values
        self.assertEqual(self.report.ai_urgency_score, 0.0)
        self.assertEqual(self.report.ai_confidence_scores, {})
        self.assertEqual(self.report.ai_explanation, "")
        self.assertEqual(self.report.ai_processing_time, 0.0)
        self.assertEqual(self.report.ai_model_version, "")
        self.assertEqual(self.report.ai_analysis_status, 'pending')
        self.assertEqual(self.report.ai_analysis_error, "")

    def test_analyze_with_ai_gateway_method(self):
        """Test the analyze_with_ai_gateway method"""
        with patch('reports.models.process_ai_analysis.delay') as mock_task:
            result = self.report.analyze_with_ai_gateway()
            
            mock_task.assert_called_once_with(self.report.id)
            self.assertEqual(result, {"status": "AI analysis triggered", "report_id": self.report.id})
            
            # Check that status was updated
            self.report.refresh_from_db()
            self.assertEqual(self.report.ai_analysis_status, 'processing')

    def test_get_ai_analysis_results_method(self):
        """Test the get_ai_analysis_results method"""
        # Test with completed analysis
        self.report.ai_analysis_status = 'completed'
        self.report.ai_urgency_score = 0.8
        self.report.ai_confidence_scores = {"sentiment": 0.9, "category": 0.85}
        self.report.ai_explanation = "High urgency due to safety concerns"
        self.report.save()
        
        results = self.report.get_ai_analysis_results()
        self.assertEqual(results["status"], "completed")
        self.assertEqual(results["urgency_score"], 0.8)
        self.assertEqual(results["confidence_scores"]["sentiment"], 0.9)
        self.assertEqual(results["explanation"], "High urgency due to safety concerns")
        
        # Test with pending analysis
        self.report.ai_analysis_status = 'pending'
        self.report.save()
        
        results = self.report.get_ai_analysis_results()
        self.assertEqual(results["status"], "pending")
        self.assertIsNone(results.get("urgency_score"))

    @patch('requests.post')
    def test_process_ai_analysis_success(self, mock_post):
        """Test successful AI analysis processing"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sentiment_score": 0.8,
            "urgency_score": 0.9,
            "category_prediction": "safety",
            "confidence_scores": {
                "sentiment": 0.85,
                "urgency": 0.92,
                "category": 0.88
            },
            "explanation": "High urgency due to safety concerns",
            "processing_time": 1.5,
            "model_version": "distilbert-base-uncased-finetuned-sst-2-english"
        }
        mock_post.return_value = mock_response
        
        result = process_ai_analysis(self.report.id)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["report_id"], self.report.id)
        
        # Check that report was updated
        self.report.refresh_from_db()
        self.assertEqual(self.report.ai_analysis_status, 'completed')
        self.assertEqual(self.report.ai_urgency_score, 0.9)
        self.assertEqual(self.report.ai_confidence_scores["sentiment"], 0.85)
        self.assertEqual(self.report.ai_explanation, "High urgency due to safety concerns")
        self.assertEqual(self.report.ai_processing_time, 1.5)
        self.assertEqual(self.report.ai_model_version, "distilbert-base-uncased-finetuned-sst-2-english")

    @patch('requests.post')
    def test_process_ai_analysis_failure(self, mock_post):
        """Test AI analysis processing failure"""
        # Mock failed response
        mock_post.side_effect = Exception("Connection error")
        
        result = process_ai_analysis(self.report.id)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("AI Gateway request failed", result["error"])
        
        # Check that report was updated with error
        self.report.refresh_from_db()
        self.assertEqual(self.report.ai_analysis_status, 'failed')
        self.assertIn("Connection error", self.report.ai_analysis_error)

    @patch('requests.post')
    def test_process_batch_ai_analysis(self, mock_post):
        """Test batch AI analysis processing"""
        # Create multiple reports
        reports = []
        for i in range(3):
            report = Report.objects.create(
                title=f"Test Report {i}",
                description=f"Test report {i} for batch analysis",
                location="Test Location",
                user=self.user,
                status='pending'
            )
            reports.append(report.id)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "report_id": reports[0],
                    "sentiment_score": 0.8,
                    "urgency_score": 0.9,
                    "category_prediction": "safety"
                },
                {
                    "report_id": reports[1],
                    "sentiment_score": 0.6,
                    "urgency_score": 0.7,
                    "category_prediction": "infrastructure"
                },
                {
                    "report_id": reports[2],
                    "sentiment_score": 0.9,
                    "urgency_score": 0.8,
                    "category_prediction": "health"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        result = process_batch_ai_analysis(reports)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed_count"], 3)
        
        # Check that all reports were updated
        for report_id in reports:
            report = Report.objects.get(id=report_id)
            self.assertEqual(report.ai_analysis_status, 'completed')

    @patch('requests.get')
    def test_check_ai_gateway_health(self, mock_get):
        """Test AI Gateway health check"""
        # Mock healthy response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "models_loaded": 3,
            "models": ["sentiment", "category", "urgency"]
        }
        mock_get.return_value = mock_response
        
        result = check_ai_gateway_health()
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["models_loaded"], 3)
        
        # Test unhealthy response
        mock_get.side_effect = Exception("Connection error")
        
        result = check_ai_gateway_health()
        self.assertEqual(result["status"], "error")
        self.assertIn("Health check failed", result["error"])

    def test_cleanup_old_ai_analysis(self):
        """Test cleanup of old AI analysis data"""
        # Create old reports with AI analysis
        old_report = Report.objects.create(
            title="Old Report",
            description="Old report for cleanup",
            location="Test Location",
            user=self.user,
            status='resolved',
            ai_analysis_status='completed',
            ai_urgency_score=0.8,
            ai_explanation="Old analysis"
        )
        old_report.created_at = timezone.now() - timedelta(days=35)
        old_report.save()
        
        # Create recent report
        recent_report = Report.objects.create(
            title="Recent Report",
            description="Recent report",
            location="Test Location",
            user=self.user,
            status='pending',
            ai_analysis_status='completed',
            ai_urgency_score=0.7,
            ai_explanation="Recent analysis"
        )
        
        result = cleanup_old_ai_analysis()
        
        self.assertEqual(result["cleaned_count"], 1)
        
        # Check that old report was cleaned
        old_report.refresh_from_db()
        self.assertEqual(old_report.ai_analysis_status, 'pending')
        self.assertEqual(old_report.ai_urgency_score, 0.0)
        self.assertEqual(old_report.ai_explanation, "")
        
        # Check that recent report was not cleaned
        recent_report.refresh_from_db()
        self.assertEqual(recent_report.ai_analysis_status, 'completed')
        self.assertEqual(recent_report.ai_urgency_score, 0.7)

    def test_process_pending_ai_analysis(self):
        """Test processing of pending AI analysis"""
        # Create multiple reports with different statuses
        pending_reports = []
        for i in range(3):
            report = Report.objects.create(
                title=f"Pending Report {i}",
                description=f"Pending report {i}",
                location="Test Location",
                user=self.user,
                status='pending',
                ai_analysis_status='pending'
            )
            pending_reports.append(report.id)
        
        # Create reports with other statuses
        Report.objects.create(
            title="Completed Report",
            description="Completed report",
            location="Test Location",
            user=self.user,
            status='pending',
            ai_analysis_status='completed'
        )
        
        with patch('reports.tasks.process_ai_analysis.delay') as mock_task:
            result = process_pending_ai_analysis()
            
            self.assertEqual(result["pending_count"], 3)
            self.assertEqual(result["triggered_count"], 3)
            self.assertEqual(mock_task.call_count, 3)


class AIViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.report = Report.objects.create(
            title="Test Report",
            description="This is a test report for AI analysis",
            location="Test Location",
            user=self.user,
            status='pending'
        )
        self.client.login(username='testuser', password='testpass123')

    @patch('reports.models.process_ai_analysis.delay')
    def test_trigger_ai_analysis_view(self, mock_task):
        """Test trigger AI analysis API endpoint"""
        url = reverse('trigger-ai-analysis', kwargs={'report_id': self.report.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "AI analysis triggered")
        mock_task.assert_called_once_with(self.report.id)

    def test_get_ai_analysis_results_view(self):
        """Test get AI analysis results API endpoint"""
        # Set up completed analysis
        self.report.ai_analysis_status = 'completed'
        self.report.ai_urgency_score = 0.8
        self.report.ai_confidence_scores = {"sentiment": 0.9}
        self.report.ai_explanation = "Test explanation"
        self.report.save()
        
        url = reverse('get-ai-analysis-results', kwargs={'report_id': self.report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["urgency_score"], 0.8)

    @patch('reports.tasks.process_batch_ai_analysis.delay')
    def test_trigger_batch_ai_analysis_view(self, mock_task):
        """Test trigger batch AI analysis API endpoint"""
        report_ids = [self.report.id]
        url = reverse('trigger-batch-ai-analysis')
        response = self.client.post(url, 
                                  data=json.dumps({'report_ids': report_ids}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "Batch AI analysis triggered")
        mock_task.assert_called_once_with(report_ids)

    @patch('requests.get')
    def test_ai_gateway_health_view(self, mock_get):
        """Test AI Gateway health API endpoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response
        
        url = reverse('ai-gateway-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_get_reports_needing_ai_analysis_view(self):
        """Test get reports needing AI analysis API endpoint"""
        # Create pending report
        pending_report = Report.objects.create(
            title="Pending Report",
            description="Pending report",
            location="Test Location",
            user=self.user,
            status='pending',
            ai_analysis_status='pending'
        )
        
        url = reverse('get-reports-needing-ai-analysis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["reports"]), 1)
        self.assertEqual(data["reports"][0]["id"], pending_report.id)