"""
AI-specific API endpoints for enhanced functionality.
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
import time

from .models import Report, ReportComment
from .ai_serializers import (
    AIReportSerializer, AIUserSerializer, AIPostSerializer,
    AIProcessingRequestSerializer, AIProcessingResponseSerializer,
    ChatbotRequestSerializer, ChatbotResponseSerializer,
    AdvancedAnalysisRequestSerializer, AdvancedAnalysisResponseSerializer
)
from users.models import User
from forum.models import Post
from reports.signals import batch_process_reports_with_ai, batch_analyze_users_with_ai
from ai_agents.orchestrator import MultiAgentOrchestrator
from ai_agents.groq_orchestrator import groq_orchestrator
from ai_agents.exception_handler import safe_ai_view_response
import logging
logger = logging.getLogger(__name__)

class AIReportListView(generics.ListAPIView):
    """List reports with AI insights."""
    
    serializer_class = AIReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reports based on AI insights."""
        queryset = Report.objects.all()
        
        # Filter by AI confidence score
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            queryset = queryset.filter(ai_confidence_score__gte=float(min_confidence))
        
        # Filter by hotspot prediction
        hotspot_only = self.request.query_params.get('hotspot_only')
        if hotspot_only and hotspot_only.lower() == 'true':
            queryset = queryset.filter(ai_hotspot_prediction=True)
        
        # Filter by AI processed status
        ai_processed = self.request.query_params.get('ai_processed')
        if ai_processed:
            if ai_processed.lower() == 'true':
                queryset = queryset.filter(ai_processed=True)
            else:
                queryset = queryset.filter(ai_processed=False)
        
        # Filter by predicted priority
        predicted_priority = self.request.query_params.get('predicted_priority')
        if predicted_priority:
            queryset = queryset.filter(ai_predicted_priority=predicted_priority)
        
        return queryset.order_by('-created_at')

class AIReportDetailView(generics.RetrieveAPIView):
    """Get detailed report with AI insights."""
    
    queryset = Report.objects.all()
    serializer_class = AIReportSerializer
    permission_classes = [IsAuthenticated]

class AIUserListView(generics.ListAPIView):
    """List users with AI insights."""
    
    serializer_class = AIUserSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter users based on AI insights."""
        queryset = User.objects.all()
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(ai_risk_level=risk_level)
        
        # Filter by behavior score
        min_behavior_score = self.request.query_params.get('min_behavior_score')
        if min_behavior_score:
            queryset = queryset.filter(ai_behavior_score__gte=float(min_behavior_score))
        
        # Filter by AI processed status
        ai_processed = self.request.query_params.get('ai_processed')
        if ai_processed:
            if ai_processed.lower() == 'true':
                queryset = queryset.exclude(ai_processing_date__isnull=True)
            else:
                queryset = queryset.filter(ai_processing_date__isnull=True)
        
        return queryset.order_by('-date_joined')

class AIUserDetailView(generics.RetrieveAPIView):
    """Get detailed user with AI insights."""
    
    queryset = User.objects.all()
    serializer_class = AIUserSerializer
    permission_classes = [IsAdminUser]

@api_view(['POST'])
@permission_classes([IsAdminUser])
def process_reports_with_ai(request):
    """
    Process reports with AI in batch.
    """
    
    serializer = AIProcessingRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    processing_type = data.get('processing_type')
    target_ids = data.get('target_ids', [])
    
    start_time = time.time()
    
    try:
        if processing_type == 'report_analysis':
            if target_ids:
                processed_count = batch_process_reports_with_ai(target_ids)
            else:
                # Process all unprocessed reports
                unprocessed_reports = Report.objects.filter(ai_processed=False)[:50]
                processed_count = batch_process_reports_with_ai([r.id for r in unprocessed_reports])
            
            processing_time = time.time() - start_time
            
            response_data = {
                'processing_type': processing_type,
                'processed_count': processed_count,
                'success_count': processed_count,
                'failed_count': 0,
                'processing_time': processing_time,
                'results': {'processed_reports': processed_count},
                'errors': []
            }
            
            return Response(AIProcessingResponseSerializer(response_data).data)
        
        elif processing_type == 'user_behavior':
            if target_ids:
                processed_count = batch_analyze_users_with_ai(target_ids)
            else:
                # Process active users
                active_users = User.objects.filter(
                    reports__isnull=False
                ).distinct()[:20]
                processed_count = batch_analyze_users_with_ai([u.id for u in active_users])
            
            processing_time = time.time() - start_time
            
            response_data = {
                'processing_type': processing_type,
                'processed_count': processed_count,
                'success_count': processed_count,
                'failed_count': 0,
                'processing_time': processing_time,
                'results': {'processed_users': processed_count},
                'errors': []
            }
            
            return Response(AIProcessingResponseSerializer(response_data).data)
        
        else:
            return Response(
                {'error': 'Unsupported processing type'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            {'error': f'Processing failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_ai_dashboard_stats(request):
    """
    Get AI dashboard statistics.
    """
    
    # Report statistics
    total_reports = Report.objects.count()
    ai_processed_reports = Report.objects.filter(ai_processed=True).count()
    hotspot_reports = Report.objects.filter(ai_hotspot_prediction=True).count()
    high_confidence_reports = Report.objects.filter(ai_confidence_score__gte=0.8).count()
    
    # User statistics
    total_users = User.objects.count()
    ai_analyzed_users = User.objects.exclude(ai_processing_date__isnull=True).count()
    high_risk_users = User.objects.filter(ai_risk_level='high').count()
    
    # Recent AI activity
    recent_ai_processed = Report.objects.filter(
        ai_processing_date__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    stats = {
        'reports': {
            'total': total_reports,
            'ai_processed': ai_processed_reports,
            'ai_processed_percentage': (ai_processed_reports / total_reports * 100) if total_reports > 0 else 0,
            'hotspot_predictions': hotspot_reports,
            'high_confidence': high_confidence_reports
        },
        'users': {
            'total': total_users,
            'ai_analyzed': ai_analyzed_users,
            'ai_analyzed_percentage': (ai_analyzed_users / total_users * 100) if total_users > 0 else 0,
            'high_risk': high_risk_users
        },
        'ai_activity': {
            'recent_processing': recent_ai_processed,
            'processing_rate': recent_ai_processed / 7  # per day
        }
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_recommendations(request):
    """
    Get AI recommendations for the current user.
    """
    
    user = request.user
    
    # Get user-specific recommendations based on AI analysis
    recommendations = []
    
    # If user has AI profile
    if user.ai_user_profile:
        user_profile = user.ai_user_profile
        
        # Add recommendations based on user behavior
        if user.ai_behavior_score < 0.3:
            recommendations.append({
                'type': 'engagement',
                'priority': 'high',
                'title': 'Increase Community Engagement',
                'description': 'Your engagement score is low. Consider participating more in community discussions.'
            })
        
        if user.ai_risk_level == 'high':
            recommendations.append({
                'type': 'risk',
                'priority': 'high',
                'title': 'Account Review Recommended',
                'description': 'Your account has been flagged for review. Please contact support.'
            })
    
    # Get report-specific recommendations
    user_reports = Report.objects.filter(user=user, ai_processed=True)
    for report in user_reports[:3]:  # Top 3 recent reports
        if report.ai_recommendations:
            recommendations.extend([
                {
                    'type': 'report',
                    'priority': 'medium',
                    'title': f"Report '{report.title}' Recommendation",
                    'description': rec
                }
                for rec in report.ai_recommendations[:2]
            ])
    
    return Response({
        'user': user.username,
        'recommendations': recommendations,
        'generated_at': timezone.now()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatbot_api(request):
    """
    Intelligent chatbot API using Llama 3.1 for civic engagement.
    """
    
    serializer = ChatbotRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    message = data.get('message')
    context = data.get('context', {})
    
    try:
        # Use Groq orchestrator for better performance and reliability
        response_data = groq_orchestrator.generate_chatbot_response(
            message, context
        )
        
        return Response(ChatbotResponseSerializer(response_data).data)
        
    except Exception as e:
        logger.error(f"Chatbot API error: {str(e)}")
        return Response({
            'error': 'Chatbot service temporarily unavailable',
            'fallback_response': 'I apologize, but I\'m currently experiencing technical difficulties. Please try again later or contact support directly.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def advanced_analysis_api(request):
    """
    Advanced AI analysis using Llama 3.1 for comprehensive report understanding.
    """
    
    serializer = AdvancedAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    report_ids = data.get('report_ids', [])
    analysis_types = data.get('analysis_types', ['comprehensive'])
    
    start_time = time.time()
    
    try:
        # Initialize orchestrator
        orchestrator = MultiAgentOrchestrator()
        
        results = []
        for report_id in report_ids[:10]:  # Limit to 10 reports for performance
            try:
                report = Report.objects.get(id=report_id)
                
                # Perform advanced analysis
                analysis_result = orchestrator.analyze_report(report)
                
                # Extract Llama-specific insights
                advanced_insights = {
                    'report_id': report_id,
                    'title': report.title,
                    'advanced_insights': getattr(analysis_result, 'advanced_insights', {}),
                    'multilingual_analysis': getattr(analysis_result, 'multilingual_analysis', {}),
                    'contextual_understanding': getattr(analysis_result, 'contextual_understanding', {}),
                    'llama_confidence': getattr(analysis_result, 'confidence', 0.0),
                    'processing_time': time.time() - start_time
                }
                
                results.append(advanced_insights)
                
            except Report.DoesNotExist:
                results.append({
                    'report_id': report_id,
                    'error': 'Report not found'
                })
        
        response_data = {
            'analysis_types': analysis_types,
            'total_reports': len(results),
            'results': results,
            'processing_time': time.time() - start_time,
            'llama_enabled': orchestrator.use_advanced_agents
        }
        
        return Response(AdvancedAnalysisResponseSerializer(response_data).data)
        
    except Exception as e:
        logger.error(f"Advanced analysis API error: {str(e)}")
        return Response({
            'error': 'Advanced analysis service temporarily unavailable',
            'details': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_capabilities(request):
    """
    Get information about available AI capabilities and agent status.
    """
    
    try:
        orchestrator = MultiAgentOrchestrator()
        capabilities = orchestrator.get_agent_capabilities()
        
        return Response({
            'capabilities': capabilities,
            'llama_enabled': orchestrator.use_advanced_agents,
            'available_agents': [agent['name'] for agent in capabilities if agent['available']],
            'system_status': 'operational' if capabilities else 'degraded'
        })
        
    except Exception as e:
        logger.error(f"AI capabilities API error: {str(e)}")
        return Response({
            'error': 'Unable to retrieve AI capabilities',
            'details': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
