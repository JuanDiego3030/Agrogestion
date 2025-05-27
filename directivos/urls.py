from django.urls import path
from . import views

urlpatterns = [
    path('directivo/login/', views.directivos_login, name='directivos_login'),
    path('directivo/requisiciones/', views.directivos_requisiciones, name='directivos_requisiciones'),
    path('directivo/firmar/<int:req_id>/', views.firmar_requisicion, name='firmar_requisicion'),
]