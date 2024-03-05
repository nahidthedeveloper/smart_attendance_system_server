from django.contrib.auth.models import AbstractUser
from django.db import models

from authentication.manager import AccountManager


class Account(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(max_length=100, unique=True)
    student_id = models.CharField(max_length=16)
    name = models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = AccountManager()

    def __str__(self):
        return self.email
