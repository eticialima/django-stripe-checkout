import json
import stripe
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import CheckoutPayment, Price, Product


PAID_STATUSES = ("paid", "succeeded")


def stripe_created_date(timestamp):
    return timezone.datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone()).date()

def home(request):
    prices = Price.objects.all()
    return render(request, 'home.html', {'prices':prices})



@login_required
@require_POST
def create_checkout_session(request, id):
    domain_url = 'http://localhost:8000/'
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    price = get_object_or_404(Price, id=id)
    checkout_session_data = {
        'payment_method_types': ['card'],
        'line_items': [
            {
                'price': price.stripe_price_id,
                'quantity': 1,
            },
        ],
        'metadata': {
            "product_id": price.product.id,
            "user_id": request.user.id,
        },
        'mode': 'payment',
        'success_url': domain_url + 'success/',
        'cancel_url': domain_url + 'cancelled/',
    }
    if request.user.is_authenticated and request.user.email:
        checkout_session_data['customer_email'] = request.user.email

    checkout_session = stripe.checkout.Session.create(**checkout_session_data)
    return redirect(checkout_session.url)
        
        
        
        
def success_view(request):
    return render(request, 'success.html')

def cancelled_view(request):
    return render(request, 'cancelled.html')


@login_required
def purchases_view(request):
    payments = CheckoutPayment.objects.filter(
        user=request.user,
        payment_status__in=PAID_STATUSES,
    ).select_related('product').order_by('-dt_created')
    return render(request, 'purchases.html', {'payments': payments})
 
 
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

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session["metadata"]["user_id"]
        product_id = session["metadata"]["product_id"]
        payment_intent = session["payment_intent"]

        CheckoutPayment.objects.update_or_create(
            payment_intent=payment_intent,
            defaults={
                "user": User.objects.get(id=user_id),
                "product": Product.objects.get(id=product_id),
                "payment_status": session["payment_status"],
                "dt_created": stripe_created_date(session["created"]),
            },
        )
        
    elif event['type'] == 'payment_intent.created':
        pass
        
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent['id']
        check = CheckoutPayment.objects.filter(payment_intent=payment_intent_id).first()

        if check:
            check.payment_status = "succeeded"
            check.dt_created = stripe_created_date(payment_intent['created'])
            check.save(update_fields=["payment_status", "dt_created"])
        else:
            metadata = payment_intent.get("metadata", {})
            user_id = metadata.get("user_id")
            product_id = metadata.get("product_id")

            if user_id and product_id:
                CheckoutPayment.objects.create(
                    user=User.objects.get(id=user_id),
                    product=Product.objects.get(id=product_id),
                    payment_intent=payment_intent_id,
                    payment_status="succeeded",
                    dt_created=stripe_created_date(payment_intent['created']),
                )

    elif event['type'] == "payment_intent.payment_failed":
        intent = event['data']['object']
        CheckoutPayment.objects.filter(payment_intent=intent['id']).update(payment_status="failed")

    return HttpResponse(status=200)




@login_required
@require_POST
def stripe_intent_view(request, id):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        req_json = json.loads(request.body)
        customer = stripe.Customer.create(email=req_json['email'])
        price = get_object_or_404(Price, id=id)
        intent = stripe.PaymentIntent.create(
            amount=price.price,
            currency='usd',
            customer=customer['id'],
            metadata={
                "price_id": price.id,
                "product_id": price.product.id,
                "user_id": request.user.id,
            }
        )
        return JsonResponse({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})



@login_required
def custom_payment_view(request):
    prices = Price.objects.all()
    context = {
        'prices':prices,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLISHABLE_KEY
    }
    return render(request, 'custom_payment.html', context)
