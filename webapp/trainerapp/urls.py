from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('train/<int:id>', train, name='train'),
    path('save/<int:id>', train_save, name='save'),
    path('upload/<int:id>', upload, name='upload'),
    path('incomplete/<int:id>', incomplete, name='incomplete'),
    path('download/<int:id>', download, name='download'),
]
