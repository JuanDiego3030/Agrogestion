from django.urls import path
from . import views

urlpatterns = [
    path('directivo/requisiciones/', views.directivos_requisiciones, name='directivos_requisiciones'),
    path('directivo/firmar/<int:req_id>/', views.firmar_requisicion, name='firmar_requisicion'),
    path('directivos/ordenes/', views.directivos_ordenes, name='directivos_ordenes'),
    path('directivos/firmar-orden/<int:orden_id>/', views.firmar_orden, name='firmar_orden'),
]