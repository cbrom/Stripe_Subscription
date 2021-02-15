from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import stripe
from .models import Subscription
from datetime import datetime
from django.contrib.auth.models import User


@login_required
def home(request):
    """
    Home url: tries to get user subscription and populate it to index.html
    Subscription trial end date is set on subscription.trial_end

    Parameters
    ----------
    request: HttpRequest
        The request from stripe server
    """
    try:
        stripe_customer = Subscription.objects.get(user=request.user)
        print(stripe_customer.status)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        subscription = stripe.Subscription.retrieve(
            stripe_customer.stripeSubscriptionId
            )
        subscription.trial_end = datetime.utcfromtimestamp(
            subscription.trial_end
            ).strftime('%Y-%m-%d')
        print(subscription.status)
        product = stripe.Product.retrieve(subscription.plan.product)

        return render(request, 'index.html', {
            'subscription': subscription,
            'product': product,
        })
    except Subscription.DoesNotExist:
        return render(request, 'index.html')
    # template = loader.get_template('index.html')
    # context = {}
    # return HttpResponse(template.render(context, request))


@csrf_exempt
def stripe_config(request):
    """
    Returns stripe public key from settings.

    Parameters
    ----------
    request: HttpRequest
        The request from stripe server

    Returns
    -------
    JsonResponse(stripe_config)
    """
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config)


@login_required
def cancel_subscription(request):
    """
    A url where subscription is cancelled.
    An existing Subscription is fetched and modified to be canceled (status)

    Method: POST
    Parameters
    ----------
    request: HttpRequest
        The request from stripe server
    """
    if request.method == 'POST':
        try:
            stripe_customer = Subscription.objects.get(user=request.user)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            subscription = stripe.Subscription.retrieve(
                stripe_customer.stripeSubscriptionId)
            product = stripe.Product.retrieve(subscription.plan.product)
            stripe.Subscription.delete(subscription.id)
            stripe_customer.status = 'canceled'
            stripe_customer.save()

            return render(request, 'index.html', {
                'subscription': subscription,
                'product': product,
            })
        except Subscription.DoesNotExist:
            return render(request, 'index.html')


@csrf_exempt
@login_required
def create_checkout_session(request):
    """
    A url where checkout session is prepared.
    A stripe session with specified parameters and trial period of 7 days is
    created and returned in JSON format.

    Parameters
    ----------
    request: HttpRequest
        The request from client

    Returns
    -------
    JsonResponse(checkout_session)
    """
    if request.method == 'GET':
        domain_url = 'http://127.0.0.1:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id
                if request.user.is_authenticated else None,
                success_url=domain_url
                + 'subscriptions/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'subscriptions/cancel/',
                payment_method_types=['card'],
                mode='subscription',
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    }
                ],
                subscription_data={
                        'trial_period_days': 7,
                },
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


@login_required
def success(request):
    """
    A url where successful stripe request is redirected to.

    Parameters
    ----------
    request: HttpRequest
        The request from stripe server
    """
    return render(request, 'success.html')


@login_required
def cancel(request):
    """
    A url where cancelled stripe request is redirected to.

    Parameters
    ----------
    request: HttpRequest
        The request from stripe server
    """
    return render(request, 'cancel.html')


@csrf_exempt
def stripe_webhook(request):
    """
    Actively listens for webhook activities(session.completed) on stripe
    product.
    Upon completed, a new Subscription record is created or an existing one
    is modified accordingly.

    Parameters
    ----------
    request: HttpRequest
        The request from stripe server

    Returns
    -------
    HttpResponse
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Fetch all the required data from session
        client_reference_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        stripe_subscription_id = session.get('subscription')

        # Get the user and create a new StripeCustomer
        user = User.objects.get(id=client_reference_id)

        try:

            stripe_customer = Subscription.objects.get(user=user)
            print(stripe_customer)
            stripe_customer.status = "subscribed"
            stripe_customer.stripeCustomerId = stripe_customer_id
            stripe_customer.stripeSubscriptionId = stripe_subscription_id
            stripe_customer.save()

        except Subscription.DoesNotExist as e:
            print("***creating***")
            Subscription.objects.create(
                user=user,
                status="subscribed",
                stripeCustomerId=stripe_customer_id,
                stripeSubscriptionId=stripe_subscription_id,
            )
        except Exception as e:
            print(e)

    return HttpResponse(status=200)
