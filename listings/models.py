# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Listing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE','판매중'
        RESERVED = 'RESERVED','예약중'
        SOLD = 'SOLD','판매완료'

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=120)
    description = models.TextField()
    price = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    image = models.ImageField(upload_to='listing/', blank=False)  # 단일 이미지
    created_at = models.DateTimeField(auto_now_add=True)
