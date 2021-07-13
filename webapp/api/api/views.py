import logging
import re
import traceback

import pandas as pd
from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import render
from django_filters import rest_framework as drf
from django_filters.rest_framework import DjangoFilterBackend
from medcat.utils.helpers import tkns_from_doc
from rest_framework import filters
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .admin import download_projects_with_text, download_projects_without_text, download_deployment_export, \
    upload_deployment_export
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

from medcat.utils.loggers import add_handlers

log = logging.getLogger('trainer')
log = add_handlers(log)


# Maps between IDs and objects 
CDB_MAP = {}
VOCAB_MAP = {}
CAT_MAP = {}

# Get the basic version of MedCAT
cat = None

def index(request):
    return render(request, 'index.html')


class TextInFilter(drf.BaseInFilter, drf.CharFilter):
    pass
class NumInFilter(drf.BaseInFilter, drf.NumberFilter):
    pass


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [permissions.IsAuthenticated, IsReadOnly]
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    filterset_fields = ['username']


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


class AnnotatedEntityFilter(drf.FilterSet):
    id__in = NumInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = AnnotatedEntity
        fields = ['id', 'user', 'project', 'document', 'entity', 'validated',
                  'deleted']


class AnnotatedEntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AnnotatedEntity.objects.all()
    serializer_class = AnnotatedEntitySerializer
    filterset_class = AnnotatedEntityFilter


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
    filterset_fields = ['id', 'annotated_entity', 'validated']


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = ['dataset']


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
    filterset_fields = ['cui', 'id', 'cdb']


class ConceptView(generics.ListAPIView):
    http_method_names = ['get', 'post', 'head']
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['$pretty_name']
    ordering = ['pretty_name']
    filterset_class = ConceptFilter
    filterset_fields = ['cui', 'cdb']


class EntityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


class RelationFilter(drf.FilterSet):
    id__in = NumInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = Relation
        fields = ['label']


class RelationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']
    queryset = Relation.objects.all()
    serializer_class = RelationSerializer
    filterset_class = RelationFilter


class EntityRelationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'head', 'delete']
    queryset = EntityRelation.objects.all()
    serializer_class = EntityRelationSerializer
    filterset_fields = ['project', 'document']


class ConceptDBViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']
    queryset = ConceptDB.objects.all()
    serializer_class = ConceptDBSerializer


class VocabularyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head']
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


class DeploymentUploadViewSet(ViewSet):
    serializer_class = DeploymentUploadSerializer

    def create(self, request):
        deployment_upload = request.FILES.get('deployment_file')
        errs = upload_deployment_export(deployment_upload.file.name)
        log.info(f'Errors encountered during previous deployment upload\n{errs}')
        return Response(errs, 200)


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

    cuis = set()
    if project.cuis is not None and project.cuis:
        cuis = set([str(cui).strip() for cui in project.cuis.split(",")])
    if project.cuis_file is not None and project.cuis_file:
        # Add cuis from json file if it exists
        cuis.update(json.load(open(project.cuis_file.path)))

    try:
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

                # Set CAT filters
                cat.config.linking['filters']['cuis'] = cuis

                spacy_doc = cat(document.text)
                add_annotations(spacy_doc=spacy_doc,
                                user=user,
                                project=project,
                                document=document,
                                cat=cat,
                                existing_annotations=anns)

    except Exception as e:
        stack = traceback.format_exc()
        return Response({'message': 'Internal Server Error', 'stacktrace': stack}, status=500)
    return Response({'message': 'Documents prepared successfully'})


@api_view(http_method_names=['POST'])
def add_annotation(request):
    # Get project id
    p_id = request.data['project_id']
    d_id = request.data['document_id']
    source_val = request.data['source_value']
    sel_occur_idx = int(request.data['selection_occur_idx'])
    cui = request.data['cui']

    icd_code = request.data.get('icd_code')
    opcs_code = request.data.get('opcs_code')

    log.debug("Annotation being added")
    log.debug(str(request.data))

    # Get project and the right version of cat
    user = request.user
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    document = Document.objects.get(id=d_id)

    if icd_code:
        icd_code = ICDCode.objects.filter(id=icd_code).first()
    if opcs_code:
        opcs_code = OPCSCode.objects.filter(id=opcs_code).first()

    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)
    id = create_annotation(source_val=source_val,
                           selection_occurrence_index=sel_occur_idx,
                           cui=cui,
                           user=user,
                           project=project,
                           document=document,
                           cat=cat,
                           icd_code=icd_code,
                           opcs_code=opcs_code)
    log.debug('Annotation added.')
    return Response({'message': 'Annotation added successfully', 'id': id})


@api_view(http_method_names=['POST'])
def add_concept(request):
    p_id = request.data['project_id']
    d_id = request.data['document_id']
    source_val = request.data['source_value']
    sel_occur_idx = int(request.data['selection_occur_idx'])
    name = request.data['name']
    cui = request.data['cui']
    context = request.data['context']
    # TODO These aren't used, but no API in current MedCAT add_name func
    # Add these fields to the add_name func of MedCAT add_name
    desc = request.data['desc']
    tui = request.data['tui']
    s_type = request.data['type']
    synonyms = request.data['synonyms']

    user = request.user
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    document = Document.objects.get(id=d_id)
    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)

    if cui in cat.cdb.cui2names:
        err_msg = f'Cannot add a concept "{name}" with cui:{cui}. CUI already linked to {cat.cdb.cui2names[cui]}'
        log.error(err_msg)
        return Response({'err': err_msg}, 400)

    spacy_doc = cat(document.text)
    spacy_entity = None
    if source_val in spacy_doc.text:
        start = spacy_doc.text.index(source_val)
        end = start + len(source_val)
        spacy_entity = tkns_from_doc(spacy_doc=spacy_doc, start=start, end=end)

    cat.add_and_train_concept(cui=cui, name=name, spacy_doc=spacy_doc, spacy_entity=spacy_entity)

    id = create_annotation(source_val=source_val,
                           selection_occurrence_index=sel_occur_idx,
                           cui=cui,
                           user=user,
                           project=project,
                           document=document,
                           cat=cat)

    # Create a new Concept
    if Concept.objects.filter(cui=cui).count() == 0:
        c = Concept()
        c.cui = cui
        c.pretty_name = name
        c.desc = desc
        c.tui = tui
        c.synonyms = synonyms
        c.semantic_type = s_type
        c.cdb = project.concept_db
        c.save()
        log.debug(f'Added new concept to concept list:{cui}')

    return Response({'message': 'Concept and Annotation added successfully', 'id': id})


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
        try:
            train_medcat(cat, project, document)
        except Exception as e:
            if project.vocab.id:
                if len(VOCAB_MAP[project.vocab.id].unigram_table) == 0:
                    return HttpResponseServerError('Vocab is missing the unigram table. On the vocab instance '
                                                   'use vocab.make_unigram_table() to build')
            else:
                return HttpResponseServerError(e.message)

    # Add cuis to filter if they did not exist
    cuis = []

    if project.cuis_file is not None and project.cuis_file:
        cuis = cuis + json.load(open(project.cuis_file.path))
    if project.cuis is not None and project.cuis:
        cuis = cuis + [str(cui).strip() for cui in project.cuis.split(",")]

    cuis = set(cuis) # Convert to set, only cuis
    if cuis:
        anns = AnnotatedEntity.objects.filter(project=project, document=document, validated=True)
        doc_cuis = [ann.entity.label for ann in anns]

        for cui in doc_cuis:
            if cui not in cuis:
                if project.cuis:
                    project.cuis = project.cuis + "," + str(cui)
                else:
                    project.cuis = str(cui)
                project.save()
                # Add this cui so we do not repeat things
                cuis.add(cui)

    return Response({'message': 'Document submited successfully'})


@api_view(http_method_names=['POST'])
def save_models(request):
    # Get project id
    p_id = request.data['project_id']
    project = ProjectAnnotateEntities.objects.get(id=p_id)
    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)

    cat.cdb.save(project.concept_db.cdb_file.path)

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


@api_view(http_method_names=['GET', 'POST'])
def update_meta_annotation(request):

    project_id = request.data['project_id']
    entity_id = request.data['entity_id']
    document_id = request.data['document_id']
    meta_task_id = request.data['meta_task_id']
    meta_task_value = request.data['meta_task_value']

    annotation = AnnotatedEntity.objects.filter(project= project_id, entity=entity_id, document=document_id)[0]
    annotation.correct = True
    annotation.validated = True
    log.debug(annotation)

    annotation.save()

    meta_task = MetaTask.objects.filter(id = meta_task_id)[0]
    meta_task_value = MetaTaskValue.objects.filter(id = meta_task_value)[0]

    meta_annotation_list = MetaAnnotation.objects.filter(annotated_entity = annotation)

    log.debug(meta_annotation_list)

    if len(meta_annotation_list) > 0:
        meta_annotation = meta_annotation_list[0]

        meta_annotation.meta_task = meta_task
        meta_annotation.meta_task_value = meta_task_value

    else:
        meta_annotation = MetaAnnotation()
        meta_annotation.annotated_entity = annotation
        meta_annotation.meta_task = meta_task
        meta_annotation.meta_task_value = meta_task_value

    log.debug(meta_annotation)
    meta_annotation.save()

    return Response({'meta_annotation': 'added meta annotation'})


@api_view(http_method_names=['POST'])
def annotate_text(request):
    p_id = request.data['project_id']
    message = request.data['message']
    cuis = request.data['cuis']
    if message is None or p_id is None:
        return HttpResponseBadRequest('No message to annotate')

    project = ProjectAnnotateEntities.objects.get(id=p_id)


    cat = get_medcat(CDB_MAP=CDB_MAP, VOCAB_MAP=VOCAB_MAP,
                     CAT_MAP=CAT_MAP, project=project)
    cat.config.linking['filters']['cuis'] = set(cuis)
    spacy_doc = cat(message)

    ents = []
    anno_tkns = []
    for ent in spacy_doc._.ents:
        cnt = Entity.objects.filter(label=ent._.cui).count()
        inc_ent = all(tkn not in anno_tkns for tkn in ent)
        if inc_ent and cnt != 0:
            anno_tkns.extend([tkn for tkn in ent])
            entity = Entity.objects.get(label=ent._.cui)
            ents.append({
                'entity': entity.id,
                'value': ent.text,
                'start_ind': ent.start_char,
                'end_ind': ent.end_char,
                'acc': ent._.context_similarity
            })

    ents.sort(key=lambda e: e['start_ind'])
    out = {'message': message, 'entities': ents}
    return Response(out)


@api_view(http_method_names=['GET'])
def download_annos(request):
    user = request.user
    if not user.is_superuser:
        return HttpResponseBadRequest('User is not super user, and not allowed to download project outputs')

    p_ids = str(request.GET['project_ids']).split(',')
    with_text_flag = request.GET.get('with_text', False)

    if p_ids is None or len(p_ids) == 0:
        return HttpResponseBadRequest('No projects to download annotations')

    projects = ProjectAnnotateEntities.objects.filter(id__in=p_ids)
    out = download_projects_with_text(projects) if with_text_flag else \
        download_projects_without_text(projects)
    return out


@api_view(http_method_names=['GET'])
def download_deployment(request):
    user = request.user
    if not user.is_superuser:
        return HttpResponseBadRequest('User is not super user, and not allowed to download a deployment')
    data_only = request.GET.get('data_only', False)
    return download_deployment_export(data_only)


@api_view(http_method_names=['GET'])
def behind_reverse_proxy(request):
    return Response(bool(int(os.environ.get('BEHIND_RP', False))))
