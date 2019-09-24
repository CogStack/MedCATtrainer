from django.http import HttpResponse
from io import StringIO
import json

from django.contrib import admin
from .models import *
from .forms import *


# Register your models here.
admin.site.register(Concept)
admin.site.register(Link)
admin.site.register(MedCATModel)
admin.site.register(Dataset)
admin.site.register(Document)
admin.site.register(Entity)
admin.site.register(ProjectMetaAnnotate)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)
admin.site.register(ConceptDB)


def download(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    project = queryset[0]

    out = {}
    out['project'] = project.name
    out['documents'] = []

    for doc in project.validated_documents.all():
        out_doc = {}
        out_doc['name'] = doc.name
        out_doc['text'] = doc.text
        out_doc['annotations'] = []

        anns = AnnotatedEntity.objects.filter(project=project, document=doc,
                                              validated=True)
        for ann in anns:
            out_ann = {}
            out_ann['user'] = ann.user.username
            out_ann['cui'] = ann.entity.label
            out_ann['value'] = ann.value
            out_ann['start'] = ann.start_ind
            out_ann['end'] = ann.end_ind
            out_ann['deleted'] = ann.deleted
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
    actions = [download]
admin.site.register(ProjectAnnotateEntities, ProjectAnnotateEntitiesAdmin)

class AnnotatedEntityAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'document', 'entity', 'value', 'deleted', 'validated')
    list_filter = ('user', 'project', 'document', 'deleted', 'validated')
    model = AnnotatedEntity
admin.site.register(AnnotatedEntity, AnnotatedEntityAdmin)
