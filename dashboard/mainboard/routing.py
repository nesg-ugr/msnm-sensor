from django.urls import re_path
from mainboard import consumer

websocket_urlpatterns = [
    re_path(r'ws/127.0.0.1:8765', consumer.SensorConsumer.as_asgi()),
]