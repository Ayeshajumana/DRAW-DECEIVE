from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/room/(?P<room_code>[0-9a-zA-Z]+)/$', consumers.DrawAndDeceiveConsumer.as_asgi()),
]
