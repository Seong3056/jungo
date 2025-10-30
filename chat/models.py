from django.db import models
from django.conf import settings
from listings.models import Listing

class ChatRoom(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_rooms")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("listing", "buyer")  # ✅ 상품 + 구매자 조합은 1개만
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.listing.title} - {self.buyer.username} ↔ {self.seller.username}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_msgs")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

    def save(self, *args, **kwargs):
        # 알림 생성 로직 제거: 기본 동작만 수행
        super().save(*args, **kwargs)
