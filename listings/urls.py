
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ListingListView,
    ListingCreateView,
    ListingDetailView,
    ListingViewSet,
)

app_name = "listings"

router = DefaultRouter()
router.register(r'api', ListingViewSet, basename='listings')

# router.urls는 lazy property → 여기서 리스트로 확정
api_urlpatterns = list(router.urls)

urlpatterns = [
    # HTML 페이지
    path("", ListingListView.as_view(), name="listing_list"),
    path("new/", ListingCreateView.as_view(), name="listing_create"),
    path("<int:pk>/", ListingDetailView.as_view(), name="listing_detail"),

    # API 라우터
    path("", include(api_urlpatterns)),
]
