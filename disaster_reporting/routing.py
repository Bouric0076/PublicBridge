from django.urls import re_path
from disaster_reporting.consumers import DisasterReportConsumer

websocket_urlpatterns = [
    re_path(r'ws/reports/$', DisasterReportConsumer.as_asgi()),
]
