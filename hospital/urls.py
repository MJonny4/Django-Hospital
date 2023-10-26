from django.urls import path
from .views import index, register, login, logout, rol, pacient, metge, visites, llista_visites, vista_modificar, get_visita_per_modificar, vista_finalitzades, vista_consultar_agenda, consultar_pacients

urlpatterns = [
    path('', index),
    path('register/<str:login>', register),
    path('login', login),
    path('logout', logout),
    path('rol', rol),

    path('pacient', pacient),
    path('metge', metge),

    path('visites', visites),
    path('api/visites/<str:metge_dia>', llista_visites),

    path('modificar', vista_modificar),
    path('api/modificar/<str:dia>/<str:hora>/<str:metge>', get_visita_per_modificar),
    path('finalitzades', vista_finalitzades),

    path('agenda', vista_consultar_agenda),
    path('consultar', consultar_pacients),
]
