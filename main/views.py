
from django.shortcuts import render
from django.http import JsonResponse

def landing_page(request):
    return render(request, 'main/PublicBridge.html')

def health_check(request):
    """Health check endpoint to keep Render deployment awake"""
    return JsonResponse({'status': 'healthy', 'service': 'PublicBridge'}, status=200)
