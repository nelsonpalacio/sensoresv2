from django.urls import path
from sensores_app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('anomalias/', views.anomalias, name='anomalias'),  # Aquí cambiar anomalias_json por anomalias
     path('anomalias/data/', views.anomalias_data_json, name='anomalias_data_json'),
    path('prediccion/', views.prediccion, name='prediccion'),

]
