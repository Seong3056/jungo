from django.urls import path
from .views import chat_list_view, chat_view

urlpatterns = [
    path("", chat_list_view, name="chat_list"),
    path("<int:listing_id>/", chat_view, name="chat_room"),
]
