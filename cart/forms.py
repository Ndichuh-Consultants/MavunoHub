from django import forms

class CheckoutForm(forms.Form):
    phone = forms.CharField(max_length=255, help_text="Enter your phone number for Mpesa payment")
    address = forms.CharField(max_length=255)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount to be paid")
