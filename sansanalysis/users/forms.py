from django import forms

class RegistrationForm(forms.Form):
    username  = forms.CharField(max_length=30)
    firstname = forms.CharField(required=False, max_length=30)
    lastname  = forms.CharField(required=False, max_length=30)
    email     = forms.EmailField()
    
    
