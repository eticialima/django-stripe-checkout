import datetime
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
                "product_id": price.product.id,
                "user_id": request.user.id,
            },
            mode='payment',
            success_url=domain_url + 'success/',
            cancel_url=domain_url + 'cancel/',
            customer_email='leticiawebhook1@gamil.com',
        )
        return redirect(checkout_session.url)
        
        
        
        
def success_view(request):
    return render(request, 'success.html')

def cancelled_view(request):
    return render(request, 'cancelled.html')
 
 
@csrf_exempt
def stripe_webhook(request): 
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Checkout (Envia as informações)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session["metadata"]["user_id"]
        product_id = session["metadata"]["product_id"]
        payment_intent = session["payment_intent"] # Codigo transição
        payment_status = session["payment_status"] # Status "Pago" mas não confirmado na plataforma
        dt_created = session["created"] # Data de Registro
        
        print(user_id)  
        print(product_id) 
        print(payment_intent)
        print(payment_status)
        print(dt_created)  
        
        ## TODO: Criar função para registrar log para checkout.
        create = CheckoutPayment.objects.create(
            user=User.objects.get(id=user_id),
            product=Product.objects.get(id=product_id),
            payment_intent=payment_intent,
            payment_status=payment_status,
            dt_created=datetime.datetime.fromtimestamp(dt_created),
        )
        create.save()
        print("save!!!")
        
    # Criação bem-sucedida de um PaymentIntent.
    elif event['type'] == 'payment_intent.created':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        dt_created = payment_intent['created']
        print(payment_intent)
        
    # Após o sucesso do processamento de um PaymentIntent
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        dt_created = payment_intent['created']
        print('Succeeded: ', payment_intent_id) # ex: pi_3MZ0rGCex4srAl3j18kmrdHu
        
        # Retorna o pagamento do cliente
        # TODO: Criar função para atualizar o status do pagamento e liberar acesso para cliente
        check = CheckoutPayment.objects.get(payment_intent=payment_intent_id)
        if check:
            check.payment_status = "succeeded"
            check.dt_created = datetime.datetime.fromtimestamp(dt_created)
            check.save()
        
        
    # Se der algum erro no pagamento
    elif event['type'] == "payment_intent.payment_failed":
        intent = event['data']['object']
        error_message = intent['last_payment_error']['message'] if intent.get('last_payment_error') else None
        print("Failed: ", intent['id']), error_message
        # Notify the customer that payment failed
        
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