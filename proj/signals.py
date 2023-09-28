from django.dispatch import receiver
from paypal.standard.ipn.signals import valid_ipn_received

from .models import Order, Payment


@receiver(valid_ipn_received)
def valid_ipn_signal(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == 'Completed':
        print('valid')
        # payment was successful
        payment = Payment.objects.get(payment_id=ipn_obj.invoice)

        # Associate the payment with the order
        order = Order.objects.get(payment=payment)
        order.items.update(ordered=True)
        order.ordered = True
        order.save()


# @receiver(valid_ipn_received)
# def invalid_ipn_signal(sender, **kwargs):
#     ipn_obj = sender
#     if ipn_obj.payment_status == 'Completed':
#         print('invalid')
#         payment = Payment.objects.get(payment_id=ipn_obj.invoice)
#
#         # Associate the payment with the order
#         payment.delete()

