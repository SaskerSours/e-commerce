import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from multiselectfield import MultiSelectField

User = get_user_model()

STATUS_CHOICE = (
    ('process', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

SIZE_CHOICES = [
    ('XS', 'XS'),
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL'),
]


class Product(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    model = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    availability = models.BooleanField()
    summary = models.TextField()
    weight = models.FloatField()
    dimensions = models.CharField(max_length=100)
    colors = models.ManyToManyField('Color', blank=True)
    sizes = models.ManyToManyField('Size', blank=True)
    image = models.ImageField(blank=True, upload_to='products/')
    date_created = models.DateTimeField(auto_now_add=True)
    countdown_target = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField()

    def time_remaining(self):
        if self.countdown_target:
            now = timezone.now()
            time_left = self.countdown_target - now

            # Проверяем, не прошло ли уже установленное время
            if time_left > timedelta(0):
                return time_left
        return None

    def time_remaining_display(self):
        time_left = self.time_remaining()

        # Check if time_left is None
        if time_left is None:
            return "Discount has expired"

        # Calculate the number of days left
        days_left = round(time_left.total_seconds() / 86400)

        # Create a string with the appropriate display
        if days_left == 0:
            return "Сьогодні"
        elif days_left == 1:
            return "Приблизно 1 день"
        else:
            return f"Приблизно {days_left} дні(-в)"

    def __str__(self):
        return self.model

    def final_price(self):
        if self.discount_price:
            return self.price - self.discount_price
        else:
            return self.price

    def average_rating(self):
        ratings = [review.rating for review in self.reviews.all()]
        return sum(ratings) / len(ratings) if ratings else 0


class ProductImages(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')


class Color(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_product')
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class OrderProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orderproduct')
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)

    weight = models.FloatField()
    colors = models.ManyToManyField('Color', blank=True)
    sizes = models.ManyToManyField('Size', blank=True)

    # def clean(self):
    #     if (self.colors.count() == 2 or self.sizes.count() == 2) and self.quantity != 2:
    #         raise ValidationError("Choose two colours or two sizes and set the item quantity to 2")
    #
    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)

    def __str__(self):
        return self.item.model

    def get_final_price(self):
        return self.item.final_price() * self.quantity


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderProduct)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=30, default='processing')
    ordered = models.BooleanField(default=False)
    ordered_date = models.DateTimeField(default=None, null=True, blank=True)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    email = models.EmailField(blank=True, null=True)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Payment(models.Model):
    payment_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payment_id)


class BlogCategories(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(null=False, unique=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_categories', kwargs={'slug': self.slug})


class Tags(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(null=False, unique=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tag_detail', kwargs={'slug': self.slug})


class Blog(models.Model):
    category = models.ForeignKey(BlogCategories, blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    image = models.ImageField(upload_to='blog_image/')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField("date published", auto_now_add=True, db_index=True)

    def formatted_text(self):
        return mark_safe(self.text)


class Comments(models.Model):
    blog = models.ForeignKey(Blog, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField(max_length=400)
    created = models.DateTimeField("date published", auto_now_add=True)


class Reply(models.Model):
    comment = models.ForeignKey(Comments, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='replies', on_delete=models.CASCADE)
    text = models.TextField(max_length=400)
    created = models.DateTimeField("date published", auto_now_add=True)


class ComparedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_1 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_1', null=True)
    product_2 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_2', null=True)
    date_added = models.DateTimeField(auto_now_add=True)
