from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from listings.models import Listing
from .models import ChatRoom, Message
from .forms import MessageForm
from django.db import models


@login_required
def chat_view(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    buyer = request.user
    seller = listing.seller

    # ✅ 동일 상품+구매자 조합으로 방을 찾거나 새로 생성
    room, created = ChatRoom.objects.get_or_create(
        listing=listing, buyer=buyer, seller=seller
    )

    messages = room.messages.all().order_by("timestamp")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                room=room,
                sender=request.user,
                content=form.cleaned_data["message"],
            )
            return redirect("chat_room", listing_id=listing.id)
    else:
        form = MessageForm()

    return render(request, "chat/chat_room.html", {
        "listing": listing,
        "room": room,
        "messages": messages,
        "form": form,
        "seller": seller,
    })
    
@login_required
def chat_list_view(request):
    user = request.user
    # ✅ 내가 buyer거나 seller인 채팅방만 표시
    rooms = ChatRoom.objects.filter(models.Q(buyer=user) | models.Q(seller=user)).order_by("-created_at")

    return render(request, "chat/chat_list.html", {"rooms": rooms, "user": user})
