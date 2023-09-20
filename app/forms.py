from django import forms

# Create a RegexValidator for first and last names
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

name_validator = RegexValidator(
    r'^[a-zA-Z ]*$',
    'Only alphabetic characters are allowed.'
)

class ContactForm(forms.Form):
    fname = forms.CharField(
        min_length=2,
        max_length=50,
        validators=[name_validator],
        widget=forms.TextInput(attrs={'placeholder': _('First Name')})
    )
    lname = forms.CharField(
        min_length=2,
        max_length=50,
        validators=[name_validator],
        widget=forms.TextInput(attrs={'placeholder': _('Last Name')})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': _('Email')})
    )
    subject = forms.CharField(
        min_length=5,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': _('Subject')})
    )
    message = forms.CharField(
        min_length=10,
        max_length=500,
        widget=forms.Textarea(attrs={'placeholder': _('Write your message'),
                                     'rows': '7'})
    )
