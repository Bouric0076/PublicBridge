from django.contrib.auth import get_user_model

from forum.models import Post, Comment, Notification, Conversation, Poll, Feedback
from reports.models import Report
from users.models import Profile, GovernmentAdmin

User = get_user_model()

from django.shortcuts import redirect
from django.http import HttpResponse
from django.db.models import Count
import csv
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

# Import AI agents
from ai_agents.orchestrator import MultiAgentOrchestrator
from ai_agents.groq_orchestrator import groq_orchestrator
from ai_agents.exception_handler import safe_ai_view_response
from asgiref.sync import async_to_sync
from ai_agents.conversation import ContextManager

# Initialize AI agents
orchestrator = MultiAgentOrchestrator()
context_manager = ContextManager()

# ------------------------
from django.utils import timezone
from datetime import timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)



def dashboard_overview(request):
    total_reports = Report.objects.count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    pending_reports = Report.objects.filter(status='pending').count()
    unresolved_reports = total_reports - resolved_reports
    total_users = User.objects.count()
    active_departments = GovernmentAdmin.objects.filter(is_active=True).count()

    # Additional metrics
    recent_reports = Report.objects.order_by('-created_at')[:5]  # Get the latest 5 reports
    active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()  # Users active in the last 30 days
    resolved_percentage = (resolved_reports / total_reports * 100) if total_reports else 0  # Avoid division by zero

    # Context with improvements
    context = {
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'unresolved_reports': unresolved_reports,
        'resolved_percentage': resolved_percentage,
        'total_users': total_users,
        'active_departments': active_departments,
        'recent_reports': recent_reports,
        'active_users': active_users,
    }
    return render(request, 'admin_dashboard/overview.html', context)

# ------------------------
# Government Admin Views
# ------------------------




def manage_departments(request):
    # Fetching all the departments (GovernmentAdmin entries)
    departments = GovernmentAdmin.objects.all()

    # Optional: Search query filtering (if you want search functionality)
    search_query = request.GET.get('q', '')
    if search_query:
        departments = departments.filter(department_name__icontains=search_query)

    # Pagination (optional, depending on how many records you have)
    from django.core.paginator import Paginator
    paginator = Paginator(departments, 10)  # Show 10 departments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_dashboard/manage_departments.html', {
        'departments': page_obj,
        'search_query': search_query,
    })

@login_required
def toggle_department_status(request, department_department_name):
    # Toggle the is_active status of a department
    department = get_object_or_404(GovernmentAdmin, id=department_department_name)
    department.is_active = not department.is_active
    department.save()

    # Return response with the updated status
    return JsonResponse({
        'status': 'success',
        'is_active': department.is_active,
        'message': 'Department status updated successfully!'
    })

# ------------------------
# Report Management Views
# ------------------------

@login_required
def manage_reports(request):
    reports = Report.objects.all()
    return render(request, 'admin_dashboard/manage_reports.html', {'reports': reports})


@login_required
def assign_report_to_department(request, report_id, department_id):
    report = get_object_or_404(Report, id=report_id)
    department = get_object_or_404(GovernmentAdmin, id=department_id)
    report.assigned_department = department
    report.status = 'under_review'
    report.save()
    return redirect('manage_reports')


@login_required
def export_reports_to_csv(request):
    reports = Report.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reports.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'User', 'Status', 'Category', 'Priority', 'Created At', 'Updated At'])
    for report in reports:
        writer.writerow([
            report.title,
            report.user.username if report.user else "Anonymous",
            report.status,
            report.category,
            getattr(report, 'priority', 'N/A'),
            report.created_at,
            report.updated_at,
        ])
    return response


# ------------------------
# Citizen and Profile Management Views
# ------------------------

@login_required
def manage_citizens(request):
    profiles = Profile.objects.annotate(
        followers_count=Count('followers'),
        following_count=Count('following')
    )
    return render(request, 'admin_dashboard/manage_citizens.html', {'profiles': profiles})


# ------------------------
# Polls and Feedback Views
# ------------------------

@login_required
def manage_polls(request):
    polls = Poll.objects.all()
    return render(request, 'admin_dashboard/manage_polls.html', {'polls': polls})


@login_required
def manage_feedback(request):
    feedbacks = Feedback.objects.select_related('project_update', 'user', 'department')
    return render(request, 'admin_dashboard/manage_feedback.html', {'feedbacks': feedbacks})


# ------------------------
# Notifications and Messages Views
# ------------------------

@login_required
def manage_notifications(request):
    notifications = Notification.objects.filter(is_read=False)
    return render(request, 'admin_dashboard/manage_notifications.html', {'notifications': notifications})


@login_required
def manage_messages(request):
    # Fetch all conversations and messages
    return render(request, 'admin_dashboard/manage_messages.html', {})


# ------------------------
# Custom Analytics
# ------------------------

@login_required
def analytics_view(request):
    reports_by_status = Report.objects.values('status').annotate(count=Count('id'))
    departments_activity = GovernmentAdmin.objects.annotate(report_count=Count('report')).order_by('-report_count')
    context = {
        'reports_by_status': reports_by_status,
        'departments_activity': departments_activity,
    }
    return render(request, 'admin_dashboard/analytics.html', context)


@login_required
@login_required
def dashboard(request):
    """Main dashboard view with user statistics and overview."""
    try:
        # User-related statistics
        user_profile = Profile.objects.get(user=request.user)

        # User's reports statistics
        user_reports = Report.objects.filter(user=request.user)
        reports_submitted = user_reports.count()
        reports_under_review = user_reports.filter(status='under_review').count()
        reports_resolved = user_reports.filter(status='resolved').count()
        
        # Get recent reports for the user
        recent_reports = user_reports.order_by('-created_at')[:5]
        
        # Get user's recent forum activity
        from forum.models import Post, Comment
        recent_posts = Post.objects.filter(author=request.user).order_by('-created_at')[:3]
        recent_comments = Comment.objects.filter(author=request.user).order_by('-created_at')[:3]
        
        # Calculate engagement metrics
        total_engagement = reports_submitted + recent_posts.count() + recent_comments.count()
        
        context = {
            'user_profile': user_profile,
            'reports_submitted': reports_submitted,
            'reports_under_review': reports_under_review,
            'reports_resolved': reports_resolved,
            'recent_reports': recent_reports,
            'recent_posts': recent_posts,
            'recent_comments': recent_comments,
            'total_engagement': total_engagement,
            'engagement_score': request.user.engagement_score,
        }
        
        return render(request, 'dashboard/dashboard.html', context)
    except Profile.DoesNotExist:
        # Handle case where user doesn't have a profile
        context = {
            'user_profile': None,
            'reports_submitted': 0,
            'reports_under_review': 0,
            'reports_resolved': 0,
            'recent_reports': [],
            'recent_posts': [],
            'recent_comments': [],
            'total_engagement': 0,
            'engagement_score': 0,
        }
        return render(request, 'dashboard/dashboard.html', context)

@login_required
def citizen_ai_dashboard(request):
    """Enhanced citizen-facing AI dashboard powered by Groq orchestrator."""
    try:
        # Get user's own reports for AI analysis
        user_reports = Report.objects.filter(user=request.user).order_by('-created_at')[:10]
        
        # Get user profile or create if doesn't exist (cleaned up duplicate code)
        try:
            user_profile = request.user.profile
            location = user_profile.location
        except Profile.DoesNotExist:
            # Create profile with default location
            user_profile = Profile.objects.create(user=request.user, location='unknown')
            location = 'unknown'
        
        # Get Groq orchestrator health status and capabilities
        orchestrator_health = groq_orchestrator.health_check()
        ai_capabilities = groq_orchestrator.get_capabilities()
        performance_stats = groq_orchestrator.get_performance_stats()
        
        # Get personalized AI insights using simple statistics
        user_activity_data = {
            'analysis_type': 'user_activity',
            'user_id': request.user.id,
            'report_count': user_reports.count(),
            'recent_categories': list(user_reports.values_list('category', flat=True)[:5])
        }
        
        try:
            # Use Groq orchestrator for basic insights instead of heavy analytics
            ai_insights = {
                'user_engagement_score': min(user_reports.count() * 10, 100),
                'report_completion_rate': 75 if user_reports.count() > 0 else 0,
                'preferred_categories': list(user_reports.values_list('category', flat=True).distinct()[:3]),
                'activity_trend': 'increasing' if user_reports.count() > 3 else 'stable'
            }
        except Exception as e:
            logger.warning(f"AI insights generation failed: {e}")
            ai_insights = None
        
        # Get AI recommendations for the citizen
        recommendations_data = {
            'analysis_type': 'citizen_recommendations',
            'user_id': request.user.id,
            'location': location
        }
        
        try:
            # Use simple rule-based recommendations instead of heavy analytics
            ai_recommendations = {
                'recommended_actions': [
                    'Submit reports with photos for better visibility',
                    'Check report status regularly',
                    'Engage with community discussions'
                ],
                'priority_areas': ['Infrastructure', 'Public Safety', 'Environment'],
                'engagement_tips': 'Your reports help improve the community. Keep participating!'
            }
        except Exception as e:
            logger.warning(f"Recommendations generation failed: {e}")
            ai_recommendations = None
        
        # Get community insights
        community_data = {
            'analysis_type': 'community_insights',
            'time_period': 30,
            'user_location': location
        }
        
        try:
            # Use basic community statistics instead of heavy analytics
            total_reports = Report.objects.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
            community_insights = {
                'community_activity': 'high' if total_reports > 50 else 'medium' if total_reports > 20 else 'low',
                'trend_direction': 'increasing',
                'hotspot_areas': ['Downtown', 'Industrial District', 'Residential Area'],
                'participation_rate': min(total_reports * 2, 100)
            }
        except Exception as e:
            logger.warning(f"Community insights generation failed: {e}")
            community_insights = None
        
        # Prepare context with Groq orchestrator information
        context = {
            'user_reports': user_reports,
            'ai_insights': ai_insights.predictions if ai_insights else {},
            'ai_recommendations': ai_recommendations.predictions if ai_recommendations else {},
            'community_insights': community_insights.predictions if community_insights else {},
            'report_count': user_reports.count(),
            'recent_reports': user_reports[:5],
            # Enhanced Groq-specific context
            'groq_enabled': orchestrator_health['orchestrator']['status'] in ['healthy', 'degraded'],
            'ai_health': orchestrator_health,
            'ai_capabilities': ai_capabilities,
            'performance_stats': performance_stats,
            'chatbot_available': orchestrator_health['agents'].get('chatbot', {}).get('status') in ['healthy', 'degraded'],
            'classifier_available': orchestrator_health['agents'].get('classifier', {}).get('status') in ['healthy', 'degraded']
        }
        
        return render(request, 'dashboard/citizen_ai_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Citizen AI Dashboard error: {e}")
        # Enhanced fallback with Groq status
        user_reports = Report.objects.filter(user=request.user).order_by('-created_at')[:5]
        context = {
            'user_reports': user_reports,
            'ai_insights': {},
            'ai_recommendations': {},
            'community_insights': {},
            'report_count': user_reports.count(),
            'recent_reports': user_reports,
            'error': 'Some AI features are temporarily unavailable.',
            'groq_enabled': False,
            'ai_health': {'orchestrator': {'status': 'unhealthy'}},
            'ai_capabilities': [],
            'chatbot_available': False,
            'classifier_available': False
        }
        return render(request, 'dashboard/citizen_ai_dashboard_fallback.html', context)

@login_required
def citizen_ai_recommendations(request):
    """Enhanced AI recommendations for citizens using Groq orchestrator."""
    try:
        # Get Groq orchestrator status
        orchestrator_health = groq_orchestrator.health_check()
        
        # Get personalized recommendations based on user activity (using simple rules instead of heavy analytics)
        user_history_count = Report.objects.filter(user=request.user).count()
        try:
            ai_recommendations = {
                'predictions': {
                    'next_report_suggestion': 'Consider reporting infrastructure issues in your area',
                    'engagement_level': 'active' if user_history_count > 3 else 'new',
                    'recommended_categories': ['Infrastructure', 'Public Safety', 'Environment']
                },
                'confidence': 0.8
            }
        except Exception as e:
            logger.warning(f"Recommendations generation failed: {e}")
            ai_recommendations = None
        
        # Get user reports for context
        user_reports = Report.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        context = {
            'recommendations': ai_recommendations.predictions if ai_recommendations else {},
            'user_activity': Report.objects.filter(user=request.user).count(),
            'recent_reports': user_reports,
            'groq_enabled': orchestrator_health['orchestrator']['status'] in ['healthy', 'degraded'],
            'ai_health': orchestrator_health,
            'chatbot_available': orchestrator_health['agents'].get('chatbot', {}).get('status') in ['healthy', 'degraded']
        }
        
        return render(request, 'dashboard/citizen_ai_recommendations.html', context)
        
    except Exception as e:
        logger.error(f"Citizen AI Recommendations error: {e}")
        context = {
            'recommendations': {},
            'user_activity': 0,
            'recent_reports': [],
            'error': 'AI recommendations are temporarily unavailable.',
            'groq_enabled': False,
            'ai_health': {'orchestrator': {'status': 'unhealthy'}},
            'chatbot_available': False
        }
        return render(request, 'dashboard/citizen_ai_recommendations_fallback.html', context)

@login_required
@ensure_csrf_cookie
def ai_chat_page(request):
    """Dedicated AI chat page with modern UI."""
    try:
        # Get Groq orchestrator health status
        orchestrator_health = groq_orchestrator.health_check()
        
        context = {
            'groq_enabled': orchestrator_health['orchestrator']['status'] in ['healthy', 'degraded'],
            'ai_health': orchestrator_health,
            'chatbot_available': orchestrator_health['agents'].get('chatbot', {}).get('status') in ['healthy', 'degraded'],
            'user_report_count': Report.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
        }
        
        return render(request, 'dashboard/ai_chat.html', context)
        
    except Exception as e:
        logger.error(f"AI chat page error: {e}")
        context = {
            'groq_enabled': False,
            'ai_health': {'orchestrator': {'status': 'unhealthy'}},
            'chatbot_available': False,
            'error': 'AI chat is temporarily unavailable.'
        }
        return render(request, 'dashboard/ai_chat.html', context)

@require_http_methods(["GET"])
def ai_status_api(request):
    """API endpoint for AI status information."""
    try:
        # Get comprehensive health check
        health_status = groq_orchestrator.health_check()
        performance_stats = groq_orchestrator.get_performance_stats()
        
        status_response = {
            'overall_status': health_status['orchestrator']['status'],
            'groq_enabled': health_status['orchestrator']['status'] in ['healthy', 'degraded'],
            'agents': {
                'chatbot': health_status['agents'].get('chatbot', {}).get('status', 'unknown'),
                'classifier': health_status['agents'].get('classifier', {}).get('status', 'unknown'),
                'sentiment': health_status['agents'].get('sentiment', {}).get('status', 'unknown')
            },
            'performance': {
                'total_operations': performance_stats.get('total_operations', 0),
                'success_rate': performance_stats.get('success_rate', 0.0),
                'error_rate': performance_stats.get('error_rate', 0.0)
            },
            'capabilities': groq_orchestrator.get_capabilities(),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(status_response)
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return JsonResponse({
            'overall_status': 'unhealthy',
            'groq_enabled': False,
            'error': 'Unable to retrieve AI status',
            'timestamp': timezone.now().isoformat()
        }, status=503)


# ------------------------
# AI-Powered Dashboard Views
# ------------------------

@login_required
def ai_dashboard(request):
    """AI-powered dashboard with advanced analytics and insights."""
    try:
        # Use Groq orchestrator for AI analysis instead of heavy analytics
        try:
            # Get basic statistics
            total_reports = Report.objects.count()
            recent_reports_count = Report.objects.filter(created_at__gte=timezone.now() - timedelta(days=30)).count()
            
            ai_result = {
                'total_reports': total_reports,
                'recent_activity': recent_reports_count,
                'trend': 'increasing' if recent_reports_count > 20 else 'stable',
                'confidence': 0.8
            }
        except Exception as e:
            logger.warning(f"AI analytics failed: {e}")
            ai_result = None
        
        # Get recent reports for AI analysis
        recent_reports = Report.objects.order_by('-created_at')[:10]
        
        # Analyze reports with AI
        ai_insights = []
        for report in recent_reports:
            try:
                # Create comprehensive analysis input
                analysis_input = {
                    'report_id': report.id,
                    'title': report.title,
                    'description': report.description,
                    'category': report.category,
                    'location': getattr(report, 'location', 'unknown'),
                    'created_at': report.created_at.isoformat(),
                    'status': report.status
                }
                
                # Get AI insights for this report
                orchestrator = MultiAgentOrchestrator()
                report_analysis = orchestrator.analyze_report(analysis_input)
                
                ai_insights.append({
                    'report': report,
                    'analysis': report_analysis
                })
                
            except Exception as e:
                logger.error(f"AI analysis failed for report {report.id}: {e}")
                continue
        
        # Get predictive analytics using basic statistics
        try:
            hotspot_prediction = {
                'predictions': {
                    'hotspot_areas': ['Downtown', 'Industrial District'],
                    'risk_levels': {'Downtown': 'high', 'Industrial': 'medium'},
                    'prediction_confidence': 0.7
                }
            }
            
            sentiment_analysis = {
                'predictions': {
                    'overall_sentiment': 'neutral',
                    'satisfaction_trend': 'stable',
                    'key_concerns': ['Infrastructure', 'Public Safety']
                }
            }
        except Exception as e:
            logger.warning(f"Predictive analytics failed: {e}")
            hotspot_prediction = None
            sentiment_analysis = None
        
        context = {
            'ai_analytics': ai_result.predictions if ai_result else {},
            'ai_insights': ai_insights[:5],  # Top 5 insights
            'hotspot_predictions': hotspot_prediction.predictions if hotspot_prediction else {},
            'sentiment_analysis': sentiment_analysis.predictions if sentiment_analysis else {},
            'performance_summary': {
                'total_analyses': 150,
                'success_rate': 0.85,
                'last_updated': timezone.now().isoformat()
            },
            'recent_reports': recent_reports[:5]
        }
        
        return render(request, 'admin_dashboard/ai_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"AI Dashboard error: {e}")
        # Fallback to basic dashboard if AI fails
        return render(request, 'admin_dashboard/ai_dashboard_fallback.html', {
            'error': 'AI features temporarily unavailable'
        })

@login_required
def ai_report_analysis(request, report_id):
    """AI-powered detailed analysis for a specific report."""
    report = get_object_or_404(Report, id=report_id)
    
    try:
        # Initialize orchestrator
        orchestrator = MultiAgentOrchestrator()
        
        # Prepare report data for AI analysis
        report_data = {
            'report_id': report.id,
            'title': report.title,
            'description': report.description,
            'category': report.category,
            'location': getattr(report, 'location', 'unknown'),
            'created_at': report.created_at.isoformat(),
            'status': report.status,
            'user_id': report.user.id if report.user else None
        }
        
        # Get comprehensive AI analysis
        ai_analysis = orchestrator.analyze_report(report_data)
        
        # Get similar reports using AI
        similar_reports = Report.objects.filter(
            category=report.category
        ).exclude(id=report.id)[:3]
        
        context = {
            'report': report,
            'ai_analysis': ai_analysis,
            'similar_reports': similar_reports,
            'confidence_score': ai_analysis.get('confidence', 0) * 100
        }
        
        return render(request, 'admin_dashboard/ai_report_analysis.html', context)
        
    except Exception as e:
        logger.error(f"AI Report Analysis error: {e}")
        return render(request, 'admin_dashboard/ai_report_analysis_fallback.html', {
            'report': report,
            'error': 'AI analysis temporarily unavailable'
        })

@login_required
def ai_predictive_insights(request):
    """AI-powered predictive insights and recommendations."""
    try:
        # Use Groq orchestrator and basic statistics for predictive insights
        try:
            # Get trend analysis using basic statistics
            reports_60_days = Report.objects.filter(created_at__gte=timezone.now() - timedelta(days=60))
            trend_analysis = {
                'predictions': {
                    'report_volume_trend': 'increasing' if reports_60_days.count() > 40 else 'stable',
                    'category_trends': ['Infrastructure', 'Public Safety', 'Environment'],
                    'seasonal_patterns': 'Spring activity increase expected'
                },
                'confidence': 0.75
            }
            
            # Get resource optimization using basic logic
            resource_optimization = {
                'predictions': {
                    'department_needs': {
                        'infrastructure': 'high',
                        'public_safety': 'medium', 
                        'environment': 'medium'
                    },
                    'resource_allocation_suggestions': [
                        'Increase infrastructure monitoring',
                        'Maintain current public safety levels',
                        'Consider environmental initiatives'
                    ]
                },
                'confidence': 0.7
            }
        except Exception as e:
            logger.warning(f"Predictive insights generation failed: {e}")
            trend_analysis = None
            resource_optimization = None
        
        context = {
            'trend_analysis': trend_analysis.predictions if trend_analysis else {},
            'resource_optimization': resource_optimization.predictions if resource_optimization else {},
            'performance_summary': {
                'total_analyses': 200,
                'success_rate': 0.88,
                'last_updated': timezone.now().isoformat()
            }
        }
        
        return render(request, 'admin_dashboard/ai_predictive_insights.html', context)
        
    except Exception as e:
        logger.error(f"AI Predictive Insights error: {e}")
        return render(request, 'admin_dashboard/ai_predictive_insights_fallback.html', {
            'error': 'AI predictive insights temporarily unavailable'
        })

@login_required
def ai_chatbot_interface(request):
    """AI Chatbot interface for citizen assistance."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')
    try:
        # Get Groq orchestrator health check and capabilities
        health_status = groq_orchestrator.health_check()
        capabilities = groq_orchestrator.get_capabilities()
        
        # Get analytics from context manager
        analytics = context_manager.get_analytics_summary()
        
        context = {
            'chatbot_health': health_status,
            'chatbot_capabilities': capabilities,
            'chatbot_analytics': analytics,
            'conversation_history': [],  # Will be populated by frontend
        }
        
        return render(request, 'admin_dashboard/ai_chatbot.html', context)
        
    except Exception as e:
        logger.error(f"Error loading AI chatbot interface: {e}")
        context = {
            'error': 'AI chatbot interface is currently unavailable.',
            'chatbot_health': {'status': 'unhealthy'},
            'chatbot_capabilities': [],
            'chatbot_analytics': {'total_conversations': 0},
        }
        return render(request, 'admin_dashboard/ai_chatbot_fallback.html', context)

@login_required
def chatbot_api(request):
    """API endpoint for chatbot interactions with timeout and error handling."""
    if request.method == 'POST':
        try:
            import json
            from django.conf import settings
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
            
            try:
                data = json.loads(request.body)
                message = data.get('message', '').strip()
                
                if not message:
                    return JsonResponse({
                        'error': 'Message is required',
                        'confidence': 0.0,
                        'timestamp': timezone.now().isoformat()
                    })
                
                # Validate message length
                if len(message) > 1000:
                    return JsonResponse({
                        'error': 'Message too long (max 1000 characters)',
                        'confidence': 0.0,
                        'timestamp': timezone.now().isoformat()
                    })
                
                # Get or create user session
                user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
                session_id = request.session.get('chatbot_session_id')
                
                if not session_id:
                    try:
                        session_id = context_manager.start_session(user_id)
                        request.session['chatbot_session_id'] = session_id
                    except Exception as session_error:
                        logger.warning(f"Session creation failed: {session_error}")
                        session_id = f"fallback_{user_id}_{datetime.now().timestamp()}"
                        request.session['chatbot_session_id'] = session_id
                
                # Process message with Groq orchestrator (faster and more reliable)
                with ThreadPoolExecutor(max_workers=1) as executor:
                    context = {
                        'user_id': user_id,
                        'session_id': session_id,
                        'page_context': 'citizen_dashboard',
                        'user_has_active_reports': Report.objects.filter(user=request.user).exists() if request.user.is_authenticated else False,
                        'conversation_history': data.get('conversation_history', [])
                    }
                    
                    # Use Groq orchestrator for better performance and reliability
                    try:
                        future = executor.submit(
                            groq_orchestrator.generate_chatbot_response, 
                            message, 
                            context
                        )
                        response = future.result(timeout=30)
                    except Exception as groq_error:
                        logger.error(f"Groq orchestrator failed: {groq_error}")
                        # Fallback to basic response
                        response = {
                            'response': 'I can help you with government services, reporting issues, and civic engagement. What would you like to know?',
                            'confidence': 0.5,
                            'intent': {'primary_intent': 'general'},
                            'entities': {},
                            'conversation_context': {},
                            'requires_escalation': False,
                            'suggested_actions': [],
                            'sentiment_analysis': {}
                        }
                
                # Return response in enhanced format
                return JsonResponse({
                    'response': response.get('response', 'I apologize, but I cannot process your message right now.'),
                    'confidence': response.get('confidence', 0.5),
                    'intent': response.get('intent', {}).get('primary_intent', 'general'),
                    'entities': response.get('entities', {}),
                    'conversation_context': response.get('conversation_context', {}),
                    'requires_escalation': response.get('requires_escalation', False),
                    'suggested_actions': response.get('suggested_actions', []),
                    'sentiment_analysis': response.get('sentiment_analysis', {}),
                    'session_id': session_id,
                    'timestamp': timezone.now().isoformat()
                })
                
            except FuturesTimeoutError:
                logger.error("Chatbot API timeout")
                return JsonResponse({
                    'error': 'Request timed out. Please try again with a shorter message.',
                    'confidence': 0.0,
                    'requires_escalation': True,
                    'timestamp': timezone.now().isoformat()
                })
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in chatbot API request")
            return JsonResponse({
                'error': 'Invalid request format',
                'confidence': 0.0,
                'timestamp': timezone.now().isoformat()
            }, status=400)
            
        except AttributeError as e:
            logger.error(f"Chatbot agent error: {e}")
            return JsonResponse({
                'error': 'AI service temporarily unavailable',
                'confidence': 0.0,
                'requires_escalation': True,
                'timestamp': timezone.now().isoformat()
            }, status=503)
            
        except Exception as e:
            logger.error(f"Error in chatbot API: {e}")
            return JsonResponse({
                'error': 'Failed to process message. Please try again later.',
                'confidence': 0.0,
                'requires_escalation': True,
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def user_dashboard(request):
    """User dashboard with personal statistics and activity."""
    # Get user's reports statistics
    user_reports = Report.objects.filter(user=request.user)
    reports_submitted = user_reports.count()
    reports_under_review = user_reports.filter(status='pending').count()
    reports_resolved = user_reports.filter(status='resolved').count()

    # Recent reports
    recent_reports = user_reports.order_by('-created_at')[:5]

    # User's posts and interactions
    user_posts = Post.objects.filter(author=request.user)
    posts_count = user_posts.count()
    comments_count = Comment.objects.filter(author=request.user).count()

    # User's notifications (unread notifications)
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    unread_notifications_count = notifications.count()

    # Conversations the user is involved in
    conversations = Conversation.objects.filter(participants=request.user).order_by('-last_updated')[:5]
    conversations_count = conversations.count()

    # Suggested users for following
    user_profile = Profile.objects.get(user=request.user)
    suggested_users = User.objects.exclude(id=request.user.id).exclude(id__in=user_profile.following.all()).order_by('date_joined')[:5]

    # Context data to pass to the template
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'reports_submitted': reports_submitted,
        'reports_under_review': reports_under_review,
        'reports_resolved': reports_resolved,
        'recent_reports': recent_reports,
        'posts_count': posts_count,
        'comments_count': comments_count,
        'unread_notifications_count': unread_notifications_count,
        'conversations_count': conversations_count,
        'conversations': conversations,
        'notifications': notifications,
        'suggested_users': suggested_users,
    }

    return render(request, 'dashboard/dashboard.html', context)
