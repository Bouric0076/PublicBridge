from rest_framework import serializers
from .models import DisasterReport, DisasterAgency

class DisasterAgencySerializer(serializers.ModelSerializer):
    """Serializer for Disaster Agencies"""

    class Meta:
        model = DisasterAgency
        fields = "__all__"  # Returns all fields

class DisasterReportSerializer(serializers.ModelSerializer):
    """Serializer for Disaster Reports"""

    user = serializers.StringRelatedField(read_only=True)  # ✅ Now read-only, avoids PATCH issues
    assigned_agency = serializers.StringRelatedField(read_only=True)  # ✅ Prevents errors
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DisasterReport
        fields = [
            "id", "user", "category", "category_display", "other_category",
            "description", "latitude", "longitude", "address", "image", "status",
            "status_display", "assigned_agency", "created_at", "is_archived"
        ]
        extra_kwargs = {
            "status": {"required": False},  # ✅ Allows PATCH to update status without requiring all fields
        }
