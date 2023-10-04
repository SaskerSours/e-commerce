from django.urls import path, include
from django.views.generic import TemplateView

from proj import views
from proj.views import ProductDetailView, reply_to_comment

urlpatterns = [

    path('', views.ProductListView.as_view(), name='index'),
    path('product/<slug>', ProductDetailView.as_view(), name='product_detail'),
    path('canvas', views.Canvas.as_view(), name='canvas'),

    path('wishlist', views.WishListUser.as_view(), name='wishlist_by_username'),
    path('add_to_wishlist/<int:pk>', views.add_to_wishlist, name="add_to_wishlist"),
    path('delete_wish_product/<int:pk>', views.delete_wish_product, name='delete_wish_product'),

    path('blog-list', views.BlogList.as_view(), name='blog-list'),
    path('blog-detail/<int:pk>', views.BlogDetail.as_view(), name='blog-detail'),
    path('reply-comment/<int:pk>', reply_to_comment, name='reply_to_comment'),
    path('blog-categories/<slug:slug>', views.BlogCategoriesList.as_view(), name='blog-categories'),

    path('cart/add/<slug>', views.add_to_cart, name='add_to_cart'),
    path('cart-page', views.CartPage.as_view(), name='cart_page'),
    path('remove-single-item/<slug>', views.remove_single_item_from_cart, name='remove_single_item_from_cart'),
    path('remove-from-cart/<slug>', views.remove_from_cart, name='remove_from_cart'),
    path('checkout', views.CheckoutView.as_view(), name='checkout'),
    path('order-confirmation', views.OrderConfirmationView.as_view(), name='order_confirmation'),

    path('payment', views.payment_process, name='payment'),

    path('compare', views.ComparePage.as_view(), name='compare'),
    path('add-compare-product/<slug>', views.add_compare_product, name='add_compare_product'),
    path('remove-compare-product/<slug>', views.remove_compare_product, name='remove_compare_product'),
    path('order-confirmation', TemplateView.as_view(template_name='order-confirmation.html'), name='order_confirmation')

]
