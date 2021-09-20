"""MedCATtrainer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.authtoken import views as auth_views
from rest_framework import routers

from api import views

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
router.register('concepts', views.ConceptViewSet)
router.register('entities', views.EntityViewSet)
router.register('project-annotate-entities', views.ProjectAnnotateEntitiesViewSet)
router.register('project-annotate-documents', views.ProjectAnnotateDocumentsViewSet)
router.register('documents', views.DocumentViewSet)
router.register('annotations', views.AnnotationViewSet)
router.register('annotated-entities', views.AnnotatedEntityViewSet)
router.register('document-annotation-tasks', views.DocumentAnnotationTaskViewSet)
router.register('document-annotation-cls-labels', views.DocumentAnnotationClassLabelViewSet)
router.register('document-annotation-values', views.DocumentAnnotationValueViewSet)
router.register('document-annotation-clf-values', views.DocumentAnnotationClfValueViewSet)
router.register('document-annotation-reg-values', views.DocumentAnnotationRegValueViewSet)
router.register('meta-annotations', views.MetaAnnotationViewSet)
router.register('meta-tasks', views.MetaTaskViewSet)
router.register('meta-task-values', views.MetaTaskValueViewSet)
router.register('relations', views.RelationViewSet)
router.register('entity-relations', views.EntityRelationViewSet)
router.register('concept-dbs', views.ConceptDBViewSet)
router.register('vocabs', views.VocabularyViewSet)
router.register('datasets', views.DatasetViewSet)
router.register('icd-codes', views.ICDCodeViewSet)
router.register('opcs-codes', views.OPCSCodeViewSet)
router.register('upload-deployment', views.DeploymentUploadViewSet, basename='upload')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/search-concepts/', views.ConceptView.as_view()),
    path('api/search-concept-infos/', views.search_concept_infos),
    path('api/prepare-documents/', views.prepare_documents),
    path('api/api-token-auth/', auth_views.obtain_auth_token),
    path('admin/', admin.site.urls),
    path('api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/add-annotation/', views.add_annotation),
    path('api/add-concept/', views.add_concept),
    path('api/submit-document/', views.submit_ent_anno_document),
    path('api/submit-doc-anno-document/', views.submit_doc_anno_document),
    path('api/save-models/', views.save_models),
    path('api/get-create-entity/', views.get_create_entity),
    path('api/create-dataset/', views.create_dataset),
    path('api/complete-projects/', views.finished_projects),
    path('api/annotate-text/', views.annotate_text),
    path('api/update-meta-annotation/', views.update_meta_annotation),
    path('api/annotate-text/', views.annotate_text),
    path('api/download-annos/', views.download_annos),
    path('api/download-deployment/', views.download_deployment),
    path('api/behind-rp/', views.behind_reverse_proxy),
    re_path('^.*$', views.index, name='index'),  # Match everything else to home
]
