import json
import stripe
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from .models import *

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.mail import send_mail

# Create your views here.
def home(request):
    prices = Price.objects.all()
    return render(request, 'home.html', {'prices':prices})



def create_checkout_session(request, id):
    domain_url = 'http://localhost:8000/'
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if request.method == 'POST':
        price = Price.objects.get(id=id)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price.stripe_price_id,
                    'quantity': 1,
                },
            ],
            metadata={
                "product_id": price.product.id
            },
            mode='payment',
            success_url=domain_url + 'success/',
            cancel_url=domain_url + 'cancel/',
        )
        return redirect(checkout_session.url)
        
        
        
        
def success_view(request):
    return render(request, 'success.html')

def cancelled_view(request):
    return render(request, 'cancelled.html')
 
 
@csrf_exempt
def stripe_webhook(request):
    endpoint_secret = 'whsec_EMYnmvp0tr7mRgUNCTJuk5z8q9cB8ikz'
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']
    elif event['type'] == 'checkout.session.async_payment_succeeded':
        session = event['data']['object']
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
    elif event['type'] == 'payment_intent.created':
        payment_intent = event['data']['object']
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        stripe_customer_id = payment_intent["customer"]
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)
        customer_email = stripe_customer['email']
        print(stripe_customer_id)
        print(stripe_customer)
        print(customer_email) 
    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return HttpResponse(status=200)

 


## custom payment
def stripe_intent_view(request, id):
    try:
        req_json = json.loads(request.body)
        customer = stripe.Customer.create(email=req_json['email'])
        price = Price.objects.get(id=id)
        intent = stripe.PaymentIntent.create(
            amount=price.price,
            currency='usd',
            customer=customer['id'],
            metadata={
                "price_id": price.id
            }
        )
        return JsonResponse({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})



 
def custom_payment_view(request):
    prices = Price.objects.all()
    context = {
        'prices':prices,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLISHABLE_KEY
    }
    return render(request, 'custom_payment.html', context)