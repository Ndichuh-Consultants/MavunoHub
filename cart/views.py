import requests
import json
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from .cart import Cart
from .forms import CheckoutForm
from order.utilities import checkout, notify_vendor, notify_customer
from requests.auth import HTTPBasicAuth


# Method to get M-Pesa access token
def get_mpesa_token():
    consumer_key = 'NmAGbMj7mEBbTBGtBhcojfi41kZkpL1cIWuZduAdOIUuATn4'
    consumer_secret = '9xxVDrTy2pRWQXfD03cB49AeYvGEFQ5Vox7SLJmQGGPjv0mWwUvjfBRy98TTSmxe'
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = response.json().get("access_token")
    return access_token


# Method to initiate STK Push
def initiate_stk_push(phone, amount):
    # Ensure amount is a float for JSON serialization
    amount = float(amount)  # Convert Decimal to float if necessary

    access_token = get_mpesa_token()

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}

    request_payload = {
        "BusinessShortCode": "174379",  # Example shortcode for M-Pesa
        "Password": "YourPassword",  # You need to decode or get this from your credentials
        "Timestamp": "20241206000000",  # Update with the actual timestamp
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": "174379",  # Example shortcode
        "PhoneNumber": phone,
        "CallBackURL": "https://sandbox.safaricom.co.ke/mpesa/",
        "AccountReference": "eMobilis",
        "TransactionDesc": "Web Development Charges"
    }

    response = requests.post(api_url, json=request_payload, headers=headers)

    # Handle response as required
    return response.json()


# Modify the cart_detail view to use M-Pesa
def cart_detail(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            amount = cart.get_total_cost()  # Ensure the amount is correct
            response = initiate_stk_push(phone, amount)

            if response.get("ResponseCode") == "0":
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']
                address = form.cleaned_data['address']
                zipcode = form.cleaned_data['zipcode']
                place = form.cleaned_data['place']

                # Create the order and clear the cart
                order = checkout(request, first_name, last_name, email, phone, address, zipcode, place, amount)

                # Clear the cart
                cart.clear()

                # Send Email Notifications
                notify_customer(order)
                notify_vendor(order)

                return redirect('cart:success')
            else:
                messages.error(request, "Payment failed. Please try again.")

    else:
        form = CheckoutForm()

    return render(request, 'cart/cart.html', {'form': form})


def success(request):
    return render(request, 'cart/success.html')
