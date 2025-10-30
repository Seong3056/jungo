from django.db import models
from django.contrib.auth.models import User
from listings.models import Listing


class ChatRoom(models.Model):
    """하나의 상품(listing)에 대해 구매자와 판매자가 대화하는 채팅방"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="chat_rooms")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buyer_rooms")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="seller_rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("listing", "buyer", "seller")

    def other_user(self, current_user):
        """현재 로그인한 사용자를 기준으로 상대방 반환"""
        return self.seller if self.buyer == current_user else self.buyer

    def __str__(self):
        return f"{self.listing.title} ({self.buyer.username} ↔ {self.seller.username})"


class Message(models.Model):
    """채팅 메시지"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.sender.username}] {self.content[:25]}"
