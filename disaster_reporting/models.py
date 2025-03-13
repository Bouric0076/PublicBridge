from django.db import models
from django.contrib.auth import get_user_model
from geopy.geocoders import Nominatim
import math

User = get_user_model()
from django.utils.timezone import now

class DisasterAgency(models.Model):
    """
    Government or emergency response agencies responsible for disaster management.
    """
    CATEGORY_CHOICES = [
        ('fire_department', 'Fire Department'),
        ('medical_services', 'Medical Services'),
        ('infrastructure', 'Infrastructure Maintenance'),
        ('environmental', 'Environmental Management'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    is_active = models.BooleanField(default=False)  # ✅ Determines if the agency is currently online
    last_seen = models.DateTimeField(null=True, blank=True)  # ✅ Tracks last active time

    def update_status(self):
        """Mark the agency as active and update last seen timestamp."""
        self.is_active = True
        self.last_seen = now()
        self.save()

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class DisasterReport(models.Model):
    CATEGORY_CHOICES = [
        ('pothole', 'Pothole'),
        ('road_damage', 'Road Damage'),
        ('fire', 'Fire'),
        ('flood', 'Flood'),
        ('earthquake', 'Earthquake'),
        ('medical', 'Medical Emergency'),
        ('building_collapse', 'Building Collapse'),
        ('power_outage', 'Power Outage'),
        ('theft', 'Theft/Robbery'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('invalid', 'Invalid'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'citizen'})
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    other_category = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='disaster_reports/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_agency = models.ForeignKey(DisasterAgency, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    def archive(self):
        """Mark this report as archived."""
        self.is_archived = True
        self.save()

    @staticmethod
    def get_address_from_coordinates(latitude, longitude):
        """Fetch an address from latitude & longitude using geopy."""
        try:
            geolocator = Nominatim(user_agent="disaster_reporting")
            location = geolocator.reverse((latitude, longitude), exactly_one=True)
            return location.address if location else "Unknown Address"
        except Exception as e:
            print(f"Error fetching address: {e}")
            return "Unknown Address"

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two latitude-longitude points (in km)."""
        R = 6371  # Earth radius in km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def find_nearest_agency(self):
        """Find the nearest disaster agency based on location."""
        agencies = DisasterAgency.objects.all()
        if not agencies.exists():
            return None  # Avoids potential NoneType errors

        nearest_agency = min(
            agencies,
            key=lambda agency: self.haversine_distance(self.latitude, self.longitude, agency.latitude, agency.longitude),
            default=None
        )

        return nearest_agency

    def save(self, *args, **kwargs):
        """Auto-assign address and agency before saving."""
        if not self.address and self.latitude and self.longitude:
            self.address = self.get_address_from_coordinates(self.latitude, self.longitude)

        if not self.assigned_agency:  # Prevents reassignment if already set
            self.assigned_agency = self.find_nearest_agency()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_category_display()} by {self.user.username} - {self.get_status_display()}"
