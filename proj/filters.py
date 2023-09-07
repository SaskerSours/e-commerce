import django_filters
from django.db.models import Q

from proj.models import ProductColor, Product

from django_filters import ChoiceFilter, MultipleChoiceFilter


class ProductFilter(django_filters.FilterSet):
    COLOR_CHOICES = [
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Green', 'Green'),
        ('Yellow', 'Yellow'),
        ('Black', 'Black'),
        ('White', 'White'),
        ('Grey', 'Grey'),
    ]
    color = MultipleChoiceFilter(label='Color', choices=COLOR_CHOICES)

    class Meta:
        model = ProductColor
        fields = ['color']


class ProductFilter2(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = []
        order_by = django_filters.OrderingFilter(
            fields=(
                ('-date_created', 'Date Created (Descending)'),
            ),
            field_labels={
                '-date_created': 'Latest',
            }
        )


def filter_products_by_color_and_size(queryset, color_name, size_name, selected_price=None):
    if color_name and size_name:
        filtered_products = queryset.filter(
            Q(productcolor__color__name=color_name) &
            Q(productsize__size__name=size_name)
        ).distinct()
    elif color_name:
        filtered_products = queryset.filter(
            Q(productcolor__color__name=color_name)
        ).distinct()
    elif size_name:
        filtered_products = queryset.filter(
            Q(productsize__size__name=size_name)
        ).distinct()
    else:
        filtered_products = queryset

    if selected_price:
        filtered_products = filtered_products.filter(price__gt=selected_price)

    return filtered_products
