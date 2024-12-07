from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from forum.models import Post
from reports.models import Report  # Import the Report model

@login_required
def dashboard(request):
    # Get the user's reports count and other stats
    user_reports = Report.objects.filter(user=request.user)
    reports_submitted = user_reports.count()
    reports_under_review = user_reports.filter(status='Under Review').count()
    reports_resolved = user_reports.filter(status='Resolved').count()

    # Get recent reports
    recent_reports = user_reports.order_by('-created_at')[:5]

    # Pass everything to the context
    context = {
        'user': request.user,
        'reports_submitted': reports_submitted,
        'reports_under_review': reports_under_review,
        'reports_resolved': reports_resolved,
        'recent_reports': recent_reports,
    }


    return render(request, 'dashboard/dashboard.html', context)

@login_required
def personalized_feed(request):
        followed_users = request.user.profile.following.all()
        posts = Post.objects.filter(author__in=followed_users).order_by('-created_at')

        context = {
            'posts': posts,
        }
        return render(request, 'forum/feed.html', context)
