
from django.urls import path
from .views import chat_view

urlpatterns = [
    path("<int:listing_id>/", chat_view, name="chat_room"),
]
