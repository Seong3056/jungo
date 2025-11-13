# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Listing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', '판매중'
        RESERVED = 'RESERVED', '예약중'
        SOLD = 'SOLD', '판매완료'

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=120)
    description = models.TextField()
    price = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    # 대표 이미지 (기존 필드)
    image = models.ImageField(upload_to='listing/', blank=False)

    # ⭐ 라즈베리파이 카메라 촬영 이미지
    capture_image = models.ImageField(upload_to='captured/', null=True, blank=True)

    # ⭐ 당근마켓 기준 중고 최저가 (AI used_price 배열의 최저값)
    used_low_price = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
