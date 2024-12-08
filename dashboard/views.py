from forum.models import Post, Comment, Notification, Conversation
from reports.models import Report
from users.models import Profile
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model

from forum.models import Post, Comment, Notification, Conversation, Poll, Feedback
from reports.models import Report
from users.models import Profile,GovernmentAdmin

User = get_user_model()

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.contrib.auth.decorators import login_required
import csv


# ------------------------
# Dashboard Overview
# ------------------------

@login_required
def dashboard_overview(request):
    total_reports = Report.objects.count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    total_users = Profile.objects.count()
    active_departments = GovernmentAdmin.objects.filter(is_active=True).count()

    context = {
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'total_users': total_users,
        'active_departments': active_departments,
    }
    return render(request, 'admin_dashboard/overview.html', context)


# ------------------------
# Government Admin Views
# ------------------------

@login_required
def manage_departments(request):
    departments = GovernmentAdmin.objects.all()
    return render(request, 'admin_dashboard/manage_departments.html', {'departments': departments})


@login_required
def toggle_department_status(request, department_id):
    department = get_object_or_404(GovernmentAdmin, id=department_id)
    department.is_active = not department.is_active
    department.save()
    return JsonResponse({'status': 'success', 'is_active': department.is_active})


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
def dashboard(request):
    # User-related statistics
    user_profile = Profile.objects.get(user=request.user)

    # User's reports statistics
    user_reports = Report.objects.filter(user=request.user)
    reports_submitted = user_reports.count()
    reports_under_review = user_reports.filter(status='Under Review').count()
    reports_resolved = user_reports.filter(status='Resolved').count()

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
