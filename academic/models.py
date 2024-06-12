from django.db import models


class Department(models.Model):
    department = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.department


class Batch(models.Model):
    batch = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.batch
