
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from listings.models import Listing
from .models import Message
from .forms import MessageForm

@login_required
def chat_view(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    seller = listing.seller
    partner = seller  # 판매자와 1:1

    # 두 사람 간 해당 상품 메시지
    msgs = Message.objects.filter(
        listing=listing,
        sender__in=[request.user, partner],
        receiver__in=[request.user, partner],
    ).order_by("timestamp")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data["message"].strip()
            if content:
                Message.objects.create(
                    listing=listing,
                    sender=request.user,
                    receiver=partner if request.user != partner else request.user,
                    content=content,
                )
        return redirect("chat_room", listing_id=listing.id)
    else:
        form = MessageForm()

    return render(request, "chat/chat_room.html", {
        "listing": listing,
        "partner": partner,
        "messages": msgs,
        "form": form,
    })
