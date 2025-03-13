import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import DisasterReport
from asgiref.sync import sync_to_async

class DisasterReportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connects WebSocket client to the 'disaster_reports' group."""
        await self.channel_layer.group_add("disaster_reports", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Removes WebSocket client from the 'disaster_reports' group."""
        await self.channel_layer.group_discard("disaster_reports", self.channel_name)

    async def receive(self, text_data):
        """Handles messages received from WebSocket (optional)."""
        data = json.loads(text_data)
        action = data.get("action")

        if action == "fetch_reports":
            reports = await self.get_reports()
            await self.send(text_data=json.dumps({"reports": reports}))

    async def send_report_update(self, event):
        """Sends new reports to all WebSocket clients in the group."""
        report_data = event["report"]
        await self.send(text_data=json.dumps({"new_report": report_data}))

    @sync_to_async
    def get_reports(self):
        """Fetches recent reports for WebSocket clients."""
        reports = DisasterReport.objects.filter(status="pending").order_by("-created_at")[:10]
        return [
            {"id": r.id, "category": r.category, "status": r.status, "latitude": r.latitude, "longitude": r.longitude}
            for r in reports
        ]
