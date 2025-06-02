from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('requisiciones/', views.compras_requisiciones, name='compras_requisiciones'),
    path('ordenes/', views.compras_ordenes, name='compras_ordenes'),
    path('logout/', views.logout, name='logout'),
    path('ver-pdf/<str:doc_type>/<int:doc_id>/', views.ver_pdf, name='ver_pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)