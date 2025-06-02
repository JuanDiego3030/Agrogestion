from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('usuarios/', views.gestion_usuarios, name='gestion_admin_usuarios'),
]