from django import forms
from django.core.validators import MinValueValidator
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from rest_framework.exceptions import ValidationError

from .models import Comments, Reply

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)


class CommentsForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        return text


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),  # Adjust 'rows' as needed
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        return text


class CheckoutForm(forms.Form):
    shipping_first_name = forms.CharField(required=False)
    shipping_last_name = forms.CharField(required=False)
    shipping_email = forms.EmailField(required=False)
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label="(Select country)").formfield()
    shipping_zip = forms.CharField(required=False)

    billing_first_name = forms.CharField(required=False)
    billing_last_name = forms.CharField(required=False)
    billing_email = forms.EmailField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label="(Select country)").formfield()
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))
