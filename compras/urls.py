from django.urls import path
from . import views

urlpatterns = [
    path('compras/login/', views.compras_login, name='compras_login'),
    path('compras/', views.compras, name='compras'),
    path('logout/', views.logout, name='logout'),
    path('compras/ver-pdf/<int:req_id>/', views.ver_pdf, name='ver_pdf'),
]