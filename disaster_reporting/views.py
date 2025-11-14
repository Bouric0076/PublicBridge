from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DisasterReport, DisasterAgency
from .serializers import DisasterReportSerializer, DisasterAgencySerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


@login_required
def live_alerts(request):
    """Render the disaster reporting page with a map and form."""
    return render(request, 'disaster_reporting/report_form.html')


### ✅ API to List and Create Disaster Reports ###
class DisasterReportListCreateView(generics.ListCreateAPIView):
    queryset = DisasterReport.objects.all()
    serializer_class = DisasterReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Auto-assign user and broadcast new reports via WebSockets."""
        # Anonymous toggle
        is_anonymous = self.request.data.get('is_anonymous') in ['true', 'True', True]
        severity = self.request.data.get('severity') or 'medium'

        geotagged_report = serializer.save(user=self.request.user, is_anonymous=is_anonymous, severity=severity)

        # AI-assisted enrichment (optional)
        try:
            from ai_agents.groq_classifier import GroqClassifierAgent
            classifier = GroqClassifierAgent()
            cls = classifier.classify_report(geotagged_report.description)
            if geotagged_report.category == 'other' and cls.get('category'):
                geotagged_report.category = cls['category']
            urgency = cls.get('urgency_level', '').lower()
            if urgency in ['low','medium','high','critical']:
                geotagged_report.severity = urgency
            geotagged_report.save()
        except Exception:
            pass

        # Handle multiple media files
        media_files = self.request.FILES.getlist('media')
        from .models import DisasterMedia
        for f in media_files:
            media_type = 'video' if getattr(f, 'content_type', '').startswith('video/') else 'image'
            DisasterMedia.objects.create(report=geotagged_report, media_type=media_type, file=f)

        # Prepare WebSocket data
        report_data = {
            "id": geotagged_report.id,
            "category": geotagged_report.category,
            "status": geotagged_report.status,
            "latitude": geotagged_report.latitude,
            "longitude": geotagged_report.longitude,
            "severity": geotagged_report.severity,
            "tracking_code": geotagged_report.tracking_code,
        }

        # Send to WebSocket group
        channel_layer = get_channel_layer()
        if channel_layer is not None:  # Safety check to prevent runtime crash if layer misconfigured
            async_to_sync(channel_layer.group_send)(
                "disaster_reports",
                {
                    "type": "send_report_update",
                    "report": report_data
                }
            )


### ✅ API to Retrieve, Update, and Partially Update a Report ###
class DisasterReportDetailView(generics.RetrieveUpdateAPIView):
    queryset = DisasterReport.objects.all()
    serializer_class = DisasterReportSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        """Allow partial updates (PATCH-style behavior)."""
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        try:
            # Broadcast status updates
            instance = self.get_object()
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                async_to_sync(channel_layer.group_send)(
                    "disaster_reports",
                    {
                        "type": "send_report_update",
                        "report": {
                            "id": instance.id,
                            "category": instance.category,
                            "status": instance.status,
                            "latitude": instance.latitude,
                            "longitude": instance.longitude,
                            "severity": instance.severity,
                            "tracking_code": instance.tracking_code,
                        }
                    }
                )
        except Exception:
            pass
        return response


### ✅ API to Mark a Report as 'Invalid' ###
class MarkReportInvalidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = DisasterReport.objects.get(pk=pk)
            report.status = "invalid"
            report.save()
            return Response({"message": "Report marked as invalid."}, status=status.HTTP_200_OK)
        except DisasterReport.DoesNotExist:
            return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)


### ✅ API to Archive a Report ###
class ArchiveReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = DisasterReport.objects.get(pk=pk)
            report.archive()
            return Response({"message": "Report archived successfully."}, status=status.HTTP_200_OK)
        except DisasterReport.DoesNotExist:
            return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)


### ✅ API to List All Disaster Agencies ###
class DisasterAgencyListView(generics.ListAPIView):
    queryset = DisasterAgency.objects.all()
    serializer_class = DisasterAgencySerializer
    permission_classes = [IsAuthenticated]
