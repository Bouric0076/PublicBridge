from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from utils.nlp_utils import analyze_text  # Import the improved NLP utility
from .models import Report, ActivityLog, AnonymousReport
from .serializers import ReportSerializer
from .forms import ReportForm, AnonymousReportForm  # Ensure you have a form for reports


class ReportViewSet(ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """API Endpoint to Update Report Status"""
        report = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Report.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        report.updated_at = timezone.now()
        report.update_status(new_status, updated_by=request.user)
        return Response({"message": "Status updated successfully"}, status=status.HTTP_200_OK)


@login_required
def submit_report(request):
    """Submit a new report"""
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, "Report submitted successfully.")
            return redirect("user_reports")
    else:
        form = ReportForm()

    return render(request, "reports/submit_userreport.html", {"form": form})


@login_required
def user_reports(request):
    """List all reports submitted by the logged-in user"""
    reports = Report.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "reports/user_reports.html", {"reports": reports})


@login_required
def submit_anonymous_report(request):
    """Handle submission of reports by anonymous users or other types"""
    if request.method == "POST":
     form = AnonymousReportForm(request.POST, request.FILES)
     if form.is_valid():
        report = form.save(commit=False)
        report.save()
        messages.success(request, "Anonymous report submitted successfully.")
        return redirect("dashboard")
    return render(request, "reports/submit_report.html")


@login_required
def edit_report(request, report_id):
    """Edit an existing report"""
    report = get_object_or_404(Report, id=report_id)

    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Report updated successfully.")
            return redirect("report_details", report_id=report.id)
    else:
        form = ReportForm(instance=report)

    return render(request, "reports/edit_report.html", {"form": form, "report": report})


@login_required
def delete_report(request, report_id):
    """Delete a specific report"""
    report = get_object_or_404(Report, id=report_id)

    if request.method == "POST":
        report.delete()
        messages.success(request, "Report deleted successfully.")
        return redirect("user_reports")

    return render(request, "reports/delete_report.html", {"report": report})


@login_required
def report_details(request, report_id):
    """View a specific report's details, including NLP insights"""
    report = get_object_or_404(Report, id=report_id)

    nlp_analysis = None
    if report.status_history:
        last_analysis = next(
            (entry["analysis"] for entry in reversed(report.status_history) if "analysis" in entry),
            None
        )
        if last_analysis:
            nlp_analysis = last_analysis

    return render(request, 'reports/reports_detail.html', {
        'report': report,
        'nlp_analysis': nlp_analysis
    })


@login_required
def analyze_report_nlp(request, report_id):
    """Analyze a report's text using NLP and store insights"""
    report = get_object_or_404(Report, id=report_id)
    nlp_results = analyze_text(report.description)

    report.status_history.append({
        "analysis": nlp_results,
        "timestamp": str(timezone.now()),
        "performed_by": request.user.username
    })
    report.save()

    ActivityLog.objects.create(
        action=f"NLP analysis performed on report {report.id}",
        performed_by=request.user,
        related_report=report
    )

    return JsonResponse({
        "message": "NLP analysis completed successfully",
        "results": nlp_results
    })
