from django import forms

class ShareForm(forms.Form):
    subject   = forms.CharField(required=False, max_length=100)
    message   = forms.CharField(required=False, widget=forms.Textarea)
    recipient = forms.EmailField()
