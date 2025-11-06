from django import forms
from django.forms.widgets import FileInput
from .models import Listing

class SingleImageInput(FileInput):
    allow_multiple_selected = False

class ListingForm(forms.ModelForm):
    image = forms.ImageField(
        required=True,
        widget=SingleImageInput(attrs={'accept': 'image/*'}),
        help_text='이미지 1장 업로드'
    )
    class Meta:
        model = Listing
        fields = ['title','price','description','status','image']
