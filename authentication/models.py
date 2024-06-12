from django.contrib.auth.models import AbstractUser
from django.db import models
from academic.models import Department, Batch

from authentication.manager import AccountManager


class Account(AbstractUser):
    username = None
    first_name = None
    last_name = None

    STATUS_CHOICES = (
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    )

    email = models.EmailField(max_length=100, unique=True)
    academic_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=50, choices=STATUS_CHOICES, null=False)
    avatar = models.FileField(upload_to='avatars')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)

    USERNAME_FIELD = 'academic_id'
    REQUIRED_FIELDS = ['email']

    objects = AccountManager()

    def __str__(self):
        return self.academic_id


class Student(models.Model):
    STATUS_CHOICES = (
        ("1", "1th"),
        ("2", "2nd"),
        ("3", "3rd"),
        ("4", "4th"),
        ("5", "5th"),
        ("6", "6th"),
        ("7", "7th"),
        ("8", "8th"),
    )

    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)
    semester = models.CharField(max_length=50, choices=STATUS_CHOICES, null=False)

    def __str__(self):
        return self.user.academic_id


class Teacher(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.academic_id
