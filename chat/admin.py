from django.contrib import admin
from .models import Message, ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "buyer", "seller", "created_at")
    search_fields = ("listing__title", "buyer__username", "seller__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "content", "timestamp")
    search_fields = ("room__listing__title", "sender__username", "content")
    list_filter = ("timestamp",)
