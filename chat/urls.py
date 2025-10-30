from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    #path("", views.chat_list_view, name="chat_list"),
    path("create/<int:listing_id>/", views.chat_room_create, name="chat_room_create"),  # ✅
    path("<int:room_id>/", views.chat_view, name="chat_room"),  # ✅
]
