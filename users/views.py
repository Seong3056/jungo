from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from listings.models import Listing
from chat.models import ChatRoom, Message
from django.db import models
from django.db.models import Prefetch

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'{user.username}님 환영합니다!')
            return redirect('home')
        messages.error(request, '입력값을 확인해주세요.')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '로그인되었습니다.')
            return redirect('home')
        messages.error(request, '아이디/비밀번호를 확인해주세요.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('home')

@login_required
def profile_view(request):
    my_items = Listing.objects.filter(seller=request.user).order_by('-id')
    message_prefetch = Prefetch(
        'messages',
        queryset=Message.objects.select_related('sender').order_by('-timestamp'),
        to_attr='ordered_messages'
    )

    my_chats = ChatRoom.objects.filter(
        models.Q(buyer=request.user) | models.Q(seller=request.user)
    ).select_related('listing', 'buyer', 'seller').prefetch_related(message_prefetch)

    # ✅ 각 채팅방에 other_user_name 속성 추가
    for chat in my_chats:
        chat.other_user_name = chat.seller.username if chat.buyer == request.user else chat.buyer.username
        ordered_messages = getattr(chat, 'ordered_messages', [])
        chat.last_message = ordered_messages[0] if ordered_messages else None

    return render(request, "registration/profile.html", {
        "my_items": my_items,
        "my_chats": my_chats,
    })
