from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from .forms import UserRegistrationForm
from .models import User  # Import your custom User model


def government_admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # FIX: Use the correct role value from your model
            if user.role == "government_admin":  # Changed from "GovernmentAdmin" to "government_admin"
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

            # Fix: Set the backend attribute before login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
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
        
        # Debug information
        print(f"DEBUG: Login attempt - Username: {username}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"DEBUG: Login successful - User: {user.username}, Role: {user.role}")
            login(request, user)
            return redirect('dashboard')
        else:
            print(f"DEBUG: Login failed - Username: {username}")
            
            # Check if user exists but password is wrong
            try:
                user_exists = User.objects.get(username=username)
                print(f"DEBUG: User exists but authentication failed - {user_exists.username}")
                error_message = 'Invalid password'
            except User.DoesNotExist:
                print(f"DEBUG: User does not exist - {username}")
                error_message = 'Username does not exist'
                
            return render(request, 'users/login.html', {'error': error_message})
    
    return render(request, 'users/login.html')


def logout_user(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout