import json

from django.contrib.auth.models import User
from .models import *
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'id']


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ['pretty_name', 'cui', 'desc', 'tui', 'synonyms', 'semantic_type',
                  'icd10', 'opcs4', 'id', 'cdb']


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
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
        cuis_from_file = ','.join(json.load(open(instance.cuis_file.path))) if instance.cuis_file else ''
        data['cuis'] = data['cuis'] + (',' + cuis_from_file) if len(data['cuis']) > 0 else cuis_from_file
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
