import copy
import logging
from datetime import datetime

from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from io import StringIO
import json
from background_task import background

from django.contrib import admin
from rest_framework.exceptions import PermissionDenied

from .models import *
from .forms import *


# Register your models here.
#from .utils import set_icd_info_objects, set_opcs_info_objects

admin.site.register(Entity)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)


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
    return download_projects_without_text(projects)


def download_projects_without_text(projects):

    all_projects_out = {'projects': []}
    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['tuis'] = project.tuis
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


def download(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    projects = queryset
    return download_projects_with_text(projects)


def download_projects_with_text(projects: QuerySet):
    all_projects_out = {'projects': []}

    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['tuis'] = project.tuis
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
            out_doc['last_modified'] = str(doc.last_modified)
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

    f_name = "MedCAT_Export_With_Text_{}.json".format(datetime.now().strftime('%Y-%m-%d:%H:%M:%S'))
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)

    return response


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


class DatasetAdmin(ReportErrorModelAdminMixin, admin.ModelAdmin):
    model = Dataset
admin.site.register(Dataset, DatasetAdmin)


class ProjectAnnotateEntitiesAdmin(admin.ModelAdmin):
    model = ProjectAnnotateEntities
    actions = [download, download_without_text, reset_project, clone_projects]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "concept_db":
            kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=True)
        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "cdb_search_filter":
            #kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=False)
            kwargs["queryset"] = ConceptDB.objects.all()

        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
admin.site.register(ProjectAnnotateEntities, ProjectAnnotateEntitiesAdmin)


class AnnotatedEntityAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'entity', 'value', 'deleted', 'validated')
    list_filter = ('user', 'project', 'deleted', 'validated')
    model = AnnotatedEntity
admin.site.register(AnnotatedEntity, AnnotatedEntityAdmin)


@background(schedule=5)
def _import_concepts(id):
    from medcat.cdb import CDB
    concept_db = ConceptDB.objects.get(id=id)
    cdb = CDB.load(concept_db.cdb_file.path)

    # Get all existing cuis for this CDB
    existing_cuis = set(Concept.objects.filter(cdb=id).values_list('cui', flat=True))

    for cui in cdb.cui2names.keys():
        if cui not in existing_cuis:
            concept = Concept()
            concept.pretty_name = cdb.cui2preferred_name.get(cui, cui)
            concept.cui = cui
            concept.tui = list(cdb.cui2type_ids.get(cui, ''))
            concept.semantic_type = [cdb.addl_info['type_id2name'].get(tui, '') for tui in list(cdb.cui2type_ids.get(cui, ''))]
            concept.desc = cdb.addl_info['cui2description'].get(cui, '')
            concept.synonyms = ", ".join(cdb.addl_info['cui2original_names'].get(cui, []))
            concept.cdb = concept_db
            concept.save()
            #set_icd_info_objects(cdb, concept, cui)
            #set_opcs_info_objects(cdb, concept, cui)


@background(schedule=5)
def _reset_cdb_filters(id):
    from medcat.cdb import CDB
    concept_db = ConceptDB.objects.get(id=id)
    cdb = CDB.load(concept_db.cdb_file.path)
    cdb.config.linking['filters'] = {'cuis': set()}
    cdb.save(concept_db.cdb_file.path)


def reset_cdb_filters(modeladmin, request, queryset)
    for concept_db in queryset:
        _reset_cdb_filters(concept_db.id)


def import_concepts(modeladmin, request, queryset):
    for concept_db in queryset:
        _import_concepts(concept_db.id)


def delete_concepts_from_cdb(modeladmin, request, queryset):
    for concept_db in queryset:
        Concept.objects.filter(cdb=concept_db).delete()
        ICDCode.objects.filter(cdb=concept_db).delete()
        OPCSCode.objects.filter(cdb=concept_db).delete()


class ConceptDBAdmin(admin.ModelAdmin):
    model = ConceptDB
    actions = [import_concepts, delete_concepts_from_cdb, reset_cdb_filters]

admin.site.register(ConceptDB, ConceptDBAdmin)


def remove_all_concepts(modeladmin, request, queryset):
    Concept.objects.all().delete()


class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    list_filter = ('cdb',)
    actions = [remove_all_concepts]


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
    list_display = ['name', 'create_time', 'dataset', 'last_modified']

admin.site.register(Document, DocumentAdmin)
