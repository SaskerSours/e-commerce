import django_filters
from django.db.models import Q

from proj.models import Product

from django_filters import ChoiceFilter, MultipleChoiceFilter


# class ProductFilter(django_filters.FilterSet):
#     COLOR_CHOICES = [
#         ('Red', 'Red'),
#         ('Blue', 'Blue'),
#         ('Green', 'Green'),
#         ('Yellow', 'Yellow'),
#         ('Black', 'Black'),
#         ('White', 'White'),
#         ('Grey', 'Grey'),
#     ]
#     color = MultipleChoiceFilter(label='Color', choices=COLOR_CHOICES)
#
#     class Meta:
#         model = ProductColor
#         fields = ['color']


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
    """Filters products by color, size, and price.

    Args:
        queryset: A queryset of products.
        color_name: The name of the color to filter by.
        size_name: The name of the size to filter by.
        selected_price: The minimum price to filter by.

    Returns:
        A queryset of filtered products.
    """

    filtered_products = queryset

    if color_name and size_name:
        filtered_products = filtered_products.filter(
            Q(colors__name=color_name) &
            Q(sizes__name=size_name)
        ).distinct()
    elif color_name:
        filtered_products = filtered_products.filter(
            Q(colors__name=color_name)
        ).distinct()
    elif size_name:
        filtered_products = filtered_products.filter(
            Q(sizes__name=size_name)
        ).distinct()

    if selected_price:
        filtered_products = filtered_products.filter(price__gt=selected_price)

    return filtered_products

