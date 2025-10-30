from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ChatRoom, Message
from listings.models import Listing

@login_required
def chat_view(request, chat_id):
    """특정 채팅방의 메시지 불러오기 + 전송 처리"""
    room = get_object_or_404(ChatRoom, id=chat_id)

    # 권한 확인 (판매자/구매자만 접근 가능)
    if request.user not in [room.buyer, room.seller]:
        return redirect('/')

    # 메시지 목록 불러오기
    messages = Message.objects.filter(room=room).order_by("timestamp")

    # 메시지 전송
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                timestamp=timezone.now()
            )
            room.updated_at = timezone.now()
            room.save()
            return redirect('chat_room', chat_id=chat_id)

    return render(request, "chat/chat_room.html", {
        "room": room,
        "messages": messages,
        "listing": room.listing,
        "other_user": room.other_user(request.user),
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
