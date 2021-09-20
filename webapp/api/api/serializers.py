import json

from django.contrib.auth.models import User
from rest_framework.fields import FileField
from rest_framework.serializers import Serializer

from .models import *
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'id', 'is_staff', 'is_superuser']


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ['pretty_name', 'cui', 'desc', 'tui', 'synonyms', 'semantic_type',
                  'icd10', 'opcs4', 'id', 'cdb']

    def to_representation(self, instance):
        data = super(ConceptSerializer, self).to_representation(instance)
        syns = data['synonyms'].split(', ')
        data['synonyms'] = data['synonyms'] if len(syns) < 10 else syns[:10]
        return data


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = '__all__'


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'


class EntityRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityRelation
        fields = '__all__'


class ConceptDBSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptDB
        fields = '__all__'


class VocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = '__all__'


class ICDCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICDCode
        fields = ['code', 'desc', 'id', 'concept']


class OPCSCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OPCSCode
        fields = ['code', 'desc', 'id', 'concept']


class ProjectAnnotateEntitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAnnotateEntities
        exclude = ('cuis_file', )

    def to_representation(self, instance):
        data = super(ProjectAnnotateEntitiesSerializer, self).to_representation(instance)
        cuis_from_file = json.load(open(instance.cuis_file.path)) if instance.cuis_file else []
        cui_list = (data.get('cuis') or '').split(',') + cuis_from_file
        data['cuis'] = ','.join(cui_list)
        return data


class ProjectAnnotateDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAnnotateDocuments
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class DocumentAnnotationTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationTask

    def to_representation(self, instance):
        if isinstance(instance, DocumentAnnotationClassificationTask):
            return DocumentAnnotationClassificationTaskSerializer().to_representation(instance)
        elif isinstance(instance, DocumentAnnotationRegressionTask):
            return DocumentAnnotationRegressionTaskSerializer().to_representation(instance)
        else:
            NotImplementedError("No serializer available for " + str(instance))


class DocumentAnnotationClassificationTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationClassificationTask
        fields = '__all__'


class DocumentAnnotationClassLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationClassLabel
        fields = '__all__'


class DocumentAnnotationRegressionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationRegressionTask
        fields = '__all__'


class DocumentAnnotationValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationValue
        fields = '__all__'

    def to_representation(self, instance):
        if isinstance(instance, DocumentAnnotationClfValue):
            return DocumentAnnotationClfValueSerializer().to_representation(instance)
        elif isinstance(instance, DocumentAnnotationRegValue):
            return DocumentAnnotationRegValueSerializer().to_representation(instance)
        else:
            NotImplementedError("No serializer available for " + str(type(instance)))


class DocumentAnnotationClfValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationClfValue
        fields = '__all__'


class DocumentAnnotationRegValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnnotationRegValue
        fields = '__all__'


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = '__all__'


class AnnotatedEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotatedEntity
        fields = '__all__'


class MetaAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAnnotation
        fields = '__all__'


class MetaTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaTask
        fields = '__all__'


class MetaTaskValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaTaskValue
        fields = '__all__'


# Serializers define the API representation.
class DeploymentUploadSerializer(Serializer):
    deployment_file = FileField()

    class Meta:
        fields = ['deployment_file']
