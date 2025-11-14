import requests

def get_address_from_coordinates(lat, lon):
    """
    Uses OpenStreetMap's Nominatim API to convert coordinates into a readable address.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    headers = {'User-Agent': 'publicbridge-app'}  # Required by Nominatim
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("display_name", "Address not found")
    return "Error fetching address"

def is_potential_duplicate(category: str, latitude: float, longitude: float, time_window_minutes: int = 120, radius_meters: int = 300):
    """Detect potential duplicate reports near the same location and time."""
    from django.utils import timezone
    from .models import DisasterReport
    cutoff = timezone.now() - timezone.timedelta(minutes=time_window_minutes)
    nearby = DisasterReport.objects.filter(
        category=category,
        created_at__gte=cutoff
    )
    for r in nearby:
        d = _haversine_distance(latitude, longitude, r.latitude, r.longitude)
        if d * 1000 <= radius_meters:
            return True
    return False

def _haversine_distance(lat1, lon1, lat2, lon2):
    import math
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
