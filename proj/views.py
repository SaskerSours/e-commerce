import random
import uuid

import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, FormView, TemplateView
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib import messages

from .filters import ProductFilter, filter_products_by_color_and_size
from .forms import CommentsForm, ReplyForm, CheckoutForm, CouponForm
from .models import Product, ProductImages, ProductColor, User, Wishlist, Blog, BlogCategories, Comments, Color, \
    Size, ComparedProduct, OrderProduct, Order, Address


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def prod(request):
    products = Product.objects.all()
    return render(request, 'test1.html', {'products': products})


def produc(request, pk):
    product = get_object_or_404(Product, id=pk)
    photos = ProductImages.objects.filter(product=product)
    color = ProductColor.objects.filter(product=product)
    return render(request, 'test2.html', {'photos': photos, 'product': product, 'color': color})


class ProductLa(ListView):
    model = ProductColor
    template_name = 'test3.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = ProductFilter(self.request.GET, queryset=self.get_queryset())
        return context


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

    # def get_context_data(self, *, object_list=None, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['products_discount'] = Product.objects.filter(discount_price__isnull=False).prefetch_related(
    #         'productimages_set').distinct()
    #
    #     latest = self.request.GET.get('latest')
    #     if latest == 'apply_filter':
    #         queryset = Product.objects.all().prefetch_related('productimages_set').order_by('-date_created')
    #         context['products'] = queryset
    #     elif latest == 'apply_filter_price':
    #         queryset = Product.objects.all().prefetch_related('productimages_set').order_by('price')
    #         context['products'] = queryset
    #     elif latest == 'apply_filter_discount':
    #         queryset = Product.objects.all().prefetch_related('productimages_set').order_by('discount_price')
    #         context['products'] = queryset
    #     else:
    #         context['products'] = self.get_queryset()
    #
    #     return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product-details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object()
        queryset = Product.objects.all().prefetch_related('productimages_set').order_by('-date_created')
        context['products_image'] = queryset
        return context

    def get_queryset(self):
        queryset = Product.objects.all().prefetch_related('productimages_set').distinct()
        return queryset


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


class WishListUser(DetailView):
    template_name = 'wishlist.html'
    model = Product

    def get_object(self, queryset=None):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return user

    def get_queryset(self):
        user = self.get_object()
        queryset = Wishlist.objects.filter(user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.get_queryset()
        return context


@login_required
def add_to_wishlist(request, pk, username):
    user_wish = get_object_or_404(User, username=username)
    product = get_object_or_404(Product, pk=pk)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect('wishlist_by_username', username=request.user)


@login_required
def delete_wish_product(request, pk, username):
    user = get_object_or_404(User, username=username)
    product = get_object_or_404(Product, pk=pk)
    try:
        wish = Wishlist.objects.get(user=user, product=product)
        wish.delete()
    except Wishlist.DoesNotExist:
        pass
    return redirect('wishlist_by_username', username=request.user)


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
            sub_total = sum(cart_item.total() for cart_item in order.items.all())

            context = {
                'object': order,
                'sub_total': sub_total
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
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("cart_page")



class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("checkout")


def add_compare_product(request, pk):
    product = get_object_or_404(Product, id=pk)

    compared_product, created = ComparedProduct.objects.get_or_create(user=request.user)

    if not compared_product.product_1:
        compared_product.product_1 = product
        compared_product.save()
    elif not compared_product.product_2:
        compared_product.product_2 = product
        compared_product.save()
    return redirect('index')


def remove_compare_product(request, pk):
    product = get_object_or_404(Product, id=pk)

    try:
        compared_product = ComparedProduct.objects.get(product_1=product)
        compared_product.product_1 = None
        compared_product.save()
        return JsonResponse({'message': 'Product removed from comparison successfully'})
    except ComparedProduct.DoesNotExist:
        try:
            compared_product = ComparedProduct.objects.get(product_2=product)
            compared_product.product_2 = None
            compared_product.save()
            return JsonResponse({'message': 'Product removed from comparison successfully'})
        except ComparedProduct.DoesNotExist:
            return JsonResponse({'error': 'Compared product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class ComparePage(DetailView):
    template_name = 'compare.html'
    model = ComparedProduct

    def get_object(self, queryset=None):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['compares'] = ComparedProduct.objects.get(user=user)
        return context

# class CheckoutPage(ListView):
#     template_name = 'checkout_page.html'
#     model = CartItemm


# def payment_process(request, username):
#     user = get_object_or_404(User, username=username)
#     cart_order_products = CartItemm.objects.filter(user=user)
#     invoice_num = str(uuid.uuid4())
#
#     for cart_item in cart_order_products:
#         CartOrderItem.objects.create(user=user, cart_order=cart_item, invoice_no=invoice_num)
#
#     host = request.get_host()
#     total_amount = sum(cart_item.total() for cart_item in cart_order_products)
#
#     paypal_dict = {
#         'business': settings.PAYPAL_RECEIVER_EMAIL,
#         'amount': str(total_amount),
#         'item_name': 'Order-Item-No-' + invoice_num,
#         'invoice': 'INVOICE_NO-' + invoice_num,
#         'currency_code': 'USD',
#         'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
#         'return_url': 'http://{}{}'.format(host, reverse('payment_done')),
#         'cancel_return': 'http://{}{}'.format(host, reverse('payment_canceled')),
#     }
#     form = PayPalPaymentsForm(initial=paypal_dict)
#     return render(request, 'checkout_page.html',
#                   {'form': form, 'total_amount': total_amount, 'cart_order_products': cart_order_products})

# class PaymentDoneView(TemplateView):
#     template_name = 'payment_done.html'
#
#     def get(self, request, *args, **kwargs):
#         payer_id = request.GET.get('PayerID')
#
#         if payer_id:
#             payment_id = request.session.get('payment_id')
#
#             if payment_id:
#                 payment = paypalrestsdk.Payment.find(payment_id)
#                 your_model_instance = YourModel.objects.create(payment_id=payment_id)
#                 your_model_instance.save()
#
#                 if payment.execute({"payer_id": payer_id}):
#                     return super().get(request, *args, **kwargs)
#
#         return HttpResponseRedirect(reverse('payment_canceled'))
