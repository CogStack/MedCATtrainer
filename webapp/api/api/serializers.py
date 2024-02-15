import json
import logging

from django.contrib.auth.models import User
from rest_framework.fields import FileField
from rest_framework.serializers import Serializer

from .models import *
from rest_framework import serializers


logger = logging.getLogger(__name__)

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'id', 'is_staff', 'is_superuser']


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


class ProjectAnnotateEntitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAnnotateEntities
        exclude = ('cuis_file', )

    def to_representation(self, instance):
        data = super(ProjectAnnotateEntitiesSerializer, self).to_representation(instance)
        try:
            cuis_from_file = json.load(open(instance.cuis_file.path)) if instance.cuis_file else []
        except FileNotFoundError:
            logger.warning('cuis file %s cannot be found. Project: %s will fail to load. File '
                           'needs to be cleared and re-uploaded to load project', instance.cuis_file,
                           instance.name)
            cuis_from_file = []
        cui_list = [s.strip() for s in data['cuis'].split(',')] + cuis_from_file if len(data['cuis']) > 0 else cuis_from_file
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
