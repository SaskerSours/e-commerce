from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email', 'password', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.username

