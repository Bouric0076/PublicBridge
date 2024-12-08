from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import AnonymousReportForm
from django.contrib.auth.decorators import login_required
from .models import Report
from .forms import ReportForm
from django.shortcuts import get_object_or_404

def submit_report(request):
    if request.method == 'POST':
        form = AnonymousReportForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'reports/success.html')  # Show a success message
    else:
        form = AnonymousReportForm()
    return render(request, 'reports/submit_report.html', {'form': form})

@login_required
def user_reports(request):
    """ View to display the user-specific reports on the dashboard. """
    user_reports = Report.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'reports/user_reports.html', {'reports': user_reports})

@login_required
def submit_userreport(request):
    """View to handle the submission of new reports."""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.status = 'Pending'  # Set the default status to 'Pending'
            report.save()
            return redirect('user_reports')  # Redirect to the report list after submission
    else:
        form = ReportForm()

    return render(request, 'reports/submit_userreport.html', {'form': form})
def report_details(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    context = {
        'report': report,
    }

    return render(request, 'reports/reports_detail.html', context)

def edit_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'The report has been updated successfully.')
            return redirect('report_details', report_id=report.id)
    else:
        form = ReportForm(instance=report)

    return render(request, 'reports/edit_report.html', {'form': form, 'report': report})

def delete_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)

    if request.method == 'POST':
        report.delete()
        messages.success(request, 'The report has been deleted successfully.')
        return redirect('dashboard')  # Redirect to the dashboard or another appropriate page

    return render(request, 'reports/delete_report.html', {'report': report})