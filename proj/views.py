import random
import uuid

import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.messages import add_message
from django.contrib.messages.context_processors import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, FormView, TemplateView
from paypal.standard.forms import PayPalPaymentsForm

from .filters import ProductFilter, filter_products_by_color_and_size
from .forms import CommentsForm, ReplyForm
from .models import Product, ProductImages, ProductColor, User, Wishlist, Blog, BlogCategories, Comments, Color, \
    Size, Cartt, CartItemm, ComparedProduct, CartOrderItem


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


def add_cart(request, pk):
    try:
        product = Product.objects.get(id=pk)
    except Product.DoesNotExist:
        pass
    cart = Cartt.objects.filter(cart_id=_cart_id(request)).first()
    if not cart:
        cart = Cartt.objects.create(cart_id=_cart_id(request))
        cart.save()

    try:
        cart_item = CartItemm.objects.filter(product=product, cart=cart, user=request.user).first()
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItemm.objects.create(product=product, quantity=1, cart=cart, user=request.user)
            cart_item.save()
    except CartItemm.DoesNotExist:
        pass

    return redirect('cart_page', username=request.user)


def remove_quantity_from_cart(request, pk):
    try:
        product = get_object_or_404(Product, id=pk)
    except Product.DoesNotExist:
        pass
    cart = Cartt.objects.get(cart_id=_cart_id(request))
    cart_item = CartItemm.objects.get(product=product, cart=cart)
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    else:
        return redirect('index')
    return redirect('cart_page', username=request.user)


def cart_remove_product(request, pk):
    try:
        product = get_object_or_404(Product, id=pk)
    except Product.DoesNotExist:
        pass
    cart = Cartt.objects.get(cart_id=_cart_id(request))
    try:
        cart_item = CartItemm.objects.get(product=product, cart=cart)
    except CartItemm.DoesNotExist:
        return redirect('index')
    cart_item.delete()

    return redirect('cart_page', username=request.user)


class CartPage(DetailView):
    template_name = 'cart_page.html'
    model = CartItemm

    def get_object(self, queryset=None):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return user

    def get_queryset(self):
        user = self.get_object()
        queryset = CartItemm.objects.filter(user=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['carts'] = self.get_queryset()
        cart_items = self.get_queryset()
        cart_total = sum(cart_item.total() for cart_item in cart_items)
        context['cart_total'] = cart_total
        return context


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


def payment_process(request, username):
    user = get_object_or_404(User, username=username)
    cart_order_products = CartItemm.objects.filter(user=user)
    invoice_num = str(uuid.uuid4())

    for cart_item in cart_order_products:
        CartOrderItem.objects.create(user=user, cart_order=cart_item, invoice_no=invoice_num)

    host = request.get_host()
    total_amount = sum(cart_item.total() for cart_item in cart_order_products)

    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': str(total_amount),
        'item_name': 'Order-Item-No-' + invoice_num,
        'invoice': 'INVOICE_NO-' + invoice_num,
        'currency_code': 'USD',
        'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
        'return_url': 'http://{}{}'.format(host, reverse('payment_done')),
        'cancel_return': 'http://{}{}'.format(host, reverse('payment_canceled')),
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, 'checkout_page.html',
                  {'form': form, 'total_amount': total_amount, 'cart_order_products': cart_order_products})

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
