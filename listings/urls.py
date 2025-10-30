from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ListingListView,
    ListingCreateView,
    ListingDetailView,
    ListingViewSet,
)

app_name = "listings"

# ✅ DRF 라우터 (API용)
router = DefaultRouter()
router.register(r'api', ListingViewSet)

urlpatterns = [
    # HTML 페이지용
    path("", ListingListView.as_view(), name="listing_list"),
    path("new/", ListingCreateView.as_view(), name="listing_create"),
    path("<int:pk>/", ListingDetailView.as_view(), name="listing_detail"),

    # ✅ API용 라우터 연결
    path("", include(router.urls)),
]
