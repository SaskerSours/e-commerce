import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from multiselectfield import MultiSelectField

User = get_user_model()


class Product(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
    ]
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    model = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    availability = models.BooleanField()
    summary = models.TextField()
    weight = models.FloatField()
    dimensions = models.CharField(max_length=100)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES, blank=True)
    image = models.ImageField(blank=True, upload_to='products/')
    date_created = models.DateTimeField(auto_now_add=True)
    countdown_target = models.DateTimeField(null=True, blank=True)

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

    def get_final_price(self):
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


class ProductColor(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.model


class Size(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_product')
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Cartt(models.Model):
    cart_id = models.CharField(max_length=250, blank=True, unique=True)

    class Meta:
        db_table = 'Cart'

    def __str__(self):
        return self.cart_id


class CartItemm(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cartitems')
    cart = models.ForeignKey(Cartt, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.product.model

    def total(self):
        return self.product.get_final_price() * self.quantity


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


class Transaction(models.Model):
    STATE_CHOICES = [
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    country = CountryField()
    state = models.CharField(max_length=2, choices=STATE_CHOICES)
    zip = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
