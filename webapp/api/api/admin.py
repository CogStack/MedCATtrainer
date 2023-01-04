import copy
import json
import logging
import re
import tarfile
from collections import defaultdict
from datetime import datetime
from glob import glob
from io import StringIO
from typing import Dict, List

import pandas as pd
import pkg_resources
import requests
from background_task import background
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import QuerySet, Q
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.exceptions import PermissionDenied

from core.settings import MEDIA_ROOT
from .forms import *
from .models import *

from .solr_utils import import_concepts_to_solr

admin.site.register(Entity)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)
admin.site.register(Relation)
admin.site.register(EntityRelation)

logger = logging.getLogger(__name__)


def reset_project(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    for project in queryset:
        # Remove all annotations and cascade to meta anns
        AnnotatedEntity.objects.filter(project=project).delete()

        # Remove cui_counts
        ProjectCuiCounter.objects.filter(project=project).delete()

        # Set all validated documents to none
        project.validated_documents.clear()


def download_without_text(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    return download_projects_without_text(projects, with_doc_name=False)


def download_without_text_with_doc_names(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    return download_projects_without_text(projects, with_doc_name=True)


def download_projects_without_text(projects, with_doc_name):

    all_projects_out = {'projects': []}
    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['documents'] = []

        if project.cuis_file is not None and project.cuis_file:
            # Add cuis from json file if it exists
            cuis_from_file = ",".join(json.load(open(project.cuis_file.path)))
            all_cuis = out['cuis'] + "," + cuis_from_file if len(out['cuis']) > 0 else cuis_from_file
            out['cuis'] = all_cuis

        for doc in project.validated_documents.all():
            out_doc = {}
            out_doc['id'] = doc.id
            out_doc['last_modified'] = str(doc.last_modified)
            out_doc['annotations'] = []
            if with_doc_name:
                out_doc['name'] = doc.name

            anns = AnnotatedEntity.objects.filter(project=project, document=doc)

            for ann in anns:
                out_ann = {}
                out_ann['id'] = ann.id
                out_ann['user'] = ann.user.username
                out_ann['validated'] = ann.validated
                out_ann['correct'] = ann.correct
                out_ann['deleted'] = ann.deleted
                out_ann['alternative'] = ann.alternative
                out_ann['killed'] = ann.killed
                out_ann['irrelevant'] = ann.irrelevant
                out_ann['last_modified'] = str(ann.last_modified)
                out_ann['manually_created'] = ann.manually_created
                out_ann['acc'] = ann.acc
                if ann.icd_code:
                    out_ann['icd_code'] = ann.icd_code.code
                if ann.opcs_code:
                    out_ann['opcs_code'] = ann.opcs_code.code
                out_ann['meta_anns'] = {}

                # Get MetaAnnotations
                meta_anns = MetaAnnotation.objects.filter(annotated_entity=ann)
                for meta_ann in meta_anns:
                    o_meta_ann = {}
                    o_meta_ann['name'] = meta_ann.meta_task.name
                    o_meta_ann['value'] = meta_ann.meta_task_value.name
                    o_meta_ann['acc'] = meta_ann.acc
                    o_meta_ann['validated'] = meta_ann.validated

                    # Add annotation
                    key = meta_ann.meta_task.name
                    out_ann['meta_anns'][key] = o_meta_ann

                out_doc['annotations'].append(out_ann)
            out['documents'].append(out_doc)
        all_projects_out['projects'].append(out)

    sio = StringIO()
    json.dump(all_projects_out, sio)
    sio.seek(0)

    f_name = "MedCAT_Export_No_Text_{}.json".format(datetime.now().strftime('%Y-%m-%d:%H:%M:%S'))
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)
    return response


_dt_fmt = '%Y-%m-%d::%H:%M-%z'


def upload_projects_export(medcat_export: Dict):
    for proj in medcat_export['projects']:
        p = ProjectAnnotateEntities()
        p.name = proj['name'] + ' IMPORTED'
        p.cuis = proj['cuis']

        # ensure current deployment has the neccessary - Entity, MetaTak, Relation, and warn on not present User objects.
        ent_labels, meta_tasks, rels, unavailable_users, available_users = set(), defaultdict(set), set(), set(), dict()
        for doc in proj['documents']:
            for anno in doc['annotations']:
                ent_labels.add(anno['cui'])
                for meta_anno in anno['meta_anns'].values():
                    meta_tasks[meta_anno['name']].add(meta_anno['value'])
                user_obj = User.objects.filter(username=anno['user']).first()
                if user_obj is None:
                    unavailable_users.add(anno['user'])
                elif anno['user'] not in available_users:
                    available_users[anno['user']] = user_obj
            for rel in doc.get('relations', []):
                rels.add(rel['relation'])
        # escape - filename
        ds_file_name = MEDIA_ROOT + '/' + re.sub('/|\.', '_', proj['name'] + '_dataset') + '.csv'
        names = [doc['name'] for doc in proj['documents']]
        if len(set(names)) != len(names):  # ensure names are unique for docs
            names = [f'{i} - {names[i]}' for i in range(len(names))]
        pd.DataFrame({'name': names,
                      'text': [doc['text'] for doc in proj['documents']]}).to_csv(ds_file_name)
        ds_mod = Dataset()
        ds_mod.original_file.name = ds_file_name
        ds_mod.save()
        p.dataset = ds_mod
        p.save()

        for u in unavailable_users:
            logger.warning(f'Username: {u} - not present in this trainer deployment.')
        for ent_lab in ent_labels:
            ent = Entity.objects.filter(label=ent_lab).first()
            if ent is None:
                ent = Entity()
                ent.label = ent_lab
                ent.save()
        for task in meta_tasks:
            if MetaTask.objects.filter(name=task).first() is None:
                m_task = MetaTask()
                m_task.name = task
                m_task.save()
        for rel in rels:
            if Relation.objects.filter(label=rel).first() is None:
                r = Relation()
                r.label = rel
                r.save()

        for doc in proj['documents']:
            doc_mod = Document.objects.filter(Q(dataset=ds_mod) & Q(text=doc['text'])).first()
            annos = []
            for anno in doc['annotations']:
                a = AnnotatedEntity()
                a.user = available_users[anno['user']]
                a.project = p
                a.document = doc_mod
                e = Entity.objects.get(label=anno['cui'])
                a.entity = e
                a.value = anno['value']
                a.start_ind = anno['start']
                a.end_ind = anno['end']
                a.validated = anno['validated']
                a.correct = anno['correct']
                a.deleted = anno['deleted']
                a.alternative = anno['alternative']
                a.killed = anno['killed']
                a.irrelevant = anno.get('irrelevant', False)  # Added later - so False by default for compatibility
                if anno.get('last_modified') is not None:
                    try:
                        a.last_modified = datetime.strptime(anno['last_modified'], '%Y-%m-%d:%H:%M:%S%z')
                    except ValueError:
                        a.last_modified = datetime.now()
                if anno.get('create_time') is not None:
                    try:
                        a.create_time = datetime.strptime(anno['create_time'], '%Y-%m-%d:%H:%M:%S%z')
                    except ValueError:
                        a.create_time = datetime.now()
                a.comment = anno.get('comment')
                a.manually_created = anno['manually_created']

                a.acc = anno['acc']
                a.save()
                annos.append(a)
                for task_name, meta_anno in anno['meta_anns'].items():
                    m_a = MetaAnnotation()
                    m_a.annotated_entity = a
                    m_a = MetaTask.objects.get(name=task_name)
                    m_a.validated = meta_anno['validated']
                    m_a.save()
                    # missing acc on the model
            anno_to_doc_ind = {a.start_ind: a for a in annos}

            for relation in doc.get('relations', []):
                er = EntityRelation()
                er.user = available_users[relation['user']]
                er.project = p
                er.document = doc_mod
                er.relation = Relation.objects.get(label=relation['relation'])
                er.validated = er.validated
                # link relations with start and end anno ents
                er.start_entity = anno_to_doc_ind[relation['start_entity_start_idx']]
                er.end_entity = anno_to_doc_ind[relation['end_entity_start_idx']]
                try:
                    er.create_time = datetime.strptime(relation['create_time'], '%Y-%m-%d:%H:%M:%S%z')
                except ValueError:
                    er.create_time = datetime.now()
                try:
                    er.last_modified = datetime.strptime(relation['last_modified_time'], '%Y-%m-%d:%H:%M:%S%z')
                except ValueError:
                    er.last_modified = datetime.now()
                er.save()
        logger.info(f"Finished annotation import for project {proj['name']}")
    logger.info('Finished importing all projects')


def download(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    projects = queryset
    return download_projects_with_text(projects)


def download_projects_with_text(projects: QuerySet):
    all_projects = _retrieve_project_data(projects)

    sio = StringIO()
    json.dump(all_projects, sio)
    sio.seek(0)

    f_name = "MedCAT_Export_With_Text_{}.json".format(datetime.now().strftime('%Y-%m-%d:%H:%M:%S'))
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)

    return response


def _retrieve_project_data(projects: QuerySet) -> Dict[str, List]:
    """
    A function to convert a list of projects and:
        - their associated documents,
        - their associated annotations,
        - their associated Meta annotations and Relation Annotations
    for serialization.
    Output schema is as follows: ((optional) indicates this field isn't required for training a MedCAT model)
    {
    "projects": [
        {
            "name": "<project_name"  # name of the project
            "id": "<id>"  # the auto-generated id of the project (optional)
            "cuis": ["cui_1", "cui_2" ... ]  # the CUI filter for the project, includes those from file / and text-box
            "documents": [
                {
                "id": "<id>"  # the auto-generated id of the document (optional)
                "name": "<name>"  # the name of the document (optional), but used in stat printing during training
                "text": "<text>"  # the text of the document
                "last_modified": "<date time>"  # the last modified-time (optional)
                "annotations": [{
                    "id": "<id>"  # the auto-generated id of the document (optional)
                    "name": "<username string>"  # the user who made the annotation (optional)
                    "cui": "<cui string>"  # the cui label for this annotation
                    "value": "<string>"  # the text span for this annotation
                    "start": <integer>  # the start index of this annotation with respect to the document text
                    "end": <integer>  # the end index of this annotation with respect to the document text
                    "validated": <boolean>  # if the annotation has been marked by a human annotator
                    "correct": <boolean>  # if the text span is correctly linked to the CUI of this annotation
                    "deleted": <boolean>  # if the text span was incorrectly linked or 'not' linked by MedCAT due to low scores
                    "alternative": <boolean>  # if the text span was incorrectly linked by MedCAT, then correctly linked by a human annotator
                    "killed":  <boolean>  # if a human annotator 'terminated' this annotation
                    "irrelevant": <boolean>  # if a human annotator has marked an annotation as irrelevant (optional)
                    "acc": <float>  # accuracy provided by MedCAT (optional)
                    "comment": "<comment string>" # the text entered by an annotator during annotation (optional)
                    "meta_anns": [
                        # list of meta annotations if applicable to project
                        {
                            "name": <string>  # Meta anno task name, i.e. temporality
                            "value": <string>  # the selected meta anno task value for, ie. "past" or "present"
                            "acc":  <float>   # default 1, (optional)
                            "validated": <boolean>  # Meta annotation has been made by a human annotator, default (true)
                        },
                        ... <more meta annotations of the same as above structure>
                    ]},
                    ... <more annotations of the same above structure>
                ]
                "relations": [
                    {
                        "start_entity": <integer>  # id of above annotation that is the start of this relation
                        "start_entity_cui": "<string>" # the cui label of the start of this relation
                        "start_entity_value": <string>  # value of the start annotation for this relation
                        "start_entity_start_idx": <integer>  # start index of text span of start of relation
                        "start_entity_end_idx": <integer>  # end index of text span of start of relation
                        "end_entity": <integer>  # id of the above annotation that is the end of this relation
                        "end_entity_cui": "<string>" # the cui label of the end of this relation
                        "end_entity_value": <string>  # value of the end annotation for this relation
                        "end_entity_start_idx": <integer>  # end index of text span of end of relation
                        "end_entity_end_idx": <integer>  # end index of text span of end of relation
                        "user": <string>  # username of annotator for relation (optional)
                        "relation": <string>  # label for this relation
                        "validated": <boolean>  # if the annotation has been validated by a human annotator, default true.
                    }
                    ... < more relations of the samve above structure>
                ]

                ... <more documents of the same above structure>
            ]
    ]
    }

    Args:
        projects (QuerySet): the projects to export data for.
    """
    all_projects = {'projects': []}
    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['documents'] = []

        if project.cuis_file is not None and project.cuis_file:
            # Add cuis from json file if it exists
            cuis_from_file = ",".join(json.load(open(project.cuis_file.path)))
            all_cuis = out['cuis'] + "," + cuis_from_file if len(out['cuis']) > 0 else cuis_from_file
            out['cuis'] = all_cuis

        for doc in project.validated_documents.all():
            out_doc = {}
            out_doc['id'] = doc.id
            out_doc['name'] = doc.name
            out_doc['text'] = doc.text
            out_doc['last_modified'] = doc.last_modified.strftime('%Y-%m-%d:%H:%M:%S')
            out_doc['annotations'] = []

            anns = AnnotatedEntity.objects.filter(project=project, document=doc)

            for ann in anns:
                out_ann = {}
                out_ann['id'] = ann.id
                out_ann['user'] = ann.user.username
                out_ann['cui'] = ann.entity.label
                out_ann['value'] = ann.value
                out_ann['start'] = ann.start_ind
                out_ann['end'] = ann.end_ind
                out_ann['validated'] = ann.validated
                out_ann['correct'] = ann.correct
                out_ann['deleted'] = ann.deleted
                out_ann['alternative'] = ann.alternative
                out_ann['killed'] = ann.killed
                out_ann['irrelevant'] = ann.irrelevant
                out_ann['create_time'] = ann.create_time
                out_ann['last_modified'] = ann.last_modified.strftime('%Y-%m-%d:%H:%M:%S')
                out_ann['comment'] = ann.comment
                out_ann['manually_created'] = ann.manually_created
                # if ann.icd_code:
                #     out_ann['icd_code'] = {'code': ann.icd_code.code, 'desc': ann.icd_code.desc}
                # if ann.opcs_code:
                #     out_ann['opcs_codes'] = {'code': ann.opcs_code, 'desc': ann.opcs_code.desc}
                #
                # out_ann['acc'] = ann.acc
                # if ann.comment:
                #     out_ann['comment'] = ann.comment
                # if ann.icd_code:
                #     out_ann['icd_code'] = ann.icd_code.code
                # if ann.opcs_code:
                #     out_ann['opcs_code'] = ann.opcs_code.code
                out_ann['meta_anns'] = {}

                # Get MetaAnnotations
                meta_anns = MetaAnnotation.objects.filter(annotated_entity=ann)
                for meta_ann in meta_anns:
                    o_meta_ann = {}
                    o_meta_ann['name'] = meta_ann.meta_task.name
                    o_meta_ann['value'] = meta_ann.meta_task_value.name
                    o_meta_ann['acc'] = meta_ann.acc
                    o_meta_ann['validated'] = meta_ann.validated

                    # Add annotation
                    key = meta_ann.meta_task.name
                    out_ann['meta_anns'][key] = o_meta_ann

                out_doc['annotations'].append(out_ann)

            # Add relations if they exist
            rels = EntityRelation.objects.filter(project=project, document=doc)
            out_rels = []
            out_rel = {}
            for rel in rels:
                out_rel['start_entity'] = rel.start_entity.id
                out_rel['start_entity_cui'] = rel.start_entity.entity.label
                out_rel['start_entity_value'] = rel.start_entity.value
                out_rel['start_entity_start_idx'] = rel.start_entity.start_ind
                out_rel['start_entity_end_idx'] = rel.start_entity.end_ind
                out_rel['end_entity'] = rel.end_entity.id
                out_rel['end_entity_cui'] = rel.end_entity.entity.label
                out_rel['end_entity_value'] = rel.end_entity.value
                out_rel['end_entity_start_idx'] = rel.end_entity.start_ind
                out_rel['end_entity_end_idx'] = rel.end_entity.end_ind
                out_rel['user'] = rel.user.username
                out_rel['relation'] = rel.relation.label
                out_rel['validated'] = rel.validated

                out_rels.append(out_rel)
                out_rel = {}
            out_doc['relations'] = out_rels

            out['documents'].append(out_doc)
        all_projects['projects'].append(out)
    return all_projects


def clone_projects(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    for project in projects:
        project_copy = copy.copy(project)
        project_copy.id = None
        project_copy.pk = None
        project_copy.name = f'{project.name} (Clone)'
        project_copy.save()

        # Add M2M fields
        for m in project.members.all():
            project_copy.members.add(m)
        for c in project.cdb_search_filter.all():
            project_copy.cdb_search_filter.add(c)
        for t in project.tasks.all():
            project_copy.tasks.add(t)

        project_copy.save()


class ReportErrorModelAdminMixin:
    """Mixin to catch all errors in the Django Admin and map them to user-visible errors."""
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.message_user(request, f'Error with previous action: {e}', level=logging.ERROR)
            return HttpResponseRedirect(request.path)


def dataset_document_counts(dataset):
    return f'{Document.objects.filter(dataset=dataset).count()}'


dataset_document_counts.short_description = 'Document Count'


class DatasetAdmin(ReportErrorModelAdminMixin, admin.ModelAdmin):
    model = Dataset
    form = DatasetForm
    list_display = ['name', 'create_time', 'description', dataset_document_counts]


admin.site.register(Dataset, DatasetAdmin)
class ProjectAnnotateEntitiesAdmin(admin.ModelAdmin):
    model = ProjectAnnotateEntities
    actions = [download, download_without_text, download_without_text_with_doc_names, reset_project, clone_projects]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'concept_db':
            kwargs['queryset'] = ConceptDB.objects.filter(use_for_training=True)
        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'cdb_search_filter':
            kwargs['queryset'] = ConceptDB.objects.all()
        if db_field.name == 'validated_documents':
            project_id = request.path.replace('/admin/api/projectannotateentities/', '').split('/')[0]
            try:
                proj = ProjectAnnotateEntities.objects.get(id=int(project_id))
                kwargs['queryset'] = Document.objects.filter(dataset=proj.dataset.id)
            except ValueError:  # a blank project has no validated_documents
                kwargs['queryset'] = Document.objects.none()
        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(ProjectAnnotateEntities, ProjectAnnotateEntitiesAdmin)


class AnnotatedEntityAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'entity', 'value', 'deleted', 'validated')
    list_filter = ('user', 'project', 'deleted', 'validated')
    model = AnnotatedEntity
admin.site.register(AnnotatedEntity, AnnotatedEntityAdmin)


@background(schedule=5)
def _reset_cdb_filters(id):
    from medcat.cdb import CDB
    concept_db = ConceptDB.objects.get(id=id)
    cdb = CDB.load(concept_db.cdb_file.path)
    cdb.config.linking['filters'] = {'cuis': set()}
    cdb.save(concept_db.cdb_file.path)


@background(schedule=5)
def import_concepts_from_cdb(cdb_model_id: int):
    from medcat.cdb import CDB

    cdb_model = ConceptDB.objects.get(id=cdb_model_id)
    cdb = CDB.load(cdb_model.cdb_file.path)

    import_concepts_to_solr(cdb, cdb_model)


def reset_cdb_filters(modeladmin, request, queryset):
    for concept_db in queryset:
        _reset_cdb_filters(concept_db.id)


def import_concepts(modeladmin, request, queryset):
    for concept_db in queryset:
        logger.info(f'Importing concepts for collection {concept_db.name}_id_{concept_db.id}')
        import_concepts_from_cdb(concept_db.id)


def delete_concepts_from_cdb(modeladmin, request, queryset):
    for concept_db in queryset:
        Concept.objects.filter(cdb=concept_db).delete()
        ICDCode.objects.filter(cdb=concept_db).delete()
        OPCSCode.objects.filter(cdb=concept_db).delete()


class ConceptDBAdmin(admin.ModelAdmin):
    model = ConceptDB
    actions = [import_concepts, delete_concepts_from_cdb, reset_cdb_filters]

admin.site.register(ConceptDB, ConceptDBAdmin)


def delete_selected(modeladmin, request, queryset):
    queryset.delete()


class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    list_filter = ('cdb',)
    actions = [delete_selected]


admin.site.register(Concept, ConceptAdmin)
admin.site.register(ICDCode)
admin.site.register(OPCSCode)


class ProjectCuiCounterAdmin(admin.ModelAdmin):
    model = ProjectCuiCounter
    list_filter = ('project',)
    list_display = ['entity', 'count', 'project']
admin.site.register(ProjectCuiCounter, ProjectCuiCounterAdmin)


def remove_all_documents(modeladmin, request, queryset):
    Document.objects.all().delete()


class DocumentAdmin(admin.ModelAdmin):
    model = Document
    actions = [remove_all_documents]
    list_filter = ('dataset',)
    list_display = ['name', 'create_time', 'dataset', 'last_modified']


admin.site.register(Document, DocumentAdmin)
