from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import secrets

from .models import ChatRoom, Message
from listings.models import Listing
from orders.models import Order

@login_required
def chat_view(request, room_id):
    """특정 채팅방의 메시지 불러오기 + 전송 처리"""
    room = get_object_or_404(ChatRoom, id=room_id)

    # 권한 확인 (판매자/구매자만 접근 가능)
    if request.user not in [room.buyer, room.seller]:
        return redirect('/')

    # 메시지 목록 불러오기
    messages = Message.objects.filter(room=room).order_by("timestamp")

    # 메시지 전송
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            msg = Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                timestamp=timezone.now()
            )
            room.updated_at = timezone.now()
            room.save()
            # If request is AJAX, return JSON to allow client to append message without full reload
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': msg.id,
                    'content': msg.content,
                    'sender': request.user.username,
                    'timestamp': msg.timestamp.strftime('%y.%m.%d %H:%M')
                }, status=201)
            return redirect('chat:chat_room', room_id=room_id)

    current_order = Order.objects.filter(
        listing=room.listing,
        buyer=room.buyer
    ).order_by("-created_at").first()

    if current_order and current_order.escrow_state == Order.EscrowState.RELEASED and not current_order.confirmation_code:
        current_order.confirmation_code = f"{secrets.randbelow(10000):04d}"
        current_order.save(update_fields=["confirmation_code"])

    return render(request, "chat/chat_room.html", {
        "room": room,
        "messages": messages,
        "listing": room.listing,
        "other_user": room.other_user(request.user),
        "order": current_order,
    })

@login_required
def chat_room_create(request, listing_id):
    """상품 상세 페이지 → 대화 시작 버튼 클릭 시 채팅방 생성/이동"""
    listing = get_object_or_404(Listing, id=listing_id)
    buyer = request.user
    seller = listing.seller

    room, created = ChatRoom.objects.get_or_create(
        listing=listing,
        buyer=buyer,
        seller=seller
    )

    return redirect("chat:chat_room", room_id=room.id)
