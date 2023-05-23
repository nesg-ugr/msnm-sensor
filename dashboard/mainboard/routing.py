from django.urls import re_path
from mainboard import consumer

websocket_urlpatterns = [
    re_path(r'ws/monitoring/', consumer.SensorConsumer.as_asgi()),
]