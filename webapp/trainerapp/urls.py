from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('train/<int:id>', train, name='train'),
    path('save/<int:id>', train_save, name='save'),
    path('upload/<int:id>', upload, name='upload')
]
