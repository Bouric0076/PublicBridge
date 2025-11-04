from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import DatabaseError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
import logging

from utils.nlp_utils import analyze_text  # Import the improved NLP utility
from .models import Report, ActivityLog, AnonymousReport
from .serializers import ReportSerializer
from .forms import ReportForm, AnonymousReportForm  # Ensure you have a form for reports

# Set up logging
logger = logging.getLogger(__name__)


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
    """Submit a new report with error handling"""
    try:
        if request.method == "POST":
            form = ReportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    report = form.save(commit=False)
                    report.user = request.user
                    report.save()
                    
                    # Log the successful report submission
                    logger.info(f"Report submitted successfully by user {request.user.username}")
                    messages.success(request, "Report submitted successfully.")
                    return redirect("user_reports")
                    
                except DatabaseError as e:
                    logger.error(f"Database error while saving report: {e}")
                    messages.error(request, "An error occurred while saving your report. Please try again.")
                except Exception as e:
                    logger.error(f"Unexpected error while saving report: {e}")
                    messages.error(request, "An unexpected error occurred. Please try again.")
            else:
                logger.warning(f"Invalid form submission by user {request.user.username}: {form.errors}")
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = ReportForm()
            
    except Exception as e:
        logger.error(f"Error in submit_report view: {e}")
        messages.error(request, "An error occurred while processing your request.")
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
    """Analyze a report's text using NLP and store insights with error handling"""
    try:
        report = get_object_or_404(Report, id=report_id)
        
        # Validate that the report has description
        if not report.description:
            return JsonResponse({
                "error": "Report has no description to analyze"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform NLP analysis with error handling
        try:
            nlp_results = analyze_text(report.description)
        except Exception as e:
            logger.error(f"NLP analysis failed for report {report_id}: {e}")
            return JsonResponse({
                "error": "NLP analysis failed. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update report with analysis results
        try:
            if not isinstance(report.status_history, list):
                report.status_history = []
            
            report.status_history.append({
                "analysis": nlp_results,
                "timestamp": str(timezone.now()),
                "performed_by": request.user.username
            })
            report.save()
            
            # Create activity log
            ActivityLog.objects.create(
                action=f"NLP analysis performed on report {report.id}",
                performed_by=request.user,
                related_report=report
            )
            
            logger.info(f"NLP analysis completed for report {report_id} by user {request.user.username}")
            
            return JsonResponse({
                "message": "NLP analysis completed successfully",
                "results": nlp_results
            })
            
        except DatabaseError as e:
            logger.error(f"Database error while saving NLP analysis: {e}")
            return JsonResponse({
                "error": "Failed to save analysis results"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Report.DoesNotExist:
        return JsonResponse({
            "error": "Report not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Unexpected error in analyze_report_nlp: {e}")
        return JsonResponse({
            "error": "An unexpected error occurred"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
