from django.contrib import admin

from .models import Product, Review, ProductImages, ProductColor, ProductSize, Color, Size, Wishlist, Blog, \
    BlogCategories, Tags, Comments, Reply, ComparedProduct, OrderProduct, Order, Address, Coupon, Payment

admin.site.register(Review)


class ProductImageAdmin(admin.StackedInline):
    model = ProductImages


admin.site.register(Color)
admin.site.register(Size)

admin.site.register(Wishlist)
admin.site.register(Blog)

admin.site.register(BlogCategories)
admin.site.register(Tags)

admin.site.register(Comments)
admin.site.register(Reply)

admin.site.register(OrderProduct)
admin.site.register(Order)

admin.site.register(Address)
admin.site.register(Coupon)
admin.site.register(Payment)


admin.site.register(ComparedProduct)


class ProductColorAdmin(admin.StackedInline):
    model = ProductColor


class ProductSizeAdmin(admin.StackedInline):
    model = ProductSize


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductColorAdmin, ProductSizeAdmin, ProductImageAdmin]

    class Meta:
        model = Product


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    pass
