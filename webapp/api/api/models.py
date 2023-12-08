import os

import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver
from django.forms import forms, ModelForm
from polymorphic.models import PolymorphicModel

STATUS_CHOICES = [
        (0, 'Not Validated'),
        (1, 'Validated'),
        ]

BOOL_CHOICES = [
        (0, 'False'),
        (1, 'True')
        ]


class ICDCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    desc = models.CharField(max_length=300)
    cdb = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.code} | {self.desc}'


class OPCSCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    desc = models.CharField(max_length=300)
    cdb = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.code} | {self.desc}'


cdb_name_validator = RegexValidator(r'^[0-9a-zA-Z_-]*$', 'Only alpahanumeric characters, -, _ are allowed for CDB names')


class ConceptDB(models.Model):
    name = models.CharField(max_length=100, default='', blank=True, validators=[cdb_name_validator])
    cdb_file = models.FileField()
    use_for_training = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super(ConceptDB, self).__init__(*args, **kwargs)
        self.__cdb_field_name = None

    @classmethod
    def from_db(cls, db, field_names, values):
        inst = super(ConceptDB, cls).from_db(db, field_names, values)
        inst.__cdb_field_name = [v for f, v in zip(field_names, values) if f == 'cdb_file'][0]
        return inst

    def save(self, *args, **kwargs):
        if self.__cdb_field_name is not None and self.__cdb_field_name != self.cdb_file.name:
            raise ValidationError('Cannot change file path of existing CDB.')
        else:
            super(ConceptDB, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Vocabulary(models.Model):
    vocab_file = models.FileField()

    def __str__(self):
        return str(self.vocab_file.name)


class Dataset(models.Model):
    name = models.CharField(max_length=150)
    original_file = models.FileField()
    create_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return str(self.name)


class DatasetForm(ModelForm):
    def clean(self):
        original_file = self.cleaned_data['original_file']
        if '.csv' in original_file.name:
            df = pd.read_csv(original_file.file, on_bad_lines='error')
        elif '.xlsx' in original_file.name:
            df = pd.read_excel(original_file.file)
        else:
            raise forms.ValidationError({'original_file': 'Must be either .csv or .xlsx'})
        if 'name' not in df.columns or 'text' not in df.columns:
            raise forms.ValidationError({'original_file': 'Must contain at least a "name" and "text" column'})


class Document(models.Model):
    name = models.CharField(max_length=150)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    text = models.TextField(default="", blank=True)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name} | {self.dataset.name} | {self.dataset.id}'


class Project(PolymorphicModel):
    PROJECT_STATUSES = [
        ("A", "Annotating"),
        ("D", "Discontinued (Fail)"),
        ("C", "Complete"),
    ]
    name = models.CharField(max_length=150)
    description = models.TextField(default="", blank=True)
    annotation_guideline_link = models.TextField(default="", blank=True,
                                                 help_text="link to an external document (i.e. GoogleDoc, MS Sharepoint)"
                                                           "outlininng a guide for annotators to follow for this project,"
                                                           "an example is available here: https://docs.google.com/document/d/1xxelBOYbyVzJ7vLlztP2q1Kw9F5Vr1pRwblgrXPS7QM/edit?usp=sharing")
    create_time = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)
    validated_documents = models.ManyToManyField(Document, default=None, blank=True)
    cuis = models.TextField(default=None, blank=True)
    cuis_file = models.FileField(null=True, blank=True,
                                 help_text='A file containing a JSON formatted list of CUI code strings, '
                                           'i.e. ["1234567","7654321"]')
    annotation_classification = models.BooleanField(default=False, help_text="If these project annotations are suitable"
                                                                             " for training a general purpose model. If"
                                                                             " in doubt uncheck this.")
    project_locked = models.BooleanField(default=False, help_text="If this project is locked and cannot or should "
                                                                  "not be touched any further.")
    project_status = models.CharField(max_length=1, choices=PROJECT_STATUSES, default="A",
                                      help_text="The status of the project to indicate the readiness")

    def __str__(self):
        return str(self.name)


class Entity(models.Model):
    label = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return str(self.label)


class Relation(models.Model):
    label = models.CharField(max_length=300, unique=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return str(self.label)


class EntityRelation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='entity_relation_document')
    relation = models.ForeignKey('Relation', on_delete=models.CASCADE)
    start_entity = models.ForeignKey('AnnotatedEntity', related_name='start_entity', on_delete=models.CASCADE)
    end_entity = models.ForeignKey('AnnotatedEntity', related_name='end_entity', on_delete=models.CASCADE)
    validated = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.start_entity} - {self.relation} - {self.end_entity}'


class AnnotatedEntity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='annotated_entity')
    entity = models.ForeignKey('Entity', on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)
    start_ind = models.IntegerField()
    end_ind = models.IntegerField()
    acc = models.FloatField()
    comment = models.TextField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    correct = models.BooleanField(default=False)
    alternative = models.BooleanField(default=False)
    manually_created = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    killed = models.BooleanField(default=False)
    irrelevant = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    # Specific to the Clinical Coding use case - feels hacky being directly on this model.
    # Should AnnotatedEntity be a polymorphic model?? and there be a specific ClinicalCodingAnnotatedEntity??
    icd_code = models.ForeignKey('ICDCode', on_delete=models.SET_NULL, blank=True, null=True)
    opcs_code = models.ForeignKey('OPCSCode', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return str(self.entity)


class MetaTaskValue(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return str(self.name)


class MetaTask(models.Model):
    name = models.CharField(max_length=150)
    values = models.ManyToManyField(MetaTaskValue, related_name='values')
    default = models.ForeignKey('MetaTaskValue', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return str(self.name)


class ProjectAnnotateEntities(Project):
    concept_db = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, blank=False, null=True)
    vocab = models.ForeignKey('Vocabulary', on_delete=models.SET_NULL, null=True)
    cdb_search_filter = models.ManyToManyField('ConceptDB', blank=True, default=None,
                                               help_text='The CDB that will be used for concept lookup. '
                                                         'This specific CDB should have been "imported" '
                                                         'via the CDB admin screen',
                                               related_name='concept_source')
    require_entity_validation = models.BooleanField(default=True,
                                                    help_text='Entities appear grey and are required to be validated '
                                                              'before submission')
    train_model_on_submit = models.BooleanField(default=True, help_text='Active learning - configured CDB is trained '
                                                                        'on each submit')
    add_new_entities = models.BooleanField(default=False,
                                           help_text='Allow the creation of new terms to be added to the CDB')
    restrict_concept_lookup = models.BooleanField(default=False,
                                                  help_text='Users can only search for concept terms from the '
                                                            'list configured for the project, i.e. either from '
                                                            'the cuis or cuis_file lists. Checking this when both'
                                                            'cuis and cuis_file are empty does nothing. If "add new '
                                                            'entities" is available & added, and cuis or cuis_file'
                                                            'is non-empty the new CUI will be added.')
    terminate_available = models.BooleanField(default=True,
                                              help_text='Enable the option to terminate concepts.')
    irrelevant_available = models.BooleanField(default=False,
                                               help_text='Enable the option to add the irrelevant button.')
    enable_entity_annotation_comments = models.BooleanField(default=False,
                                                            help_text="Enable to allow annotators to leave comments"
                                                                      " for each annotation")
    tasks = models.ManyToManyField(MetaTask, blank=True, default=None)
    relations = models.ManyToManyField(Relation, blank=True, default=None,
                                       help_text='Relations that will be available for this project')


class MetaAnnotation(models.Model):
    annotated_entity = models.ForeignKey('AnnotatedEntity', on_delete=models.CASCADE)
    meta_task = models.ForeignKey('MetaTask', on_delete=models.CASCADE)
    meta_task_value = models.ForeignKey('MetaTaskValue', on_delete=models.CASCADE)
    acc = models.FloatField(default=1)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return str(self.annotated_entity)


class ExportedProject(models.Model):
    trainer_export_file = models.FileField(help_text='Previously exported MedCATtrainer .json file')

    def __str__(self):
        return self.trainer_export_file.name


class ProjectMetrics(models.Model):
    report_name_generated = models.TextField(help_text='report name that links this metrics report to a previously '
                                                       'ran bg task')
    report_name = models.TextField(help_text='A user specified report name that should be more user friendly than '
                                             'the generated one')
    report = models.FileField(help_text='the outputted metrics for configured')
    projects = models.ManyToManyField('ProjectAnnotateEntities', blank=True)

    def __str__(self):
        return f'generated report name: {self.report_name}, user specified report name:f{self.report_name}'


@receiver(models.signals.post_delete, sender=ConceptDB)
def auto_delete_cdb_file_on_delete(sender, instance, **kwargs):
    _remove_file(instance, 'cdb_file')


@receiver(models.signals.post_delete, sender=Vocabulary)
def auto_delete_vocab_file_on_delete(sender, instance, **kwargs):
    _remove_file(instance, 'vocab_file')


@receiver(models.signals.post_delete, sender=Dataset)
def auto_delete_dataset_file_on_delete(sender, instance, **kwargs):
    _remove_file(instance, 'original_file')


def _remove_file(instance, prop):
    if getattr(instance, prop):
        if os.path.isfile(getattr(instance, prop).path):
            os.remove(getattr(instance, prop).path)
