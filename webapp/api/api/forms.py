from django import forms
from .models import *
from .data_utils import *
from django.db.models.signals import post_save
from django.dispatch import receiver


# Extract text from the uploaded dataset
@receiver(post_save, sender=Dataset)
def save_dataset(sender, instance, **kwargs):
    text_from_csv(instance)
