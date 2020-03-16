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


class ConceptDB(models.Model):
    name = models.CharField(max_length=100, default='', blank=True)
    cdb_file = models.FileField()
    use_for_training = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Concept(models.Model):
    pretty_name = models.CharField(max_length=300)
    cui = models.CharField(max_length=100, unique=True)
    desc = models.TextField(default="", blank=True)
    tui = models.CharField(max_length=20)
    semantic_type = models.CharField(max_length=200, blank=True, null=True)
    vocab = models.CharField(max_length=100)
    synonyms = models.TextField(default='', blank=True)
    icd10 = models.ManyToManyField(ICDCode, default=None, blank=True, related_name='concept')
    opcs4 = models.ManyToManyField(OPCSCode, default=None, blank=True, related_name='concept')
    cdb = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.pretty_name)


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
    correct = models.BooleanField(default=False)
    alternative = models.BooleanField(default=False)
    manually_created = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    killed = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    # Specific to the Clinical Coding use case - feels hacky being directly on this model.
    # Should AnnotatedEntity be a polymorphic model?? and there be a specific ClinicalCodingAnnotatedEntity??
    icd_code = models.ForeignKey('ICDCode', on_delete=models.SET_NULL, blank=True, null=True)
    opcs_code = models.ForeignKey('OPCSCode', on_delete=models.SET_NULL, blank=True, null=True)

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
    concept_db = models.ForeignKey('ConceptDB', on_delete=models.SET_NULL, null=True)
    vocab = models.ForeignKey('Vocabulary', on_delete=models.SET_NULL, null=True)
    cdb_search_filter = models.ManyToManyField('ConceptDB', blank=True, default=None,
                                               related_name='concept_source')
    require_entity_validation = models.BooleanField(default=True)
    train_model_on_submit = models.BooleanField(default=True)
    clinical_coding_project = models.BooleanField(default=False)
    add_new_entities = models.BooleanField(default=False)
    tasks = models.ManyToManyField(MetaTask, blank=True, default=None)


class MetaAnnotation(models.Model):
    annotated_entity = models.ForeignKey('AnnotatedEntity', on_delete=models.CASCADE)
    meta_task = models.ForeignKey('MetaTask', on_delete=models.CASCADE)
    meta_task_value = models.ForeignKey('MetaTaskValue', on_delete=models.CASCADE)
    acc = models.FloatField(default=1)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return str(self.annotated_entity)



