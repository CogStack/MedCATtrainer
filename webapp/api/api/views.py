import os
import re
from datetime import datetime

import pandas as pd
from django.core.files import File
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django_filters import rest_framework as drf
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import *
from .permissions import *
from .serializers import *
from .utils import get_medcat, add_annotations, remove_annotations, train_medcat, create_annotation

# For local testing, put envs
"""
from environs import Env
env = Env()
env.read_env("/home/ubuntu/projects/MedAnno/MedAnno/env_umls", recurse=False)
print(os.environ)
"""

from medcat.utils.helpers import prepare_name
from medcat.utils.loggers import basic_logger
log = basic_logger("api.views")


# Maps between IDs and objects 
CDB_MAP = {}
VOCAB_MAP = {}
CAT_MAP = {}

# Get the basic version of MedCAT
cat = None

def index(request):
    return render(request, 'index.html')

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [permissions.IsAuthenticated, IsReadOnly]
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class ProjectAnnotateEntitiesViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProjectAnnotateEntities.objects.all()
    serializer_class = ProjectAnnotateEntitiesSerializer
    filterset_fields = ['members', 'dataset', 'id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            projects = ProjectAnnotateEntities.objects.all()
        else:
            projects = ProjectAnnotateEntities.objects.filter(members=user.id)

        return projects


class AnnotatedEntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AnnotatedEntity.objects.all()
    serializer_class = AnnotatedEntitySerializer
    filterset_fields = ['id', 'user', 'project', 'document', 'entity', 'validated',
                        'deleted']


class MetaTaskValueViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'head']
    queryset = MetaTaskValue.objects.all()
    serializer_class = MetaTaskValueSerializer


class MetaTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'head']
    queryset = MetaTask.objects.all()
    serializer_class = MetaTaskSerializer


class MetaAnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'head', 'post', 'put', 'delete']
    queryset = MetaAnnotation.objects.all()
    serializer_class = MetaAnnotationSerializer
    filterset_fields = ['id', 'annotated_entity','validated']


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = ['dataset']


class TextInFilter(drf.BaseInFilter, drf.CharFilter):
    pass
class NumInFilter(drf.BaseInFilter, drf.NumberFilter):
    pass


class ConceptFilter(drf.FilterSet):
    tui__in = TextInFilter(field_name='tui', lookup_expr='in')
    cui__in = TextInFilter(field_name='cui', lookup_expr='in')
    cdb__in = NumInFilter(field_name='cdb', lookup_expr='in')
    id__in = NumInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = Concept
        fields = ['tui', 'cui', 'cdb']


class ConceptViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsReadOnly]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filterset_class = ConceptFilter
    filterset_fields = ['cui', 'tui', 'id', 'cdb']


class ConceptView(generics.ListAPIView):
    http_method_names = ['get', 'post', 'head']
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['pretty_name']
    filterset_class = ConceptFilter
    filterset_fields = ['tui', 'cui', 'cdb']


class EntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


class ConceptDBViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    queryset = ConceptDB.objects.all()
    serializer_class = ConceptDBSerializer


class VocabularyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer


class DatasetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer


class ICDCodeFilter(drf.FilterSet):
    code__in = TextInFilter(field_name='code', lookup_expr='in')
    id__in = NumInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = ICDCode
        fields = ['code', 'id']


class OPCSCodeFilter(drf.FilterSet):
    code__in = TextInFilter(field_name='code', lookup_expr='in')
    id__in = NumInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = OPCSCode
        fields = ['code', 'id']


class ICDCodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    queryset = ICDCode.objects.all()
    serializer_class = ICDCodeSerializer
    filterset_class = ICDCodeFilter
    filterset_fields = ['code', 'id']


class OPCSCodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
    queryset = OPCSCode.objects.all()
    serializer_class = OPCSCodeSerializer
    filterset_class = OPCSCodeFilter
    filterset_fields = ['code', 'id']


@api_view(http_method_names=['GET'])
def search_concept_infos(request):
    out = {}
    query = request.GET.get('code', '')
    cdb_query = request.GET.get('cdb', '')
    if len(query) >= 3 and len(cdb_query) > 0 and re.match('^\w\d\d', query):
        if len(query) > 3 and query[3] != '.':
            query = query[:3] + '.' + query[3:]
        cdb_query = cdb_query.split(',')
        icd_codes = ICDCode.objects.filter(cdb__in=cdb_query, code__startswith=query)
        if len(icd_codes):
            out['icd_codes'] = [ICDCodeSerializer(i).data for i in icd_codes]
        opcs_codes = OPCSCode.objects.filter(cdb__in=cdb_query, code__startswith=query)
        if len(opcs_codes):
            out['opcs_codes'] = [OPCSCodeSerializer(o).data for o in opcs_codes]
    return Response(out)


@api_view(http_method_names=['POST'])
def prepare_documents(request):
    # Get the user
    user = request.user
    # Get doc ids
    d_ids = request.data['document_ids']

    # Get project id
    p_id = request.data['project_id']
    project = ProjectAnnotateEntities.objects.get(id=p_id)

    # Is the entity creation forced
    force = request.data.get('force', 0)

    # Should we update
    update = request.data.get('update', 0)

    cuis = []
    tuis = []
    if project.tuis is not None and project.tuis:
        tuis = [str(tui).strip() for tui in project.tuis.split(",")]
    if project.cuis is not None and project.cuis:
        cuis = [str(cui).strip() for cui in project.cuis.split(",")]

    for d_id in d_ids:
        document = Document.objects.get(id=d_id)
        if force:
            # Remove all annotations if creation is forced
            remove_annotations(document, project, partial=False)
        elif update:
            # Remove annotations that are not verified if creation is update
            remove_annotations(document, project, partial=True)

        # Get annotated entities
        anns = AnnotatedEntity.objects.filter(document=document).filter(project=project)

        is_validated = document in project.validated_documents.all()

        # If the document is not already annotated, annotate it
        if (len(anns) == 0 and not is_validated) or update:
            # Based on the project id get the right medcat
            cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                             CAT_MAP=CAT_MAP, project=project)

            spacy_doc = cat(document.text)
            add_annotations(spacy_doc=spacy_doc,
                            user=user,
                            project=project,
                            document=document,
                            cdb=cat.cdb,
                            tuis=tuis,
                            cuis=cuis)
    return Response({'message': 'Documents prepared successfully'})


@api_view(http_method_names=['POST'])
def name2cuis(request):
    print(request.data)
    text = request.data['text']
    p_id = request.data['project_id']
    project = ProjectAnnotateEntities.objects.get(id=p_id)

    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)

    name, _ = prepare_name(cat=cat, name=text)
    out = {'cuis': list(cat.cdb.name2cui.get(name, []))}

    return Response(out)


@api_view(http_method_names=['POST'])
def add_annotation(request):
    # Get project id
    p_id = request.data['project_id']
    d_id = request.data['document_id']
    source_val = request.data['source_value']
    sel_occur_idx = int(request.data['selection_occur_idx'])
    cui = request.data['cui']

    log.debug("Annotation being added")
    log.debug(str(request.data))
    log.debug("Done")

    # Get project and the right version of cat
    user = request.user
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    document = Document.objects.get(id=d_id)

    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)
    id = create_annotation(source_val=source_val,
                           selection_occurrence_index=sel_occur_idx,
                           cui=cui,
                           user=user,
                           project=project,
                           document=document,
                           cat=cat)

    return Response({'message': 'Annotation added successfully', 'id': id})


@api_view(http_method_names=['POST'])
def submit_document(request):
    # Get project id
    p_id = request.data['project_id']
    d_id = request.data['document_id']

    # Get project and the right version of cat
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    document = Document.objects.get(id=d_id)

    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)

    if project.train_model_on_submit:
        train_medcat(cat, project, document)

    return Response({'message': 'Document submited successfully'})


@api_view(http_method_names=['POST'])
def save_models(request):
    # Get project id
    p_id = request.data['project_id']
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)

    cat.cdb.save_dict(project.concept_db.cdb_file.path)

    return Response({'message': 'Models saved'})


@api_view(http_method_names=['POST'])
def get_create_entity(request):
    label = request.data['label']
    cnt = Entity.objects.filter(label=label).count()
    id = 0
    if cnt == 0:
        ent = Entity()
        ent.label = label
        ent.save()
        id = ent.id
    else:
        ent = Entity.objects.get(label=label)
        id = ent.id

    return Response({'entity_id': id})


@api_view(http_method_names=['POST'])
def create_dataset(request):
    filename = f'{settings.MEDIA_ROOT}/{request.data["dataset_name"]}.csv'
    log.debug(request.data['dataset'])
    pd.DataFrame(request.data['dataset']).to_csv(filename, index=False)

    ds = Dataset()
    ds.original_file = File(open(filename))
    ds.name = request.data['dataset_name']
    ds.description = request.data.get('description', 'n/a')
    ds.save()
    log.debug(f'Saved new dataset:{ds.original_file.path}')
    id = ds.id
    return Response({'dataset_id': id})


@api_view(http_method_names=['GET'])
def finished_projects(request):
    project_ids = request.GET.get('projects')
    if project_ids is None:
        return HttpResponseBadRequest('projects param required')
    projects = ProjectAnnotateEntities.objects.filter(id__in=project_ids.split(','))

    validated_projects = {}
    for project in projects:
        validated = project.validated_documents.all().values_list('id', flat=True)
        all_documents = Document.objects.filter(dataset=project.dataset.id).values_list('id', flat=True)
        validated_projects[project.id] = len(set(all_documents) - set(validated)) == 0

    return Response({'validated_projects': validated_projects})


@api_view(http_method_names=['GET'])
def test(request):
    d_ids = [1003]
    p_id = 1
    user = request.user

    project = ProjectAnnotateEntities.objects.get(id=p_id)

    # Is the entity creation forced
    force = request.data.get('force', 0)

    # Should we update
    update = request.data.get('update', 1)

    cuis = []
    tuis = []
    if project.tuis is not None and project.tuis:
        tuis = [x.strip() for x in project.tuis.split(",")]
    if project.cuis is not None and project.cuis:
        cuis = [x.strip() for x in project.cuis.split(",")]

    for d_id in d_ids:
        document = Document.objects.get(id=d_id)
        if force:
            # Remove all annotations if creation is forced
            remove_annotations(document, project, partial=False)
        elif update:
            # Remove all annotations if creation is forced
            remove_annotations(document, project, partial=True)

        # Get annotated entities
        anns = AnnotatedEntity.objects.filter(document=document).filter(project=project)

        # If the document is not already annotated, annotate it
        if len(anns) == 0 or update:
            # Based on the project id get the right medcat
            cat.cdb = cdb
            cat.vocab = vocab
            cat.train = False

            print(len(cat.cdb.name2cui))
            print(cat.spacy_cat.MIN_CUI_COUNT)
            print(cat.spacy_cat.MIN_ACC)

            spacy_doc = cat(document.text)
            add_annotations(spacy_doc=spacy_doc,
                            user=user,
                            project=project,
                            document=document,
                            cdb=cat.cdb,
                            tuis=tuis,
                            cuis=cuis)

    return Response({'message': 'Documents prepared successfully'})
