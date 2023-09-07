from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff']


# Зареєструйте ваш адміністративний клас для моделі CustomUser
admin.site.register(CustomUser, CustomUserAdmin)
