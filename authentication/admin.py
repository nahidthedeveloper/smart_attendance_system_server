from django.contrib import admin
from .models import Account, Teacher, Student

# Register your models here.
admin.site.register(Account)
admin.site.register(Teacher)
admin.site.register(Student)
