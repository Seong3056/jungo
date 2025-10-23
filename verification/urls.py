from django.urls import path
from .views import request_verification
urlpatterns = [ path('request/', request_verification) ]
