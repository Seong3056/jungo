from rest_framework import serializers
from .models import Order
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id','listing','buyer','amount','escrow_state','created_at']
        read_only_fields = ['buyer','created_at','escrow_state']
