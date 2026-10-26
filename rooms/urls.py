from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('create/', views.create_room_view, name='create_room'),
    path('join/', views.join_room_view, name='join_room'),
    path('join/<str:code>/', views.join_room_view, name='join_room_with_code'),
    path('room/<str:code>/', views.room_view, name='room_view'),
    path('room/<str:code>/leave/', views.leave_room_view, name='leave_room'),
]
