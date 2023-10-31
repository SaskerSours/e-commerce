import os
import random
import uuid

import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, FormView, TemplateView
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib import messages

from .filters import filter_products_by_color_and_size
from .forms import CommentsForm, ReplyForm, CheckoutForm, CouponForm, PaymentForm, OrderProductForm
from .models import Product, ProductImages, User, Wishlist, Blog, BlogCategories, Comments, Color, \
    Size, ComparedProduct, OrderProduct, Order, Address, Payment


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


# def filter_by_date_created():
#     filtered_products = Product.objects.order_by('-date_created')
#     return filtered_products


# class ProductListView(ListView):
#     template_name = 'index3.html'
#     model = Product
#     context_object_name = 'products'
#     filterset_class = ProductFilter2


class ProductListView(ListView):
    model = Product
    template_name = 'index3.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Основний запит до бази даних з врахуванням пов'язаних даних (prefetch_related)
        queryset = Product.objects.all().prefetch_related('productimages_set', 'reviews')
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        latest = self.request.GET.get('latest')
        base_queryset = Product.objects.all().prefetch_related('productimages_set')

        if latest == 'apply_filter':
            base_queryset = base_queryset.order_by('-date_created')

        elif latest == 'apply_filter_price':
            base_queryset = base_queryset.order_by('price')

        elif latest == 'apply_filter_discount':
            base_queryset = base_queryset.order_by('discount_price')

        context['products_discount'] = base_queryset.filter(discount_price__isnull=False).distinct()
        context['products'] = base_queryset

        return context


class ProductDetailView(View):
    template_name = 'product-details.html'

    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        product = Product.objects.get(slug=slug)
        queryset = Product.objects.all().prefetch_related('productimages_set').distinct()
        context = {
            'product': product,
            'products_image': queryset
        }
        return render(request, self.template_name, context)


class Canvas(ListView):
    template_name = 'off-canvas-left.html'
    model = Product
    context_object_name = 'products'
    paginate_by = 3

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products_colors'] = Color.objects.all()
        context['products_sizes'] = Size.objects.all()
        context['selected_price'] = self.request.GET.get('selected_price')

        return context

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related('productimages_set')
        color_name = self.request.GET.get('color')
        size_name = self.request.GET.get('size')
        selected_price = self.request.GET.get('selected_price')  # Получаем выбранную цену из запроса

        if color_name or size_name or selected_price:
            queryset = filter_products_by_color_and_size(queryset, color_name, size_name)

            if selected_price:
                queryset = queryset.filter(price__gt=selected_price)

        return queryset


class WishListUser(View):
    template_name = 'wishlist.html'

    def get(self, request, *args, **kwargs):
        wishlist = Wishlist.objects.filter(user=self.request.user)
        context = {
            'products': wishlist
        }
        return render(request, self.template_name, context)


@login_required
def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist_by_username')


@login_required
def delete_wish_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        wish = Wishlist.objects.get(user=request.user, product=product)
        wish.delete()
    except Wishlist.DoesNotExist:
        pass
    return redirect('wishlist_by_username')


class BlogList(ListView):
    template_name = 'blog-list.html'
    model = Blog
    context_object_name = 'blogs'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_categories'] = BlogCategories.objects.all()
        context['blog_last'] = self.get_queryset().order_by('-pub_date')[:2]
        return context

    def get_queryset(self):
        queryset = Blog.objects.all()
        return queryset


def reply_to_comment(request, pk):
    commentik = get_object_or_404(Comments, pk=pk)
    blog = commentik.blog  # Access the related Blog object

    if request.method == 'POST':
        reply_form = ReplyForm(request.POST)
        if reply_form.is_valid():
            author = request.user
            comment = reply_form.save(commit=False)
            comment.comment = commentik
            comment.author = author
            comment.save()

            return redirect('blog-detail', pk=blog.pk)  # Redirect to the related blog's detail page

    return redirect('blog-detail', pk=blog.pk)


class BlogDetail(DetailView, FormView):
    form_class = CommentsForm
    template_name = 'blog-details.html'
    model = Blog
    paginate_by = 3

    def form_valid(self, form):
        blog = self.get_object()
        author = self.request.user

        comment = form.save(commit=False)
        comment.blog = blog
        comment.author = author
        comment.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_categories'] = BlogCategories.objects.all()
        context['blog'] = self.get_object()
        context['blog_last'] = self.get_queryset().order_by('-pub_date')[:2]

        all_comments = Comments.objects.filter(blog=self.get_object()).prefetch_related('replies')

        paginator = Paginator(all_comments, self.paginate_by)
        page = self.request.GET.get('page')
        comments = paginator.get_page(page)

        context['comments'] = comments
        return context

    def get_success_url(self):
        # Use the reverse function to generate the success URL
        blog_pk = self.kwargs['pk']  # Get the 'pk' from the URL
        return redirect('blog-detail', kwargs={'pk': blog_pk})


class BlogCategoriesList(ListView):
    template_name = 'blog_category-list.html'
    model = Blog
    context_object_name = 'blogs'

    def get_queryset(self):
        slug = self.kwargs['slug']
        blog_by_categories = get_object_or_404(BlogCategories, slug=slug)
        return Blog.objects.filter(category=blog_by_categories)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog_last'] = self.get_queryset().order_by('-pub_date')[:2]
        context['blog_categories'] = BlogCategories.objects.all()
        return context


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_to_cart(request, slug):
    item = get_object_or_404(Product, slug=slug)
    order_item, created = OrderProduct.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect('cart_page')
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect('cart_page')
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect('cart_page')


def remove_from_cart(request, slug):
    item = get_object_or_404(Product, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderProduct.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect('cart_page')
        else:
            messages.info(request, "This item was not in your cart")
            return redirect('product', slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect('product', slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Product, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderProduct.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect('cart_page')
        else:
            messages.info(request, "This item was not in your cart")
            return redirect('product_detail', slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect('product_detail', slug=slug)


class CartPage(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            context = {
                'object': order,
            }
            return render(self.request, 'cart_page.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout_page.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_first_name = form.cleaned_data.get(
                        'shipping_first_name')
                    shipping_last_name = form.cleaned_data.get(
                        'shipping_last_name')
                    shipping_email = form.cleaned_data.get(
                        'shipping_email')
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_first_name, shipping_last_name, shipping_email, shipping_address1,
                                      shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            first_name=shipping_first_name,
                            last_name=shipping_last_name,
                            email=shipping_email,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")
                        return redirect('checkout')

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_first_name = form.cleaned_data.get(
                        'billing_first_name')
                    billing_last_name = form.cleaned_data.get(
                        'billing_last_name')
                    billing_email = form.cleaned_data.get(
                        'billing_email')
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form(
                            [billing_first_name, billing_last_name, billing_email, billing_address1, billing_country,
                             billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            first_name=billing_first_name,
                            last_name=billing_last_name,
                            email=billing_email,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('payment')
                elif payment_option == 'P':
                    return redirect('payment')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("cart_page")


def add_compare_product(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
    except ObjectDoesNotExist:
        return messages.warning(request, 'Product not found sorry for the inconvenience')

    compared_product, created = ComparedProduct.objects.get_or_create(user=request.user)

    if not compared_product.product_1:
        compared_product.product_1 = product
        compared_product.save()
    elif not compared_product.product_2:
        compared_product.product_2 = product
        compared_product.save()
        messages.info('Product added to compare')
    return redirect('compare')


def remove_compare_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    try:
        compared_product = ComparedProduct.objects.get(product_1=product)
        compared_product.product_1 = None
        compared_product.save()

        messages.info(request, 'Product removed from compare')
        return redirect('compare')
    except ComparedProduct.DoesNotExist:
        try:
            compared_product = ComparedProduct.objects.get(product_2=product)
            compared_product.product_2 = None
            compared_product.save()

            messages.info(request, 'Product removed from compare')
            return redirect('compare')
        except ComparedProduct.DoesNotExist:
            messages.warning(request, 'Product not found in compare')
            return redirect('compare')


class ComparePage(View):
    def get(self, *args, **kwargs):
        try:
            compared_product = ComparedProduct.objects.get(user=self.request.user)
            context = {
                'compares': compared_product,
            }
            return render(self.request, 'compare.html', context)
        except ComparedProduct.DoesNotExist:
            return render(self.request, 'compare.html')


def payment_process(request):
    try:
        order = Order.objects.get(user=request.user)
        host = request.get_host()
        total_amount = order.get_total()
        custom_payment_id = str(uuid.uuid4().hex)
        paypal_dict = {
            'business': os.getenv("PAYPAL_RECEIVER_EMAIL"),
            'amount': str(total_amount),
            'item_name': f'Order-Item-No-{order.pk}',
            'invoice': f'{custom_payment_id}',
            'currency_code': 'USD',
            'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
            'return_url': 'http://{}{}'.format(host, reverse('payment_done')),
            'cancel_return': 'http://{}{}'.format(host, reverse('payment_canceled')),
        }
        payment = Payment()
        payment.user = request.user
        payment.amount = total_amount
        payment.payment_id = custom_payment_id
        payment.save()
        order.payment = payment
        order.save()
        form = PayPalPaymentsForm(initial=paypal_dict)
        return render(request, 'core/payment_process.html',
                      {'form': form, 'total_amount': total_amount})
    except ObjectDoesNotExist:
        messages.warning(
            request, "You have not a order to pay")
    return redirect("checkout")


class OrderConfirmationView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order_qs = Order.objects.filter(user=self.request.user, ordered=True)
        order = order_qs[0]
        products = order.items.all().prefetch_related('item').all()
        contex = {
            'order': order,
            'products': products,
        }
        return render(self.request, 'order-confirmation.html', contex)


def create_order_product(request, slug):
    if request.method == 'POST':
        # If the form is submitted, process the data
        form = OrderProductForm(request.POST)
        if form.is_valid():
            product = Product.objects.get(slug=slug)
            form.item = product
            # Form data is valid, save the instance

            order_product = form.save()
            # Optionally, redirect to a success page or perform further actions
            return redirect('success_url_name')  # Replace 'success_url_name' with your actual URL name
    else:
        # If it's a GET request, create a blank form
        form = OrderProductForm()

    return render(request, 'test.html', {'form': form})
