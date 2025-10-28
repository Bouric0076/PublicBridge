from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from .models import Report
from .tasks import process_ai_analysis, check_ai_gateway_health, process_batch_ai_analysis

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_ai_analysis(request, report_id):
    """
    Trigger AI analysis for a specific report.
    
    POST /api/reports/{report_id}/ai-analyze/
    
    Returns:
        202 Accepted: Analysis queued successfully
        400 Bad Request: Report already being processed
        404 Not Found: Report not found
    """
    try:
        report = get_object_or_404(Report, id=report_id)
        
        # Check if analysis is already in progress
        if report.ai_analysis_status == 'processing':
            return Response(
                {"error": "AI analysis already in progress for this report"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if analysis is already completed
        if report.ai_analysis_status == 'completed':
            return Response(
                {
                    "message": "AI analysis already completed",
                    "results": report.get_ai_analysis_results()
                },
                status=status.HTTP_200_OK
            )
        
        # Trigger AI analysis
        report.analyze_with_ai_gateway()
        
        return Response(
            {
                "message": "AI analysis queued successfully",
                "report_id": report_id,
                "status": "processing"
            },
            status=status.HTTP_202_ACCEPTED
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger AI analysis for report {report_id}: {e}")
        return Response(
            {"error": "Failed to queue AI analysis"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_analysis_results(request, report_id):
    """
    Get AI analysis results for a specific report.
    
    GET /api/reports/{report_id}/ai-results/
    
    Returns:
        200 OK: Analysis results
        202 Accepted: Analysis still in progress
        404 Not Found: Report not found
    """
    try:
        report = get_object_or_404(Report, id=report_id)
        
        if report.ai_analysis_status == 'processing':
            return Response(
                {
                    "message": "AI analysis in progress",
                    "status": "processing"
                },
                status=status.HTTP_202_ACCEPTED
            )
        
        elif report.ai_analysis_status == 'completed':
            results = report.get_ai_analysis_results()
            if results:
                return Response(
                    {
                        "report_id": report_id,
                        "status": "completed",
                        "results": results,
                        "analysis_completed_at": report.updated_at.isoformat()
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "No AI analysis results available"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif report.ai_analysis_status == 'failed':
            return Response(
                {
                    "status": "failed",
                    "error": report.ai_analysis_error or "AI analysis failed"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        else:  # pending
            return Response(
                {
                    "message": "AI analysis not started",
                    "status": "pending"
                },
                status=status.HTTP_200_OK
            )
        
    except Exception as e:
        logger.error(f"Failed to get AI analysis results for report {report_id}: {e}")
        return Response(
            {"error": "Failed to retrieve AI analysis results"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_batch_ai_analysis(request):
    """
    Trigger AI analysis for multiple reports.
    
    POST /api/reports/ai-analyze-batch/
    
    Request body:
        {
            "report_ids": [1, 2, 3, ...]
        }
    
    Returns:
        202 Accepted: Batch analysis queued successfully
        400 Bad Request: Invalid request data
    """
    try:
        report_ids = request.data.get('report_ids', [])
        
        if not report_ids:
            return Response(
                {"error": "No report IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(report_ids, list):
            return Response(
                {"error": "report_ids must be a list"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate report IDs exist
        valid_report_ids = []
        invalid_report_ids = []
        
        for report_id in report_ids:
            try:
                report = Report.objects.get(id=report_id)
                # Only queue reports that aren't currently being processed
                if report.ai_analysis_status != 'processing':
                    valid_report_ids.append(report_id)
                else:
                    invalid_report_ids.append(report_id)
            except Report.DoesNotExist:
                invalid_report_ids.append(report_id)
        
        if not valid_report_ids:
            return Response(
                {
                    "error": "No valid report IDs found",
                    "invalid_report_ids": invalid_report_ids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Queue batch analysis
        process_batch_ai_analysis.delay(valid_report_ids)
        
        return Response(
            {
                "message": "Batch AI analysis queued successfully",
                "queued_report_ids": valid_report_ids,
                "skipped_report_ids": invalid_report_ids,
                "total_queued": len(valid_report_ids)
            },
            status=status.HTTP_202_ACCEPTED
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger batch AI analysis: {e}")
        return Response(
            {"error": "Failed to queue batch AI analysis"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_gateway_health(request):
    """
    Check AI Gateway health status.
    
    GET /api/ai-gateway/health/
    
    Returns:
        200 OK: Health status
        503 Service Unavailable: AI Gateway unavailable
    """
    try:
        # Check AI Gateway health asynchronously
        result = check_ai_gateway_health.delay().get(timeout=10)
        
        if result.get("success"):
            return Response(
                {
                    "status": "healthy",
                    "ai_gateway_status": result.get("status"),
                    "model_status": result.get("model_status", {}),
                    "checked_at": timezone.now().isoformat()
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "status": "unhealthy",
                    "error": result.get("error", "Unknown error"),
                    "checked_at": timezone.now().isoformat()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
    except Exception as e:
        logger.error(f"Failed to check AI Gateway health: {e}")
        return Response(
            {
                "status": "error",
                "error": "Failed to check AI Gateway health",
                "details": str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reports_needing_ai_analysis(request):
    """
    Get reports that need AI analysis.
    
    GET /api/reports/ai-pending/
    
    Query parameters:
        limit: Maximum number of reports to return (default: 50)
        
    Returns:
        200 OK: List of reports needing AI analysis
    """
    try:
        limit = int(request.query_params.get('limit', 50))
        
        # Get reports that need AI analysis
        pending_reports = Report.objects.filter(
            models.Q(sentiment__isnull=True) | 
            models.Q(nlp_category__isnull=True) |
            models.Q(ai_analysis_status='pending')
        ).order_by('-created_at')[:limit]
        
        reports_data = []
        for report in pending_reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'category': report.category,
                'status': report.status,
                'created_at': report.created_at.isoformat(),
                'ai_analysis_status': report.ai_analysis_status,
                'has_sentiment': report.sentiment is not None,
                'has_nlp_category': report.nlp_category is not None
            })
        
        return Response(
            {
                'count': len(reports_data),
                'reports': reports_data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Failed to get reports needing AI analysis: {e}")
        return Response(
            {"error": "Failed to retrieve reports"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )