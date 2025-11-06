
from django import forms
class MessageForm(forms.Form):
    message = forms.CharField(
        label="", max_length=2000,
        widget=forms.TextInput(attrs={"placeholder":"메시지를 입력하세요...", "class":"input", "autocomplete":"off"})
    )
