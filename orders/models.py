from django.db import models
from django.contrib.auth import get_user_model
from listings.models import Listing
User = get_user_model()

class Order(models.Model):
    class EscrowState(models.TextChoices):
        HELD = 'HELD','보관중'
        RELEASED = 'RELEASED','지급완료'
        REFUNDED = 'REFUNDED','환불완료'
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name='orders')
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    amount = models.PositiveIntegerField()
    escrow_state = models.CharField(max_length=16, choices=EscrowState.choices, default=EscrowState.HELD)
    confirmation_code = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
