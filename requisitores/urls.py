from django.urls import path
from . import views

urlpatterns = [
    path('requisitores/login/', views.requisitores_login, name='requisitores_login'),
    path('requisitores/requisiciones/', views.requisitores_requisiciones, name='requisitores_requisiciones'),
    path('requisitores/logout/', views.logout, name='requisitores_logout')
]