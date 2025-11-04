import uuid

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import logout

from reports.models import Report
from .models import Ministry
from .forms import MinistryRegistrationForm


def register_ministry(request):
    """Register a new ministry (awaiting approval)."""
    if request.method == "POST":
        form = MinistryRegistrationForm(request.POST)
        if form.is_valid():
            ministry = form.save(commit=False)
            ministry.password = make_password(request.POST.get("password"))  # Hash password
            ministry.is_approved = False  # Requires GovernmentAdmin approval
            ministry.save()
            messages.success(request, "Registration submitted. Awaiting approval.")
            return redirect("success")  # Redirect to a success page
    else:
        form = MinistryRegistrationForm()

    return render(request, "ministries/register.html", {"form": form})


def success_view(request):
    """Success page after registration submission."""
    return render(request, "ministries/success.html")


def login_ministry(request):
    """Authenticate and log in a ministry using email and password."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            ministry = Ministry.objects.get(email=email)

            if not ministry.is_approved:
                messages.error(request, "Your ministry is pending approval.")
                return redirect("ministry-login")

            if check_password(password, ministry.password):  # Validate hashed password
                request.session["ministry_id"] = str(ministry.ministry_id)  # Store in session
                messages.success(request, "Login successful!")
                return redirect("ministry-dashboard")
            else:
                messages.error(request, "Invalid credentials. Please try again.")
        except Ministry.DoesNotExist:
            messages.error(request, "Ministry not found.")

    return render(request, "ministries/login.html")


def logout_ministry(request):
    """Log out the ministry and clear session."""
    logout(request)
    request.session.flush()  # Clear session data
    messages.success(request, "You have been logged out.")
    return redirect("ministry-login")


def ministry_dashboard(request):
    """Show reports assigned to the logged-in ministry."""
    ministry_id = request.session.get("ministry_id")  # Fetch ministry ID from session

    if not ministry_id:
        messages.error(request, "You must be logged in as a ministry.")
        return redirect("ministry-login")  # Redirect to login if not authenticated

    ministry = get_object_or_404(Ministry, ministry_id=ministry_id)  # Fetch Ministry instance
    reports = Report.objects.filter(ministry=ministry)
    resolved_reports = reports.filter(status="resolved").count()
    pending_reports = reports.filter(status="pending").count()
    under_review_reports = reports.filter(status="under_review").count()
    rejected_reports = reports.filter(status="rejected").count()

    return render(request, "ministries/ministry_dashboard.html", {
        "ministry": ministry, 
        "reports": reports,
        "resolved_reports": resolved_reports,
        "pending_reports": pending_reports,
        "under_review_reports": under_review_reports,
        "rejected_reports": rejected_reports,
    })


def update_report_status(request, report_id):
    """Update the status of an assigned report."""
    ministry_id = request.session.get("ministry_id")

    if not ministry_id:
        messages.error(request, "You must be logged in as a ministry.")
        return redirect("ministry-login")

    # Fetch report using the report_id
    report = get_object_or_404(Report, report_id=report_id, ministry__ministry_id=ministry_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(Report.STATUS_CHOICES):  # ✅ Validate status correctly
            report.update_status(new_status, request.user)  # ✅ Use method to track history
            report.refresh_from_db()  # ✅ Ensure fresh data
            messages.success(request, f"Report '{report.title}' updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")

        return redirect("ministry-dashboard")

    return render(request, "ministries/update_report_status.html", {"report": report})


def assigned_reports(request):
    """View assigned reports for the logged-in ministry."""
    ministry_id = request.session.get("ministry_id")

    if not ministry_id:
        messages.error(request, "You must be logged in as a ministry.")
        return redirect("ministry-login")

    ministry = get_object_or_404(Ministry, ministry_id=ministry_id)
    reports = Report.objects.filter(ministry=ministry, status="under_review")

    return render(request, "ministries/assigned_reports.html", {"reports": reports})


def resolved_reports(request):
    """View resolved reports for the logged-in ministry."""
    ministry_id = request.session.get("ministry_id")

    if not ministry_id:
        messages.error(request, "You must be logged in as a ministry.")
        return redirect("ministry-login")

    ministry = get_object_or_404(Ministry, ministry_id=ministry_id)
    reports = Report.objects.filter(ministry=ministry, status="resolved")

    return render(request, "ministries/resolved_reports.html", {"reports": reports})


def report_details(request, report_id):
    """View details of a specific report."""
    ministry_id = request.session.get("ministry_id")

    if not ministry_id:
        messages.error(request, "You must be logged in as a ministry.")
        return redirect("ministry-login")

    report = get_object_or_404(Report, id=report_id, ministry__ministry_id=ministry_id)

    return render(request, "ministries/report_details.html", {"report": report})
