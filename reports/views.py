
from django.shortcuts import render, redirect
from .forms import AnonymousReportForm
from django.contrib.auth.decorators import login_required
from .models import Report
from .forms import ReportForm

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
    """ View to handle the submission of new reports. """
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            return redirect('user_reports')  # Redirect to the report list after submission
    else:
        form = ReportForm()

    return render(request, 'reports/submit_userreport.html', {'form': form})
