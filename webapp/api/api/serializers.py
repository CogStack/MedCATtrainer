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
        model = Relation
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
        cui_list = data['cuis'].split(',') + cuis_from_file
        data['cuis'] = ','.join(cui_list)
        return data


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
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
