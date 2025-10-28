import pytest
import asyncio
import httpx
from typing import Dict, Any
import json

# AI Gateway API Tests
class TestAIGatewayAPI:
    """Test cases for AI Gateway API."""
    
    @pytest.fixture
    def ai_gateway_base_url(self):
        return "http://localhost:8001"
    
    @pytest.fixture
    def sample_report_data(self):
        return {
            "report": {
                "title": "Pothole on Main Street",
                "description": "Large pothole causing traffic issues and potential damage to vehicles. Needs immediate attention.",
                "category": "Infrastructure",
                "location": "Main Street and 5th Avenue",
                "urgency": "high"
            },
            "analysis_types": ["sentiment", "urgency", "category"],
            "include_explanation": True
        }
    
    @pytest.mark.asyncio
    async def test_health_check(self, ai_gateway_base_url):
        """Test AI Gateway health check endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ai_gateway_base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "model_status" in data
    
    @pytest.mark.asyncio
    async def test_analyze_report(self, ai_gateway_base_url, sample_report_data):
        """Test report analysis endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=sample_report_data
            )
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "report_id" in data
            assert "sentiment_score" in data
            assert "urgency_score" in data
            assert "category_prediction" in data
            assert "confidence_scores" in data
            assert "processing_time" in data
            assert "model_version" in data
            
            # Check score ranges
            assert 0 <= data["sentiment_score"] <= 1
            assert 0 <= data["urgency_score"] <= 1
            assert data["category_prediction"] in [
                "Infrastructure", "Safety", "Environmental", "Health",
                "Transportation", "Utilities", "Public Services", "Other"
            ]
    
    @pytest.mark.asyncio
    async def test_batch_analysis(self, ai_gateway_base_url):
        """Test batch analysis endpoint."""
        batch_data = {
            "reports": [
                {
                    "title": "Pothole Issue",
                    "description": "Large pothole on main street",
                    "category": "Infrastructure"
                },
                {
                    "title": "Medical Emergency",
                    "description": "Someone needs immediate medical attention",
                    "category": "Health"
                }
            ],
            "analysis_types": ["sentiment", "urgency", "category"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze/batch",
                json=batch_data
            )
            assert response.status_code == 200
            data = response.json()
            
            assert "results" in data
            assert len(data["results"]) == 2
            assert data["total_processed"] == 2
    
    @pytest.mark.asyncio
    async def test_model_info(self, ai_gateway_base_url):
        """Test model information endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ai_gateway_base_url}/models")
            assert response.status_code == 200
            data = response.json()
            
            assert "models" in data
            assert "device" in data
            assert "model_versions" in data
            assert "sentiment" in data["model_versions"]
            assert "category" in data["model_versions"]
            assert "urgency" in data["model_versions"]
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, ai_gateway_base_url):
        """Test Prometheus metrics endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ai_gateway_base_url}/metrics")
            assert response.status_code == 200
            assert "ai_gateway_requests_total" in response.text
            assert "ai_gateway_request_duration_seconds" in response.text
    
    @pytest.mark.asyncio
    async def test_invalid_request(self, ai_gateway_base_url):
        """Test handling of invalid requests."""
        invalid_data = {
            "report": {
                "title": "",  # Empty title should be invalid
                "description": "Test description"
            },
            "analysis_types": ["sentiment"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=invalid_data
            )
            assert response.status_code == 422  # Validation error

# Integration Tests
class TestSystemIntegration:
    """Integration tests for the complete system."""
    
    @pytest.fixture
    def django_base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture
    def ai_gateway_base_url(self):
        return "http://localhost:8001"
    
    @pytest.mark.asyncio
    async def test_end_to_end_report_flow(self, django_base_url, ai_gateway_base_url):
        """Test complete report submission and AI analysis flow."""
        # This test would require a full system setup
        # Including Django API endpoints for report submission
        
        # Step 1: Submit report to Django
        report_data = {
            "title": "Test Integration Report",
            "description": "Testing end-to-end flow",
            "category": "Infrastructure",
            "urgency": "medium",
            "email": "test@example.com"
        }
        
        # Step 2: Trigger AI analysis
        ai_request_data = {
            "report": report_data,
            "analysis_types": ["sentiment", "urgency", "category"]
        }
        
        async with httpx.AsyncClient() as client:
            # Analyze with AI Gateway
            ai_response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=ai_request_data
            )
            assert ai_response.status_code == 200
            
            ai_data = ai_response.json()
            assert ai_data["sentiment_score"] is not None
            assert ai_data["urgency_score"] is not None
            assert ai_data["category_prediction"] is not None
    
    @pytest.mark.asyncio
    async def test_health_checks(self, django_base_url, ai_gateway_base_url):
        """Test health checks for all services."""
        async with httpx.AsyncClient() as client:
            # Test AI Gateway health
            ai_health = await client.get(f"{ai_gateway_base_url}/health")
            assert ai_health.status_code == 200
            
            # Test Django health (if implemented)
            # django_health = await client.get(f"{django_base_url}/health/")
            # assert django_health.status_code == 200

# Performance Tests
class TestPerformance:
    """Performance tests for AI Gateway."""
    
    @pytest.fixture
    def ai_gateway_base_url(self):
        return "http://localhost:8001"
    
    @pytest.fixture
    def sample_reports_batch(self):
        return {
            "reports": [
                {
                    "title": f"Test Report {i}",
                    "description": f"This is test report number {i} with some description content for analysis.",
                    "category": "Infrastructure"
                }
                for i in range(50)  # Batch of 50 reports
            ],
            "analysis_types": ["sentiment", "urgency", "category"]
        }
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, ai_gateway_base_url, sample_reports_batch):
        """Test batch processing performance."""
        import time
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze/batch",
                json=sample_reports_batch
            )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Should process 50 reports in less than 30 seconds
        assert processing_time < 30.0
        assert data["total_processed"] == 50
        
        print(f"Processed 50 reports in {processing_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, ai_gateway_base_url):
        """Test handling of concurrent requests."""
        sample_data = {
            "report": {
                "title": "Concurrent Test Report",
                "description": "Testing concurrent request handling",
                "category": "Infrastructure"
            },
            "analysis_types": ["sentiment"]
        }
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                return await client.post(
                    f"{ai_gateway_base_url}/analyze",
                    json=sample_data
                )
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "sentiment_score" in data

# Error Handling Tests
class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    @pytest.fixture
    def ai_gateway_base_url(self):
        return "http://localhost:8001"
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, ai_gateway_base_url):
        """Test handling of empty text inputs."""
        empty_data = {
            "report": {
                "title": "",
                "description": "",
                "category": "Infrastructure"
            },
            "analysis_types": ["sentiment", "urgency", "category"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=empty_data
            )
            
            # Should handle gracefully with default values
            assert response.status_code == 200
            data = response.json()
            assert data["sentiment_score"] == 0.5  # Neutral
            assert data["urgency_score"] == 0.3  # Medium urgency
    
    @pytest.mark.asyncio
    async def test_very_long_text_handling(self, ai_gateway_base_url):
        """Test handling of very long text inputs."""
        long_description = "This is a very long description. " * 1000  # Very long text
        
        long_data = {
            "report": {
                "title": "Long Text Test",
                "description": long_description,
                "category": "Infrastructure"
            },
            "analysis_types": ["sentiment", "urgency", "category"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=long_data
            )
            
            # Should handle long text gracefully
            assert response.status_code == 200
            data = response.json()
            assert "sentiment_score" in data
            assert "urgency_score" in data
    
    @pytest.mark.asyncio
    async def test_special_characters_handling(self, ai_gateway_base_url):
        """Test handling of special characters and unicode."""
        special_data = {
            "report": {
                "title": "Special Chars: àáâãäåæçèéêë 🚗 🚑",
                "description": "Unicode test: 你好世界 🌍 ñáéíóú",
                "category": "Infrastructure"
            },
            "analysis_types": ["sentiment"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_gateway_base_url}/analyze",
                json=special_data
            )
            
            # Should handle unicode gracefully
            assert response.status_code == 200
            data = response.json()
            assert "sentiment_score" in data