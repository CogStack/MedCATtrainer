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
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework.authtoken import views as auth_views
from rest_framework import routers
import api.views
from django.conf.urls.static import static
from django.conf import settings

router = routers.DefaultRouter()
router.register(r'users', api.views.UserViewSet)
router.register(r'concepts', api.views.ConceptViewSet)
router.register(r'entities', api.views.EntityViewSet)
router.register(r'project-annotate-entities', api.views.ProjectAnnotateEntitiesViewSet)
router.register(r'annotated-entities', api.views.AnnotatedEntityViewSet)
router.register(r'documents', api.views.DocumentViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('search-concepts', api.views.ConceptView.as_view()),
    path('prepare-documents', api.views.prepare_documents),
    path('name-to-cuis', api.views.name2cuis),
    path('api-token-auth/', auth_views.obtain_auth_token),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('test', api.views.test),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
