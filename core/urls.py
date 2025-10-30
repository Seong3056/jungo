from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import HomeView

urlpatterns = [
    path('chat/', include('chat.urls')),
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('listings/', include('listings.html_urls')),
    path('accounts/', include('users.urls')),
    path('api/listings/', include('listings.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/verify/', include('verification.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
