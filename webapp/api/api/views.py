from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import *
from rest_framework import viewsets
from rest_framework import permissions
from .data_utils import text_classification_csv_import
from .permissions import *
from .models import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .utils import get_medcat, add_annotations, remove_annotations, train_medcat
import os

# For local testing, put envs
"""
from environs import Env
env = Env()
env.read_env("/home/ubuntu/projects/MedAnno/MedAnno/env_umls", recurse=False)
print(os.environ)
"""

from medcat.cat import CAT
from medcat.utils.vocab import Vocab
from medcat.cdb import CDB
from medcat.utils.helpers import prepare_name


# Maps between IDs and objects 
CDB_MAP = {}
VOCAB_MAP = {}

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


class ConceptViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsReadOnly]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer 
    filterset_fields = ['cui', 'tui']


class ProjectAnnotateEntitiesViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ProjectAnnotateEntities.objects.all()
    serializer_class = ProjectAnnotateEntitiesSerializer
    filterset_fields = ['members', 'dataset', 'id']


class AnnotatedEntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AnnotatedEntity.objects.all()
    serializer_class = AnnotatedEntitySerializer
    filterset_fields = ['id', 'user', 'project', 'document', 'entity', 'correct']


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer 
    filterset_fields = ['dataset']


class ConceptView(generics.ListAPIView):
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['pretty_name']


class EntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsReadOnly]
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


@api_view(http_method_names=['POST'])
def prepare_documents(request):
    global cat
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
        tuis = project.tuis.split(",")
    if project.cuis is not None and project.cuis:
        cuis = project.cuis.split(",")

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
            cat = get_medcat(cat, CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP, project=project)

            if cat is None:
                cat = CAT(cdb=cdb, vocab=vocab)
                cat.train = False
            else:
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


@api_view(http_method_names=['POST'])
def name2cuis(request):
    print(request.data)
    text = request.data['text']
    p_id = request.data['project_id']
    project = ProjectAnnotateEntities.objects.get(id=p_id)

    cdb, vocab = get_medcat_models(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP, project=project)
    cat.cdb = cdb
    cat.vocab = vocab
    print("HERE")

    name, _ = prepare_name(cat=cat, name=text)
    out = {'cuis': list(cat.cdb.name2cui.get(name, []))}

    return Response(out)


@api_view(http_method_names=['POST'])
def add_synonym(request):
    # Get project id
    p_id = request.data['project_id']
    text = request.data['context']
    source_val = request.data['synonym']
    cui = request.data['cui']

    # Get project and the right version of cat
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    cat = get_medcat(cat, CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP, project=project)
    cat.add_name(cui=cui, source_val=source_val, text=text)

    return Response({'message': 'Synonym added successfully'})


@api_view(http_method_names=['POST'])
def submit_document(request):
    # Get project id
    p_id = request.data['project_id']
    d_id = request.data['document_id']

    # Get project and the right version of cat
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    document = Document.objects.get(id=d_id)

    cat = get_medcat(cat, CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP, project=project)
    train_medcat(cat, project, document)

    return Response({'message': 'Document submited successfully'})


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
        tuis = project.tuis.split(",")
    if project.cuis is not None and project.cuis:
        cuis = project.cuis.split(",")

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
            cdb, vocab = get_medcat_models(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP, project=project)
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
