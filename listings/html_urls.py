from django.urls import path
from .views import ListingListView, ListingCreateView, ListingDetailView
urlpatterns = [
    path('', ListingListView.as_view(), name='listing_list'),
    path('new/', ListingCreateView.as_view(), name='listing_create'),
    path('<int:pk>/', ListingDetailView.as_view(), name='listing_detail'),
]
