from django.urls import path 
from payments import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('create-checkout-session/<int:id>/', views.create_checkout_session, name='create-checkout-session'),

    path('success/', views.success_view, name='success'),
    path('cancelled/', views.cancelled_view, name='cancelled'),  
    
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),




    ## custom payment
    path('create-payment-intent/<int:id>/', views.stripe_intent_view, name='create-payment-intent'),
    path('custom-payment/', views.custom_payment_view, name='custom-payment')
]