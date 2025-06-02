from django.urls import path
from . import views

urlpatterns = [
    path('requisitores/requisiciones/', views.requisitores_requisiciones, name='requisitores_requisiciones'),
    path('requisitores/logout/', views.logout, name='requisitores_logout')
]