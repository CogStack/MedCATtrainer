from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('api', api, name='api'),
    path('train_usecase', train_usecase, name='train_usecase'),
    path('train_annotations', train_annotations, name='train_annotations'),
    path('add_concept_manual', add_concept_manual, name='add_concept_manual'),
    path('add_cntx', add_cntx, name='add_cntx'),
    path('train/<int:id>', train, name='train'),
    path('save/<int:id>', train_save, name='save'),
    path('upload/<int:id>', upload, name='upload'),
    path('incomplete/<int:id>', incomplete, name='incomplete'),
    path('download/<int:id>', download, name='download'),
]
