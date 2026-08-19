# Django Stripe Checkout Payments

A simple Django project with Stripe Checkout and Payment Intent payment flows.

![Project preview](doc/preview.png)

## Features

- User registration and login.
- Product and price listing.
- Stripe Checkout integration.
- Custom payment flow with Payment Intent.
- Stripe webhook endpoint.
- Django admin panel.  

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root rename env_example to .env 

Run the migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open:

- App: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Custom payment: `http://127.0.0.1:8000/custom-payment/`
- Webhook Stripe: `http://127.0.0.1:8000/webhooks/stripe/`

## Stripe

Configure the Stripe keys in `core/settings.py` or adapt the project to read them from `.env`:

```python
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."
```

To test webhooks locally, use the Stripe CLI:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe/
``` 