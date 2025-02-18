from django.contrib import messages
from django.contrib.auth import logout
# users/views.py

from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
# users/views.py
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import UserRegistrationForm


# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def government_admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if "GovernmentAdmin" == user.role:
                login(request, user)
                return redirect("govadmin_dashboard")
            else:
                messages.error(request, "Only authenticated GovernmentAdmins can access this page.")
                return redirect("govadmin_login")
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, "governmentadmin/login.html")

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user if the form is valid

            # Automatically log the user in
            login(request, user)

            # Redirect to the dashboard after registration
            return redirect('dashboard')
        else:
            # If the form is invalid, errors will be displayed on the template
            return render(request, 'users/register.html', {'form': form})
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})
    return render(request, 'users/login.html')

# Create your views here.



def logout_user(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout
