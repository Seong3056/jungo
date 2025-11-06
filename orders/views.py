import secrets

from django.db.models import Q
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.all().order_by('-created_at')
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.filter(Q(buyer=user) | Q(listing__seller=user))
        else:
            queryset = queryset.none()

        listing_id = self.request.query_params.get('listing')
        buyer_id = self.request.query_params.get('buyer')
        seller_id = self.request.query_params.get('seller')

        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        if buyer_id:
            queryset = queryset.filter(buyer_id=buyer_id)
        if seller_id:
            queryset = queryset.filter(listing__seller_id=seller_id)

        return queryset

    def perform_create(self, serializer):
        listing = serializer.validated_data.get('listing')
        if listing.seller == self.request.user:
            raise serializers.ValidationError({'detail': '본인 물품은 구매할 수 없습니다.'})
        serializer.save(buyer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if request.user != order.listing.seller:
            return Response({'detail': '판매자만 구매확정할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        if order.escrow_state == Order.EscrowState.RELEASED:
            return Response({'detail': '이미 구매확정이 완료되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        order.escrow_state = Order.EscrowState.RELEASED
        if not order.confirmation_code:
            order.confirmation_code = f"{secrets.randbelow(10000):04d}"
        order.save(update_fields=['escrow_state', 'confirmation_code'])
        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)
