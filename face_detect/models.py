import os

from django.db import models
from authentication.models import Account


class Dataset(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    sample = models.CharField(max_length=200, default="0")
    is_sampleUploaded = models.BooleanField(default=False)
    is_trained = models.BooleanField(default=False)

    @property
    def is_deleted(self):
        dataset_path = os.path.join('faceRecognition_data', 'training_dataset', self.user.academic_id)
        return not os.path.exists(dataset_path)
