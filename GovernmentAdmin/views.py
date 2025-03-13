# Create your views here.
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from forum.models import Post, ProjectUpdate, Poll, Comment
from ministries.models import Ministry
from reports.models import ActivityLog, AssignmentQueue, ReportAttachment
from reports.models import Report
from users.decorators import government_admin_required


from django.shortcuts import render

from rest_framework import viewsets
from disaster_reporting.models import DisasterReport
from .serializers import DisasterReportSerializer

class DisasterReportViewSet(viewsets.ModelViewSet):
    queryset = DisasterReport.objects.all().order_by('-created_at')
    serializer_class = DisasterReportSerializer


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from disaster_reporting.models import DisasterReport, DisasterAgency  # Only geotagged reports
from django.utils.timezone import now

@login_required
def admin_dashboard(request):
    """Renders the admin dashboard with geotagged reports and agency data."""
    geotagged_reports = DisasterReport.objects.filter(status="Pending").values(
        "id", "category", "status", "latitude", "longitude"
    )  # Convert QuerySet to JSON format

    active_agencies = DisasterAgency.objects.filter(is_active=True)

    context = {
        "geotagged_reports": list(geotagged_reports),  # Ensure it's JSON-safe
        "active_agencies": active_agencies,
    }
    return render(request, "governmentadmin/geotagged_reports.html", context)



# Views for the admin dashboard and other pages
def dashboard_overview(request):
    return render(request, 'admin_dashboard/overview.html')

def manage_departments(request):
    return render(request, 'admin_dashboard/manage_departments.html')

def manage_reports(request):
    return render(request, 'admin_dashboard/manage_reports.html')

def manage_citizens(request):
    return render(request, 'admin_dashboard/manage_citizens.html')


def disaster_dashboard(request):
    reports = DisasterReport.objects.all()
    return render(request, 'governmentadmin/disaster_dashboard.html', {'reports': reports})

def approve_ministry(request, ministry_id):
    try:
        ministry = Ministry.objects.get(ministry_id=ministry_id)
        ministry.is_approved = True  # Approving the ministry
        ministry.save()
        messages.success(request, f"Ministry {ministry.name} approved.")
    except Ministry.DoesNotExist:
        messages.error(request, "Ministry not found.")

    return redirect("view-pending-ministries")  # Redirect to pending ministries list


def view_pending_ministries(request):
    pending_ministries = Ministry.objects.filter(is_approved=False)  # Only pending ministries
    return render(request, "governmentadmin/pending_approvals.html", {"ministries": pending_ministries})

def view_reports(request):
    """Display all reports categorized by status."""
    pending_reports = Report.objects.filter(status="Pending")
    under_review_reports = Report.objects.filter(status="Under Review")
    resolved_reports = Report.objects.filter(status="Resolved")

    return render(request, "governmentadmin/reports_dashboard.html", {
        "pending_reports": pending_reports,
        "under_review_reports": under_review_reports,
        "resolved_reports": resolved_reports
    })

def assign_report_list(request):
    """Display a list of reports that need assignment."""
    reports = Report.objects.filter(status="pending")  # Fetch only pending reports
    ministries = Ministry.objects.filter(is_approved=True)

    return render(request, "governmentadmin/assign_report.html", {"reports": reports, "ministries": ministries})


def assign_report(request, report_id):
    """Assign a specific report to a ministry."""
    report = get_object_or_404(Report, report_id=report_id)  # Ensure the report exists
    ministries = Ministry.objects.filter(is_approved=True)  # Fetch all approved ministries

    if request.method == "POST":
        ministry_id = request.POST.get("ministry_id")  # Get ministry ID from form

        if not ministry_id:
            messages.error(request, "Please select a valid ministry.")
            return redirect("assign_report", report_id=report_id)

        try:
            # Convert ministry_id to UUID before querying
            ministry_uuid = uuid.UUID(ministry_id)
            ministry = get_object_or_404(Ministry, ministry_id=ministry_uuid)

            # Assign ministry and update report status
            report.ministry = ministry
            report.status = "under_review"
            report.save()

            messages.success(request, f"Report '{report.title}' assigned to {ministry.name}.")

            return redirect("assign_reports")  # Redirect to reports list

        except ValueError:
            messages.error(request, "Invalid Ministry ID format.")
            return redirect("assign_report", report_id=report_id)

    return render(request, "governmentadmin/assign_report_detail.html", {"report": report, "ministries": ministries})

@login_required
@government_admin_required
def govadmin_dashboard(request):
    # Fetch counts for statistics
    posts_count = Post.objects.count()
    comments_count = Comment.objects.count()
    project_updates_count = ProjectUpdate.objects.count()
    polls_count = Poll.objects.count()

    # Report statistics
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status="pending").count()
    resolved_reports = Report.objects.filter(status="resolved").count()

    # Recent reports (latest 5)
    recent_reports = Report.objects.order_by('-created_at')[:5]

    # Activity logs (latest 10)
    activity_logs = ActivityLog.objects.all().order_by('-timestamp')[:10]

    # Report assignment queue (latest 10)
    assignment_queue = AssignmentQueue.objects.all().order_by('-assigned_at')[:10]

    # File attachments for reports (latest 10)
    file_attachments = ReportAttachment.objects.all().order_by('-uploaded_at')[:10]

    context = {
        'posts_count': posts_count,
        'comments_count': comments_count,
        'project_updates_count': project_updates_count,
        'polls_count': polls_count,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'recent_reports': recent_reports,
        'activity_logs': activity_logs,
        'assignment_queue': assignment_queue,
        'file_attachments': file_attachments,
    }

    return render(request, "governmentadmin/dashboard.html", context)

@login_required
def manage_ministries(request):
    if not request.user.is_government_admin:
        return render(request, "governmentadmin/error.html", {"message": "Access Denied"})

    ministries = Ministry.objects.all()
    return render(request, "governmentadmin/manage_ministries.html", {"ministries": ministries})