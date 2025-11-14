from rest_framework import serializers
from .models import DisasterReport, DisasterAgency, DisasterMedia

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
    media_files = serializers.SerializerMethodField()

    class Meta:
        model = DisasterReport
        fields = [
            "id", "user", "category", "category_display", "other_category",
            "description", "latitude", "longitude", "address", "image", "severity",
            "is_anonymous", "tracking_code", "status", "status_display", "assigned_agency",
            "created_at", "is_archived", "media_files"
        ]
        extra_kwargs = {
            "status": {"required": False},  # ✅ Allows PATCH to update status without requiring all fields
        }

    def get_media_files(self, obj):
        return [
            {
                'id': m.id,
                'media_type': m.media_type,
                'file_url': m.file.url if hasattr(m.file, 'url') else '',
                'uploaded_at': m.uploaded_at.isoformat(),
            }
            for m in obj.media_files.all()
        ]

class DisasterMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisasterMedia
        fields = ['id', 'report', 'media_type', 'file', 'uploaded_at']
