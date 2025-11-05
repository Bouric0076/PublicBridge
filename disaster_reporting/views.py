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
        geotagged_report = serializer.save(user=self.request.user)

        # Prepare WebSocket data
        report_data = {
            "id": geotagged_report.id,
            "category": geotagged_report.category,
            "status": geotagged_report.status,
            "latitude": geotagged_report.latitude,
            "longitude": geotagged_report.longitude,
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
        return super().update(request, *args, **kwargs)


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
