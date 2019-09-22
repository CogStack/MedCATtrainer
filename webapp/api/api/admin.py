from django.contrib import admin
from .models import *
from .forms import *

# Register your models here.
admin.site.register(Concept)
admin.site.register(Link)
admin.site.register(MedCATModel)
admin.site.register(Dataset)
admin.site.register(Document)
admin.site.register(ProjectAnnotateEntities)
admin.site.register(Entity)
admin.site.register(AnnotatedEntity)
admin.site.register(ProjectMetaAnnotate)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)
admin.site.register(ConceptDB)
