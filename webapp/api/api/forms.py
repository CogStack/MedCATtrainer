import json
import os

from django.db.models.fields.files import FileField
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from api.data_utils import dataset_from_file, delete_orphan_docs, upload_projects_export
from api.models import Dataset, ExportedProject


@receiver(post_save, sender=Dataset)
def save_dataset(sender, instance, **kwargs):
    dataset_from_file(instance)


@receiver(pre_save, sender=Dataset)
def pre_save_dataset(sender, instance, **kwargs):
    if instance.id:
        delete_orphan_docs(instance)
        remove_dataset_file(sender, instance, **kwargs)


@receiver(post_delete, sender=Dataset)
def remove_dataset_file(sender, instance, **kwargs):
    """
    Removes corresponding file from Dataset.original_file FileField.
    """
    if instance.original_file:
        if os.path.isfile(instance.original_file.path):
            os.remove(instance.original_file.path)


@receiver(post_save, sender=ExportedProject)
def save_exported_projects(sender, instance, **kwargs):
    if not instance.trainer_export_file.path.endswith('.json'):
        raise Exception("Please make sure the file is a .json file")
    upload_projects_export(json.load(open(instance.trainer_export_file.path)))
