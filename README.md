# Stripe Subscription

Stripe Subscription is a sample project that lets users subscribe with stripe.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install requirements.txt
```
also install strip-cli (https://stripe.com/docs/stripe-cli#install)

## Usage

- Configure .env (existing keys can be reused except for STRIPE_ENDPOINT_SECRET)

Run from terminal:
```python
python manage.py makemigrations
python manage.py makemigrations subscription
python manage.py migrate
```

On a separate terminal run:
stripe listen --forward-to27.0.0.1:8000/subscriptions/webhook/
You will get ```Ready! Your webhook signing secret is whsec_secret_key```

- Replace STRIPE_ENDPOINT_SECRET with the above secret key

Then run ```python manage.py runserver```