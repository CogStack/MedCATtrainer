from django.db import models
from django.conf import settings
from polymorphic.models import PolymorphicModel


STATUS_CHOICES = [
        (0, 'Not Validated'),
        (1, 'Validated'),
        ]

BOOL_CHOICES = [
        (0, 'False'),
        (1, 'True')
        ]


class Concept(models.Model):
    pretty_name = models.CharField(max_length=300)
    cui = models.CharField(max_length=100, unique=True)
    desc = models.TextField(default="", blank=True)
    tui = models.CharField(max_length=20)
    semantic_type = models.CharField(max_length=200, blank=True, null=True)
    vocab = models.CharField(max_length=100)
    synonyms = models.TextField(default='', blank=True)
    icd10 = models.TextField(default='', blank=True)
    cdb = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, blank=True, null=True)


    def __str__(self):
        return str(self.pretty_name)


class Link(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    concept = models.ForeignKey('Concept', on_delete=models.CASCADE)
    name = models.CharField(max_length=300)


class ConceptDB(models.Model):
    cdb_file = models.FileField()

    def __str__(self):
        return str(self.cdb_file.name)


class Vocabulary(models.Model):
    vocab_file = models.FileField()

    def __str__(self):
        return str(self.vocab_file.name)



class MedCATModel(models.Model):
    name = models.CharField(max_length=100)
    cdb = models.ForeignKey('ConceptDB', on_delete=models.CASCADE)
    vocab = models.ForeignKey('Vocabulary', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)


class Dataset(models.Model):
    name = models.CharField(max_length=150)
    original_file = models.FileField()
    create_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return str(self.name)


class Document(models.Model):
    name = models.CharField(max_length=150)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    text = models.TextField(default="", blank=True)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)


class Project(PolymorphicModel):
    name = models.CharField(max_length=150)
    description = models.TextField(default="", blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)
    validated_documents = models.ManyToManyField(Document, default=None, blank=True)
    cuis = models.TextField(default=None, blank=True)
    tuis = models.TextField(default=None, blank=True)

    def __str__(self):
        return str(self.name)


class Entity(models.Model):
    label = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return str(self.label)


class AnnotatedEntity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='annotated_entity')
    entity = models.ForeignKey('Entity', on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)
    start_ind = models.IntegerField()
    end_ind = models.IntegerField()
    acc = models.FloatField()
    validated = models.BooleanField(default=False)
    alternative = models.BooleanField(default=False)
    manually_created = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)


    def __str__(self):
        return str(self.entity)


class MetaTaskValue(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return str(self.name)


class MetaTask(models.Model):
    name = models.CharField(max_length=150)
    values = models.ManyToManyField(MetaTaskValue, related_name='values')
    description = models.TextField(default="", blank=True)


class ProjectAnnotateEntities(Project):
    medcat_models = models.ForeignKey('MedCATModel', on_delete=models.SET_NULL, blank=True, null=True)
    require_entity_validation = models.BooleanField(default=False)


class ProjectMetaAnnotate(Project):
    # Takse documents and models from the annotate entities project
    project_annotate_entities = models.ForeignKey('ProjectAnnotateEntities', on_delete=models.CASCADE)
    tasks = models.ManyToManyField(MetaTask)


class MetaAnnotation(models.Model):
    annotated_entity = models.ForeignKey('AnnotatedEntity', on_delete=models.CASCADE)
    meta_task = models.ForeignKey('MetaTask', on_delete=models.CASCADE)
    meta_task_value = models.ForeignKey('MetaTaskValue', on_delete=models.CASCADE)
    acc = models.FloatField()
    validated = models.BooleanField()
