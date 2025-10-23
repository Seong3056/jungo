from rest_framework import serializers
from .models import Listing
class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id','seller','title','description','price','status','created_at','image']
        read_only_fields = ['seller','created_at']
