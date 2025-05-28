from django.urls import path, include

urlpatterns = [
    path('', include('compras.urls')),
    path('', include('directivos.urls')),
    path('', include('gestion_admin.urls')),
    path('', include('requisitores.urls')),
]