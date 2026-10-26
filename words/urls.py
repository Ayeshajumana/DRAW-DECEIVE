from django.urls import path
from . import views

urlpatterns = [
    path('', views.word_packs_view, name='word_packs'),
    path('create/', views.create_word_pack, name='create_word_pack'),
]
