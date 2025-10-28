import requests
import logging
from typing import Dict, Any, Optional
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Report

logger = logging.getLogger(__name__)

# AI Gateway Configuration
AI_GATEWAY_URL = settings.AI_GATEWAY_URL
AI_GATEWAY_TIMEOUT = settings.AI_GATEWAY_TIMEOUT
AI_GATEWAY_MAX_RETRIES = settings.AI_GATEWAY_MAX_RETRIES
AI_GATEWAY_RETRY_DELAY = settings.AI_GATEWAY_RETRY_DELAY


@shared_task(bind=True, max_retries=AI_GATEWAY_MAX_RETRIES, default_retry_delay=AI_GATEWAY_RETRY_DELAY)
def process_ai_analysis(self, report_id: int) -> Dict[str, Any]:
    """
    Process AI analysis for a report using the AI Gateway.
    
    Args:
        report_id: ID of the report to analyze
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Get the report
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            logger.error(f"Report {report_id} not found")
            return {"error": "Report not found"}
        
        # Prepare request data
        report_data = {
            "title": report.title,
            "description": report.description,
            "category": report.category,
            "location": getattr(report, 'location', None),
            "urgency": str(report.urgency) if hasattr(report, 'urgency') else None
        }
        
        request_data = {
            "report": report_data,
            "analysis_types": ["sentiment", "urgency", "category"],
            "include_explanation": True
        }
        
        # Make request to AI Gateway
        response = requests.post(
            f"{AI_GATEWAY_URL}/analyze",
            json=request_data,
            timeout=AI_GATEWAY_TIMEOUT
        )
        
        if response.status_code != 200:
            logger.error(f"AI Gateway returned status {response.status_code}: {response.text}")
            raise Exception(f"AI Gateway error: {response.status_code}")
        
        analysis_result = response.json()
        
        # Update report with AI analysis results
        report.sentiment = analysis_result.get('sentiment_score', 0.5)
        report.nlp_category = analysis_result.get('category_prediction', report.category)
        
        # Store additional AI fields if they exist in the model
        if hasattr(report, 'ai_urgency_score'):
            report.ai_urgency_score = analysis_result.get('urgency_score', 0.5)
        
        if hasattr(report, 'ai_confidence_scores'):
            report.ai_confidence_scores = analysis_result.get('confidence_scores', {})
        
        if hasattr(report, 'ai_explanation'):
            report.ai_explanation = analysis_result.get('explanation', '')
        
        if hasattr(report, 'ai_processing_time'):
            report.ai_processing_time = analysis_result.get('processing_time', 0)
        
        if hasattr(report, 'ai_model_version'):
            report.ai_model_version = analysis_result.get('model_version', '1.0.0')
        
        report.save()
        
        logger.info(f"AI analysis completed for report {report_id}")
        return {
            "success": True,
            "report_id": report_id,
            "analysis": analysis_result
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to AI Gateway failed: {e}")
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying AI analysis for report {report_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=AI_GATEWAY_RETRY_DELAY * (self.request.retries + 1))
        else:
            return {"error": f"AI Gateway request failed after {self.max_retries} retries", "details": str(e)}
    
    except Exception as e:
        logger.error(f"AI analysis failed for report {report_id}: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying AI analysis for report {report_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=AI_GATEWAY_RETRY_DELAY * (self.request.retries + 1))
        else:
            return {"error": f"AI analysis failed after {self.max_retries} retries", "details": str(e)}


@shared_task
def process_batch_ai_analysis(report_ids: list) -> Dict[str, Any]:
    """
    Process AI analysis for multiple reports in batch.
    
    Args:
        report_ids: List of report IDs to analyze
        
    Returns:
        Dict containing batch processing results
    """
    results = []
    successful = 0
    failed = 0
    
    for report_id in report_ids:
        try:
            result = process_ai_analysis.delay(report_id).get()
            if result.get("success"):
                successful += 1
            else:
                failed += 1
            results.append({
                "report_id": report_id,
                "result": result
            })
        except Exception as e:
            logger.error(f"Batch processing failed for report {report_id}: {e}")
            failed += 1
            results.append({
                "report_id": report_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_processed": len(report_ids),
        "successful": successful,
        "failed": failed,
        "results": results
    }


@shared_task
def cleanup_old_ai_analysis() -> Dict[str, Any]:
    """
    Clean up old AI analysis results that may be outdated.
    
    Returns:
        Dict containing cleanup results
    """
    try:
        # Get reports with AI analysis older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_reports = Report.objects.filter(
            updated_at__lt=cutoff_date,
            ai_model_version__isnull=False
        )
        
        cleaned_count = 0
        for report in old_reports:
            # Reset AI fields
            if hasattr(report, 'ai_urgency_score'):
                report.ai_urgency_score = None
            if hasattr(report, 'ai_confidence_scores'):
                report.ai_confidence_scores = None
            if hasattr(report, 'ai_explanation'):
                report.ai_explanation = None
            if hasattr(report, 'ai_processing_time'):
                report.ai_processing_time = None
            if hasattr(report, 'ai_model_version'):
                report.ai_model_version = None
            
            report.save()
            cleaned_count += 1
        
        logger.info(f"Cleaned up AI analysis for {cleaned_count} old reports")
        return {
            "success": True,
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def check_ai_gateway_health() -> Dict[str, Any]:
    """
    Check the health status of the AI Gateway.
    
    Returns:
        Dict containing health check results
    """
    try:
        response = requests.get(f"{AI_GATEWAY_URL}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"AI Gateway health check: {health_data.get('status', 'unknown')}")
            return {
                "success": True,
                "status": health_data.get('status', 'unknown'),
                "timestamp": health_data.get('timestamp'),
                "model_status": health_data.get('model_status', {})
            }
        else:
            logger.error(f"AI Gateway health check failed with status {response.status_code}")
            return {
                "success": False,
                "error": f"Health check returned status {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"AI Gateway health check failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task
def process_pending_ai_analysis() -> Dict[str, Any]:
    """
    Process reports that need AI analysis but haven't been processed yet.
    
    Returns:
        Dict containing processing results
    """
    try:
        # Get reports that need AI analysis
        # This could be reports without sentiment analysis or with outdated analysis
        pending_reports = Report.objects.filter(
            models.Q(sentiment__isnull=True) | 
            models.Q(nlp_category__isnull=True) |
            models.Q(ai_model_version__isnull=True)
        ).order_by('-created_at')[:50]  # Process up to 50 at a time
        
        report_ids = [report.id for report in pending_reports]
        
        if not report_ids:
            logger.info("No pending reports found for AI analysis")
            return {
                "success": True,
                "processed_count": 0,
                "message": "No pending reports found"
            }
        
        # Process in batch
        result = process_batch_ai_analysis.delay(report_ids).get()
        
        logger.info(f"Processed {result['total_processed']} pending reports for AI analysis")
        return result
        
    except Exception as e:
        logger.error(f"Failed to process pending AI analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }