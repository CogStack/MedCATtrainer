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
import api.views


router = routers.DefaultRouter()
router.register(r'users', api.views.UserViewSet)
router.register(r'entities', api.views.EntityViewSet)
router.register(r'project-annotate-entities', api.views.ProjectAnnotateEntitiesViewSet)
router.register(r'documents', api.views.DocumentViewSet)
router.register(r'annotated-entities', api.views.AnnotatedEntityViewSet)
router.register(r'meta-annotations', api.views.MetaAnnotationViewSet)
router.register(r'meta-tasks', api.views.MetaTaskViewSet)
router.register(r'meta-task-values', api.views.MetaTaskValueViewSet)
router.register(r'relations', api.views.RelationViewSet)
router.register(r'entity-relations', api.views.EntityRelationViewSet)
router.register(r'concept-dbs', api.views.ConceptDBViewSet)
router.register(r'vocabs', api.views.VocabularyViewSet)
router.register(r'datasets', api.views.DatasetViewSet)
router.register(r'icd-codes', api.views.ICDCodeViewSet)
router.register(r'opcs-codes', api.views.OPCSCodeViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/search-concepts/', api.views.search_solr),
    path('api/prepare-documents/', api.views.prepare_documents),
    path('api/api-token-auth/', auth_views.obtain_auth_token),
    path('admin/', admin.site.urls),
    path('api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/add-annotation/', api.views.add_annotation),
    path('api/add-concept/', api.views.add_concept),
    path('api/import-cdb-concepts/', api.views.import_cdb_concepts),
    path('api/submit-document/', api.views.submit_document),
    path('api/save-models/', api.views.save_models),
    path('api/get-create-entity/', api.views.get_create_entity),
    path('api/create-dataset/', api.views.create_dataset),
    path('api/complete-projects/', api.views.finished_projects),
    path('api/update-meta-annotation/', api.views.update_meta_annotation),
    path('api/annotate-text/', api.views.annotate_text),
    path('api/download-annos/', api.views.download_annos),
    path('api/behind-rp/', api.views.behind_reverse_proxy),
    path('api/version/', api.views.version),
    path('api/concept-db-search-index-created/', api.views.concept_search_index_available),
    path('api/model-loaded/', api.views.model_loaded),
    path('api/cache-model/<int:p_id>/', api.views.cache_model),
    path('api/upload-deployment/', api.views.upload_deployment),
    path('api/metrics/', api.views.metrics),
    re_path('^.*$', api.views.index, name='index'),  # Match everything else to home
]
