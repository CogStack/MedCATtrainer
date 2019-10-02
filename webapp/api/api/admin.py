from django.http import HttpResponse
from io import StringIO
import json
from background_task import background

from django.contrib import admin
from .models import *
from .forms import *


# Register your models here.
admin.site.register(Dataset)
admin.site.register(Entity)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)


def download_without_text(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    project = queryset[0]

    out = {}
    out['name'] = project.name
    out['id'] = project.id
    out['tuis'] = project.tuis
    out['documents'] = []

    for doc in project.validated_documents.all():
        out_doc = {}
        out_doc['id'] = doc.id
        out_doc['last_modified'] = str(doc.last_modified)
        out_doc['annotations'] = []

        anns = AnnotatedEntity.objects.filter(project=project, document=doc,
                                              validated=True)
        for ann in anns:
            out_ann = {}
            out_ann['id'] = ann.id
            out_ann['user'] = ann.user.username
            out_ann['deleted'] = ann.deleted
            out_ann['alternative'] = ann.alternative
            out_ann['last_modified'] = str(ann.last_modified)
            out_ann['manually_created'] = ann.manually_created
            out_ann['acc'] = ann.acc
            out_doc['annotations'].append(out_ann)
        out['documents'].append(out_doc)

    sio = StringIO()
    json.dump(out, sio)
    sio.seek(0)

    f_name = "{}.json".format(project.name)
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)
    return response


def download(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    project = queryset[0]

    out = {}
    out['name'] = project.name
    out['id'] = project.id
    out['cuis'] = project.cuis
    out['tuis'] = project.tuis
    out['documents'] = []

    for doc in project.validated_documents.all():
        out_doc = {}
        out_doc['id'] = doc.id
        out_doc['name'] = doc.name
        out_doc['text'] = doc.text
        out_doc['last_modified'] = str(doc.last_modified)
        out_doc['annotations'] = []

        anns = AnnotatedEntity.objects.filter(project=project, document=doc,
                                              validated=True)
        for ann in anns:
            out_ann = {}
            out_ann['id'] = ann.id
            out_ann['user'] = ann.user.username
            out_ann['cui'] = ann.entity.label
            out_ann['value'] = ann.value
            out_ann['start'] = ann.start_ind
            out_ann['end'] = ann.end_ind
            out_ann['deleted'] = ann.deleted
            out_ann['alternative'] = ann.alternative
            out_ann['last_modified'] = str(ann.last_modified)
            out_ann['manually_created'] = ann.manually_created
            out_ann['acc'] = ann.acc
            out_doc['annotations'].append(out_ann)
        out['documents'].append(out_doc)

    sio = StringIO()
    json.dump(out, sio)
    sio.seek(0)

    f_name = "{}.json".format(project.name)
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)
    return response


class ProjectAnnotateEntitiesAdmin(admin.ModelAdmin):
    model = ProjectAnnotateEntities
    actions = [download, download_without_text]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "concept_db":
            kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=True)
        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "cdb_search_filter":
            kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=False)

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
    cdb = CDB()
    cdb.load_dict(concept_db.cdb_file.path)
    tuis = None

    for cui in cdb.cui2pretty_name:
        tui = cdb.cui2tui.get(cui, 'unk')
        if tuis is None or tui in tuis:
            concept = Concept()
            concept.pretty_name = cdb.cui2pretty_name.get(cui, '')
            concept.cui = cui
            concept.tui = tui
            concept.semantic_type = cdb.tui2name.get(tui, '')
            concept.desc = cdb.cui2desc.get(cui, '')
            concept.synonyms = ",".join(cdb.cui2original_names.get(cui, []))
            concept.cdb = concept_db
            icd10 = ''
            try:
                for pair in cdb.cui2info[cui]['icd10']:
                    icd10 += pair['chapter'] + " | " + pair['name']
                    icd10 += '\n'
                icd10.strip()
            except:
                pass
            concept.icd10 = icd10
            #concept.vocab = cdb.cui2ontos.get(cui, '')

            try:
                concept.save()
            except:
                pass


def import_concepts(modeladmin, request, queryset):
    for concept_db in queryset:
        _import_concepts(concept_db.id)

def delete_concepts_from_cdb(modeladmin, request, queryset):
    for concept_db in queryset:
        Concept.objects.filter(cdb=concept_db).delete()


class ConceptDBAdmin(admin.ModelAdmin):
    model = ConceptDB
    actions = [import_concepts, delete_concepts_from_cdb]
admin.site.register(ConceptDB, ConceptDBAdmin)


def remove_all_concepts(modeladmin, request, queryset):
    Concept.objects.all().delete()

class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    actions = [remove_all_concepts]
admin.site.register(Concept, ConceptAdmin)


def remove_all_documents(modeladmin, request, queryset):
    Document.objects.all().delete()

class DocumentAdmin(admin.ModelAdmin):
    model = Document
    actions = [remove_all_documents]
    list_display = ['name', 'create_time', 'dataset', 'last_modified']

admin.site.register(Document, DocumentAdmin)
